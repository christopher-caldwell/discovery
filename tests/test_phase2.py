from pathlib import Path

import pytest
from conftest import ready

FIXTURE = Path(__file__).parent / "fixtures/phase2"


@pytest.fixture
def investigation(run):
    need, lane = ready(run)
    call = run["call"]
    call("phase", "advance")
    call("lane", "activate", lane["ref"])
    surface = next(
        s for s in call("surface", "list")["result"] if s["research_lane_id"] == lane["id"]
    )
    return {**run, "need": need, "lane": lane, "surface": surface}


def record(env, method=None, report="evidence/vendor-webhook-doc.md"):
    args = [
        "research",
        "record",
        env["surface"]["ref"],
        "--query",
        "Inspect fabricated ordering guidance",
        "--summary",
        "Fixture documentation permits retries and reordering",
        "--origin-uri",
        (FIXTURE / report).as_uri(),
        "--report",
        str(FIXTURE / report),
    ]
    if method:
        args += ["--method", method]
    return env["call"](*args)["result"]


def evidence(env, kind="primary", source=False, document="evidence/vendor-webhook-doc.md"):
    path = env["source"] / "app.txt" if source else FIXTURE / document
    extra = ["--source-backed"] if source else []
    artifact = env["call"](
        "artifact", "capture", "--file", str(path), "--origin-uri", path.as_uri(), *extra
    )["result"]
    return env["call"](
        "evidence",
        "create",
        "--lane",
        env["lane"]["ref"],
        "--artifact",
        artifact["ref"],
        "--kind",
        kind,
        "--locator",
        "lines 1-20",
        "--observation",
        "Synthetic vendor contract permits reordered retries",
    )["result"]


def claim(env, impact="material"):
    return env["call"](
        "claim",
        "create",
        "--lane",
        env["lane"]["ref"],
        "--kind",
        "vendor_capability",
        "--impact",
        impact,
        "--text",
        "Delivery is at-least-once without ordering guarantees",
    )["result"]


def argument(env, c, e, role="supports"):
    result = env["call"](
        "argument",
        "create",
        "--claim",
        c["ref"],
        "--role",
        role,
        "--evidence",
        e["ref"],
        "--reasoning",
        "Fixture source directly states the contract",
        "--limitations",
        "Synthetic evidence only",
    )["result"]
    env["call"](
        "argument",
        "verify",
        result["ref"],
        "--outcome",
        "passed",
        "--report",
        str(FIXTURE / "evidence/reproduction.md"),
    )
    return result


def closure(env):
    call = env["call"]
    # Initial methods and surfaces must actually be searched, even in a fixture.
    for m in call("method", "list")["result"]:
        if (
            m["research_lane_id"] == env["lane"]["id"]
            and m["method_category"] == "primary"
            and m["disposition"] == "pending"
        ):
            record(env, m["ref"])
            call(
                "method",
                "disposition",
                m["ref"],
                "--disposition",
                "completed",
                "--reason",
                "Fixture inspection recorded",
            )
    call(
        "surface",
        "disposition",
        env["surface"]["ref"],
        "--disposition",
        "searched",
        "--reason",
        "Recorded primary research",
    )
    result = call("lane", "closure-begin", env["lane"]["ref"])["result"]
    for m in result["methods"]:
        record(env, m["ref"])
        call(
            "method",
            "disposition",
            m["ref"],
            "--disposition",
            "completed",
            "--reason",
            "No new material lead in this synthetic sweep",
        )
    return result


def finish(env):
    env["call"](
        "lane",
        "close",
        env["lane"]["ref"],
        "--answer",
        "Ordering is not guaranteed",
        "--limitations",
        "Synthetic case only",
    )
    env["call"](
        "research-need",
        "answer",
        env["need"]["ref"],
        "--answer",
        "Consumers need ordering-independent processing",
    )


