# ruff: noqa: F811 -- imported pytest fixtures are requested by parameter name.

import json
from pathlib import Path

import pytest
from conftest import question, ready
from test_completion import designed, plan_experiment  # noqa: F401
from test_phase2 import (  # noqa: F401
    FIXTURE,
    argument,
    claim,
    closure,
    evidence,
    investigation,
    record,
)

from discovery.adapters.process import sandbox
from discovery.domain.encoding import uid
from discovery.domain.policy import POLICY


def nonblocking_question(call):
    return call(
        "question",
        "create",
        "--non-blocking",
        "--text",
        "May the display label default to the repository name?",
        "--rationale",
        "Presentation fallback does not change stored behavior",
        "--authority",
        "product",
        "--authority-confidence",
        "0.6",
    )["result"]


def test_blocking_question_cannot_be_assumed_and_interim_remains_available(run):
    q = question(run["call"])["result"]
    result = run["call"](
        "question",
        "assume",
        q["ref"],
        "--text",
        "Assume FIFO delivery",
        "--justification",
        "Convenient for design",
        "--scope",
        "All consumers",
        "--invalidates-when",
        "Owner disagrees",
        "--impact",
        "material",
        expected=2,
    )
    assert result["error"]["code"] == "BLOCKING_QUESTION"
    report = run["call"]("report", "export")["result"]
    text = (Path(report["directory"]) / "report.md").read_text()
    assert "cannot yet be made" in text and "Q-001" in text


def test_assumption_authority_and_custom_surface_survive_recovery_and_regression(run):
    call = run["call"]
    q = nonblocking_question(call)
    call(
        "question",
        "respondent-add",
        q["ref"],
        "--rank",
        "1",
        "--kind",
        "role",
        "--name",
        "Unknown product owner",
        "--confidence",
        "0.4",
        "--rationale",
        "The repository identifies the product role but no individual",
        "--identity-unknown",
    )
    assumed = call(
        "question",
        "assume",
        q["ref"],
        "--text",
        "Use the repository name only as an absent-label fallback",
        "--justification",
        "It affects presentation only and remains clearly conditional",
        "--scope",
        "Empty display labels",
        "--invalidates-when",
        "A product owner supplies a different fallback",
        "--impact",
        "material",
    )["result"]
    added = call(
        "surface",
        "create",
        "--name",
        "deployment_configuration",
        "--reason",
        "Runtime defaults may override repository configuration",
    )["result"]
    assert call("phase", "check")["result"]["can_advance"] is False
    call(
        "surface",
        "disposition",
        added["ref"],
        "--disposition",
        "unavailable",
        "--reason",
        "No deployment material was supplied",
    )
    need, _ = ready(run)
    recovered = call("resume", "--compact")["result"]
    assert recovered["assumptions"][0]["scope"] == "Empty display labels"
    assert recovered["question_respondents"][0]["identity_status"] == "unknown"
    assert any(
        s["surface_name"] == "deployment_configuration" for s in recovered["research_surfaces"]
    )
    call("phase", "advance")
    call(
        "phase",
        "regress",
        "--to",
        "1",
        "--cause",
        f"need:{need['ref']}",
        "--reason",
        "Intent needs revalidation",
    )
    current = [
        s
        for s in call("surface", "list")["result"]
        if s["phase_revision_id"] == call("status")["result"]["phase"]["phase_revision_id"]
    ]
    custom = next(s for s in current if s["surface_name"] == "deployment_configuration")
    assert custom["disposition"] == "pending"
    assert custom["addition_reason"]
    assert assumed["ref"].startswith("AS-")


