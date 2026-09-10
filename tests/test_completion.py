import json
import sys

import pytest
from test_phase2 import argument, claim, closure, evidence, finish, investigation  # noqa: F401


@pytest.fixture
def designed(investigation):  # noqa: F811
    env = investigation
    if env["call"]("spec", "snapshot")["result"]["run"]["subagents_enabled"]:
        reconcile_empty_group(env, phase=2)
    c = claim(env)
    e = evidence(env)
    argument(env, c, e)
    closure(env)
    call = env["call"]
    call("claim", "evaluate", c["ref"])
    finish(env)
    call("phase", "advance")
    s = call(
        "strategy",
        "create",
        "--name",
        "Revision-aware consumer",
        "--description",
        "Compare revision before applying event",
    )["result"]
    call("strategy", "select", s["ref"], "--reason", "Supports ordering constraint")
    d = call(
        "decision",
        "create",
        "--strategy",
        s["ref"],
        "--claim",
        c["ref"],
        "--text",
        "Reject stale revisions",
        "--rationale",
        "Late retries must not regress state",
        "--impact",
        "material",
    )["result"]
    call("decision", "accept", d["ref"], "--reason", "Chosen implementation")
    o = call(
        "obligation",
        "create",
        "--decision",
        d["ref"],
        "--text",
        "Prove retry behavior",
        "--impact",
        "material",
        "--profile",
        "primary",
    )["result"]
    call("obligation", "attach-evidence", o["ref"], "--evidence-ref", e["ref"])
    call(
        "obligation",
        "satisfy",
        o["ref"],
        "--reason",
        "Fixture primary contract supplies required behavior",
    )
    call(
        "requirement",
        "create",
        "--decision",
        d["ref"],
        "--need",
        env["need"]["ref"],
        "--text",
        "Ignore old revisions",
        "--acceptance",
        "seq 2 then seq 1 retains state 2",
        "--verification",
        "Regression test plus idempotent duplicate delivery",
    )
    narrative = env["root"].parent / "narrative.md"
    narrative.write_text(
        "Implement a revision comparison and test duplicate and late delivery. "
        "Fictional fixture only."
    )
    return {
        **env,
        "decision": d,
        "obligation": o,
        "evidence": e,
        "claim": c,
        "narrative": narrative,
    }


def draft(env):
    return env["call"]("spec", "draft", "--narrative", str(env["narrative"]))["result"]


def test_proposed_material_decision_exposes_failed_proof_before_acceptance(designed):
    call = designed["call"]
    strategy = call("strategy", "list")["result"][0]["ref"]
    decision = call(
        "decision",
        "create",
        "--strategy",
        strategy,
        "--claim",
        designed["claim"]["ref"],
        "--text",
        "Classify duplicate failures",
        "--rationale",
        "Candidate to review",
        "--impact",
        "material",
    )["result"]["ref"]
    obligation = call(
        "obligation",
        "create",
        "--decision",
        decision,
        "--text",
        "Existing state must not hide an unrelated constraint failure",
        "--impact",
        "material",
        "--profile",
        "primary",
    )["result"]["ref"]
    call("obligation", "fail", obligation, "--reason", "A counterexample contradicts the candidate")
    gate = call("phase", "check")["result"]
    assert not gate["can_advance"]
    assert any(v["code"] == "DECISION_UNDECIDED" for v in gate["violations"])
    expected = {
        "code": "PROOF_UNSATISFIED",
        "message": "Existing state must not hide an unrelated constraint failure",
    }
    assert expected in gate["violations"]
    call("decision", "reject", decision, "--reason", "Discard the defeated candidate")
    assert expected not in call("phase", "check")["result"]["violations"]


def challenges(env):
    call = env["call"]
    checks = call("challenge", "initialize")["result"]["checks"]
    for c in checks:
        call(
            "challenge",
            "complete",
            c["ref"],
            "--disposition",
            "completed_no_finding",
            "--reason",
            "Synthetic adversarial check completed",
            "--report",
            str(env["narrative"]),
        )
    return checks