def test_real_phase2_to_phase3_path(investigation):
    env = investigation
    e, c = evidence(env), claim(env)
    argument(env, c, e)
    assert env["call"]("claim", "evaluate", c["ref"])["result"]["status"] == "proposed"
    closure(env)
    assert env["call"]("claim", "evaluate", c["ref"])["result"]["status"] == "admissible"
    assert env["call"]("lane", "check", env["lane"]["ref"])["result"]["satisfied"]
    finish(env)
    assert env["call"]("phase", "advance")["result"]["phase"] == 3
    assert (
        env["call"]("phase", "advance", expected=2)["error"]["details"]["violations"][0]["code"]
        == "PHASE_NOT_IMPLEMENTED"
    )
    assert env["call"]("audit", "verify")["result"]["valid"]


def test_new_lead_invalidates_closure_and_answers(investigation):
    env = investigation
    e, c = evidence(env), claim(env)
    argument(env, c, e)
    sweep = closure(env)
    env["call"]("claim", "evaluate", c["ref"])
    finish(env)
    activity = env["call"](
        "research",
        "record",
        env["surface"]["ref"],
        "--query",
        "Late search",
        "--summary",
        "More work",
        "--origin-uri",
        "fixture://late",
        "--report",
        str(FIXTURE / "UNKNOWN.md"),
        expected=2,
    )
    assert activity["error"]["code"] == "INVALID_STATE"
    prior = env["call"]("resume")["result"]
    assert prior["research_needs"][0]["need_status"] == "answered"
    # Existing search may reveal a previously overlooked lead.
    from discovery.adapters.sqlite.connection import connect

    con = connect(env["root"] / "discovery.sqlite")
    aid = con.execute(
        "SELECT research_activity_uuid FROM research_activity WHERE research_lane_id=? LIMIT 1",
        (env["lane"]["id"],),
    ).fetchone()[0]
    con.close()
    lead = env["call"](
        "lead",
        "create",
        "--lane",
        env["lane"]["ref"],
        "--activity",
        aid,
        "--text",
        "Clarify retry policy",
        "--impact",
        "material",
    )["result"]
    assert env["call"]("resume")["result"]["research_needs"][0]["need_status"] == "covered"
    assert (
        env["call"]("lane", "closure-begin", env["lane"]["ref"], expected=2)["error"]["code"]
        == "LANE_HAS_OPEN_LEADS"
    )
    env["call"](
        "lead",
        "disposition",
        lead["ref"],
        "--disposition",
        "irrelevant",
        "--reason",
        "Separate product contract",
    )
    assert not env["call"]("lane", "check", env["lane"]["ref"])["result"]["satisfied"]
    assert closure(env)["iteration"] == sweep["iteration"] + 1
    env["call"]("claim", "evaluate", c["ref"])
    finish(env)


def test_material_unknown_closes_but_blocks_phase(investigation):
    env = investigation
    q = env["call"](
        "question",
        "create",
        "--technical",
        "--text",
        "How long must retries be retained?",
        "--authority",
        "product",
        "--authority-confidence",
        "0.7",
        "--rationale",
        "Policy is absent from source",
    )["result"]
    closure(env)
    assert (
        env["call"](
            "lane",
            "close",
            env["lane"]["ref"],
            "--answer",
            "UNKNOWN",
            "--limitations",
            "Needs human policy",
            expected=2,
        )["error"]["code"]
        == "UNKNOWN_REQUIRES_QUESTION"
    )
    env["call"](
        "lane",
        "close",
        env["lane"]["ref"],
        "--answer",
        "UNKNOWN",
        "--question",
        q["ref"],
        "--limitations",
        "Needs human policy",
    )
    env["call"](
        "research-need", "answer", env["need"]["ref"], "--answer", "UNKNOWN pending product answer"
    )
    assert "BLOCKING_QUESTION_OPEN" in {
        v["code"] for v in env["call"]("phase", "check")["result"]["violations"]
    }
    env["call"](
        "question", "resolve", q["ref"], "--answer", "Product chooses 30 days; recorded test answer"
    )
    assert not env["call"]("phase", "check")["result"]["can_advance"]
    closure(env)
    blocked = env["call"](
        "lane",
        "close",
        env["lane"]["ref"],
        "--answer",
        "UNKNOWN",
        "--question",
        q["ref"],
        "--limitations",
        "Still unknown",
        expected=2,
    )
    assert blocked["error"]["code"] == "UNKNOWN_REQUIRES_QUESTION"
    e, c = evidence(env), claim(env)
    argument(env, c, e)
    closure(env)
    env["call"]("claim", "evaluate", c["ref"])
    finish(env)
    assert env["call"]("phase", "check")["result"]["can_advance"]


