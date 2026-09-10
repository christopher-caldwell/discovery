"""Deterministic design/proof/challenge gates; scores do not establish truth."""

from discovery.domain.encoding import canonical, digest
from discovery.domain.investigation import claim_violations, phase_two_violations

STRUCTURE = (
    "clarification_question",
    "assumption",
    "research_need",
    "research_lane",
    "research_lane_need",
    "claim",
    "argument",
    "argument_evidence",
    "evidence",
    "implementation_strategy",
    "technical_decision",
    "technical_decision_claim",
    "proof_obligation",
    "proof_obligation_evidence",
    "proof_obligation_experiment",
    "experiment",
    "technical_requirement",
)


def structure(state: dict) -> dict:
    linked = {
        x["evidence_id"] for x in state["argument_evidence"] + state["proof_obligation_evidence"]
    }
    linked.update(a["resolution_evidence_id"] for a in state["argument"])
    content = {t: state[t] for t in STRUCTURE}
    content["evidence"] = [e for e in state["evidence"] if e["evidence_id"] in linked]
    return {
        **content,
        "source_baselines": [
            {k: s[k] for k in ("repository_uri", "baseline_revision", "baseline_tree_hash")}
            for s in state["sources"]
        ],
    }


def structure_hash(state: dict) -> str:
    return digest(canonical(structure(state)).encode())


def current_spec(state: dict) -> dict | None:
    return next(
        iter(
            sorted(
                (s for s in state["technical_spec_revision"] if s["spec_status"] != "superseded"),
                key=lambda s: s["revision_no"],
                reverse=True,
            )
        ),
        None,
    )


def obligation_supported(state: dict, obligation: dict) -> bool:
    oid = obligation["proof_obligation_id"]
    evidence_ids = {
        x["evidence_id"]
        for x in state["proof_obligation_evidence"]
        if x["proof_obligation_id"] == oid and x["relationship"] == "supports"
    }
    evidence = [
        e
        for e in state["evidence"]
        if e["evidence_id"] in evidence_ids and e["evidence_status"] == "active"
    ]
    experiments = {
        x["experiment_id"]
        for x in state["proof_obligation_experiment"]
        if x["proof_obligation_id"] == oid
    }
    passed = any(
        e["experiment_id"] in experiments
        and e["experiment_status"] == "passed"
        and e["execution_exit_code"] == 0
        and e["execution_artifact_id"]
        and not e["superseded_by_experiment_id"]
        for e in state["experiment"]
    )
    if obligation["evidence_profile"] == "empirical":
        return passed or any(e["evidence_kind"] == "empirical" for e in evidence)
    return passed or any(e["evidence_kind"] in ("primary", "empirical") for e in evidence)


def design_violations(state: dict, *, draft: bool = True) -> list[dict]:
    failures = phase_two_violations(state)

    def fail(code, message):
        failures.append({"code": code, "message": message})

    selected = [s for s in state["implementation_strategy"] if s["strategy_status"] == "selected"]
    if len(selected) != 1:
        fail("STRATEGY_SELECTION_REQUIRED", "Exactly one strategy must be selected.")
    if any(s["strategy_status"] == "candidate" for s in state["implementation_strategy"]):
        fail("STRATEGY_UNDECIDED", "Reject or select all competing strategies.")
    decisions = [d for d in state["technical_decision"] if d["decision_status"] == "accepted"]
    if not decisions:
        fail("DECISION_REQUIRED", "The selected strategy needs accepted decisions.")
    for d in state["technical_decision"]:
        did = d["technical_decision_id"]
        if d["decision_status"] == "proposed" and d["impact"] != "contextual":
            fail("DECISION_UNDECIDED", d["decision_statement"])
        if d["decision_status"] != "accepted":
            continue
        if (
            not selected
            or d["implementation_strategy_id"] != selected[0]["implementation_strategy_id"]
        ):
            fail("DECISION_STRATEGY_MISMATCH", d["decision_statement"])
        links = [
            x["claim_id"]
            for x in state["technical_decision_claim"]
            if x["technical_decision_id"] == did
        ]
        claims = [c for c in state["claim"] if c["claim_id"] in links]
        if d["impact"] != "contextual" and not claims:
            fail("DECISION_TRACE_REQUIRED", d["decision_statement"])
        for c in claims:
            if c["claim_status"] != "admissible" or claim_violations(state, c):
                fail("DECISION_CLAIM_UNSUPPORTED", c["claim_statement"])
        obligations = [o for o in state["proof_obligation"] if o["technical_decision_id"] == did]
        if d["impact"] != "contextual" and not obligations:
            fail("PROOF_REQUIRED", d["decision_statement"])
        for o in obligations:
            if o["obligation_status"] == "not_applicable" and o["disposition_reason"].strip():
                continue
            if o["obligation_status"] != "satisfied" or not obligation_supported(state, o):
                fail("PROOF_UNSATISFIED", o["obligation_description"])
        for e in state["experiment"]:
            if e["technical_decision_id"] == did and not e["superseded_by_experiment_id"]:
                if e["experiment_status"] != "passed" or e["execution_exit_code"] != 0:
                    fail("EXPERIMENT_INCOMPLETE", e["experiment_name"])
        if not any(r["technical_decision_id"] == did for r in state["technical_requirement"]):
            fail("REQUIREMENT_TRACE_REQUIRED", d["decision_statement"])
    for need in state["research_need"]:
        if need["need_status"] != "superseded" and not any(
            r["research_need_id"] == need["research_need_id"]
            and any(d["technical_decision_id"] == r["technical_decision_id"] for d in decisions)
            for r in state["technical_requirement"]
        ):
            fail("NEED_REQUIREMENT_UNCOVERED", need["need_statement"])
    if draft:
        spec = current_spec(state)
        if not spec or spec["structure_sha256"] != structure_hash(state):
            fail("SPEC_STALE", "Compile a draft from the current structured state.")
    return failures


