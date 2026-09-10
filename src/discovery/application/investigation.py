import json
import sqlite3
from pathlib import Path

from discovery.adapters.sqlite.queries import state
from discovery.adapters.sqlite.records import entity, resolve
from discovery.domain.encoding import now
from discovery.domain.errors import require
from discovery.domain.investigation import lane_violations


def reopen(con: sqlite3.Connection, lane_id: int) -> None:
    """Invalidate closure and answers, including dependent lanes, without erasing prior work."""
    ids = [
        r[0]
        for r in con.execute(
            "WITH RECURSIVE affected(id) AS (SELECT ? UNION SELECT d.research_lane_id "
            "FROM research_lane_dependency d JOIN affected a ON "
            "d.depends_on_research_lane_id=a.id) "
            "SELECT id FROM affected",
            (lane_id,),
        )
    ]
    for lid in ids:
        con.execute(
            "UPDATE claim SET claim_status='proposed',dt_modified=? "
            "WHERE research_lane_id=? AND claim_status IN ('admissible','evidenced','survived')",
            (now(), lid),
        )
        con.execute(
            "UPDATE research_lane SET lane_status='active', closure_status='stale', "
            "dt_modified=? WHERE research_lane_id=? AND lane_status<>'superseded'",
            (now(), lid),
        )
        con.execute(
            "UPDATE research_need SET need_status='covered',dt_modified=? "
            "WHERE need_status='answered' AND research_need_id IN "
            "(SELECT research_need_id FROM research_lane_need WHERE research_lane_id=?)",
            (now(), lid),
        )


def active_lane(con: sqlite3.Connection, ref: str) -> dict:
    lane = resolve(con, "lane", ref)
    require(
        lane["lane_status"] in ("active", "procedurally_exhausted"),
        "LANE_NOT_ACTIVE",
        "Activate the lane first.",
    )
    return lane