def test_complete_traversal_exports_and_final_replay(designed):
    env = designed
    call = env["call"]
    draft(env)
    assert call("phase", "advance")["result"]["phase"] == 4
    challenges(env)
    assert call("phase", "check")["result"]["can_advance"]
    from discovery.domain.encoding import uid

    request = uid()
    result = call("phase", "advance", request=request)["result"]
    assert result["status"] == "finalized"
    assert call("phase", "advance", request=request)["replayed"]
    assert (
        call(
            "strategy", "create", "--name", "Forbidden", "--description", "after final", expected=2
        )["error"]["code"]
        == "RUN_NOT_ACTIVE"
    )
    exports = call("spec", "export")["result"]
    from pathlib import Path

    handoff = json.loads((Path(exports["directory"]) / "handoff.json").read_text())
    assert (
        handoff["final"]
        and handoff["requirements"]
        and handoff["traceability"]["technical_decision_claim"]
    )
    assert call("audit", "verify")["result"]["valid"]
    assert call("resume")["result"]["status"] == "finalized"
    for gate in (
        call("phase", "check")["result"],
        call("status")["result"]["gate"],
    ):
        assert not gate["can_advance"]
        assert [v["code"] for v in gate["violations"]] == ["RUN_NOT_ACTIVE"]
    assert result["spec"]["assurance"]["overall"] == 100


def test_draft_staleness_and_revised_checklist(designed):
    env = designed
    call = env["call"]
    draft(env)
    call(
        "requirement",
        "create",
        "--decision",
        env["decision"]["ref"],
        "--need",
        env["need"]["ref"],
        "--text",
        "Observe rejected events",
        "--acceptance",
        "Count increments",
        "--verification",
        "Inspect metric",
    )
    assert "SPEC_STALE" in {v["code"] for v in call("phase", "check")["result"]["violations"]}
    draft(env)
    call("phase", "advance")
    challenges(env)
    call("spec", "revise", "--narrative", str(env["narrative"]))
    assert not call("phase", "check")["result"]["can_advance"]
    challenges(env)
    assert call("phase", "check")["result"]["can_advance"]


def test_defeater_requires_regression_and_distinct_resolution(designed):
    env = designed
    call = env["call"]
    draft(env)
    call("phase", "advance")
    check = call("challenge", "initialize")["result"]["checks"][0]
    d = call(
        "defeater",
        "create",
        "--check",
        check["ref"],
        "--decision",
        env["decision"]["ref"],
        "--evidence-ref",
        env["evidence"]["ref"],
        "--text",
        "Sequence reset breaks ordering",
        "--impact",
        "material",
    )["result"]
    call(
        "defeater",
        "accept-contextual-risk",
        d["ref"],
        "--reason",
        "Majority thinks fine",
        expected=2,
    )
    call("defeater", "confirm", d["ref"], "--reason", "Credible reset case")
    assert (
        call(
            "defeater",
            "defeat",
            d["ref"],
            "--evidence-ref",
            env["evidence"]["ref"],
            "--reason",
            "No change",
            "--report",
            str(env["narrative"]),
            expected=2,
        )["error"]["code"]
        == "REGRESSION_REQUIRED"
    )
    call(
        "phase",
        "regress",
        "--to",
        "3",
        "--cause",
        "defeater:" + d["ref"],
        "--reason",
        "Repair reset handling",
    )
    assert (
        call(
            "defeater",
            "defeat",
            d["ref"],
            "--evidence-ref",
            env["evidence"]["ref"],
            "--reason",
            "Self resolution",
            "--report",
            str(env["narrative"]),
            expected=2,
        )["error"]["code"]
        == "RESOLUTION_EVIDENCE_REQUIRED"
    )
    e = evidence(env, document="evidence/reproduction.md")
    call(
        "defeater",
        "defeat",
        d["ref"],
        "--evidence-ref",
        e["ref"],
        "--reason",
        "Synthetic additional evidence narrows valid sequence domain",
        "--report",
        str(env["narrative"]),
    )
    draft(env)
    call("phase", "advance")
    challenges(env)
    assert call("phase", "check")["result"]["can_advance"]

    call("evidence", "retract", e["ref"], "--reason", "Resolution evidence was withdrawn")
    assert call("defeater", "list")["result"][0]["defeater_status"] == "open"
    assert not call("phase", "check")["result"]["can_advance"]


