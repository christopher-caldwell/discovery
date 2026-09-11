import importlib.util
import json
import sys
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "isolated_run", Path(__file__).with_name("isolated_run.py")
)
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)


def test_copy_exclusions_and_symlinks_are_reported(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    (source / "code.py").write_text("source")
    (source / ".discovery").mkdir()
    (source / "tickets").mkdir()
    (source / "escape").symlink_to("/Users")
    omitted = harness.copy_source(source, tmp_path / "output")
    assert set(omitted) == {".discovery", "tickets", "escape"}
    assert [p.name for p in (tmp_path / "output").iterdir()] == ["code.py"]


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS Seatbelt integration")
def test_process_boundary_and_frozen_inputs(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    (work / "source").mkdir()
    (work / "ticket.md").write_text("ticket")
    hidden = tmp_path / "hidden"
    hidden.mkdir()
    sentinel = hidden / "answers.txt"
    sentinel.write_text("private answer")
    policy = harness.profile(
        [Path(p) for p in harness.SYSTEM_READ]
        + [work, Path(sys.executable).resolve().parent.parent],
        [work],
    )
    policy += (
        f"(deny file-write* (subpath {json.dumps(str(work / 'source'))}) "
        f"(literal {json.dumps(str(work / 'ticket.md'))}))"
    )
    sb = tmp_path / "boundary.sb"
    sb.write_text(policy)
    env = {
        "EVAL_PYTHON": str(Path(sys.executable).resolve()),
        "PATH": "/usr/bin:/bin",
        "HOME": str(work),
    }
    assert harness.probe(sb, env, work, [sentinel])["passed"]
    # Local services and app automation are unavailable through the same boundary.
    command = [
        str(Path(sys.executable).resolve()),
        "-c",
        'import socket; s=socket.socket(); s.connect(("127.0.0.1",443))',
    ]
    r = harness.boundary(sb, command, env, work, capture_output=True, text=True)
    assert r.returncode != 0
    assert "Operation not permitted" in r.stderr
    git = harness.boundary(
        sb, ["/usr/bin/git", "--version"], env, work, capture_output=True, text=True
    )
    assert git.returncode == 0, git.stderr


def test_existing_run_is_not_cleaned_up_and_new_failure_cleans_only_owned_auth(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace

    existing = tmp_path / "existing"
    auth = existing / "home/.codex/auth.json"
    auth.parent.mkdir(parents=True)
    auth.write_text("test sentinel, not a credential")
    with pytest.raises(FileExistsError):
        harness.prepare(SimpleNamespace(run_dir=existing))
    assert auth.read_text() == "test sentinel, not a credential"

    fresh = tmp_path / "fresh"

    def fail_after_copy(args, root):
        path = root / "home/.codex/auth.json"
        path.parent.mkdir(parents=True)
        path.write_text("new test sentinel")
        raise RuntimeError("injected preparation failure")

    monkeypatch.setattr(harness, "prepare_created", fail_after_copy)
    with pytest.raises(RuntimeError, match="injected"):
        harness.prepare(SimpleNamespace(run_dir=fresh))
    assert not (fresh / "home/.codex/auth.json").exists()
    assert auth.exists()


def recovery_fixture(tmp_path):
    import hashlib
    import sqlite3
    from types import SimpleNamespace

    old = tmp_path / "old-session"
    source, run = old / "work/source", old / "work/run"
    source.mkdir(parents=True)
    run.mkdir()
    ticket = old / "work/ticket.md"
    ticket.write_text("original ticket")
    (source / "source.py").write_text("print('source')")
    for p in (old / "work/outcome.md", old / "work/request.txt", old / "control/events.jsonl"):
        p.parent.mkdir(exist_ok=True)
        p.write_text("old operator chat must be denied")
    with sqlite3.connect(run / "discovery.sqlite") as db:
        db.executescript("""
        CREATE TABLE source_repository (repository_root TEXT);
        CREATE TABLE discovery_run (input_artifact_id INTEGER);
        CREATE TABLE artifact (artifact_id INTEGER, artifact_sha256 TEXT);
        INSERT INTO discovery_run VALUES (1);
        """)
        db.execute("INSERT INTO source_repository VALUES (?)", (str(source),))
        db.execute(
            "INSERT INTO artifact VALUES (1, ?)", (hashlib.sha256(ticket.read_bytes()).hexdigest(),)
        )
    return SimpleNamespace(resume_run=run, source=source, ticket=ticket)


def test_recovery_requires_original_source_and_ticket(tmp_path):
    args = recovery_fixture(tmp_path)
    assert harness.recovery_inputs(args) == (args.resume_run, args.source, args.ticket)
    args.ticket.write_text("replacement")
    with pytest.raises(ValueError, match="immutable input"):
        harness.recovery_inputs(args)


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS Seatbelt integration")
def test_recovery_boundary_permits_only_selected_durable_state(tmp_path):
    args = recovery_fixture(tmp_path)
    work = tmp_path / "new-session/work"
    work.mkdir(parents=True)
    sb = tmp_path / "resume.sb"
    policy = harness.profile(
        [Path(p) for p in harness.SYSTEM_READ]
        + [
            work,
            args.resume_run,
            args.source,
            args.ticket,
            Path(sys.executable).resolve().parent.parent,
        ],
        [work, args.resume_run],
    )
    sb.write_text(policy)
    env = {
        "EVAL_PYTHON": str(Path(sys.executable).resolve()),
        "PATH": "/usr/bin:/bin",
        "HOME": str(work),
    }
    old = args.resume_run.parent
    denied = [old / "outcome.md", old / "request.txt", old.parent / "control/events.jsonl"]
    result = harness.probe(sb, env, work, denied, args.source, args.ticket, args.resume_run)
    assert result["passed"]
    assert len(result["checks"]) == 3
    assert (args.source / "source.py").read_text() == "print('source')"
    assert not list(args.resume_run.glob("isolation-probe-*"))


def test_checkpoint_recovery_requires_real_denied_history(tmp_path, monkeypatch):
    checkpoint = tmp_path / "snapshot" / "run"
    checkpoint.mkdir(parents=True)
    with pytest.raises(ValueError, match="deny-probe"):
        harness.recovery_denial_probes(checkpoint, [tmp_path / "missing.md"])
    old_report = tmp_path / "old-report.md"
    old_report.write_text("Evaluator knowledge must not reach the resumed model")
    assert harness.recovery_denial_probes(checkpoint, [old_report]) == [old_report]
    monkeypatch.chdir(tmp_path)
    assert harness.recovery_denial_probes(checkpoint, [Path("old-report.md")]) == [old_report]
    (checkpoint.parent / "outcome.md").write_text("Prior session outcome")
    assert harness.recovery_denial_probes(checkpoint, []) == [checkpoint.parent / "outcome.md"]


def test_timing_preserves_partial_events_and_excludes_old_reports(tmp_path, monkeypatch):
    work = tmp_path / "work"
    control = tmp_path / "control"
    control.mkdir()
    old = work / ".discovery/runs/old/exports/reports/hash/report.md"
    old.parent.mkdir(parents=True)
    old.write_text("old report")
    clock = [100.0]
    monkeypatch.setattr(harness.time, "monotonic", lambda: clock[0])
    recorder = harness.TimingRecorder(tmp_path, {"work": str(work)}, 100.0)
    events = control / "events.jsonl"
    complete = b'{"type":"item.started","item":{"id":"one"}}\n'
    events.write_bytes(complete + b'{"type":')
    clock[0] = 101.0
    recorder.observe()
    assert recorder.index == 1
    assert recorder.first == {}
    report = work / ".discovery/runs/new/exports/reports/new/report.md"
    report.parent.mkdir(parents=True)
    report.touch()
    recorder.observe()
    assert recorder.first == {}
    report.write_text("candidate for human review")
    technical = work / "run/exports/spec/technical-spec.md"
    technical.parent.mkdir(parents=True)
    technical.write_text("technical specification candidate")
    with events.open("ab") as stream:
        stream.write(b'"item.completed"}\nunfinished')
    clock[0] = 102.0
    recorder.observe()
    recorder.observe(final=True)
    rows = [json.loads(line) for line in recorder.path.read_text().splitlines()]
    recorded = [r for r in rows if r["kind"] == "event"]
    assert [r["event_index"] for r in recorded] == [1, 2, 3]
    assert recorded[-1]["invalid_event"] is True
    assert sum(r["byte_length"] for r in recorded) == events.stat().st_size
    assert recorded[1]["byte_offset"] == len(complete)
    assert recorder.first["interim_report"]["observed_elapsed_seconds"] == 2
    assert recorder.first["interim_report"]["path"] == str(report)
    assert recorder.first["technical_specification"]["path"] == str(technical)


@pytest.mark.parametrize("timeout", [False, True])
def test_execute_records_live_delivery_and_keeps_timeout_cleanup(tmp_path, monkeypatch, timeout):
    import subprocess

    work = tmp_path / "work"
    (tmp_path / "control").mkdir()
    work.mkdir()
    (work / "request.txt").write_text("test input")
    auth = tmp_path / "home/.codex/auth.json"
    auth.parent.mkdir(parents=True)
    auth.write_text("test sentinel")
    # Exercise the real process/pipe/timeout loop without requiring model credentials.
    original_popen = subprocess.Popen
    monkeypatch.setattr(
        harness.subprocess, "Popen", lambda argv, **kw: original_popen(argv[3:], **kw)
    )
    script = """import sys, pathlib, time, json
assert sys.stdin.read() == 'test input'
print(json.dumps({'type': 'item.started'}), flush=True)
pathlib.Path('outcome.md').write_text('early candidate')
time.sleep(0.6)
print(json.dumps({'type': 'item.completed'}), flush=True)
"""
    manifest = {
        "work": str(work),
        "profile": "unused-test-profile",
        "env": dict(harness.os.environ),
        "command": [sys.executable, "-c", script],
        "timeout_seconds": 0.4 if timeout else 3,
    }
    harness.execute(tmp_path, manifest)
    result = json.loads((tmp_path / "control/result.json").read_text())
    assert result["timed_out"] is timeout
    assert result["timing"]["first_observed"]["outcome"]["observed_elapsed_seconds"] < 0.5
    assert result["timing"]["event_count"] == (1 if timeout else 2)
    assert result["exit_code"] != 0 if timeout else result["exit_code"] == 0
    assert not auth.exists()
    raw = (tmp_path / "control/events.jsonl").read_text()
    assert "observed_elapsed_seconds" not in raw