def write(
    con: sqlite3.Connection, actor: int, name: str, data: dict, prepared: dict, root: Path
) -> dict:
    run = con.execute("SELECT * FROM discovery_run").fetchone()
    require(run["current_phase_no"] == 2, "WRONG_PHASE", "Investigation commands require Phase 2.")
    if name == "lane.activate":
        lane = resolve(con, "lane", data["ref"])
        require(
            lane["lane_status"] == "planned",
            "INVALID_STATE",
            "Only planned lanes can activate; use lane reopen otherwise.",
        )
        con.execute(
            "UPDATE research_lane SET lane_status='active',dt_modified=? WHERE research_lane_id=?",
            (now(), lane["research_lane_id"]),
        )
        return {"uuid": lane["research_lane_uuid"], "status": "active"}
    if name in ("lane.reopen", "lane.closure-begin", "lane.close"):
        lane = active_lane(con, data["ref"])
        lid = lane["research_lane_id"]
        if name == "lane.reopen":
            reopen(con, lid)
        elif name == "lane.closure-begin":
            require(
                lane["lane_status"] == "active",
                "INVALID_STATE",
                "Reopen a closed lane before another sweep.",
            )
            require(
                not con.execute(
                    "SELECT 1 FROM lead WHERE research_lane_id=? AND lead_status='pending'", (lid,)
                ).fetchone(),
                "LANE_HAS_OPEN_LEADS",
                "Investigate pending leads before closure.",
            )
            iteration = lane["closure_iteration"] + 1
            con.execute(
                "UPDATE research_lane SET "
                "closure_iteration=?,closure_status='running',dt_modified=? WHERE "
                "research_lane_id=?",
                (iteration, now(), lid),
            )
            policy = json.loads(run["config_json"])
            methods = [
                entity(
                    con,
                    "method",
                    research_lane_id=lid,
                    method_category="closure",
                    method_name=method,
                    iteration_no=iteration,
                )
                for method in policy["closure_methods_by_impact"][lane["impact"]]
            ]
            return {"uuid": lane["research_lane_uuid"], "iteration": iteration, "methods": methods}
        else:
            require(lane["lane_status"] == "active", "INVALID_STATE", "Lane already closed.")
            failures = lane_violations(state(con, root), lane)
            require(not failures, "LANE_GATE_FAILED", "Lane cannot close.", violations=failures)
            if (
                not data["answer"].strip().upper().startswith("UNKNOWN")
                and lane["impact"] != "contextual"
            ):
                rank = {"contextual": 0, "material": 1, "critical": 2}
                supported = any(
                    c["claim_status"] == "admissible" and rank[c["impact"]] >= rank[lane["impact"]]
                    for c in con.execute("SELECT * FROM claim WHERE research_lane_id=?", (lid,))
                )
                require(
                    supported,
                    "ANSWER_CLAIM_REQUIRED",
                    "A known material answer needs an admissible claim at the lane's impact.",
                )
            qid = None
            if data["question"]:
                qid = resolve(con, "question", data["question"])["clarification_question_id"]
            if (
                data["answer"].strip().upper().startswith("UNKNOWN")
                and lane["impact"] != "contextual"
            ):
                require(
                    qid,
                    "UNKNOWN_REQUIRES_QUESTION",
                    "Material UNKNOWN must reference a blocking question.",
                )
                q = con.execute(
                    "SELECT * FROM clarification_question WHERE clarification_question_id=?", (qid,)
                ).fetchone()
                require(
                    q["is_blocking"] == 1 and q["question_status"] == "open",
                    "UNKNOWN_REQUIRES_QUESTION",
                    "UNKNOWN requires an open blocking question.",
                )
            con.execute(
                "UPDATE research_lane SET "
                "lane_status='procedurally_exhausted',closure_status='completed',"
                "answer_text=?,limitations=?,answer_question_id=?,dt_modified=? "
                "WHERE research_lane_id=?",
                (data["answer"], data["limitations"], qid, now(), lid),
            )
        return {"uuid": lane["research_lane_uuid"], "operation": name}
    if name == "need.answer":
        need = resolve(con, "need", data["ref"])
        lanes = con.execute(
            "SELECT lane_row.* FROM research_lane lane_row JOIN research_lane_need n "
            "USING(research_lane_id) WHERE n.research_need_id=?",
            (need["research_need_id"],),
        ).fetchall()
        require(
            lanes
            and all(lane_row["lane_status"] == "procedurally_exhausted" for lane_row in lanes),
            "RESEARCH_NEED_UNCOVERED",
            "All covering lanes must close first.",
        )
        require(need["need_status"] != "superseded", "INVALID_STATE", "Need is superseded.")
        if data["answer"].strip().upper().startswith("UNKNOWN") and need["impact"] != "contextual":
            require(
                any(
                    row["answer_question_id"]
                    and con.execute(
                        "SELECT 1 FROM clarification_question WHERE clarification_question_id=? "
                        "AND is_blocking=1 AND question_status='open'",
                        (row["answer_question_id"],),
                    ).fetchone()
                    for row in lanes
                ),
                "UNKNOWN_REQUIRES_QUESTION",
                "An unresolved material need requires a covering lane linked "
                "to an open blocking question.",
            )
        con.execute(
            "UPDATE research_need SET need_status='answered',answer_text=?,dt_modified=? "
            "WHERE research_need_id=?",
            (data["answer"], now(), need["research_need_id"]),
        )
        return {"uuid": need["research_need_uuid"], "status": "answered"}
    if name == "lead.create":
        lane = active_lane(con, data["lane"])
        activity = resolve(con, "activity", data["activity"])
        require(
            activity["research_lane_id"] == lane["research_lane_id"],
            "SCOPE_MISMATCH",
            "Lead activity must belong to its lane.",
        )
        lead = entity(
            con,
            "lead",
            research_lane_id=lane["research_lane_id"],
            source_research_activity_id=activity["research_activity_id"],
            lead_description=data["text"],
            impact=data["impact"],
            created_by_actor_id=actor,
        )
        reopen(con, lane["research_lane_id"])
        return lead
    if name == "lead.disposition":
        lead = resolve(con, "lead", data["ref"])
        require(lead["lead_status"] == "pending", "INVALID_STATE", "Lead already terminal.")
        status = data["disposition"]
        duplicate, question = None, None
        if status == "duplicate":
            other = resolve(con, "lead", data["duplicate_of"])
            require(
                other["research_lane_id"] == lead["research_lane_id"]
                and other["lead_status"] not in ("pending", "duplicate")
                and other["lead_id"] != lead["lead_id"],
                "INVALID_DUPLICATE",
                "Duplicate must reference a terminal, nonduplicate lead in the same lane.",
            )
            duplicate = other["lead_id"]
        if status == "requires_human_input":
            q = resolve(con, "question", data["question"])
            require(
                q["is_blocking"] or lead["impact"] == "contextual",
                "BLOCKING_QUESTION_REQUIRED",
                "Material lead needs a blocking question.",
            )
            question = q["clarification_question_id"]
        if status == "investigated":
            activity = resolve(con, "activity", data["activity"])
            require(
                activity["research_lane_id"] == lead["research_lane_id"]
                and activity["research_activity_id"] != lead["source_research_activity_id"],
                "LEAD_ACTIVITY_REQUIRED",
                "Investigating a lead requires a separate same-lane research activity.",
            )
        con.execute(
            "UPDATE lead SET "
            "lead_status=?,disposition_reason=?,duplicate_of_lead_id=?,"
            "clarification_question_id=?,dt_modified=? WHERE lead_id=?",
            (status, data["reason"], duplicate, question, now(), lead["lead_id"]),
        )
        return {"uuid": lead["lead_uuid"], "status": status}
    if name == "method.create":
        lane = active_lane(con, data["lane"])
        result = entity(
            con,
            "method",
            research_lane_id=lane["research_lane_id"],
            method_category="primary",
            method_name=data["name"],
        )
        reopen(con, lane["research_lane_id"])
        return result
    if name in ("method.disposition", "surface.disposition", "research.record"):
        kind = "method" if name.startswith("method") else "surface"
        target = resolve(con, kind, data["ref"])
        lid = target["research_lane_id"]
        require(
            lid is not None, "SCOPE_MISMATCH", "Phase 2 writes must target a lane surface/method."
        )
        lane = active_lane(con, f"L-{lid}")
        require(
            lane["lane_status"] == "active",
            "INVALID_STATE",
            "Reopen a closed lane before more research.",
        )
        method = (
            target
            if kind == "method"
            else (resolve(con, "method", data["method"]) if data.get("method") else None)
        )
        if method:
            require(
                method["research_lane_id"] == lid,
                "SCOPE_MISMATCH",
                "Method and surface must belong to the same lane.",
            )
            require(
                method["method_category"] != "closure"
                or (
                    method["iteration_no"] == lane["closure_iteration"]
                    and lane["closure_status"] == "running"
                ),
                "LANE_CLOSURE_STALE",
                "Method belongs to an inactive closure iteration.",
            )
        if name == "research.record":
            artifact = entity(
                con,
                "artifact",
                artifact_kind="research_result",
                media_type="text/plain",
                captured_by_actor_id=actor,
                origin_uri=data["origin_uri"],
                **prepared["artifact"],
            )
            return entity(
                con,
                "activity",
                research_lane_id=lid,
                research_surface_id=target["research_surface_id"],
                research_method_id=method["research_method_id"] if method else None,
                actor_id=actor,
                activity_kind="search",
                query_or_action=data["query"],
                result_summary=data["summary"],
                result_artifact_id=artifact["id"],
            )
        tid = target[f"research_{kind}_id"]
        disposition = data["disposition"]
        if disposition in ("searched", "completed"):
            require(
                con.execute(
                    f"SELECT 1 FROM research_activity WHERE research_{kind}_id=?", (tid,)
                ).fetchone(),
                "METHOD_ACTIVITY_REQUIRED" if kind == "method" else "SURFACE_ACTIVITY_REQUIRED",
                "Record concrete research activity first.",
            )
        con.execute(
            f"UPDATE research_{kind} SET disposition=?,disposition_reason=?,"
            f"dt_modified=? WHERE research_{kind}_id=?",
            (disposition, data["reason"], now(), tid),
        )
        return {"uuid": target[f"research_{kind}_uuid"], "disposition": disposition}
    raise AssertionError(name)