def test_contradiction_not_outvoted(investigation):
    env = investigation
    e, c = evidence(env), claim(env)
    for _ in range(3):
        argument(env, c, e)
    contrary = evidence(env, kind="empirical", document="evidence/reproduction.md")
    challenge = argument(env, c, contrary, "refutes")
    closure(env)
    assert env["call"]("claim", "evaluate", c["ref"])["result"]["status"] == "contested"
    assert not env["call"]("lane", "check", env["lane"]["ref"])["result"]["satisfied"]
    env["call"](
        "argument",
        "resolve-counter",
        challenge["ref"],
        "--evidence-ref",
        contrary["ref"],
        "--reason",
        "Invalid self-resolution",
        expected=2,
    )
    resolution = evidence(env, kind="empirical")
    env["call"](
        "argument",
        "resolve-counter",
        challenge["ref"],
        "--evidence-ref",
        resolution["ref"],
        "--reason",
        "Counterexample concerns consumer handling rather than vendor guarantees",
    )
    closure(env)
    assert env["call"]("claim", "evaluate", c["ref"])["result"]["status"] == "admissible"
    env["call"]("evidence", "retract", resolution["ref"], "--reason", "Resolution was unreliable")
    assert env["call"]("claim", "evaluate", c["ref"])["result"]["status"] == "contested"
    replacement = evidence(env, kind="empirical")
    env["call"](
        "argument",
        "resolve-counter",
        challenge["ref"],
        "--evidence-ref",
        replacement["ref"],
        "--reason",
        "Fresh independently reviewed resolution",
    )
    closure(env)
    assert env["call"]("claim", "evaluate", c["ref"])["result"]["status"] == "admissible"


def test_secondary_evidence_cannot_admit_material_claim(investigation):
    env = investigation
    e, c = evidence(env, kind="secondary"), claim(env)
    argument(env, c, e)
    closure(env)
    result = env["call"]("claim", "evaluate", c["ref"])["result"]
    assert result["status"] == "proposed"
    assert "PRIMARY_EVIDENCE_REQUIRED" in {f["code"] for f in result["violations"]}


def test_critical_requires_empirical_and_falsification(investigation):
    env = investigation
    e, c = evidence(env), claim(env, "critical")
    argument(env, c, e)
    closure(env)
    codes = {f["code"] for f in env["call"]("claim", "check", c["ref"])["result"]["violations"]}
    assert {"EMPIRICAL_EVIDENCE_REQUIRED", "VERIFICATION_METHOD_REQUIRED"} <= codes
    for method in ("falsification", "empirical_verification"):
        env["call"]("method", "create", "--lane", env["lane"]["ref"], "--name", method)
    empirical = evidence(env, "empirical")
    argument(env, c, empirical)
    closure(env)
    assert env["call"]("claim", "evaluate", c["ref"])["result"]["status"] == "admissible"


def test_source_refresh_retracts_source_evidence_only(investigation):
    env = investigation
    source, external = evidence(env, source=True), evidence(env)
    c = claim(env)
    argument(env, c, source)
    closure(env)
    env["call"]("claim", "evaluate", c["ref"])
    finish(env)
    (env["source"] / "app.txt").write_text("changed source")
    assert not env["call"]("phase", "check")["result"]["can_advance"]
    refreshed = env["call"]("source", "refresh", "--reason", "Synthetic source changed")["result"]
    assert refreshed["retracted_evidence"] == [source["uuid"]]
    rows = {e["uuid"]: e for e in env["call"]("evidence", "list")["result"]}
    assert rows[source["uuid"]]["evidence_status"] == "retracted"
    assert rows[external["uuid"]]["evidence_status"] == "active"
    assert env["call"]("resume")["result"]["lanes"][0]["lane_status"] == "active"
    assert env["call"]("audit", "verify")["result"]["valid"]