def plan_experiment(env):
    return env["call"](
        "experiment",
        "plan",
        "--decision",
        env["decision"]["ref"],
        "--name",
        "Isolated proof",
        "--hypothesis",
        "Writes stay in the copy",
        "--procedure",
        "Execute deterministic Python snippet",
    )["result"]


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS Seatbelt execution adapter")
def test_experiment_isolation_replay_and_proof(designed):
    env = designed
    call = env["call"]
    experiment = plan_experiment(env)
    from discovery.domain.encoding import uid

    request = uid()
    command = json.dumps(
        [
            "/usr/bin/python3",
            "-c",
            'from pathlib import Path; Path("app.txt").write_text("copy changed"); '
            'print("proof passed")',
        ]
    )
    result = call("experiment", "exec", experiment["ref"], "--command", command, request=request)[
        "result"
    ]
    assert result["exit_code"] == 0 and (env["source"] / "app.txt").read_text() == "baseline"
    assert call("experiment", "exec", experiment["ref"], "--command", command, request=request)[
        "replayed"
    ]
    call(
        "experiment",
        "finish",
        experiment["ref"],
        "--outcome",
        "passed",
        "--conclusion",
        "Observed isolated result",
        "--limitations",
        "Synthetic local source only",
    )
    proof = call(
        "obligation",
        "create",
        "--decision",
        env["decision"]["ref"],
        "--text",
        "Empirical copy isolation",
        "--impact",
        "critical",
        "--profile",
        "empirical",
    )["result"]
    call(
        "obligation",
        "attach-experiment",
        proof["ref"],
        "--experiment",
        experiment["ref"],
    )
    call(
        "obligation",
        "satisfy",
        proof["ref"],
        "--reason",
        "Passed experiment registered",
    )
    assert call("audit", "verify")["result"]["valid"]


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS Seatbelt execution adapter")
def test_experiment_cannot_write_original_or_use_network(designed):
    env = designed
    call = env["call"]
    exp = plan_experiment(env)
    code = (
        f'from pathlib import Path; Path({str(env["source"] / "app.txt")!r}).write_text("corrupt")'
    )
    result = call(
        "experiment", "exec", exp["ref"], "--command", json.dumps(["/usr/bin/python3", "-c", code])
    )["result"]
    assert result["exit_code"] != 0 and (env["source"] / "app.txt").read_text() == "baseline"
    call(
        "experiment",
        "finish",
        exp["ref"],
        "--outcome",
        "passed",
        "--conclusion",
        "Pretend",
        "--limitations",
        "none",
        expected=2,
    )
    exp = plan_experiment(env)
    result = call(
        "experiment",
        "exec",
        exp["ref"],
        "--command",
        json.dumps(
            ["/usr/bin/python3", "-c", 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0))']
        ),
    )["result"]
    assert result["exit_code"] != 0


def test_interrupted_reservation_does_not_rerun(designed, monkeypatch):
    from discovery.application import experiments
    from discovery.domain.encoding import uid

    env = designed
    call = env["call"]
    exp = plan_experiment(env)
    request = uid()
    invocations = []

    def fail(*args):
        invocations.append(True)
        raise OSError("Injected interruption")

    monkeypatch.setattr(experiments, "run_process", fail)
    args = ("experiment", "exec", exp["ref"], "--command", '["/usr/bin/true"]')
    assert call(*args, request=request, expected=3)["error"]["code"] == "IO_ERROR"
    assert call(*args, request=request, expected=2)["error"]["code"] == "EXPERIMENT_INTERRUPTED"
    assert len(invocations) == 1
    call("experiment", "abort", exp["ref"], "--reason", "No receipt; process result unknown")
    replacement = plan_experiment(env)
    call(
        "experiment",
        "replace",
        exp["ref"],
        "--replacement",
        replacement["ref"],
        "--reason",
        "Fresh recorded attempt",
    )
    assert call("audit", "verify")["result"]["valid"]


