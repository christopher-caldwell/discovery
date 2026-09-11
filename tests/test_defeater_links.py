"""One canonical finding can be investigated by several current Phase 4 checks."""
# ruff: noqa: F811 -- pytest fixtures are requested by parameter name.

import json
from pathlib import Path

import pytest
from test_completion import designed, draft  # noqa: F401
from test_phase2 import evidence, investigation  # noqa: F401

from discovery.adapters.sqlite.connection import connect
from discovery.domain.completion import review_hash
from discovery.domain.encoding import uid


@pytest.fixture
def challenged(designed):
    env = designed
    draft(env)
    env["call"]("phase", "advance")
    checks = env["call"]("challenge", "initialize")["result"]["checks"]
    finding = env["call"](
        "defeater",
        "create",
        "--check",
        checks[0]["ref"],
        "--decision",
        env["decision"]["ref"],
        "--evidence-ref",
        env["evidence"]["ref"],
        "--text",
        "One shared contract concern",
        "--impact",
        "material",
    )["result"]
    return {**env, "checks": checks, "finding": finding}


def link(env, check, **kwargs):
    return env["call"](
        "defeater",
        "link-check",
        env["finding"]["ref"],
        "--check",
        check["ref"],
        "--reason",
        "Same contract concern applies",
        **kwargs,
    )


def complete(env, check, disposition="completed_findings"):
    return env["call"](
        "challenge",
        "complete",
        check["ref"],
        "--disposition",
        disposition,
        "--reason",
        "Reviewed this check against the canonical finding",
        "--report",
        str(env["narrative"]),
    )


def test_shared_defeater_has_one_resolution_and_gate_and_durable_links(challenged):
    env = challenged
    call = env["call"]
    before = call("spec", "snapshot")["result"]
    request = uid()
    assert link(env, env["checks"][1], request=request)["result"]["linked"]
    assert link(env, env["checks"][1], request=request)["replayed"]
    after = call("spec", "snapshot")["result"]
    assert review_hash(before) != review_hash(after)
    assert after["defeater"] == before["defeater"]
    assert len(after["defeater"]) == 1 and len(after["defeater_check"]) == 2
    assert after["defeater"][0]["adversarial_check_id"] == env["checks"][0]["id"]
    for i, check in enumerate(env["checks"]):
        complete(env, check, "completed_findings" if i < 2 else "completed_no_finding")
    gates = call("phase", "check")["result"]["violations"]
    assert sum(v["code"] == "DEFEATER_OPEN" for v in gates) == 1
    assert not any(v["code"] == "CHALLENGE_INCOMPLETE" for v in gates)
    resolution = evidence(env, document="evidence/reproduction.md")
    call(
        "defeater",
        "defeat",
        env["finding"]["ref"],
        "--evidence-ref",
        resolution["ref"],
        "--reason",
        "Distinct reproduction resolves the common concern",
        "--report",
        str(env["narrative"]),
    )
    resolved = call("spec", "snapshot")["result"]
    assert not link(env, env["checks"][1])["result"]["linked"]
    duplicate = call("spec", "snapshot")["result"]
    assert duplicate["defeater_check"] == resolved["defeater_check"]
    assert duplicate["defeater"] == resolved["defeater"]
    assert call("phase", "check")["result"]["can_advance"]
    report = call("report", "export")["result"]
    packet = json.loads((Path(report["directory"]) / "report.json").read_text())
    assert len(packet["state"]["defeater_check"]) == 2
    markdown = (Path(report["directory"]) / "report.md").read_text()
    assert "Checks: CH-001, CH-002" in markdown
    call("phase", "advance")
    bundle = call("spec", "export")["result"]
    handoff = json.loads((Path(bundle["directory"]) / "handoff.json").read_text())
    assert len(handoff["defeater_checks"]) == 2
    assert call("audit", "verify")["result"]["valid"]


@pytest.mark.parametrize(
    "invalid",
    [
        "completed_check",
        "terminal_finding",
        "wrong_phase",
        "historical_spec",
        "historical_traversal",
    ],
)
def test_new_link_cannot_bypass_scope_or_terminal_checks(challenged, invalid):
    env = challenged
    call = env["call"]
    target = env["checks"][1]
    if invalid == "completed_check":
        complete(env, target, "completed_no_finding")
    elif invalid == "terminal_finding":
        resolution = evidence(env, document="evidence/reproduction.md")
        call(
            "defeater",
            "defeat",
            env["finding"]["ref"],
            "--evidence-ref",
            resolution["ref"],
            "--reason",
            "Resolved",
            "--report",
            str(env["narrative"]),
        )
    elif invalid == "historical_spec":
        call("spec", "revise", "--narrative", str(env["narrative"]))
        target = call("challenge", "initialize")["result"]["checks"][1]
    else:
        call(
            "phase",
            "regress",
            "--to",
            "3",
            "--cause",
            "defeater:" + env["finding"]["ref"],
            "--reason",
            "New traversal required",
        )
        if invalid == "historical_traversal":
            draft(env)
            call("phase", "advance")
            target = call("challenge", "initialize")["result"]["checks"][1]
    before = call("spec", "snapshot")["result"]
    error = link(env, target, expected=2)["error"]["code"]
    assert error == (
        "WRONG_PHASE"
        if invalid == "wrong_phase"
        else "SCOPE_MISMATCH"
        if invalid.startswith("historical")
        else "INVALID_STATE"
    )
    after = call("spec", "snapshot")["result"]
    assert after["defeater_check"] == before["defeater_check"]
    assert after["defeater"] == before["defeater"]
    assert call("audit", "verify")["result"]["valid"]


