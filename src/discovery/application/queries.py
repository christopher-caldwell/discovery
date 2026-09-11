from pathlib import Path

from discovery.adapters.sqlite.audit import verify
from discovery.adapters.sqlite.connection import connect
from discovery.adapters.sqlite.queries import plan, state
from discovery.adapters.sqlite.records import ENTITIES, resolve
from discovery.domain.encoding import canonical, digest
from discovery.domain.errors import require
from discovery.domain.gates import phase_violations
from discovery.domain.investigation import claim_violations, lane_violations


def query(
    root: Path,
    name: str,
    ref: str | None = None,
    *,
    scope: dict | None = None,
    actor_uuid: str | None = None,
) -> dict | list:
    con = connect(root / "discovery.sqlite")
    try:
        con.execute("PRAGMA query_only=ON")
        con.execute("BEGIN")
        require(
            con.execute("PRAGMA user_version").fetchone()[0] in (5, 6)
            or (
                name == "audit.verify"
                and con.execute("PRAGMA user_version").fetchone()[0] in (3, 4)
            ),
            "SCHEMA_VERSION_UNSUPPORTED",
            "Schema 5 or 6 required for reads; use run upgrade for schema 3 or 4.",
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
        if scope and scope.get("agent_run"):
            require(
                name == "resume",
                "AGENT_SCOPE_REQUIRED",
                "Isolated investigators may read only their scoped resume packet.",
            )
            from discovery.application.agents import read

            return read(con, scope, root)
        if actor_uuid:
            active = con.execute(
                (
                    "SELECT 1 FROM agent_run a JOIN actor USING(actor_id) JOIN "
                    "investigation_group g USING(investigation_group_id) WHERE "
                    "actor.actor_uuid=? AND g.group_status='open' AND a.run_status IN "
                    "('running','completed')"
                ),
                (actor_uuid,),
            ).fetchone()
            require(
                not active,
                "AGENT_SCOPE_REQUIRED",
                "Use --agent-run and --lease for isolated context.",
            )
        if name == "assessment.list":
            from discovery.application.assessments import project

            return project(state(con, root))
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
        if name == "spec.snapshot":
            return snapshot
        if name == "report.export":
            from discovery.application.reporting import export_report

            return export_report(root, snapshot, audit)
        if name == "assurance.calculate":
            from discovery.domain.completion import assurance

            return assurance(snapshot)
        if name == "spec.export":
            import json

            from discovery.adapters.filesystem.artifacts import atomic_write
            from discovery.domain.completion import current_spec

            spec = current_spec(snapshot)
            require(spec is not None, "SPEC_REQUIRED", "Compile a spec first.")
            bundle = json.loads(spec["bundle_json"])
            folder = root / "exports" / spec["technical_spec_revision_uuid"]
            for filename, a in bundle.items():
                path = folder / filename
                require(
                    not folder.is_symlink()
                    and not path.is_symlink()
                    and folder.resolve().is_relative_to(root.resolve()),
                    "EXPORT_CONFLICT",
                    "Export path contains a symlink.",
                )
                content = (root / a["storage_path"]).read_bytes()
                require(
                    not path.exists() or path.read_bytes() == content,
                    "EXPORT_CONFLICT",
                    "Export file already has different content.",
                )
                atomic_write(path, content)
            return {"directory": str(folder), "files": [str(folder / n) for n in bundle]}
        if name in ("lane.check", "claim.check"):
            kind = name.split(".")[0]
            record = resolve(con, kind, ref)
            violations = (lane_violations if kind == "lane" else claim_violations)(snapshot, record)
            return {"satisfied": not violations, "violations": violations}
        violations = phase_violations(snapshot)
        gate = {"can_advance": not violations, "violations": violations}
        reporting = {
            "command": "report export",
            "available": True,
            "kind": "interim",
            "requires_phase_completion": False,
            "finalizes_run": False,
            "meaning": (
                "Export recorded observations and limitations now, including for blocked or "
                "explanation-only requests. Phase gates govern advancement, not this export; "
                "the report retains unmet gates and does not imply verified conclusions."
            ),
        }
        if name == "phase.check":
            return {**gate, "reporting": reporting}
        run = snapshot["run"]
        result = {
            "run_uuid": run["discovery_run_uuid"],
            "title": run["run_title"],
            "status": run["run_status"],
            "phase": snapshot["phase"],
            "source_baselines": snapshot["sources"],
            "gate": gate,
            "reporting": reporting,
            "audit_head": audit["head_hash"],
        }
        if name == "status":
            return result
        next_actions = ["status", "resume", "phase check", "audit verify", "report export"]
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
            if run["current_phase_no"] == 3:
                next_actions += [
                    "strategy create/select/reject",
                    "decision create/accept/reject",
                    "obligation create/satisfy",
                    "experiment plan/exec/finish",
                    "requirement create",
                    "spec draft",
                ]
            if run["current_phase_no"] == 4:
                next_actions += [
                    "challenge initialize/complete",
                    "defeater create/link-check/confirm/defeat",
                    "spec revise",
                    "assurance calculate",
                ]
            if not violations:
                next_actions.append("phase advance")
        from discovery.application.assessments import project

        packet = {
            **result,
            "confidence": project(snapshot),
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
            "research_activities": snapshot["research_activity"],
            "research_reports": [
                a
                for a in snapshot["artifact"]
                if a["artifact_id"]
                in {r["result_artifact_id"] for r in snapshot["research_activity"]}
            ],
            "lanes": snapshot["research_lane"],
            "open_leads": [x for x in snapshot["lead"] if x["lead_status"] == "pending"],
            "claims": snapshot["claim"],
            "evidence": snapshot["evidence"],
            "arguments": snapshot["argument"],
            "research_methods": snapshot["research_method"],
            "strategies": snapshot["implementation_strategy"],
            "decisions": snapshot["technical_decision"],
            "requirements": snapshot["technical_requirement"],
            "experiments": snapshot["experiment"],
            "specifications": snapshot["technical_spec_revision"],
            "adversarial_checks": snapshot["adversarial_check"],
            "proof_obligations": snapshot["proof_obligation"],
            "defeaters": snapshot["defeater"],
            "defeater_checks": snapshot.get("defeater_check", []),
            "legal_next_actions": next_actions,
            "recent_events": [
                dict(r)
                for r in con.execute(
                    "SELECT event_uuid, command_name, dt_created "
                    "FROM event_log ORDER BY event_log_id DESC LIMIT 5"
                )
            ],
        }
        if scope and scope.get("compact"):
            from discovery.application.context import compact_resume

            return compact_resume(packet)
        return packet
    finally:
        con.rollback()
        con.close()
