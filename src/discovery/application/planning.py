import sqlite3
from pathlib import Path

from discovery.adapters.filesystem.artifacts import capture
from discovery.adapters.sqlite.queries import plan
from discovery.adapters.sqlite.records import entity, insert, resolve
from discovery.application.investigation import complete_record, reopen
from discovery.domain.encoding import canonical, digest, now, uid
from discovery.domain.errors import require


def write(
    con: sqlite3.Connection, actor: int, name: str, data: dict, prepared: dict, root: Path
) -> dict:
    run = con.execute("SELECT * FROM discovery_run").fetchone()
    require(
        run["current_phase_no"] == 1
        or (
            run["current_phase_no"] == 2
            and (
                name in ("need.create", "lane.create", "lane.depends-on", "question.resolve")
                or (name == "question.create" and data.get("technical"))
            )
        ),
        "WRONG_PHASE",
        "Intent and plan edits require Phase 1; regress first.",
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
            q["question_status"] == "open", "INVALID_STATE", "Question is already dispositioned."
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
            "This slice records current Phase 1 surface discovery only.",
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
