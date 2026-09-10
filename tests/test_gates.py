from copy import deepcopy

import pytest
from conftest import ready

from discovery.adapters.sqlite.connection import connect
from discovery.adapters.sqlite.queries import state
from discovery.domain.gates import phase_violations


@pytest.mark.parametrize(
    "case,code",
    [
        ("missing_surface", "REQUIRED_SURFACE_PENDING"),
        ("searched_without_activity", "SURFACE_ACTIVITY_REQUIRED"),
        ("reason_missing", "SURFACE_REASON_REQUIRED"),
        ("uncovered_need", "RESEARCH_NEED_UNCOVERED"),
        ("orphan_lane", "ORPHAN_LANE"),
        ("method_missing", "REQUIRED_METHOD_PENDING"),
        ("lane_surface_missing", "LANE_SURFACE_REQUIRED"),
        ("lane_scope_missing", "LANE_INCOMPLETE"),
        ("profile_weakened", "INVALID_EVIDENCE_PROFILE"),
        ("critical_assumption", "CRITICAL_ASSUMPTION"),
        ("assumed_blocker", "INVALID_ASSUMPTION"),
    ],
)
def test_gate_rejects_structurally_invalid_plans(run, case, code):
    ready(run)
    con = connect(run["root"] / "discovery.sqlite")
    snapshot = deepcopy(state(con, run["root"]))
    con.close()
    phase_surface = next(s for s in snapshot["research_surface"] if s["research_lane_id"] is None)
    if case == "missing_surface":
        snapshot["research_surface"].remove(phase_surface)
    elif case == "searched_without_activity":
        phase_surface["disposition"] = "searched"
    elif case == "reason_missing":
        phase_surface["disposition_reason"] = ""
    elif case in ("uncovered_need", "orphan_lane"):
        snapshot["research_lane_need"] = []
    elif case == "method_missing":
        snapshot["research_method"] = []
    elif case == "lane_surface_missing":
        snapshot["research_surface"] = [
            s for s in snapshot["research_surface"] if s["research_lane_id"] is None
        ]
    elif case == "lane_scope_missing":
        snapshot["research_lane"][0]["scope"] = ""
    elif case == "profile_weakened":
        snapshot["research_lane"][0]["evidence_profile"] = "contextual"
    elif case == "critical_assumption":
        snapshot["assumption"] = [
            {
                "impact": "critical",
                "assumption_status": "active",
                "assumption_text": "Critical unknown",
            }
        ]
    elif case == "assumed_blocker":
        snapshot["clarification_question"] = [
            {"is_blocking": 1, "question_status": "assumed", "clarification_question_id": 1}
        ]
    assert code in {violation["code"] for violation in phase_violations(snapshot)}
