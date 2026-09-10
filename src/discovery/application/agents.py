"""Leased report isolation. Canonical import happens only after all replicas terminate."""

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from discovery.adapters.filesystem.artifacts import capture
from discovery.adapters.sqlite.queries import state
from discovery.adapters.sqlite.records import entity, resolve
from discovery.application.investigation import reopen
from discovery.domain.completion import current_spec, structure, structure_hash
from discovery.domain.encoding import canonical, now
from discovery.domain.errors import require


def expiry(seconds: int) -> str:
    return (datetime.now(UTC) + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def authorize(con: sqlite3.Connection, data: dict, *, terminal: bool = False) -> dict:
    a = resolve(con, "agent", data.get("agent_run") or data.get("ref"))
    require(
        a["lease_token_sha256"] and a["lease_token_sha256"] == data.get("lease_hash"),
        "LEASE_INVALID",
        "Lease does not own this investigator.",
    )
    require(a["dt_lease_expires"] > now(), "LEASE_EXPIRED", "Lease expired; explicitly reclaim it.")
    require(
        a["run_status"] == "running" or (terminal and a["run_status"] in ("completed", "failed")),
        "AGENT_NOT_RUNNING",
        "Investigator is not running.",
    )
    group = resolve(
        con,
        "group",
        str(
            con.execute(
                (
                    "SELECT investigation_group_uuid FROM investigation_group WHERE "
                    "investigation_group_id=?"
                ),
                (a["investigation_group_id"],),
            ).fetchone()[0]
        ),
    )
    run = con.execute("SELECT * FROM discovery_run").fetchone()
    require(
        group["group_status"] == "open"
        and group["phase_revision_id"] == run["current_phase_revision_id"],
        "AGENT_CONTEXT_STALE",
        "Investigator belongs to a closed or historical group.",
    )
    return a


def read(con: sqlite3.Connection, data: dict, root: Path) -> dict:
    a = authorize(con, data, terminal=True)
    artifact = con.execute(
        "SELECT * FROM artifact WHERE artifact_id=?", (a["context_artifact_id"],)
    ).fetchone()
    context = json.loads((root / artifact["storage_path"]).read_text())
    return {
        "agent_uuid": a["agent_run_uuid"],
        "status": a["run_status"],
        "expires": a["dt_lease_expires"],
        "context": context,
        "own_findings": [
            dict(r)
            for r in con.execute(
                "SELECT * FROM investigator_finding WHERE agent_run_id=?", (a["agent_run_id"],)
            )
        ],
    }


def write(
    con: sqlite3.Connection, actor: int, name: str, data: dict, prepared: dict, root: Path
) -> dict:
    run = con.execute("SELECT * FROM discovery_run").fetchone()
    require(
        run["current_phase_no"] in (2, 4),
        "WRONG_PHASE",
        "Investigators operate in Phase 2 or Phase 4.",
    )
    require(run["subagents_enabled"], "SUBAGENTS_DISABLED", "This run has subagents disabled.")
    if name == "group.dispatch":
        snapshot = state(con, root)
        lane = None
        spec = None
        if run["current_phase_no"] == 2:
            lane = resolve(con, "lane", data["lane"])
            require(lane["lane_status"] != "superseded", "INVALID_STATE", "Lane is superseded.")
        else:
            spec = current_spec(snapshot)
            require(
                spec and spec["structure_sha256"] == structure_hash(snapshot),
                "SPEC_STALE",
                "Compile current design first.",
            )
        count = data["count"]
        minimum = 2 if run["subagent_mode"] == "overlap" else 1
        require(
            minimum <= count <= 8 and (run["subagent_mode"] == "overlap" or count == 1),
            "INVALID_ARGUMENT",
            "Partitioned groups have one investigator; overlap groups have 2–8.",
        )
        # Independent groups see source/plan scope, not prior sibling reports or conclusions.
        context = {
            "run_uuid": run["discovery_run_uuid"],
            "source": snapshot["sources"],
            "request_artifact": next(
                a for a in snapshot["artifact"] if a["artifact_id"] == run["input_artifact_id"]
            ),
            "questions": snapshot["clarification_question"],
            "needs": snapshot["research_need"],
            "lane": lane,
            "policy": snapshot["policy"],
            "design": structure(snapshot) if spec else None,
            "spec": spec,
        }
        artifact = entity(
            con,
            "artifact",
            artifact_kind="isolated_context",
            media_type="application/json",
            captured_by_actor_id=actor,
            **capture(root, canonical(context).encode()),
        )
        g = entity(
            con,
            "group",
            phase_revision_id=run["current_phase_revision_id"],
            research_lane_id=lane["research_lane_id"] if lane else None,
            technical_spec_revision_id=spec["technical_spec_revision_id"] if spec else None,
            requested_count=count,
            context_artifact_id=artifact["id"],
            created_by_actor_id=actor,
        )
        agents = [
            entity(
                con,
                "agent",
                phase_revision_id=run["current_phase_revision_id"],
                research_lane_id=lane["research_lane_id"] if lane else None,
                actor_id=actor,
                run_role=(
                    "adversarial_challenger"
                    if run["current_phase_no"] == 4
                    else ("replica" if count > 1 else "primary")
                ),
                overlap_group_uuid=g["uuid"] if count > 1 else None,
                context_artifact_id=artifact["id"],
                investigation_group_id=g["id"],
            )
            for _ in range(count)
        ]
        if lane:
            reopen(con, lane["research_lane_id"])
        return {
            **g,
            "agents": agents,
            "context_sha256": con.execute(
                "SELECT artifact_sha256 FROM artifact WHERE artifact_id=?", (artifact["id"],)
            ).fetchone()[0],
        }
    if name in ("agent.start", "agent.reclaim"):
        a = resolve(con, "agent", data["ref"])
        require(
            data.get("lease_hash"),
            "LEASE_REQUIRED",
            "Supply a fresh random lease of at least 32 characters.",
        )
        if name == "agent.start":
            require(a["run_status"] == "pending", "INVALID_STATE", "Agent already started.")
        else:
            require(
                a["run_status"] == "running" and a["dt_lease_expires"] <= now(),
                "LEASE_ACTIVE",
                "Only expired running leases can be reclaimed.",
            )
            require(
                a["lease_token_sha256"] != data["lease_hash"],
                "LEASE_INVALID",
                "Reclaim needs a fresh token.",
            )
        group = con.execute(
            "SELECT * FROM investigation_group WHERE investigation_group_id=?",
            (a["investigation_group_id"],),
        ).fetchone()
        require(
            group
            and group["group_status"] == "open"
            and group["phase_revision_id"] == run["current_phase_revision_id"],
            "AGENT_CONTEXT_STALE",
            "Group is no longer active.",
        )
        require(
            actor != group["created_by_actor_id"],
            "INDEPENDENT_ACTOR_REQUIRED",
            "Use an investigator identity distinct from the orchestrator.",
        )
        require(
            not con.execute(
                "SELECT 1 FROM agent_run WHERE investigation_group_id=? AND actor_id=? "
                "AND dt_started IS NOT NULL AND agent_run_id<>?",
                (a["investigation_group_id"], actor, a["agent_run_id"]),
            ).fetchone(),
            "INDEPENDENT_ACTOR_REQUIRED",
            "Each replica needs a distinct attributed actor.",
        )
        deadline = expiry(json.loads(run["config_json"])["agent_lease_duration"])
        con.execute(
            (
                "UPDATE agent_run SET "
                "run_status='running',actor_id=?,lease_token_sha256=?,dt_lease_expires=?,dt_started=coalesce(dt_started,?)"
                " WHERE agent_run_id=?"
            ),
            (actor, data["lease_hash"], deadline, now(), a["agent_run_id"]),
        )
        return {"uuid": a["agent_run_uuid"], "expires": deadline}
    if name in ("agent.heartbeat", "agent.complete", "agent.finding"):
        a = authorize(con, data)
        require(
            a["actor_id"] == actor,
            "AGENT_ACTOR_MISMATCH",
            "The active lease belongs to another actor.",
        )
        deadline = expiry(json.loads(run["config_json"])["agent_lease_duration"])
        con.execute(
            "UPDATE agent_run SET dt_lease_expires=? WHERE agent_run_id=?",
            (deadline, a["agent_run_id"]),
        )
        if name == "agent.heartbeat":
            return {"uuid": a["agent_run_uuid"], "expires": deadline}
        if name == "agent.complete":
            report = entity(
                con,
                "artifact",
                artifact_kind="isolated_report",
                media_type="text/plain",
                captured_by_actor_id=actor,
                **prepared["artifact"],
            )
            require(
                data["outcome"] not in ("no_findings", "passed")
                or not con.execute(
                    "SELECT 1 FROM investigator_finding WHERE agent_run_id=? AND position<>?",
                    (a["agent_run_id"], "not_seen"),
                ).fetchone(),
                "FINDINGS_PRESENT",
                "Outcome must acknowledge recorded findings.",
            )
            con.execute(
                (
                    "UPDATE agent_run SET "
                    "run_status=?,run_outcome=?,report_artifact_id=?,dt_completed=? "
                    "WHERE agent_run_id=?"
                ),
                (
                    "failed" if data["outcome"] == "inconclusive" else "completed",
                    data["outcome"],
                    report["id"],
                    now(),
                    a["agent_run_id"],
                ),
            )
            return {"uuid": a["agent_run_uuid"], "outcome": data["outcome"]}
        if run["current_phase_no"] == 4:
            require(
                data["position"] in ("refute", "unique", "not_seen"),
                "INVALID_ARGUMENT",
                "Adversarial investigators submit challenges or not_seen.",
            )
        artifact = None
        if data["position"] != "not_seen":
            require(
                "artifact" in prepared,
                "EVIDENCE_REQUIRED",
                "A finding requires a captured source/report artifact.",
            )
            request_hash = con.execute(
                "SELECT artifact_sha256 FROM artifact WHERE artifact_id=?",
                (run["input_artifact_id"],),
            ).fetchone()[0]
            require(
                prepared["artifact"]["artifact_sha256"] != request_hash,
                "ASSERTION_NOT_EVIDENCE",
                "Request bytes cannot become investigator evidence.",
            )
            artifact = entity(
                con,
                "artifact",
                artifact_kind="isolated_finding_evidence",
                media_type="text/plain",
                origin_uri=data["origin_uri"],
                captured_by_actor_id=actor,
                **prepared["artifact"],
            )
        claim = resolve(con, "claim", data["claim"]) if data.get("claim") else None
        decision = resolve(con, "decision", data["decision"]) if data.get("decision") else None
        if claim and a["research_lane_id"]:
            require(
                claim["research_lane_id"] == a["research_lane_id"],
                "SCOPE_MISMATCH",
                "Claim belongs to another lane.",
            )
        return entity(
            con,
            "finding",
            agent_run_id=a["agent_run_id"],
            position=data["position"],
            finding_text=data["text"],
            impact=data["impact"],
            claim_id=claim["claim_id"] if claim else None,
            technical_decision_id=decision["technical_decision_id"] if decision else None,
            artifact_id=artifact["id"] if artifact else None,
        )
    if name.startswith("group."):
        g = resolve(con, "group", data["ref"])
        require(g["group_status"] == "open", "INVALID_STATE", "Group is terminal.")
        members = [
            dict(a)
            for a in con.execute(
                "SELECT * FROM agent_run WHERE investigation_group_id=?",
                (g["investigation_group_id"],),
            )
        ]
        require(
            g["phase_revision_id"] == run["current_phase_revision_id"],
            "AGENT_CONTEXT_STALE",
            "Group targets a historical traversal.",
        )
        if name == "group.supersede":
            con.execute(
                (
                    "UPDATE investigation_group SET "
                    "group_status='superseded',disposition_reason=? WHERE "
                    "investigation_group_id=?"
                ),
                (data["reason"], g["investigation_group_id"]),
            )
            con.execute(
                (
                    "UPDATE agent_run SET run_status='cancelled' WHERE "
                    "investigation_group_id=? AND run_status IN ('pending','running')"
                ),
                (g["investigation_group_id"],),
            )
            return {
                "uuid": g["investigation_group_uuid"],
                "status": "superseded",
                "requested": len(members),
            }
        require(
            all(a["run_status"] == "completed" for a in members),
            "CONSENSUS_INCOMPLETE",
            (
                "All requested replicas must complete; failed groups need an "
                "explicit replacement group."
            ),
        )
        findings = [
            dict(f)
            for f in con.execute(
                (
                    "SELECT f.* FROM investigator_finding f JOIN agent_run a "
                    "USING(agent_run_id) WHERE a.investigation_group_id=?"
                ),
                (g["investigation_group_id"],),
            )
        ]
        require(
            all(f["disposition"] != "pending" for f in findings),
            "FINDINGS_UNRECONCILED",
            "Reconcile every finding, including unique findings.",
        )
        report = entity(
            con,
            "artifact",
            artifact_kind="reconciliation",
            media_type="text/plain",
            captured_by_actor_id=actor,
            **prepared["artifact"],
        )
        con.execute(
            (
                "UPDATE investigation_group SET "
                "group_status='reconciled',report_artifact_id=?,disposition_reason=?"
                " WHERE investigation_group_id=?"
            ),
            (report["id"], data["reason"], g["investigation_group_id"]),
        )
        return {
            "uuid": g["investigation_group_uuid"],
            "requested": len(members),
            "completed": len(members),
            "positions": {
                p: sum(f["position"] == p for f in findings)
                for p in ("support", "refute", "not_seen", "unique")
            },
            "meaning": "Convergence is descriptive; canonical evidence gates still apply.",
        }
    if name == "finding.reconcile":
        f = resolve(con, "finding", data["ref"])
        a = resolve(
            con,
            "agent",
            str(
                con.execute(
                    "SELECT agent_run_uuid FROM agent_run WHERE agent_run_id=?",
                    (f["agent_run_id"],),
                ).fetchone()[0]
            ),
        )
        g = con.execute(
            "SELECT * FROM investigation_group WHERE investigation_group_id=?",
            (a["investigation_group_id"],),
        ).fetchone()
        require(
            g["phase_revision_id"] == run["current_phase_revision_id"]
            and g["group_status"] == "open",
            "AGENT_CONTEXT_STALE",
            "Group is historical.",
        )
        require(
            not con.execute(
                (
                    "SELECT 1 FROM agent_run WHERE investigation_group_id=? AND "
                    "run_status<>'completed'"
                ),
                (g["investigation_group_id"],),
            ).fetchone(),
            "CONSENSUS_INCOMPLETE",
            "Sibling outputs are reconciled only after all finish.",
        )
        require(f["disposition"] == "pending", "INVALID_STATE", "Finding already reconciled.")
        lid = g["research_lane_id"]
        lead = None
        defeater = None
        if f["position"] == "not_seen":
            status = "dismissed"
        else:
            # Every substantive finding becomes work. Majority cannot dismiss it.
            if lid:
                surface = con.execute(
                    "SELECT * FROM research_surface WHERE research_lane_id=? LIMIT 1", (lid,)
                ).fetchone()
                activity = entity(
                    con,
                    "activity",
                    research_lane_id=lid,
                    research_surface_id=surface["research_surface_id"],
                    actor_id=actor,
                    activity_kind="search",
                    query_or_action="Reconcile isolated finding",
                    result_summary=f["finding_text"],
                    result_artifact_id=f["artifact_id"],
                )
                lead = entity(
                    con,
                    "lead",
                    research_lane_id=lid,
                    source_research_activity_id=activity["id"],
                    lead_description=f["finding_text"],
                    impact=f["impact"],
                    created_by_actor_id=actor,
                )
                if f["claim_id"] and f["position"] in ("support", "refute"):
                    evidence = entity(
                        con,
                        "evidence",
                        research_lane_id=lid,
                        artifact_id=f["artifact_id"],
                        evidence_kind="secondary",
                        source_locator="Isolated investigator finding",
                        observation=f["finding_text"],
                        extracted_by_actor_id=actor,
                    )
                    arg = entity(
                        con,
                        "argument",
                        claim_id=f["claim_id"],
                        argument_role="refutes" if f["position"] == "refute" else "supports",
                        reasoning=f["finding_text"],
                        limitations=(
                            "Investigator report requires canonical verification and direct "
                            "corroboration"
                        ),
                        created_by_actor_id=actor,
                    )
                    con.execute(
                        "INSERT INTO argument_evidence VALUES (?,?)", (arg["id"], evidence["id"])
                    )
                reopen(con, lid)
                if f["position"] == "refute" and f["claim_id"]:
                    con.execute(
                        "UPDATE claim SET claim_status='contested' WHERE claim_id=?",
                        (f["claim_id"],),
                    )
            else:
                check = resolve(con, "challenge", data["check"])
                require(
                    check["technical_spec_revision_id"] == g["technical_spec_revision_id"],
                    "SCOPE_MISMATCH",
                    "Check must target the group spec.",
                )
                require(
                    f["claim_id"] or f["technical_decision_id"],
                    "TARGET_REQUIRED",
                    "Adversarial finding needs a claim or decision target.",
                )
                defeater = entity(
                    con,
                    "defeater",
                    phase_revision_id=run["current_phase_revision_id"],
                    adversarial_check_id=check["adversarial_check_id"],
                    challenge=f["finding_text"],
                    impact=f["impact"],
                    created_by_actor_id=actor,
                )
                if f["claim_id"]:
                    con.execute(
                        "INSERT INTO defeater_claim VALUES (?,?)", (defeater["id"], f["claim_id"])
                    )
                if f["technical_decision_id"]:
                    con.execute(
                        "INSERT INTO defeater_decision VALUES (?,?)",
                        (defeater["id"], f["technical_decision_id"]),
                    )
                target_claim = f["claim_id"]
                if not target_claim:
                    target_claim = con.execute(
                        "SELECT claim_id FROM technical_decision_claim "
                        "WHERE technical_decision_id=? LIMIT 1",
                        (f["technical_decision_id"],),
                    ).fetchone()
                    require(
                        target_claim,
                        "TARGET_REQUIRED",
                        "Decision needs a traced claim for evidence scope.",
                    )
                    target_claim = target_claim[0]
                lane_id = con.execute(
                    "SELECT research_lane_id FROM claim WHERE claim_id=?", (target_claim,)
                ).fetchone()[0]
                evidence = entity(
                    con,
                    "evidence",
                    research_lane_id=lane_id,
                    artifact_id=f["artifact_id"],
                    evidence_kind="secondary",
                    source_locator="Independent adversarial report",
                    observation=f["finding_text"],
                    extracted_by_actor_id=actor,
                )
                con.execute(
                    "INSERT INTO defeater_evidence VALUES (?,?,?)",
                    (defeater["id"], evidence["id"], "supports_challenge"),
                )
            status = "imported"
        con.execute(
            (
                "UPDATE investigator_finding SET "
                "disposition=?,disposition_reason=?,lead_id=?,defeater_id=? WHERE "
                "investigator_finding_id=?"
            ),
            (
                status,
                data["reason"],
                lead["id"] if lead else None,
                defeater["id"] if defeater else None,
                f["investigator_finding_id"],
            ),
        )
        return {
            "uuid": f["investigator_finding_uuid"],
            "status": status,
            "lead": lead,
            "defeater": defeater,
        }
    raise AssertionError(name)


def guard(con: sqlite3.Connection, name: str, logical: dict, actor: dict, prior: bool) -> None:
    if logical.get("agent_run") or (
        name.startswith("agent.") and name not in ("agent.start", "agent.reclaim")
    ):
        a = authorize(con, logical, terminal=bool(prior))
        identity = con.execute(
            "SELECT actor_uuid FROM actor WHERE actor_id=?", (a["actor_id"],)
        ).fetchone()[0]
        require(
            identity == actor["uuid"],
            "AGENT_ACTOR_MISMATCH",
            "Lease belongs to another actor.",
        )
        require(
            name in ("agent.heartbeat", "agent.complete", "agent.finding"),
            "AGENT_SCOPE_REQUIRED",
            "Isolated investigators submit findings/reports only.",
        )
    elif (
        name not in ("run.init", "run.upgrade", "agent.start", "agent.reclaim")
        and con.execute("PRAGMA user_version").fetchone()[0] == 5
    ):
        active = con.execute(
            (
                "SELECT 1 FROM agent_run a JOIN actor USING(actor_id) JOIN "
                "investigation_group g USING(investigation_group_id) WHERE "
                "actor.actor_uuid=? AND g.group_status='open' AND a.run_status IN "
                "('running','completed')"
            ),
            (actor["uuid"],),
        ).fetchone()
        require(
            not active,
            "AGENT_SCOPE_REQUIRED",
            "Isolated actors cannot mutate canonical state before reconciliation.",
        )