def test_lead_disposition_requires_links(investigation):
    env = investigation
    activity = record(env)
    lead = env["call"](
        "lead",
        "create",
        "--lane",
        env["lane"]["ref"],
        "--activity",
        activity["ref"],
        "--text",
        "Retry trace",
        "--impact",
        "material",
    )["result"]
    for disposition in ("investigated", "duplicate", "requires_human_input"):
        assert (
            env["call"](
                "lead",
                "disposition",
                lead["ref"],
                "--disposition",
                disposition,
                "--reason",
                "Test",
                expected=2,
            )["error"]["code"]
            == "INVALID_ARGUMENT"
        )
    env["call"](
        "lead",
        "disposition",
        lead["ref"],
        "--disposition",
        "investigated",
        "--activity",
        activity["ref"],
        "--reason",
        "Same originating activity",
        expected=2,
    )
    investigated = record(env, report="evidence/reproduction.md")
    env["call"](
        "lead",
        "disposition",
        lead["ref"],
        "--disposition",
        "investigated",
        "--activity",
        investigated["ref"],
        "--reason",
        "Reproduced late retry behavior",
    )
    duplicate = env["call"](
        "lead",
        "create",
        "--lane",
        env["lane"]["ref"],
        "--activity",
        activity["ref"],
        "--text",
        "Same retry trace",
        "--impact",
        "material",
    )["result"]
    env["call"](
        "lead",
        "disposition",
        duplicate["ref"],
        "--disposition",
        "duplicate",
        "--duplicate-of",
        lead["ref"],
        "--reason",
        "Identical reproduction",
    )


def test_known_material_answer_needs_claim(investigation):
    env = investigation
    closure(env)
    result = env["call"](
        "lane",
        "close",
        env["lane"]["ref"],
        "--answer",
        "Trust me",
        "--limitations",
        "No evidence",
        expected=2,
    )
    assert result["error"]["code"] == "ANSWER_CLAIM_REQUIRED"


def test_request_copy_is_still_an_assertion(investigation):
    env = investigation
    captured = env["call"](
        "artifact", "capture", "--file", str(env["ticket"]), "--origin-uri", env["ticket"].as_uri()
    )["result"]
    result = env["call"](
        "evidence",
        "create",
        "--lane",
        env["lane"]["ref"],
        "--artifact",
        captured["ref"],
        "--kind",
        "primary",
        "--locator",
        "full document",
        "--observation",
        "Repeated assertion",
        expected=2,
    )
    assert result["error"]["code"] == "ASSERTION_NOT_EVIDENCE"


def test_source_capture_rejects_untracked_runtime_scope(investigation):
    env = investigation
    excluded = env["source"] / ".discovery"
    excluded.mkdir()
    path = excluded / "result.txt"
    path.write_text("Not fingerprinted source")
    result = env["call"](
        "artifact",
        "capture",
        "--file",
        str(path),
        "--origin-uri",
        path.as_uri(),
        "--source-backed",
        expected=2,
    )
    assert result["error"]["code"] == "SCOPE_MISMATCH"


def test_closure_retry_and_historical_method_rejection(investigation):
    from discovery.domain.encoding import uid

    env = investigation
    request = uid()
    first = env["call"]("lane", "closure-begin", env["lane"]["ref"], request=request)
    replay = env["call"]("lane", "closure-begin", env["lane"]["ref"], request=request)
    assert replay["replayed"] and replay["result"] == first["result"]
    env["call"]("lane", "reopen", env["lane"]["ref"], "--reason", "Another avenue")
    env["call"]("lane", "closure-begin", env["lane"]["ref"])
    result = env["call"](
        "method",
        "disposition",
        first["result"]["methods"][0]["ref"],
        "--disposition",
        "not_applicable",
        "--reason",
        "Stale attempt",
        expected=2,
    )
    assert result["error"]["code"] == "LANE_CLOSURE_STALE"