def test_question_reclassification_resolution_and_withdrawal_are_explicit(run):
    call = run["call"]
    blocking = question(call)["result"]
    changed = call(
        "question",
        "reclassify",
        blocking["ref"],
        "--non-blocking",
        "--reason",
        "The uncertainty changes presentation only",
    )["result"]
    assert changed["is_blocking"] is False
    assumed = call(
        "question",
        "assume",
        blocking["ref"],
        "--text",
        "Use a neutral label until the owner answers",
        "--justification",
        "The fallback is reversible",
        "--scope",
        "Empty presentation labels",
        "--invalidates-when",
        "The owner supplies a label",
        "--impact",
        "contextual",
    )["result"]
    call(
        "question",
        "resolve",
        blocking["ref"],
        "--answer",
        "Use the service name",
        "--confirms-assumption",
    )
    stored = next(
        item for item in call("assumption", "list")["result"] if item["ref"] == assumed["ref"]
    )
    assert stored["assumption_status"] == "discharged"

    withdrawn = nonblocking_question(call)
    result = call(
        "question",
        "withdraw",
        withdrawn["ref"],
        "--reason",
        "The display label is no longer part of the requested outcome",
    )["result"]
    assert result["status"] == "withdrawn"


def test_research_capture_bundles_persistence_without_semantic_approval(investigation):
    env = investigation
    request = uid()
    args = (
        "research",
        "capture",
        env["surface"]["ref"],
        "--query",
        "Inspect the vendor contract",
        "--summary",
        "Contract describes retry ordering",
        "--origin-uri",
        (FIXTURE / "evidence/vendor-webhook-doc.md").as_uri(),
        "--report",
        str(FIXTURE / "evidence/vendor-webhook-doc.md"),
        "--evidence-kind",
        "primary",
        "--locator",
        "lines 1-20",
        "--observation",
        "Delivery is at-least-once",
        "--observation",
        "Ordering is not guaranteed",
        "--complete-surface",
        "The contract was inspected",
    )
    first = env["call"](*args, request=request)["result"]
    replay = env["call"](*args, request=request)
    assert replay["replayed"] and replay["result"] == first
    assert len(first["evidence"]) == 2
    assert not env["call"]("claim", "list")["result"]
    assert env["call"]("lane", "list")["result"][0]["lane_status"] == "active"


def test_research_finding_bundles_bookkeeping_without_semantic_approval(investigation):
    env = investigation
    request = uid()
    args = (
        "research",
        "finding",
        env["surface"]["ref"],
        "--query",
        "Inspect the vendor contract",
        "--summary",
        "Contract describes retry ordering",
        "--origin-uri",
        (FIXTURE / "evidence/vendor-webhook-doc.md").as_uri(),
        "--report",
        str(FIXTURE / "evidence/vendor-webhook-doc.md"),
        "--evidence-kind",
        "primary",
        "--locator",
        "lines 1-20",
        "--observation",
        "Ordering is not guaranteed",
        "--claim",
        "Delivery is at-least-once without ordering guarantees",
        "--claim-kind",
        "vendor_capability",
        "--impact",
        "material",
        "--verification-method",
        "authoritative_record",
        "--verification-rationale",
        "The current contract is authoritative for the vendor guarantee",
        "--reasoning",
        "The scoped contract language directly supports the proposed claim",
        "--argument-limitations",
        "The fixture is synthetic",
    )
    first = env["call"](*args, request=request)["result"]
    replay = env["call"](*args, request=request)
    assert replay["replayed"] and replay["result"] == first
    assert first["claim"]["ref"].startswith("C-")
    assert first["argument"]["ref"].startswith("ARG-")
    claim_row = env["call"]("claim", "list")["result"][0]
    argument_row = env["call"]("argument", "list")["result"][0]
    assert claim_row["claim_status"] == "proposed"
    assert argument_row["verification_status"] == "pending"
    assert env["call"]("lane", "list")["result"][0]["lane_status"] == "active"


def test_closure_rigor_is_proportional_to_consequence():
    methods = POLICY["closure_methods_by_impact"]
    assert methods["contextual"] == ["evidence_gaps"]
    assert methods["material"] == ["contradiction", "evidence_gaps"]
    assert methods["critical"] == [
        "terminology",
        "snowballing",
        "contradiction",
        "evidence_gaps",
    ]


