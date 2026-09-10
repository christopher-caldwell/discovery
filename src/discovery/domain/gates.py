"""Pure policy over a normalized snapshot; semantic judgments are recorded inputs."""

from discovery.domain.completion import adversarial_violations, design_violations
from discovery.domain.investigation import phase_two_violations


def phase_violations(state: dict) -> list[dict]:
    failures = []

    def fail(code: str, message: str) -> None:
        failures.append({"code": code, "message": message})

    phase = state["phase"]["phase_no"]
    if state["run"]["run_status"] != "active":
        fail("RUN_NOT_ACTIVE", "Run is not active.")
    for source in state["sources"]:
        if source["observed_drift"] or source["drift_status"] != "current":
            fail(
                "SOURCE_DRIFT",
                "Source baseline changed; use source refresh and revalidate affected evidence.",
            )
    for q in state["clarification_question"]:
        if q["question_status"] == "open":
            fail(
                "BLOCKING_QUESTION_OPEN" if q["is_blocking"] else "QUESTION_UNDISPOSITIONED",
                q["question_text"],
            )
        if q["question_status"] == "assumed":
            assumptions = [
                a
                for a in state["assumption"]
                if a["clarification_question_id"] == q["clarification_question_id"]
                and a["assumption_status"] == "active"
            ]
            if q["is_blocking"] or not assumptions:
                fail(
                    "INVALID_ASSUMPTION",
                    "A blocking question cannot be assumed; others need an active assumption.",
                )
    for a in state["assumption"]:
        if a["impact"] == "critical" and a["assumption_status"] == "active":
            fail("CRITICAL_ASSUMPTION", a["assumption_text"])
    # Finalization emits a new immutable specification. Its reviewed draft's
    # checklist must not be interpreted as missing work on a closed run.
    if state["run"]["run_status"] != "active":
        return failures
    if phase == 2:
        return failures + phase_two_violations(state)
    if phase == 3:
        return failures + design_violations(state)
    if phase == 4:
        return failures + adversarial_violations(state)
    revision = state["phase"]["phase_revision_id"]
    surfaces = [
        s
        for s in state["research_surface"]
        if s["phase_revision_id"] == revision and s["research_lane_id"] is None
    ]
    for name in state["policy"]["mandatory_phase1_surfaces"]:
        if not any(s["surface_name"] == name and s["is_mandatory"] for s in surfaces):
            fail("REQUIRED_SURFACE_PENDING", f"Missing mandatory surface: {name}")
    for s in surfaces:
        if s["disposition"] == "pending":
            fail("REQUIRED_SURFACE_PENDING", s["surface_name"])
        elif s["disposition"] == "searched":
            if not any(
                a["research_surface_id"] == s["research_surface_id"]
                for a in state["research_activity"]
            ):
                fail("SURFACE_ACTIVITY_REQUIRED", s["surface_name"])
        elif not s["disposition_reason"].strip():
            fail("SURFACE_REASON_REQUIRED", s["surface_name"])
    needs = {
        n["research_need_id"]: n for n in state["research_need"] if n["need_status"] != "superseded"
    }
    lanes = {
        n["research_lane_id"]: n for n in state["research_lane"] if n["lane_status"] != "superseded"
    }
    links = state["research_lane_need"]
    for nid, need in needs.items():
        if not need["source_artifact_id"]:
            fail("NEED_PROVENANCE_REQUIRED", need["need_statement"])
        if not any(x["research_need_id"] == nid and x["research_lane_id"] in lanes for x in links):
            fail("RESEARCH_NEED_UNCOVERED", need["need_statement"])
    rank = {"contextual": 0, "material": 1, "critical": 2}
    for lid, lane in lanes.items():
        linked = [
            needs[x["research_need_id"]]
            for x in links
            if x["research_lane_id"] == lid and x["research_need_id"] in needs
        ]
        if not linked:
            fail("ORPHAN_LANE", lane["lane_question"])
        if any(rank[n["impact"]] > rank[lane["impact"]] for n in linked):
            fail("LANE_IMPACT_TOO_LOW", lane["lane_question"])
        if any(
            not lane[key].strip()
            for key in ("lane_question", "why_it_matters", "scope", "evidence_profile")
        ):
            fail("LANE_INCOMPLETE", lane["lane_question"])
        if lane["evidence_profile"] != lane["impact"]:
            fail("INVALID_EVIDENCE_PROFILE", lane["lane_question"])
        if not any(
            m["research_lane_id"] == lid and m["is_mandatory"] and m["method_category"] == "primary"
            for m in state["research_method"]
        ):
            fail("REQUIRED_METHOD_PENDING", lane["lane_question"])
        if not any(
            s["research_lane_id"] == lid and s["is_mandatory"] for s in state["research_surface"]
        ):
            fail("LANE_SURFACE_REQUIRED", lane["lane_question"])
    graph = {lid: set() for lid in lanes}
    for edge in state["research_lane_dependency"]:
        a, b = edge["research_lane_id"], edge["depends_on_research_lane_id"]
        if a not in lanes or b not in lanes:
            fail("INVALID_LANE_DEPENDENCY", "Dependency references a superseded lane.")
        else:
            graph[a].add(b)
    while graph:
        roots = {key for key, deps in graph.items() if not deps}
        if not roots:
            fail("LANE_DEPENDENCY_CYCLE", "Lane dependencies must form a DAG.")
            break
        graph = {key: deps - roots for key, deps in graph.items() if key not in roots}
    if not any(
        r["phase_revision_id"] == revision and r["artifact_sha256"] == state["plan_sha256"]
        for r in state["reviews"]
    ):
        fail("STALE_REVIEW", "A passed semantic review of this exact plan snapshot is required.")
    return failures
