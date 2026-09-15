"""Human-readable specs retain exact machine records without repeating payloads."""
# ruff: noqa: F811 -- imported pytest fixtures are requested by parameter name.

import copy
import json

from test_completion import designed, plan_experiment  # noqa: F401
from test_phase2 import investigation  # noqa: F401
from test_receipt_evidence import execute_receipt

from discovery.application.specification import prepare
from discovery.domain.completion import structure_hash


def rendered(env, tmp_path):
    snapshot = env["call"]("spec", "snapshot")["result"]
    result = prepare(tmp_path, snapshot, b"Scoped proposal for review.")
    files = {
        name: (tmp_path / artifact["storage_path"]).read_text()
        for name, artifact in result["files"].items()
    }
    return snapshot, result, files


def test_spec_summarizes_receipts_without_losing_payload_or_stale_detection(
    designed, monkeypatch, tmp_path
):
    env = designed
    _, artifact = execute_receipt(env, monkeypatch)
    snapshot, result, files = rendered(env, tmp_path / "rendered")
    text = files["technical-spec.md"]
    handoff = json.loads(files["handoff.json"])
    manifest = json.loads(files["evidence-manifest.json"])
    original = snapshot["experiment"][0]
    assert original["command_json"]
    assert handoff["traceability"]["experiment"][0] == original
    assert '"command_json"' not in text and '"environment_json"' not in text
    receipt = next(a for a in manifest["artifacts"] if a["artifact_id"] == artifact["id"])
    assert artifact["ref"] in text
    assert receipt["artifact_sha256"] in text and receipt["storage_path"] in text
    assert (env["root"] / receipt["storage_path"]).is_file()
    assert "relative to the original Discovery run directory" in text
    assert result["structure_sha256"] == structure_hash(snapshot)
    changed = copy.deepcopy(snapshot)
    changed["experiment"][0]["command_json"] = '["different-command"]'
    assert structure_hash(changed) != result["structure_sha256"]
    assert snapshot["experiment"][0] == original


def test_spec_labels_rejected_requirements_and_missing_receipt(designed, tmp_path):
    env = designed
    call = env["call"]
    other = call(
        "decision",
        "create",
        "--strategy",
        call("strategy", "list")["result"][0]["ref"],
        "--claim",
        env["claim"]["ref"],
        "--text",
        "Discarded approach",
        "--rationale",
        "An alternative",
        "--impact",
        "material",
    )["result"]
    rejected = call(
        "requirement",
        "create",
        "--decision",
        other["ref"],
        "--need",
        env["need"]["ref"],
        "--text",
        "Historical acceptance rule",
        "--acceptance",
        "Old rule",
        "--verification",
        "Historical probe",
    )["result"]
    call("decision", "reject", other["ref"], "--reason", "Alternative discarded")
    plan_experiment(env)
    _, _, files = rendered(env, tmp_path / "rendered")
    text = files["technical-spec.md"]
    current, history = text.split("### Historical rejected decisions", 1)
    assert "### Current accepted decisions" in current
    assert "Historical acceptance rule" not in current
    assert "Historical acceptance rule" in history and rejected["ref"] in history
    assert "not current acceptance work" in history and "; rejected)" in history
    assert "no execution receipt" in text and "planned" in text
    assert "```json" not in text
    handoff = json.loads(files["handoff.json"])
    assert any(
        r["requirement_text"] == "Historical acceptance rule" for r in handoff["requirements"]
    )


def test_renderer_owns_exactly_one_spec_title(designed, tmp_path):
    snapshot = designed["call"]("spec", "snapshot")["result"]
    result = prepare(
        tmp_path / "rendered",
        snapshot,
        b"# Authored duplicate title\n\n## Executive conclusion\n\nBuild the scoped change.",
    )
    artifact = result["files"]["technical-spec.md"]
    text = (tmp_path / "rendered" / artifact["storage_path"]).read_text()
    assert text.startswith("# Ordering discovery\n\n## Executive conclusion")
    assert "Authored duplicate title" not in text
    assert sum(line.startswith("# ") for line in text.splitlines()) == 1