def test_research_capture_invalidates_an_in_progress_closure(investigation):
    env = investigation
    call = env["call"]
    for method in call("method", "list")["result"]:
        if method["research_lane_id"] == env["lane"]["id"]:
            record(env, method["ref"])
            call(
                "method",
                "disposition",
                method["ref"],
                "--disposition",
                "completed",
                "--reason",
                "Initial research completed",
            )
    call(
        "surface",
        "disposition",
        env["surface"]["ref"],
        "--disposition",
        "searched",
        "--reason",
        "Initial research recorded",
    )
    sweep = call("lane", "closure-begin", env["lane"]["ref"])["result"]
    method = sweep["methods"][0]
    args = (
        "research",
        "capture",
        env["surface"]["ref"],
        "--method",
        method["ref"],
        "--query",
        "Inspect newly discovered material",
        "--summary",
        "New material was found during closure",
        "--origin-uri",
        (FIXTURE / "evidence/vendor-webhook-doc.md").as_uri(),
        "--report",
        str(FIXTURE / "evidence/vendor-webhook-doc.md"),
        "--evidence-kind",
        "primary",
        "--locator",
        "lines 1-20",
        "--observation",
        "The closure sweep found new evidence",
    )
    rejected = call(*args, "--complete-method", "Sweep complete", expected=2)
    assert rejected["error"]["code"] == "LANE_CLOSURE_STALE"
    call(*args)
    lane = call("lane", "list")["result"][0]
    assert lane["closure_status"] == "stale"


def test_claim_verification_matches_assertion_and_unavailable_proof_blocks(investigation):
    env = investigation
    primary = evidence(env)
    authoritative = claim(env, "critical", verification="authoritative_record")
    argument(env, authoritative, primary)
    env["call"](
        "claim",
        "challenge",
        authoritative["ref"],
        "--surface",
        env["surface"]["ref"],
        "--query",
        "Search the authority record for a conflicting rule",
        "--summary",
        "No conflicting rule was found in the scoped record",
        "--origin-uri",
        (FIXTURE / "evidence/vendor-webhook-doc.md").as_uri(),
        "--report",
        str(FIXTURE / "evidence/vendor-webhook-doc.md"),
        "--evidence-kind",
        "primary",
        "--locator",
        "lines 1-20",
        "--observation",
        "No scoped exception contradicts the authority claim",
        "--role",
        "supports",
        "--reasoning",
        "The targeted contradiction search did not overturn the claim",
        "--limitations",
        "Synthetic authority fixture only",
    )
    closure(env)
    result = env["call"]("claim", "evaluate", authoritative["ref"])["result"]
    assert result["status"] == "admissible"
    assert "EMPIRICAL_EVIDENCE_REQUIRED" not in {v["code"] for v in result["violations"]}

    unavailable = claim(env, verification="experiment")
    env["call"](
        "claim",
        "verification",
        unavailable["ref"],
        "--method",
        "experiment",
        "--availability",
        "unavailable",
        "--rationale",
        "Runtime behavior needs a production-compatible probe",
        "--limitations",
        "The required service is not available",
    )
    codes = {
        v["code"] for v in env["call"]("claim", "check", unavailable["ref"])["result"]["violations"]
    }
    assert "REQUIRED_VERIFICATION_UNAVAILABLE" in codes


