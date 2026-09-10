from pathlib import Path

from discovery.adapters.sqlite.audit import verify
from discovery.adapters.sqlite.connection import connect
from discovery.adapters.sqlite.queries import plan, state
from discovery.adapters.sqlite.records import ENTITIES, resolve
from discovery.domain.encoding import canonical, digest
from discovery.domain.errors import require
from discovery.domain.gates import phase_violations
from discovery.domain.investigation import claim_violations, lane_violations


def query(root: Path, name: str, ref: str | None = None) -> dict | list:
    con = connect(root / "discovery.sqlite")
    try:
        con.execute("PRAGMA query_only=ON")
        con.execute("BEGIN")
        require(
            con.execute("PRAGMA user_version").fetchone()[0] == 4
            or (name == "audit.verify" and con.execute("PRAGMA user_version").fetchone()[0] == 3),
            "SCHEMA_VERSION_UNSUPPORTED",
            "Schema 4 required; use run upgrade for schema 3.",
        )
        require(
            con.execute("SELECT 1 FROM discovery_run").fetchone(),
            "RUN_NOT_FOUND",
            "No initialized run.",
        )
        audit = verify(con, root)
        if name == "audit.verify":
            return audit
        require(
            audit["valid"], "AUDIT_INTEGRITY_FAILURE", "Run integrity verification failed.", **audit
        )
        if name.endswith(".list"):
            kind = name.split(".")[0]
            table, prefix = ENTITIES[kind]
            return [
                {**dict(r), "uuid": r[table + "_uuid"], "ref": f"{prefix}-{r[table + '_id']:03d}"}
                for r in con.execute(f"SELECT * FROM {table} ORDER BY {table}_id")
            ]
        if name == "plan.snapshot":
            packet = plan(con)
            return {"plan_sha256": digest(canonical(packet).encode()), "context": packet}
        snapshot = state(con, root)
        if name in ("lane.check", "claim.check"):
            kind = name.split(".")[0]
            record = resolve(con, kind, ref)
            violations = (lane_violations if kind == "lane" else claim_violations)(snapshot, record)
            return {"satisfied": not violations, "violations": violations}
        violations = phase_violations(snapshot)
        gate = {"can_advance": not violations, "violations": violations}
        if name == "phase.check":
            return gate
        run = snapshot["run"]
        result = {
            "run_uuid": run["discovery_run_uuid"],
            "title": run["run_title"],
            "status": run["run_status"],
            "phase": snapshot["phase"],
            "source_baselines": snapshot["sources"],
            "gate": gate,
            "audit_head": audit["head_hash"],
        }
        if name == "status":
            return result
        next_actions = ["status", "resume", "phase check", "audit verify"]
        if run["run_status"] == "active":
            if run["current_phase_no"] == 1:
                next_actions += [
                    "question create",
                    "question resolve",
                    "research-need create",
                    "lane create",
                    "surface disposition",
                    "research record",
                    "plan snapshot",
                    "plan review",
                    "source refresh",
                ]
            else:
                next_actions += ["phase regress"]
                if run["current_phase_no"] == 2:
                    next_actions += [
                        "question create --technical",
                        "question resolve",
                        "lane activate",
                        "lead create",
                        "research record",
                        "artifact capture",
                        "evidence create",
                        "claim create",
                        "argument create",
                        "argument verify",
                        "claim evaluate",
                        "lane closure-begin",
                        "lane close",
                        "research-need answer",
                        "source refresh",
                    ]
            if not violations:
                next_actions.append("phase advance")
        return {
            **result,
            "policy": snapshot["policy"],
            "input_artifact_id": run["input_artifact_id"],
            "intent": "Request assertions and answered questions; intent extraction is deferred.",
            "input_artifact": dict(
                con.execute(
                    "SELECT * FROM artifact WHERE artifact_id=?", (run["input_artifact_id"],)
                ).fetchone()
            ),
            "questions": snapshot["clarification_question"],
            "assumptions": snapshot["assumption"],
            "research_needs": snapshot["research_need"],
            "lanes": snapshot["research_lane"],
            "open_leads": [x for x in snapshot["lead"] if x["lead_status"] == "pending"],
            "claims": snapshot["claim"],
            "evidence": snapshot["evidence"],
            "arguments": snapshot["argument"],
            "research_methods": snapshot["research_method"],
            "proof_obligations": snapshot["proof_obligation"],
            "defeaters": snapshot["defeater"],
            "legal_next_actions": next_actions,
            "recent_events": [
                dict(r)
                for r in con.execute(
                    "SELECT event_uuid, command_name, dt_created "
                    "FROM event_log ORDER BY event_log_id DESC LIMIT 5"
                )
            ],
        }
    finally:
        con.rollback()
        con.close()
