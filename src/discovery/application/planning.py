import sqlite3
from pathlib import Path

from discovery.adapters.filesystem.artifacts import capture
from discovery.adapters.sqlite.queries import plan
from discovery.adapters.sqlite.records import entity, insert, resolve
from discovery.application.investigation import complete_record, reopen
from discovery.domain.encoding import canonical, digest, now, uid
from discovery.domain.errors import require

RANK = {"contextual": 0, "material": 1, "critical": 2}


def invalidate_assumption_dependents(con: sqlite3.Connection, assumption_id: int) -> None:
    claim_ids = [
        row[0]
        for row in con.execute(
            "SELECT claim_id FROM assumption_claim WHERE assumption_id=?",
            (assumption_id,),
        )
    ]
    for claim_id in claim_ids:
        claim = con.execute("SELECT * FROM claim WHERE claim_id=?", (claim_id,)).fetchone()
        if claim["claim_status"] not in ("rejected", "superseded"):
            con.execute(
                "UPDATE claim SET claim_status='proposed',dt_modified=? WHERE claim_id=?",
                (now(), claim_id),
            )
            reopen(con, claim["research_lane_id"])
    con.execute(
        "UPDATE technical_decision SET decision_status='proposed',dt_modified=? "
        "WHERE technical_decision_id IN (SELECT technical_decision_id "
        "FROM assumption_decision WHERE assumption_id=?) "
        "AND decision_status='accepted'",
        (now(), assumption_id),
    )