def test_critical_claim_provisions_and_bundles_falsification(investigation):
    env = investigation
    request = uid()
    critical = claim(env, "critical", verification="authoritative_record")
    provisioned = critical["falsification_method"]
    assert provisioned["ref"].startswith("M-")
    methods = [
        method
        for method in env["call"]("method", "list")["result"]
        if method["research_lane_id"] == env["lane"]["id"]
        and method["method_name"] == "falsification"
    ]
    assert len(methods) == 1 and methods[0]["disposition"] == "pending"
    assert {
        "action": "challenge critical claim",
        "ref": critical["ref"],
        "why": "Record a substantive attempt to disprove this claim.",
    } in env["call"]("resume", "--compact")["result"]["investigator_actions"]

    args = (
        "claim",
        "challenge",
        critical["ref"],
        "--surface",
        env["surface"]["ref"],
        "--query",
        "Search the authoritative record for exceptions to the claimed guarantee",
        "--summary",
        "No exception was found in the scoped contract",
        "--origin-uri",
        (FIXTURE / "evidence/vendor-webhook-doc.md").as_uri(),
        "--report",
        str(FIXTURE / "evidence/vendor-webhook-doc.md"),
        "--evidence-kind",
        "primary",
        "--locator",
        "lines 1-20",
        "--observation",
        "The scoped contract contains no ordering guarantee",
        "--role",
        "supports",
        "--reasoning",
        "The attempted counterexample search did not overturn the scoped claim",
        "--limitations",
        "Only the supplied contract version was inspected",
    )
    first = env["call"](*args, request=request)["result"]
    replay = env["call"](*args, request=request)
    assert replay["replayed"] and replay["result"] == first
    assert first["falsification_method"]["status"] == "completed"
    assert first["semantic_status"].startswith("recorded")
    stored = next(
        method
        for method in env["call"]("method", "list")["result"]
        if method["ref"] == provisioned["ref"]
    )
    assert stored["disposition"] == "completed"
    assert env["call"]("claim", "list")["result"][0]["claim_status"] == "proposed"
    assert env["call"]("lane", "list")["result"][0]["lane_status"] == "active"

    other = claim(env, "critical", verification="authoritative_record")
    codes = {
        violation["code"]
        for violation in env["call"]("claim", "check", other["ref"])["result"]["violations"]
    }
    assert "VERIFICATION_METHOD_REQUIRED" in codes


def test_runtime_experiment_cannot_establish_product_intent(investigation):
    env = investigation
    claim_row = env["call"](
        "claim",
        "create",
        "--lane",
        env["lane"]["ref"],
        "--kind",
        "intended_behavior",
        "--impact",
        "material",
        "--verification-method",
        "experiment",
        "--verification-rationale",
        "A runtime probe was proposed for an intent claim",
        "--text",
        "Product intends deliveries to be ordered",
    )["result"]
    violations = env["call"]("claim", "check", claim_row["ref"])["result"]["violations"]
    assert "VERIFICATION_METHOD_MISMATCH" in {item["code"] for item in violations}


def test_invalidating_assumption_reopens_linked_claim(run):
    low_impact = run["call"](
        "assumption",
        "create",
        "--text",
        "Treat a cosmetic label as stable",
        "--justification",
        "It is reversible",
        "--scope",
        "Display only",
        "--invalidates-when",
        "The label changes",
        "--impact",
        "contextual",
    )["result"]
    q = nonblocking_question(run["call"])
    assumption = run["call"](
        "question",
        "assume",
        q["ref"],
        "--text",
        "Treat the vendor document as current for this bounded fixture",
        "--justification",
        "The fixture has no remote service and the condition is explicit",
        "--scope",
        "Vendor ordering claim",
        "--invalidates-when",
        "A newer authoritative contract is found",
        "--impact",
        "material",
    )["result"]
    need, lane = ready(run)
    call = run["call"]
    call("phase", "advance")
    call("lane", "activate", lane["ref"])
    surface = next(
        s for s in call("surface", "list")["result"] if s["research_lane_id"] == lane["id"]
    )
    env = {**run, "need": need, "lane": lane, "surface": surface}
    item = claim(env)
    argument(env, item, evidence(env))
    closure(env)
    assert call("claim", "evaluate", item["ref"])["result"]["status"] == "admissible"
    rejected = call(
        "assumption",
        "link-claim",
        low_impact["ref"],
        "--target",
        item["ref"],
        "--reason",
        "This intentionally understates the dependent claim",
        expected=2,
    )
    assert rejected["error"]["code"] == "ASSUMPTION_IMPACT_TOO_LOW"
    call(
        "assumption",
        "link-claim",
        assumption["ref"],
        "--target",
        item["ref"],
        "--reason",
        "The scoped claim relies on document freshness",
    )
    ambiguous = call(
        "question",
        "resolve",
        q["ref"],
        "--answer",
        "The newer contract changes the ordering rule",
        expected=2,
    )
    assert ambiguous["error"]["code"] == "ASSUMPTION_RELATION_REQUIRED"
    call(
        "question",
        "resolve",
        q["ref"],
        "--answer",
        "The newer contract changes the ordering rule",
        "--contradicts-assumption",
    )
    assert call("claim", "list")["result"][0]["claim_status"] == "proposed"
    assert call("lane", "list")["result"][0]["closure_status"] == "stale"
    assert call("phase", "check")["result"]["can_advance"] is False


