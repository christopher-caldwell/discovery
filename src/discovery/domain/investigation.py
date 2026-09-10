"""Phase 2 structural assurance; semantic truth remains an attributed judgment."""


def claim_violations(state: dict, claim: dict) -> list[dict]:
    failures = []

    def fail(code: str, message: str) -> None:
        failures.append({"code": code, "message": message})

    args = [a for a in state["argument"] if a["claim_id"] == claim["claim_id"]]
    evidence = {e["evidence_id"]: e for e in state["evidence"] if e["evidence_status"] == "active"}
    artifacts = {a["artifact_id"]: a for a in state["artifact"]}
    active_sources = {
        s["source_repository_id"] for s in state["sources"] if not s["observed_drift"]
    }

    def admissible(e: dict) -> bool:
        artifact = artifacts.get(e["artifact_id"], {})
        return bool(
            artifact
            and e["source_locator"].strip()
            and (
                artifact["source_repository_id"] is None
                or artifact["source_repository_id"] in active_sources
            )
        )

    support = []
    for argument in args:
        linked = [
            evidence[x["evidence_id"]]
            for x in state["argument_evidence"]
            if x["argument_id"] == argument["argument_id"] and x["evidence_id"] in evidence
        ]
        if argument["argument_role"] in ("refutes", "qualifies"):
            resolution = evidence.get(argument["resolution_evidence_id"])
            if not (
                argument["counter_status"] == "resolved"
                and resolution
                and admissible(resolution)
                and argument["resolution_reason"].strip()
            ):
                fail(
                    "COUNTEREVIDENCE_OPEN",
                    "Contrary or qualifying arguments require an evidenced disposition.",
                )
        if argument["argument_role"] == "supports" and argument["verification_status"] == "passed":
            support.extend(e for e in linked if admissible(e))
    if not support:
        fail(
            "ARGUMENT_NOT_VERIFIED",
            "A passed supporting argument with active artifact-backed evidence is required.",
        )
    profile = state["policy"]["evidence_profiles"].get(claim["impact"], [])
    if "primary_evidence" in profile and not any(
        e["evidence_kind"] in ("primary", "empirical") for e in support
    ):
        fail("PRIMARY_EVIDENCE_REQUIRED", "Direct/primary evidence is required for this impact.")
    lane_id = claim["research_lane_id"]
    lane = next(
        (
            lane_row
            for lane_row in state["research_lane"]
            if lane_row["research_lane_id"] == lane_id
        ),
        None,
    )
    for requirement in ("contradiction_search", "falsification", "empirical_verification"):
        if requirement not in profile:
            continue
        method_name = "contradiction" if requirement == "contradiction_search" else requirement
        methods = [
            m
            for m in state["research_method"]
            if m["research_lane_id"] == lane_id and m["method_name"] == method_name
        ]
        if method_name == "contradiction":
            methods = [
                m
                for m in methods
                if lane
                and m["method_category"] == "closure"
                and m["iteration_no"] == lane["closure_iteration"]
                and lane["closure_status"] in ("running", "completed")
            ]
        if not any(m["disposition"] == "completed" for m in methods):
            fail("VERIFICATION_METHOD_REQUIRED", f"Complete {method_name} for this claim's lane.")
    if "empirical_verification" in profile and not any(
        e["evidence_kind"] == "empirical" for e in support
    ):
        fail("EMPIRICAL_EVIDENCE_REQUIRED", "Critical claims require empirical evidence.")
    return failures


def lane_violations(state: dict, lane: dict) -> list[dict]:
    lid = lane["research_lane_id"]
    failures = []

    def fail(code: str, message: str) -> None:
        failures.append({"code": code, "message": message})

    if lane["lane_status"] not in ("active", "procedurally_exhausted"):
        fail("LANE_NOT_ACTIVE", "Activate the lane before closure.")
    if lane["closure_status"] not in ("running", "completed") or not lane["closure_iteration"]:
        fail("LANE_CLOSURE_STALE", "A fresh complete closure cycle is required.")
    if any(
        lane_row["research_lane_id"] == lid and lane_row["lead_status"] == "pending"
        for lane_row in state["lead"]
    ):
        fail("LANE_HAS_OPEN_LEADS", "Dispose every pending lead.")
    methods = [
        m
        for m in state["research_method"]
        if m["research_lane_id"] == lid
        and m["is_mandatory"]
        and (m["method_category"] == "primary" or m["iteration_no"] == lane["closure_iteration"])
    ]
    required = state["policy"]["closure_methods_by_impact"][lane["impact"]]
    for name in required:
        if not any(m["method_name"] == name and m["method_category"] == "closure" for m in methods):
            fail("REQUIRED_METHOD_PENDING", f"Missing closure method: {name}")
    for method in methods:
        if method["disposition"] == "pending":
            fail("REQUIRED_METHOD_PENDING", method["method_name"])
        elif method["disposition"] == "completed":
            if not any(
                a["research_method_id"] == method["research_method_id"]
                for a in state["research_activity"]
            ):
                fail("METHOD_ACTIVITY_REQUIRED", method["method_name"])
        elif not method["disposition_reason"].strip():
            fail("METHOD_REASON_REQUIRED", method["method_name"])
    for surface in state["research_surface"]:
        if surface["research_lane_id"] != lid:
            continue
        if surface["disposition"] == "pending":
            fail("REQUIRED_SURFACE_PENDING", surface["surface_name"])
        elif surface["disposition"] == "searched":
            if not any(
                a["research_surface_id"] == surface["research_surface_id"]
                for a in state["research_activity"]
            ):
                fail("SURFACE_ACTIVITY_REQUIRED", surface["surface_name"])
        elif not surface["disposition_reason"].strip():
            fail("SURFACE_REASON_REQUIRED", surface["surface_name"])
    for claim in state["claim"]:
        if claim["research_lane_id"] != lid or claim["impact"] == "contextual":
            continue
        if claim["claim_status"] in ("rejected", "superseded"):
            continue
        if claim["claim_status"] != "admissible":
            fail("CLAIM_NOT_ADMISSIBLE", claim["claim_statement"])
        failures.extend(claim_violations(state, claim))
    for dependency in state["research_lane_dependency"]:
        if dependency["research_lane_id"] == lid:
            other = next(
                lane_row
                for lane_row in state["research_lane"]
                if lane_row["research_lane_id"] == dependency["depends_on_research_lane_id"]
            )
            if other["lane_status"] != "procedurally_exhausted":
                fail("LANE_DEPENDENCY_OPEN", other["lane_question"])
    return failures


def phase_two_violations(state: dict) -> list[dict]:
    failures = []
    for need in state["research_need"]:
        if need["need_status"] not in ("answered", "superseded"):
            failures.append({"code": "RESEARCH_NEED_UNANSWERED", "message": need["need_statement"]})
    for lane in state["research_lane"]:
        if lane["lane_status"] == "superseded":
            continue
        if lane["lane_status"] != "procedurally_exhausted":
            failures.append({"code": "LANE_NOT_EXHAUSTED", "message": lane["lane_question"]})
        failures.extend(lane_violations(state, lane))
    if any(lane_row["lead_status"] == "pending" for lane_row in state["lead"]):
        failures.append(
            {"code": "LANE_HAS_OPEN_LEADS", "message": "Pending research leads remain."}
        )
    from discovery.domain.agents import group_violations

    return failures + group_violations(state, 2)