def test_copied_counterevidence_cannot_resolve_itself(investigation):
    env = investigation
    c = claim(env)
    contrary = evidence(env, document="evidence/reproduction.md")
    a = argument(env, c, contrary, "refutes")
    copied = evidence(env, document="evidence/reproduction.md")
    result = env["call"](
        "argument",
        "resolve-counter",
        a["ref"],
        "--evidence-ref",
        copied["ref"],
        "--reason",
        "Same bytes under another ID",
        expected=2,
    )
    assert result["error"]["code"] == "RESOLUTION_EVIDENCE_REQUIRED"


def test_method_and_evidence_scope_cannot_cross_lanes(investigation):
    env = investigation
    other = env["call"](
        "lane",
        "create",
        "--text",
        "How are retries scheduled?",
        "--rationale",
        "Separate issue",
        "--scope",
        "Retry scheduler",
        "--need",
        env["need"]["ref"],
        "--impact",
        "material",
        "--method",
        "scheduler",
        "--surface",
        "scheduler_docs",
    )["result"]
    env["call"]("lane", "activate", other["ref"])
    method = next(
        m for m in env["call"]("method", "list")["result"] if m["research_lane_id"] == other["id"]
    )
    result = env["call"](
        "research",
        "record",
        env["surface"]["ref"],
        "--method",
        method["ref"],
        "--query",
        "Wrong lane",
        "--summary",
        "Mismatch",
        "--origin-uri",
        "fixture://scope",
        "--report",
        str(FIXTURE / "UNKNOWN.md"),
        expected=2,
    )
    assert result["error"]["code"] == "SCOPE_MISMATCH"
    e = evidence(env)
    other_env = {**env, "lane": other}
    c = claim(other_env)
    result = env["call"](
        "argument",
        "create",
        "--claim",
        c["ref"],
        "--role",
        "supports",
        "--evidence",
        e["ref"],
        "--reasoning",
        "Wrong scope",
        "--limitations",
        "Synthetic",
        expected=2,
    )
    assert result["error"]["code"] == "SCOPE_MISMATCH"


def test_retraction_blocks_previously_closed_lane(investigation):
    env = investigation
    e, c = evidence(env), claim(env)
    argument(env, c, e)
    closure(env)
    env["call"]("claim", "evaluate", c["ref"])
    finish(env)
    env["call"]("evidence", "retract", e["ref"], "--reason", "Fixture evidence found unreliable")
    packet = env["call"]("resume")["result"]
    assert packet["lanes"][0]["lane_status"] == "active"
    assert packet["research_needs"][0]["need_status"] == "covered"
    assert not packet["gate"]["can_advance"]


def test_source_refresh_replay_and_activity_listing(investigation):
    from discovery.domain.encoding import uid

    env = investigation
    activity = record(env)
    assert activity["uuid"] in {r["uuid"] for r in env["call"]("research", "list")["result"]}
    (env["source"] / "app.txt").write_text("replacement")
    request = uid()
    first = env["call"]("source", "refresh", "--reason", "Update fixture", request=request)
    replay = env["call"]("source", "refresh", "--reason", "Update fixture", request=request)
    assert replay["replayed"] and replay["result"] == first["result"]
    assert len(env["call"]("source", "list")["result"]) == 2


def test_unknown_need_cannot_bypass_blocking_question(investigation):
    env = investigation
    e, c = evidence(env), claim(env)
    argument(env, c, e)
    closure(env)
    env["call"]("claim", "evaluate", c["ref"])
    finish(env)
    result = env["call"](
        "research-need",
        "answer",
        env["need"]["ref"],
        "--answer",
        "UNKNOWN; human must decide",
        expected=2,
    )
    assert result["error"]["code"] == "UNKNOWN_REQUIRES_QUESTION"