def test_critical_decision_rejects_lower_impact_trace(designed):
    call = designed["call"]
    strategy = call("strategy", "list")["result"][0]
    result = call(
        "decision",
        "create",
        "--strategy",
        strategy["ref"],
        "--claim",
        designed["claim"]["ref"],
        "--text",
        "Treat every delivery as a financial settlement",
        "--rationale",
        "This deliberately exceeds the supporting claim's impact",
        "--impact",
        "critical",
        expected=2,
    )
    assert result["error"]["code"] == "DECISION_CLAIM_IMPACT_TOO_LOW"


def test_local_receipt_is_portable_and_restricted_mode_never_falls_back(tmp_path, monkeypatch):
    copied = tmp_path / "copy"
    copied.mkdir()
    receipt = sandbox.execute(
        copied,
        ["/usr/bin/python3", "-c", "from pathlib import Path; Path('made').write_text('ok')"],
        10,
        mode="local",
    )
    assert receipt["exit_code"] == 0
    assert receipt["execution_mode"] == "local"
    assert receipt["enforced_restrictions"] == []
    assert "no OS security boundary" in receipt["isolation"]
    assert receipt["platform"]["system"]
    assert receipt["adapter"] == "local-process"
    assert receipt["before_tree"] != receipt["after_tree"]

    monkeypatch.setattr(sandbox.platform, "system", lambda: "Linux")
    with pytest.raises(Exception) as error:
        sandbox.execute(copied, ["/usr/bin/true"], 10, mode="restricted")
    assert getattr(error.value, "code", None) == "SANDBOX_UNAVAILABLE"

    monkeypatch.setattr(sandbox.platform, "system", lambda: "Windows")
    receipt = sandbox.execute(copied, ["/usr/bin/true"], 10, mode="local")
    assert receipt["execution_mode"] == "local"


def test_local_cli_records_actual_result_and_preserves_original(designed):
    env = designed
    original = (env["source"] / "app.txt").read_bytes()
    experiment = plan_experiment(env)
    command = json.dumps(
        [
            "/usr/bin/python3",
            "-c",
            "from pathlib import Path; Path('probe.txt').write_text('ok'); print('observed')",
        ]
    )
    result = env["call"](
        "experiment",
        "exec",
        experiment["ref"],
        "--command",
        command,
    )["result"]
    artifact = next(
        a
        for a in env["call"]("artifact", "list")["result"]
        if a["artifact_id"] == result["artifact"]["id"]
    )
    receipt = json.loads((env["root"] / artifact["storage_path"]).read_text())
    assert receipt["execution_mode"] == "local"
    assert receipt["included_source_snapshot_unchanged_after_execution"] is True
    assert receipt["stdout"]["text"].strip() == "observed"
    assert (env["source"] / "app.txt").read_bytes() == original
    env["call"](
        "experiment",
        "finish",
        experiment["ref"],
        "--outcome",
        "passed",
        "--conclusion",
        "The scoped probe produced the expected observation",
        "--limitations",
        "Local disposable execution did not enforce a security boundary",
    )


def test_local_experiment_rejects_explicit_original_source_path(designed):
    env = designed
    experiment = plan_experiment(env)
    command = json.dumps(
        [
            "/usr/bin/python3",
            "-c",
            "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('changed')",
            str(env["source"] / "app.txt"),
        ]
    )
    result = env["call"](
        "experiment",
        "exec",
        experiment["ref"],
        "--command",
        command,
        expected=2,
    )
    assert result["error"]["code"] == "UNSAFE_EXPERIMENT_COMMAND"
    assert (env["source"] / "app.txt").read_text() == "baseline"
    assert env["call"]("experiment", "list")["result"][-1]["experiment_status"] == "planned"
