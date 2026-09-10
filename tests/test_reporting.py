import json
from pathlib import Path

from conftest import question


def test_blocked_report_preserves_questions_without_advancement_or_scoring(run):
    call = run["call"]
    question(call)
    before = call("audit", "verify")["result"]
    gate = call("phase", "check")["result"]
    result = call("report", "export")["result"]
    folder = Path(result["directory"])
    packet = json.loads((folder / "report.json").read_text())
    text = (folder / "report.md").read_text()
    assert packet["gate"] == {k: v for k, v in gate.items() if k != "reporting"}
    assert not gate["can_advance"]
    for status in (gate, call("status")["result"], call("resume")["result"]):
        assert status["reporting"]["available"]
        assert status["reporting"]["command"] == "report export"
        assert not status["reporting"]["requires_phase_completion"]
        assert not status["reporting"]["finalizes_run"]
    assert not packet["is_final_specification"]
    assert packet["confidence"]["score"] is None
    assert packet["confidence"]["status"] == "not_assessed"
    assert packet["state"]["clarification_question"][0]["question_status"] == "open"
    assert "Which ordering guarantee is required?" in text
    assert "attributed hypothesis" in text
    assert "BLOCKING_QUESTION_OPEN" in text
    assert "No claims registered" in text
    assert call("audit", "verify")["result"] == before
    assert call("report", "export")["result"] == result
    assert call("spec", "export", expected=2)["error"]["code"] == "SPEC_REQUIRED"
    call("question", "resolve", "Q-001", "--answer", "Fixture owner requires per-key ordering.")
    updated = call("report", "export")["result"]
    assert updated["directory"] != result["directory"]
    assert (folder / "report.json").read_text() == json.dumps(
        packet, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def test_report_observes_drift_without_rewriting_history(run):
    call = run["call"]
    before = call("report", "export")["result"]
    (run["source"] / "app.txt").write_text("changed after capture")
    after = call("report", "export")["result"]
    packet = json.loads((Path(after["directory"]) / "report.json").read_text())
    assert before["audit_head"] == after["audit_head"]
    assert before["snapshot_sha256"] != after["snapshot_sha256"]
    assert any(v["code"] == "SOURCE_DRIFT" for v in packet["gate"]["violations"])
    assert call("audit", "verify")["result"]["valid"]


def test_report_refuses_conflicting_file_or_symlink(run):
    call = run["call"]
    result = call("report", "export")["result"]
    folder = Path(result["directory"])
    path = folder / "report.md"
    original = path.read_bytes()
    path.write_text("user notes")
    assert call("report", "export", expected=2)["error"]["code"] == "EXPORT_CONFLICT"
    assert path.read_text() == "user notes"
    path.unlink()
    outside = run["root"].parent / "outside.md"
    outside.write_bytes(original)
    path.symlink_to(outside)
    assert call("report", "export", expected=2)["error"]["code"] == "EXPORT_CONFLICT"
    assert outside.read_bytes() == original


def test_wrong_phase_capture_does_not_leave_orphan_bytes(run):
    call = run["call"]
    before = call("audit", "verify")["result"]
    for index in range(2):
        file = run["root"].parent / f"rejected-{index}.txt"
        file.write_text(f"Unregistered source content {index}")
        result = call(
            "artifact", "capture", "--file", str(file), "--origin-uri", file.as_uri(), expected=2
        )
        assert result["error"]["code"] == "WRONG_PHASE"
        assert "research record" in result["error"]["message"]
    assert call("audit", "verify")["result"] == before


def test_capture_replays_after_regression_without_new_artifact(run):
    from conftest import ready

    from discovery.domain.encoding import uid

    call = run["call"]
    ready(run)
    call("phase", "advance")
    request = uid()
    file = run["source"] / "app.txt"
    args = (
        "artifact",
        "capture",
        "--file",
        str(file),
        "--origin-uri",
        file.as_uri(),
        "--source-backed",
    )
    first = call(*args, request=request)
    call(
        "phase", "regress", "--to", "1", "--reason", "Review intent again", "--cause", "need:RN-001"
    )
    before = call("audit", "verify")["result"]
    replay = call(*args, request=request)
    assert replay["replayed"] and replay["result"] == first["result"]
    assert call("audit", "verify")["result"] == before