def adversarial_violations(state: dict) -> list[dict]:
    failures = design_violations(state)
    spec = current_spec(state)
    checks = [
        c
        for c in state["adversarial_check"]
        if spec
        and c["technical_spec_revision_id"] == spec["technical_spec_revision_id"]
        and c["phase_revision_id"] == state["phase"]["phase_revision_id"]
    ]
    for category in state["policy"]["phase4_challenge_categories"]:
        if not any(
            c["check_category"] == category
            and c["check_status"] != "pending"
            and (
                c["report_artifact_id"]
                or c["check_status"] in ("not_applicable", "unavailable", "inaccessible")
            )
            for c in checks
        ):
            failures.append({"code": "CHALLENGE_INCOMPLETE", "message": category})
    for d in state["defeater"]:
        if d["defeater_status"] == "defeated":
            linked = {
                x["evidence_id"]
                for x in state["defeater_evidence"]
                if x["defeater_id"] == d["defeater_id"] and x["relationship"] == "refutes_challenge"
            }
            if not d["resolution_artifact_id"] or not any(
                e["evidence_id"] in linked and e["evidence_status"] == "active"
                for e in state["evidence"]
            ):
                failures.append({"code": "DEFEATER_RESOLUTION_STALE", "message": d["challenge"]})
        if d["defeater_status"] not in ("defeated", "superseded", "accepted"):
            failures.append({"code": "DEFEATER_OPEN", "message": d["challenge"]})
        if d["defeater_status"] == "accepted" and d["impact"] != "contextual":
            failures.append({"code": "MATERIAL_RISK_UNACCEPTABLE", "message": d["challenge"]})
    from discovery.domain.agents import group_violations

    return failures + group_violations(state, 4)


def assurance(state: dict) -> dict:
    """Percent coverage with explicit limitations; never a probability of correctness."""
    checks = [
        c
        for c in state["adversarial_check"]
        if current_spec(state)
        and c["technical_spec_revision_id"] == current_spec(state)["technical_spec_revision_id"]
        and c["phase_revision_id"] == state["phase"]["phase_revision_id"]
    ]
    coverage = sum(c["check_status"].startswith("completed") for c in checks)
    total = len(state["policy"]["phase4_challenge_categories"])
    obligations = [
        o
        for o in state["proof_obligation"]
        if any(
            d["technical_decision_id"] == o["technical_decision_id"]
            and d["decision_status"] == "accepted"
            for d in state["technical_decision"]
        )
    ]
    dimensions = {
        "intent": 100
        if not any(q["question_status"] == "open" for q in state["clarification_question"])
        else 0,
        "research_coverage": 100 if not phase_two_violations(state) else 0,
        "evidence_strength": 100 if not design_violations(state, draft=False) else 0,
        "implementation_validation": round(
            100
            * sum(o["obligation_status"] == "satisfied" for o in obligations)
            / max(1, len(obligations))
        ),
        "adversarial_resilience": min(100, round(100 * coverage / max(1, total))),
    }
    return {
        "model": "structural-coverage-v1",
        "dimensions": dimensions,
        "overall": min(dimensions.values()),
        "meaning": (
            "Procedural coverage indicators, not correctness probabilities. "
            "N/A and unavailable reduce demonstrated coverage."
        ),
    }


def review_hash(state: dict) -> str:
    return digest(
        canonical(
            {
                k: state[k]
                for k in (
                    "adversarial_check",
                    "defeater",
                    "defeater_evidence",
                    "investigation_group",
                    "investigator_finding",
                    "technical_spec_revision",
                )
            }
        ).encode()
    )
