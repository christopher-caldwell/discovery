import secrets

import pytest
from conftest import ready

from discovery.domain.encoding import uid


@pytest.fixture
def group(run):
    need, lane = ready(run)
    call = run["call"]
    call("phase", "advance")
    g = call("group", "dispatch", "--lane", lane["ref"], "--count", "2")["result"]
    report = run["root"].parent / "isolated-report.md"
    report.write_text(
        "Synthetic independent finding: ordering is not guaranteed. Offline limitation."
    )
    return {**run, "group": g, "lane": lane, "need": need, "report": report}


def start(env, index):
    identity = uid()
    token = secrets.token_hex(32)
    ref = env["group"]["agents"][index]["ref"]
    env["call"]("--lease", token, "agent", "start", ref, identity=identity)
    return identity, token, ref


@pytest.mark.parametrize("run", ["overlap"], indirect=True)
def test_overlap_isolation_reconciliation_and_no_token_leak(group):
    env = group
    call = env["call"]
    a, token, ref = start(env, 0)
    b, token2, ref2 = start(env, 1)
    first = call("--agent-run", ref, "--lease", token, "resume", identity=a)["result"]
    second = call("--agent-run", ref2, "--lease", token2, "resume", identity=b)["result"]
    assert first["context"] == second["context"]
    f = call(
        "--lease",
        token,
        "agent",
        "finding",
        ref,
        "--position",
        "unique",
        "--text",
        "Unseen retry case",
        "--impact",
        "material",
        "--origin-uri",
        env["report"].as_uri(),
        "--report",
        str(env["report"]),
        identity=a,
    )["result"]
    assert not call("--agent-run", ref2, "--lease", token2, "resume", identity=b)["result"][
        "own_findings"
    ]
    assert call("claim", "list", identity=a, expected=2)["error"]["code"] == "AGENT_SCOPE_REQUIRED"
    assert (
        call("--agent-run", ref, "--lease", token, "claim", "list", identity=a, expected=2)[
            "error"
        ]["code"]
        == "AGENT_SCOPE_REQUIRED"
    )
    call(
        "--lease",
        token,
        "agent",
        "complete",
        ref,
        "--outcome",
        "findings",
        "--report",
        str(env["report"]),
        identity=a,
    )
    assert (
        call(
            "finding",
            "reconcile",
            f["ref"],
            "--reason",
            "Unique finding needs investigation",
            expected=2,
        )["error"]["code"]
        == "CONSENSUS_INCOMPLETE"
    )
    call(
        "--lease",
        token2,
        "agent",
        "complete",
        ref2,
        "--outcome",
        "no_findings",
        "--report",
        str(env["report"]),
        identity=b,
    )
    imported = call("finding", "reconcile", f["ref"], "--reason", "Do not erase unique finding")[
        "result"
    ]
    assert imported["lead"]
    result = call(
        "group",
        "reconcile",
        env["group"]["ref"],
        "--reason",
        "All isolated reports considered",
        "--report",
        str(env["report"]),
    )["result"]
    assert result["requested"] == 2 and result["positions"]["unique"] == 1
    assert not call("phase", "check")["result"]["can_advance"]
    assert call("audit", "verify")["result"]["valid"]
    import sqlite3

    con = sqlite3.connect(env["root"] / "discovery.sqlite")
    payload = " ".join(r[0] for r in con.execute("SELECT payload_json FROM event_log"))
    con.close()
    assert token not in payload and token2 not in payload


@pytest.mark.parametrize("run", ["overlap"], indirect=True)
def test_expired_reclaimed_stale_token_and_scope(group, monkeypatch):
    from discovery.application import agents

    env = group
    call = env["call"]
    identity, token, ref = start(env, 0)
    assert (
        call(
            "--lease",
            secrets.token_hex(32),
            "agent",
            "heartbeat",
            ref,
            identity=identity,
            expected=2,
        )["error"]["code"]
        == "LEASE_INVALID"
    )
    with monkeypatch.context() as patch:
        patch.setattr(agents, "now", lambda: "9999-01-01T00:00:00Z")
        assert (
            call("--lease", token, "agent", "heartbeat", ref, identity=identity, expected=2)[
                "error"
            ]["code"]
            == "LEASE_EXPIRED"
        )
        fresh = secrets.token_hex(32)
        new_actor = uid()
        call("--lease", fresh, "agent", "reclaim", ref, identity=new_actor)
    assert (
        call("--lease", token, "agent", "heartbeat", ref, identity=identity, expected=2)["error"][
            "code"
        ]
        == "LEASE_INVALID"
    )
    assert call("--lease", fresh, "agent", "heartbeat", ref, identity=new_actor)["ok"]
    call("group", "supersede", env["group"]["ref"], "--reason", "Replace failed independent group")
    assert (
        call("--lease", fresh, "agent", "heartbeat", ref, identity=new_actor, expected=2)["error"][
            "code"
        ]
        == "AGENT_NOT_RUNNING"
    )
    assert call("audit", "verify")["result"]["valid"]


@pytest.mark.parametrize("run", ["overlap"], indirect=True)
def test_failed_replica_preserves_denominator(group):
    env = group
    call = env["call"]
    identity, token, ref = start(env, 0)
    call(
        "--lease",
        token,
        "agent",
        "complete",
        ref,
        "--outcome",
        "inconclusive",
        "--report",
        str(env["report"]),
        identity=identity,
    )
    assert (
        call(
            "group",
            "reconcile",
            env["group"]["ref"],
            "--reason",
            "Ignore failed replica",
            "--report",
            str(env["report"]),
            expected=2,
        )["error"]["code"]
        == "CONSENSUS_INCOMPLETE"
    )
    call("group", "supersede", env["group"]["ref"], "--reason", "Explicit replacement required")
    groups = call("group", "list")["result"]
    assert groups[0]["requested_count"] == 2
    assert any(a["run_status"] == "cancelled" for a in call("agent", "list")["result"])


@pytest.mark.parametrize("run", ["partitioned"], indirect=True)
def test_partitioned_mode_dispatches_one_investigator(run):
    _, lane = ready(run)
    call = run["call"]
    call("phase", "advance")
    assert (
        call("group", "dispatch", "--lane", lane["ref"], "--count", "2", expected=2)["error"][
            "code"
        ]
        == "INVALID_ARGUMENT"
    )
    group = call("group", "dispatch", "--lane", lane["ref"], "--count", "1")["result"]
    assert len(group["agents"]) == 1
    assert call("audit", "verify")["result"]["valid"]