def write(
    con: sqlite3.Connection, actor: int, name: str, data: dict, prepared: dict, root: Path
) -> dict:
    run = con.execute("SELECT * FROM discovery_run").fetchone()
    phase = run["current_phase_no"]
    require(
        phase == 1
        or (
            phase == 2
            and (
                name
                in (
                    "need.create",
                    "lane.create",
                    "lane.depends-on",
                    "question.resolve",
                    "question.respondent-add",
                    "assumption.discharge",
                    "assumption.invalidate",
                    "assumption.link-claim",
                )
                or (name == "question.create" and data.get("technical"))
            )
        )
        or (
            phase in (3, 4)
            and name
            in (
                "question.resolve",
                "assumption.discharge",
                "assumption.invalidate",
                "assumption.link-decision",
            )
        ),
        "WRONG_PHASE",
        (
            "research record applies to Phase 1 planning or Phase 2 lane surfaces. "
            "In Phase 3/4, capture the report with artifact capture and link appropriate "
            "evidence, proof or defeater records; do not regress merely to save a review."
            if name == "research.record"
            else "Intent and plan edits require Phase 1; regress first."
        ),
    )
    revision = run["current_phase_revision_id"]
    provenance = {"phase_revision_id": revision, "created_by_actor_id": actor}
    if name == "question.create":
        return entity(
            con,
            "question",
            question_text=data["text"],
            is_blocking=int(not data["non_blocking"]),
            authority_category=data["authority"],
            authority_confidence=data["authority_confidence"],
            authority_rationale=data["rationale"],
            **provenance,
        )
    if name == "question.resolve":
        q = resolve(con, "question", data["ref"])
        require(
            q["question_status"] in ("open", "assumed"),
            "INVALID_STATE",
            "Question is already dispositioned.",
        )
        assumptions = con.execute(
            "SELECT * FROM assumption WHERE clarification_question_id=? "
            "AND assumption_status='active'",
            (q["clarification_question_id"],),
        ).fetchall()
        if assumptions:
            confirms = bool(data.get("confirms_assumption"))
            contradicts = bool(data.get("contradicts_assumption"))
            require(
                confirms != contradicts,
                "ASSUMPTION_RELATION_REQUIRED",
                "Resolving an assumed question requires exactly one of "
                "--confirms-assumption or --contradicts-assumption.",
            )
            status = "discharged" if confirms else "invalidated"
            note = (
                "Confirmed by the recorded answer"
                if confirms
                else "Contradicted by the recorded answer"
            )
            for assumption in assumptions:
                con.execute(
                    "UPDATE assumption SET assumption_status=?,resolution_notes=?,dt_modified=? "
                    "WHERE assumption_id=?",
                    (status, note, now(), assumption["assumption_id"]),
                )
                if contradicts:
                    invalidate_assumption_dependents(con, assumption["assumption_id"])
        else:
            require(
                not data.get("confirms_assumption") and not data.get("contradicts_assumption"),
                "INVALID_ARGUMENT",
                "Assumption relationship flags apply only to an assumed question.",
            )
        con.execute(
            "UPDATE clarification_question SET question_status='answered', answer_text=?, "
            "answered_by_actor_id=?, dt_modified=? WHERE clarification_question_id=?",
            (data["answer"], actor, now(), q["clarification_question_id"]),
        )
        if run["current_phase_no"] == 2:
            affected = con.execute(
                "SELECT research_lane_id FROM research_lane WHERE answer_question_id=? "
                "UNION SELECT research_lane_id FROM lead WHERE clarification_question_id=?",
                (q["clarification_question_id"], q["clarification_question_id"]),
            ).fetchall()
            for row in affected:
                reopen(con, row[0])
        return {"uuid": q["clarification_question_uuid"], "status": "answered"}
    if name == "question.assume":
        q = resolve(con, "question", data["ref"])
        require(q["question_status"] == "open", "INVALID_STATE", "Question is not open.")
        require(not q["is_blocking"], "BLOCKING_QUESTION", "A blocking question cannot be assumed.")
        require(
            data["impact"] != "critical",
            "CRITICAL_ASSUMPTION",
            "Critical uncertainty must block.",
        )
        assumption = entity(
            con,
            "assumption",
            phase_revision_id=revision,
            clarification_question_id=q["clarification_question_id"],
            assumption_text=data["text"],
            impact=data["impact"],
            justification=data["justification"],
            scope=data["scope"],
            invalidation_condition=data["invalidates_when"],
            created_by_actor_id=actor,
        )
        con.execute(
            "UPDATE clarification_question SET question_status='assumed',dt_modified=? "
            "WHERE clarification_question_id=?",
            (now(), q["clarification_question_id"]),
        )
        return {**assumption, "question_ref": data["ref"], "status": "active"}
    if name == "question.withdraw":
        q = resolve(con, "question", data["ref"])
        require(q["question_status"] == "open", "INVALID_STATE", "Only open questions withdraw.")
        con.execute(
            "UPDATE clarification_question SET question_status='withdrawn',answer_text=?,"
            "answered_by_actor_id=?,dt_modified=? WHERE clarification_question_id=?",
            (data["reason"], actor, now(), q["clarification_question_id"]),
        )
        return {"uuid": q["clarification_question_uuid"], "status": "withdrawn"}
    if name == "question.reclassify":
        q = resolve(con, "question", data["ref"])
        require(q["question_status"] == "open", "INVALID_STATE", "Only open questions reclassify.")
        blocking = int(data["blocking"])
        con.execute(
            "UPDATE clarification_question SET is_blocking=?,authority_rationale=?,dt_modified=? "
            "WHERE clarification_question_id=?",
            (
                blocking,
                q["authority_rationale"] + " Reclassification: " + data["reason"],
                now(),
                q["clarification_question_id"],
            ),
        )
        return {"uuid": q["clarification_question_uuid"], "is_blocking": bool(blocking)}
    if name == "question.respondent-add":
        q = resolve(con, "question", data["ref"])
        require(q["question_status"] == "open", "INVALID_STATE", "Question is not open.")
        require(data["rank"] >= 1, "INVALID_ARGUMENT", "Respondent rank starts at 1.")
        artifact_id = None
        if data.get("artifact"):
            artifact_id = resolve(con, "artifact", data["artifact"])["artifact_id"]
        result = entity(
            con,
            "respondent",
            clarification_question_id=q["clarification_question_id"],
            respondent_rank=data["rank"],
            respondent_kind=data["kind"],
            respondent_name=data["name"],
            respondent_confidence=data["confidence"],
            rationale=data["rationale"],
            supporting_artifact_id=artifact_id,
            created_by_actor_id=actor,
            identity_status="unknown" if data["identity_unknown"] else "known",
        )
        return result
    if name == "assumption.create":
        require(
            data["impact"] != "critical",
            "CRITICAL_ASSUMPTION",
            "Critical uncertainty must block.",
        )
        return entity(
            con,
            "assumption",
            phase_revision_id=revision,
            assumption_text=data["text"],
            impact=data["impact"],
            justification=data["justification"],
            scope=data["scope"],
            invalidation_condition=data["invalidates_when"],
            created_by_actor_id=actor,
        )
    if name in ("assumption.discharge", "assumption.invalidate"):
        assumption = resolve(con, "assumption", data["ref"])
        require(
            assumption["assumption_status"] == "active",
            "INVALID_STATE",
            "Assumption is not active.",
        )
        status = "discharged" if name.endswith("discharge") else "invalidated"
        con.execute(
            "UPDATE assumption SET assumption_status=?,resolution_notes=?,dt_modified=? "
            "WHERE assumption_id=?",
            (status, data["reason"], now(), assumption["assumption_id"]),
        )
        if status == "invalidated":
            invalidate_assumption_dependents(con, assumption["assumption_id"])
        return {"uuid": assumption["assumption_uuid"], "status": status}
    if name in ("assumption.link-claim", "assumption.link-decision"):
        assumption = resolve(con, "assumption", data["ref"])
        require(
            assumption["assumption_status"] == "active",
            "INVALID_STATE",
            "Assumption is not active.",
        )
        kind = "claim" if name.endswith("claim") else "decision"
        target = resolve(con, kind, data["target"])
        require(
            RANK[assumption["impact"]] >= RANK[target["impact"]],
            "ASSUMPTION_IMPACT_TOO_LOW",
            "An assumption cannot understate the impact of its dependent conclusion.",
        )
        require(
            not (kind == "decision" and target["impact"] == "critical"),
            "CRITICAL_DECISION_REQUIRES_CLAIM",
            "A critical decision cannot rely on an assumption; link an admissible critical claim.",
        )
        table = "assumption_claim" if kind == "claim" else "assumption_decision"
        key = "claim_id" if kind == "claim" else "technical_decision_id"
        con.execute(
            f"INSERT INTO {table} (assumption_id,{key},dependency_reason,linked_by_actor_id) "
            "VALUES (?,?,?,?)",
            (assumption["assumption_id"], target[key], data["reason"], actor),
        )
        uuid_field = "claim_uuid" if kind == "claim" else "technical_decision_uuid"
        return {
            "assumption_uuid": assumption["assumption_uuid"],
            "target_uuid": target[uuid_field],
        }
    if name == "need.create":
        return entity(
            con,
            "need",
            need_statement=data["text"],
            why_it_matters=data["rationale"],
            impact=data["impact"],
            source_artifact_id=run["input_artifact_id"],
            **provenance,
        )
    if name == "lane.create":
        needs = [resolve(con, "need", ref) for ref in data["needs"]]
        rank = {"contextual": 0, "material": 1, "critical": 2}
        require(
            all(
                n["need_status"] != "superseded" and rank[n["impact"]] <= rank[data["impact"]]
                for n in needs
            ),
            "LANE_IMPACT_TOO_LOW",
            "Lane impact must cover every linked active need.",
        )
        lane = entity(
            con,
            "lane",
            lane_question=data["text"],
            why_it_matters=data["rationale"],
            scope=data["scope"],
            impact=data["impact"],
            evidence_profile=data["impact"],
            **provenance,
        )
        for need in needs:
            con.execute(
                "UPDATE research_need SET need_status='covered',dt_modified=? WHERE "
                "research_need_id=?",
                (now(), need["research_need_id"]),
            )
            con.execute(
                "INSERT INTO research_lane_need VALUES (?,?)",
                (lane["id"], need["research_need_id"]),
            )
        for method in data["methods"]:
            insert(
                con,
                "research_method",
                research_method_uuid=uid(),
                research_lane_id=lane["id"],
                method_category="primary",
                method_name=method,
            )
        for surface in data["surfaces"]:
            entity(
                con,
                "surface",
                research_lane_id=lane["id"],
                surface_kind=surface,
                surface_name=surface,
                **provenance,
            )
        return lane
    if name == "surface.create":
        require(
            not con.execute(
                "SELECT 1 FROM research_surface WHERE phase_revision_id=? "
                "AND research_lane_id IS NULL AND surface_name=?",
                (revision, data["name"]),
            ).fetchone(),
            "INVALID_STATE",
            "A current planning surface already has this name.",
        )
        return entity(
            con,
            "surface",
            phase_revision_id=revision,
            surface_kind="investigator_added",
            surface_name=data["name"],
            is_mandatory=1,
            addition_reason=data["reason"],
            created_by_actor_id=actor,
        )
    if name == "lane.depends-on":
        lane = resolve(con, "lane", data["ref"])
        dep = resolve(con, "lane", data["depends_on"])
        a, b = lane["research_lane_id"], dep["research_lane_id"]
        cycle = con.execute(
            "WITH RECURSIVE reachable(id) AS (SELECT ? UNION SELECT d.depends_on_research_lane_id "
            "FROM research_lane_dependency d JOIN reachable r ON d.research_lane_id=r.id) "
            "SELECT 1 FROM reachable WHERE id=?",
            (b, a),
        ).fetchone()
        require(not cycle, "LANE_DEPENDENCY_CYCLE", "Dependency would create a cycle.")
        con.execute("INSERT INTO research_lane_dependency VALUES (?,?,?)", (a, b, data["reason"]))
        if run["current_phase_no"] == 2:
            reopen(con, a)
        return {
            "lane_uuid": lane["research_lane_uuid"],
            "depends_on_uuid": dep["research_lane_uuid"],
        }
    if name in ("surface.disposition", "research.record"):
        surface = resolve(con, "surface", data["ref"])
        require(
            surface["phase_revision_id"] == revision and surface["research_lane_id"] is None,
            "WRONG_PHASE",
            "Phase 1 requires a current planning surface from surface list "
            "(research_lane_id is null). Lane surfaces are researched in Phase 2.",
        )
        sid = surface["research_surface_id"]
        if name == "research.record":
            require(
                not data.get("complete_method"),
                "WRONG_PHASE",
                "Method completion requires a linked Phase 2 lane method.",
            )
            artifact = entity(
                con,
                "artifact",
                artifact_kind="research_result",
                media_type="text/plain",
                captured_by_actor_id=actor,
                origin_uri=data["origin_uri"],
                **capture(root, prepared["content"]),
            )
            result = entity(
                con,
                "activity",
                research_surface_id=sid,
                actor_id=actor,
                activity_kind="search",
                query_or_action=data["query"],
                result_summary=data["summary"],
                result_artifact_id=artifact["id"],
            )
            complete_record(con, sid, None, data)
            return result
        if data["disposition"] == "searched":
            require(
                con.execute(
                    "SELECT 1 FROM research_activity WHERE research_surface_id=?", (sid,)
                ).fetchone(),
                "SURFACE_ACTIVITY_REQUIRED",
                "Record actual research before marking searched.",
            )
        con.execute(
            "UPDATE research_surface SET disposition=?, disposition_reason=?, dt_dispositioned=?, "
            "dt_modified=? WHERE research_surface_id=?",
            (data["disposition"], data["reason"], now(), now(), sid),
        )
        return {"uuid": surface["research_surface_uuid"], "disposition": data["disposition"]}
    if name == "plan.review":
        actual = digest(canonical(plan(con)).encode())
        require(
            actual == data["plan_hash"] == prepared["context"]["artifact_sha256"],
            "STALE_REVIEW",
            "Plan changed since the supplied snapshot.",
        )
        context = entity(
            con,
            "artifact",
            artifact_kind="plan_context",
            media_type="application/json",
            captured_by_actor_id=actor,
            **prepared["context"],
        )
        report = entity(
            con,
            "artifact",
            artifact_kind="semantic_review",
            media_type="text/plain",
            captured_by_actor_id=actor,
            **prepared["artifact"],
        )
        return entity(
            con,
            "review",
            phase_revision_id=revision,
            actor_id=actor,
            run_role="semantic_verifier",
            run_status="completed",
            run_outcome=data["outcome"],
            context_artifact_id=context["id"],
            report_artifact_id=report["id"],
            dt_started=now(),
            dt_completed=now(),
            status_details="Synchronous attributed review submission",
        )
    raise AssertionError(f"Unknown planning command: {name}")
