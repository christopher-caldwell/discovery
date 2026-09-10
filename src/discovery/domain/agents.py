def group_violations(state: dict, phase: int) -> list[dict]:
    if not state["run"]["subagents_enabled"]:
        return []
    revisions = {
        p["phase_revision_id"]
        for p in state["phase_revision"]
        if p["phase_no"] == phase and p["revision_status"] != "invalidated"
    }
    groups = [
        g
        for g in state["investigation_group"]
        if g["phase_revision_id"] in revisions and g["group_status"] != "superseded"
    ]
    failures = []
    scopes = (
        [
            lane["research_lane_id"]
            for lane in state["research_lane"]
            if lane["lane_status"] != "superseded"
        ]
        if phase == 2
        else [None]
    )
    if phase == 4:
        from discovery.domain.completion import current_spec

        spec = current_spec(state)
        groups = [
            g
            for g in groups
            if spec and g["technical_spec_revision_id"] == spec["technical_spec_revision_id"]
        ]
    for scope in scopes:
        relevant = [g for g in groups if g["research_lane_id"] == scope]
        if not relevant or any(g["group_status"] != "reconciled" for g in relevant):
            failures.append(
                {
                    "code": "CONSENSUS_INCOMPLETE",
                    "message": f"Reconciliation incomplete: scope {scope}, phase {phase}.",
                }
            )
    return failures