def reconcile_empty_group(env, phase):
    import secrets

    from discovery.domain.encoding import uid

    call = env["call"]
    extra = ["--lane", env["lane"]["ref"]] if phase == 2 else []
    group = call("group", "dispatch", "--count", "2", *extra)["result"]
    report = env["root"].parent / "independent.md"
    report.write_text(
        "Independent synthetic review completed with no additional findings. Offline scope only."
    )
    for member in group["agents"]:
        actor = uid()
        token = secrets.token_hex(32)
        call("--lease", token, "agent", "start", member["ref"], identity=actor)
        call(
            "--lease",
            token,
            "agent",
            "complete",
            member["ref"],
            "--outcome",
            "no_findings",
            "--report",
            str(report),
            identity=actor,
        )
    call(
        "group",
        "reconcile",
        group["ref"],
        "--reason",
        "Both independent reports considered",
        "--report",
        str(report),
    )
    return group


@pytest.mark.parametrize("run", ["overlap"], indirect=True)
def test_overlap_gates_in_both_investigation_and_adversarial_phases(designed):
    env = designed
    call = env["call"]
    draft(env)
    call("phase", "advance")
    challenges(env)
    assert "CONSENSUS_INCOMPLETE" in {
        v["code"] for v in call("phase", "check")["result"]["violations"]
    }
    reconcile_empty_group(env, phase=4)
    assert call("phase", "advance")["result"]["status"] == "finalized"
    assert call("audit", "verify")["result"]["valid"]