def test_link_reason_is_audited_and_relation_tamper_fails(challenged):
    env = challenged
    link(env, env["checks"][1])
    with connect(env["root"] / "discovery.sqlite") as db:
        db.execute("UPDATE defeater_check SET link_reason='tampered'")
    assert env["call"]("audit", "verify", expected=2)["error"]["code"] == "AUDIT_INTEGRITY_FAILURE"


def test_direct_creation_rejects_completed_check_without_changing_state(challenged):
    env = challenged
    call = env["call"]
    target = env["checks"][1]
    complete(env, target, "completed_no_finding")
    before = call("spec", "snapshot")["result"]
    audit = call("audit", "verify")["result"]
    result = call(
        "defeater",
        "create",
        "--check",
        target["ref"],
        "--decision",
        env["decision"]["ref"],
        "--evidence-ref",
        env["evidence"]["ref"],
        "--text",
        "Late concern cannot silently alter a completed check",
        "--impact",
        "material",
        expected=2,
    )
    assert result["error"]["code"] == "INVALID_STATE"
    assert call("spec", "snapshot")["result"] == before
    assert call("audit", "verify")["result"] == audit

    request = uid()
    args = (
        "defeater",
        "create",
        "--check",
        env["checks"][2]["ref"],
        "--decision",
        env["decision"]["ref"],
        "--evidence-ref",
        env["evidence"]["ref"],
        "--text",
        "Finding created before check completion",
        "--impact",
        "material",
    )
    original = call(*args, request=request)
    complete(env, env["checks"][2])
    audit = call("audit", "verify")["result"]
    replay = call(*args, request=request)
    assert replay["replayed"] and replay["result"] == original["result"]
    assert call("audit", "verify")["result"] == audit


@pytest.mark.parametrize("run", ["overlap"], indirect=True)
def test_import_rejects_completed_check_and_replays_after_later_completion(challenged):
    import secrets

    env = challenged
    call = env["call"]
    group = call("group", "dispatch", "--count", "2")["result"]
    finding = None
    for index, member in enumerate(group["agents"]):
        actor, token = uid(), secrets.token_hex(32)
        call("--lease", token, "agent", "start", member["ref"], identity=actor)
        if index == 0:
            finding = call(
                "--lease",
                token,
                "agent",
                "finding",
                member["ref"],
                "--position",
                "unique",
                "--text",
                "One imported concern",
                "--impact",
                "material",
                "--decision",
                env["decision"]["ref"],
                "--origin-uri",
                env["narrative"].as_uri(),
                "--report",
                str(env["narrative"]),
                identity=actor,
            )["result"]
        call(
            "--lease",
            token,
            "agent",
            "complete",
            member["ref"],
            "--outcome",
            "findings" if index == 0 else "no_findings",
            "--report",
            str(env["narrative"]),
            identity=actor,
        )
    complete(env, env["checks"][1], "completed_no_finding")
    before = call("spec", "snapshot")["result"]
    audit = call("audit", "verify")["result"]
    result = call(
        "finding",
        "reconcile",
        finding["ref"],
        "--check",
        env["checks"][1]["ref"],
        "--reason",
        "Attempted late import",
        expected=2,
    )
    assert result["error"]["code"] == "INVALID_STATE"
    assert call("spec", "snapshot")["result"] == before
    assert call("audit", "verify")["result"] == audit

    request = uid()
    args = (
        "finding",
        "reconcile",
        finding["ref"],
        "--check",
        env["checks"][2]["ref"],
        "--reason",
        "Import into a pending check",
    )
    original = call(*args, request=request)
    assert original["result"]["defeater"]
    complete(env, env["checks"][2])
    audit = call("audit", "verify")["result"]
    replay = call(*args, request=request)
    assert replay["replayed"] and replay["result"] == original["result"]
    assert call("audit", "verify")["result"] == audit


@pytest.mark.parametrize("run", ["overlap"], indirect=True)
def test_schema6_isolated_actor_cannot_omit_scope_to_mutate_canonical_state(challenged):
    import secrets

    env = challenged
    call = env["call"]
    group = call("group", "dispatch", "--count", "2")["result"]
    actor, token = uid(), secrets.token_hex(32)
    member = group["agents"][0]
    call("--lease", token, "agent", "start", member["ref"], identity=actor)
    before = call("spec", "snapshot")["result"]
    audit = call("audit", "verify")["result"]
    result = call(
        "defeater",
        "confirm",
        env["finding"]["ref"],
        "--reason",
        "Missing lease scope must not grant canonical authority",
        identity=actor,
        expected=2,
    )
    assert result["error"]["code"] == "AGENT_SCOPE_REQUIRED"
    assert call("spec", "snapshot")["result"] == before
    assert call("audit", "verify")["result"] == audit