def test_final_compilation_rechecks_adversarial_snapshot(designed, monkeypatch):
    from discovery.application import specification
    from discovery.domain.encoding import uid

    env = designed
    call = env["call"]
    draft(env)
    call("phase", "advance")
    challenges(env)
    original = specification.prepare

    def stale(*args, **kwargs):
        result = original(*args, **kwargs)
        if kwargs.get("final"):
            result["review_sha256"] = "0" * 64
        return result

    before = call("audit", "verify")["result"]["event_count"]
    monkeypatch.setattr(specification, "prepare", stale)
    assert call("phase", "advance", request=uid(), expected=2)["error"]["code"] == "SPEC_STALE"
    assert call("audit", "verify")["result"]["event_count"] == before
    assert call("status")["result"]["status"] == "active"


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS Seatbelt execution adapter")
def test_experiment_timeout_is_recorded_and_cannot_pass(designed):
    env = designed
    call = env["call"]
    exp = plan_experiment(env)
    result = call(
        "experiment",
        "exec",
        exp["ref"],
        "--timeout",
        "1",
        "--command",
        json.dumps(["/usr/bin/python3", "-c", "import time; time.sleep(10)"]),
    )["result"]
    assert result["timed_out"] and result["exit_code"] != 0
    call(
        "experiment",
        "finish",
        exp["ref"],
        "--outcome",
        "passed",
        "--conclusion",
        "Not actually completed",
        "--limitations",
        "Timed out",
        expected=2,
    )
    assert call("audit", "verify")["result"]["valid"]


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS Seatbelt execution adapter")
def test_killed_cli_reservation_recovers_without_duplicate_execution(designed):
    import os
    import signal
    import subprocess
    import time

    from discovery.domain.encoding import uid

    env = designed
    call = env["call"]
    experiment = plan_experiment(env)
    request = uid()
    command = json.dumps(
        [
            "/usr/bin/python3",
            "-c",
            "import os,time; from pathlib import Path; "
            'p=Path("invocations.txt"); '
            'p.write_text(p.read_text()+"run\\n" if p.exists() else "run\\n"); '
            'Path("ready.tmp").write_text(str(os.getpid())); '
            'Path("ready.tmp").rename("ready.pid"); time.sleep(30)',
        ]
    )
    args = ("experiment", "exec", experiment["ref"], "--command", command, "--timeout", "60")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "discovery",
            "--json",
            "--run",
            str(env["root"]),
            "--actor-id",
            env["actor"],
            "--actor-name",
            "Test investigator",
            "--actor-kind",
            "model",
            "--request-id",
            request,
            *args,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    sandbox = env["root"] / "scratch" / "experiments" / experiment["uuid"] / "source"
    marker = sandbox / "ready.pid"
    worker_pid = None
    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        assert marker.exists(), "Experiment never reached the execution checkpoint"
        worker_pid = int(marker.read_text())
        process.kill()
        process.communicate(timeout=5)
        assert process.returncode == -signal.SIGKILL
        assert call(*args, request=request, expected=2)["error"]["code"] == "EXPERIMENT_INTERRUPTED"
        assert (sandbox / "invocations.txt").read_text() == "run\n"
        # A killed controller cannot promise subprocess cleanup. The test owns
        # this exact child process group and stops it before replacing the attempt.
        os.killpg(worker_pid, signal.SIGKILL)
        worker_pid = None
        call(
            "experiment",
            "abort",
            experiment["ref"],
            "--reason",
            "Controller killed; child stopped; receipt absent",
        )
        replacement = plan_experiment(env)
        call(
            "experiment",
            "replace",
            experiment["ref"],
            "--replacement",
            replacement["ref"],
            "--reason",
            "Explicit fresh attempt after interruption",
        )
        assert call("audit", "verify")["result"]["valid"]
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=5)
        if worker_pid:
            try:
                os.killpg(worker_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS Seatbelt execution adapter")
def test_command_file_captures_bytes_and_preserves_replay(designed):
    from discovery.domain.encoding import uid

    env = designed
    call = env["call"]
    exp = plan_experiment(env)
    command_file = env["root"].parent / "command with spaces.json"
    payload = "quotes '\"; dollars $(not_a_command); backticks `unchanged`\nsecond line"
    code = f"from pathlib import Path; Path('once.txt').write_text({payload!r})"
    original = json.dumps(["/usr/bin/python3", "-c", code])
    command_file.write_text(original)
    request = uid()
    result = call(
        "experiment", "exec", exp["ref"], "--command-file", str(command_file), request=request
    )["result"]
    assert result["exit_code"] == 0
    record = call("experiment", "list")["result"][-1]
    from pathlib import Path

    generated = Path(record["sandbox_path"]) / "once.txt"
    assert generated.read_text() == payload
    generated.write_text("replay must not execute")
    assert call("experiment", "exec", exp["ref"], "--command", original, request=request)[
        "replayed"
    ]
    assert generated.read_text() == "replay must not execute"
    command_file.write_text(json.dumps(["/usr/bin/python3", "-c", 'print("changed")']))
    assert (
        call(
            "experiment",
            "exec",
            exp["ref"],
            "--command-file",
            str(command_file),
            request=request,
            expected=2,
        )["error"]["code"]
        == "IDEMPOTENCY_CONFLICT"
    )
    assert call("audit", "verify")["result"]["valid"]


@pytest.mark.parametrize("content", [b"not json", b"{}", b'[""]', b'["echo", "\\u0000"]', b"\xff"])
def test_invalid_command_file_never_reserves_attempt(designed, content):
    env = designed
    call = env["call"]
    exp = plan_experiment(env)
    path = env["root"].parent / "invalid.json"
    path.write_bytes(content)
    before = call("audit", "verify")["result"]["event_count"]
    assert (
        call("experiment", "exec", exp["ref"], "--command-file", str(path), expected=2)["error"][
            "code"
        ]
        == "INVALID_ARGUMENT"
    )
    assert call("experiment", "list")["result"][-1]["experiment_status"] == "planned"
    assert call("audit", "verify")["result"]["event_count"] == before


def test_interim_report_includes_answered_need_and_resolvable_artifact_links(designed):
    from pathlib import Path

    call = designed["call"]
    result = call("report", "export")["result"]
    folder = Path(result["directory"])
    packet = json.loads((folder / "report.json").read_text())
    text = (folder / "report.md").read_text()
    answered = [n for n in packet["state"]["research_need"] if n["need_status"] == "answered"]
    assert answered and all(n["answer_text"] in text for n in answered)
    assert packet["state"]["claim"]
    assert packet["audit"]["valid"]
    request = next(
        a
        for a in packet["state"]["artifact"]
        if a["artifact_id"] == packet["state"]["run"]["input_artifact_id"]
    )
    relative = "../../../" + request["storage_path"]
    assert f"]({relative})" in text
    assert (folder / relative).resolve().is_file()
