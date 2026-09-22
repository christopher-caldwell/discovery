import sqlite3
from pathlib import Path

from discovery.adapters.sqlite.queries import state
from discovery.adapters.sqlite.records import entity, resolve
from discovery.domain.completion import current_spec, structure_hash
from discovery.domain.encoding import now
from discovery.domain.errors import require


def record_check_link(con, defeater_id, check_id, actor, reason="Original owning check"):
    con.execute(
        "INSERT INTO defeater_check "
        "(defeater_id,adversarial_check_id,link_reason,linked_by_actor_id) VALUES (?,?,?,?)",
        (defeater_id, check_id, reason, actor),
    )


def write(
    con: sqlite3.Connection, actor: int, name: str, data: dict, prepared: dict, root: Path
) -> dict:
    snapshot = state(con, root)
    run = snapshot["run"]
    phase = run["current_phase_no"]
    # Earlier phases may defeat a confirmed challenge after explicit regression and repair.
    require(phase == 4 or name == "defeater.defeat", "WRONG_PHASE", "Challenges require Phase 4.")
    spec = current_spec(snapshot)
    if name.startswith("challenge.") or name in ("defeater.create", "defeater.link-check"):
        require(
            spec and spec["structure_sha256"] == structure_hash(snapshot),
            "SPEC_STALE",
            "Current compiled design required.",
        )
    if name == "challenge.initialize":
        require(
            not any(
                c["technical_spec_revision_id"] == spec["technical_spec_revision_id"]
                and c["phase_revision_id"] == run["current_phase_revision_id"]
                for c in snapshot["adversarial_check"]
            ),
            "INVALID_STATE",
            "Checklist already initialized for this spec and traversal.",
        )
        return {
            "checks": [
                entity(
                    con,
                    "challenge",
                    phase_revision_id=run["current_phase_revision_id"],
                    technical_spec_revision_id=spec["technical_spec_revision_id"],
                    check_category=c,
                    check_name=c,
                    scope="Entire current specification",
                    created_by_actor_id=actor,
                )
                for c in snapshot["policy"]["phase4_challenge_categories"]
            ]
        }
    if name == "challenge.complete":
        c = resolve(con, "challenge", data["ref"])
        require(
            c["technical_spec_revision_id"] == spec["technical_spec_revision_id"]
            and c["phase_revision_id"] == run["current_phase_revision_id"],
            "SCOPE_MISMATCH",
            "Check targets a historical spec/traversal.",
        )
        require(c["check_status"] == "pending", "INVALID_STATE", "Check already completed.")
        if data["disposition"] == "completed_findings":
            require(
                any(
                    link["adversarial_check_id"] == c["adversarial_check_id"]
                    for link in snapshot["defeater_check"]
                ),
                "DEFEATER_REQUIRED",
                "Record linked defeaters first.",
            )
        report = entity(
            con,
            "artifact",
            artifact_kind="adversarial_report",
            media_type="text/plain",
            captured_by_actor_id=actor,
            **prepared["artifact"],
        )
        con.execute(
            (
                "UPDATE adversarial_check SET "
                "check_status=?,disposition_reason=?,report_artifact_id=?,completed_by_actor_id=?,dt_modified=?"
                " WHERE adversarial_check_id=?"
            ),
            (
                data["disposition"],
                data["reason"],
                report["id"],
                actor,
                now(),
                c["adversarial_check_id"],
            ),
        )
        return {"uuid": c["adversarial_check_uuid"], "status": data["disposition"]}
    if name == "challenge.review":
        checks = [resolve(con, "challenge", ref) for ref in data["checks"]]
        require(
            len({c["adversarial_check_id"] for c in checks}) == len(checks),
            "INVALID_ARGUMENT",
            "List each reviewed challenge once.",
        )
        for check in checks:
            require(
                check["technical_spec_revision_id"] == spec["technical_spec_revision_id"]
                and check["phase_revision_id"] == run["current_phase_revision_id"],
                "SCOPE_MISMATCH",
                "Every check must target the current spec and traversal.",
            )
            require(check["check_status"] == "pending", "INVALID_STATE", "Check already completed.")
            if data["disposition"] == "completed_findings":
                require(
                    any(
                        link["adversarial_check_id"] == check["adversarial_check_id"]
                        for link in snapshot["defeater_check"]
                    ),
                    "DEFEATER_REQUIRED",
                    "Every finding disposition needs a linked defeater.",
                )
        report = entity(
            con,
            "artifact",
            artifact_kind="adversarial_report",
            media_type="text/plain",
            captured_by_actor_id=actor,
            **prepared["artifact"],
        )
        for check in checks:
            con.execute(
                "UPDATE adversarial_check SET check_status=?,disposition_reason=?,"
                "report_artifact_id=?,completed_by_actor_id=?,dt_modified=? "
                "WHERE adversarial_check_id=?",
                (
                    data["disposition"],
                    data["reason"],
                    report["id"],
                    actor,
                    now(),
                    check["adversarial_check_id"],
                ),
            )
        return {
            "checks": [c["adversarial_check_uuid"] for c in checks],
            "status": data["disposition"],
            "report": report,
        }
    if name == "defeater.create":
        c = resolve(con, "challenge", data["check"])
        require(
            c["technical_spec_revision_id"] == spec["technical_spec_revision_id"]
            and c["phase_revision_id"] == run["current_phase_revision_id"],
            "SCOPE_MISMATCH",
            "Challenge targets a historical spec.",
        )
        require(c["check_status"] == "pending", "INVALID_STATE", "Check already completed.")
        require(
            data.get("claim") or data.get("decision"),
            "TARGET_REQUIRED",
            "Target a claim or decision.",
        )
        e = resolve(con, "evidence", data["evidence_ref"])
        require(
            e["evidence_status"] == "active", "INVALID_STATE", "Challenge evidence must be active."
        )
        d = entity(
            con,
            "defeater",
            phase_revision_id=run["current_phase_revision_id"],
            adversarial_check_id=c["adversarial_check_id"],
            challenge=data["text"],
            impact=data["impact"],
            created_by_actor_id=actor,
        )
        record_check_link(con, d["id"], c["adversarial_check_id"], actor)
        for kind, table in [("claim", "defeater_claim"), ("decision", "defeater_decision")]:
            if data.get(kind):
                target = resolve(con, kind, data[kind])
                field = "claim_id" if kind == "claim" else "technical_decision_id"
                con.execute(f"INSERT INTO {table} VALUES (?,?)", (d["id"], target[field]))
        con.execute(
            "INSERT INTO defeater_evidence VALUES (?,?,?)",
            (d["id"], e["evidence_id"], "supports_challenge"),
        )
        return d
    d = resolve(con, "defeater", data["ref"])
    if name == "defeater.link-check":
        c = resolve(con, "challenge", data["check"])
        owner = next(
            check
            for check in snapshot["adversarial_check"]
            if check["adversarial_check_id"] == d["adversarial_check_id"]
        )
        require(
            c["technical_spec_revision_id"]
            == owner["technical_spec_revision_id"]
            == spec["technical_spec_revision_id"]
            and c["phase_revision_id"]
            == owner["phase_revision_id"]
            == d["phase_revision_id"]
            == run["current_phase_revision_id"],
            "SCOPE_MISMATCH",
            "Defeater and check must target the same current spec and Phase 4 traversal.",
        )
        require(
            isinstance(data["reason"], str) and data["reason"].strip(),
            "INVALID_ARGUMENT",
            "Explain why this canonical finding also covers the check.",
        )
        existing = con.execute(
            "SELECT 1 FROM defeater_check WHERE defeater_id=? AND adversarial_check_id=?",
            (d["defeater_id"], c["adversarial_check_id"]),
        ).fetchone()
        if existing:
            return {
                "uuid": d["defeater_uuid"],
                "check_uuid": c["adversarial_check_uuid"],
                "linked": False,
                "status": d["defeater_status"],
            }
        require(c["check_status"] == "pending", "INVALID_STATE", "Check already completed.")
        require(
            d["defeater_status"] in ("open", "inconclusive", "confirmed"),
            "INVALID_STATE",
            "Cannot attach a terminal defeater to another check.",
        )
        record_check_link(con, d["defeater_id"], c["adversarial_check_id"], actor, data["reason"])
        return {
            "uuid": d["defeater_uuid"],
            "check_uuid": c["adversarial_check_uuid"],
            "linked": True,
            "status": d["defeater_status"],
        }
    require(
        d["defeater_status"] in ("open", "inconclusive", "confirmed"),
        "INVALID_STATE",
        "Defeater already terminal.",
    )
    report_id = None
    if name == "defeater.defeat":
        require(
            d["defeater_status"] != "confirmed"
            or d["confirmed_phase_revision_id"] != run["current_phase_revision_id"],
            "REGRESSION_REQUIRED",
            "Confirmed challenge requires explicit regression before repair.",
        )
        e = resolve(con, "evidence", data["evidence_ref"])
        require(
            e["evidence_status"] == "active", "INVALID_STATE", "Resolution evidence must be active."
        )
        hashes = {
            r[0]
            for r in con.execute(
                (
                    "SELECT a.artifact_sha256 FROM defeater_evidence de JOIN evidence "
                    "e USING(evidence_id) JOIN artifact a USING(artifact_id) WHERE "
                    "de.defeater_id=?"
                ),
                (d["defeater_id"],),
            )
        }
        h = con.execute(
            "SELECT artifact_sha256 FROM artifact WHERE artifact_id=?", (e["artifact_id"],)
        ).fetchone()[0]
        require(
            h not in hashes,
            "RESOLUTION_EVIDENCE_REQUIRED",
            "Use distinct evidence to defeat the challenge.",
        )
        con.execute(
            "INSERT INTO defeater_evidence VALUES (?,?,?)",
            (d["defeater_id"], e["evidence_id"], "refutes_challenge"),
        )
        report = entity(
            con,
            "artifact",
            artifact_kind="defeater_resolution",
            media_type="text/plain",
            captured_by_actor_id=actor,
            **prepared["artifact"],
        )
        report_id = report["id"]
        status = "defeated"
    elif name == "defeater.confirm":
        status = "confirmed"
    else:
        require(
            d["impact"] == "contextual",
            "MATERIAL_RISK_UNACCEPTABLE",
            "Only contextual risks may be accepted.",
        )
        status = "accepted"
    con.execute(
        (
            "UPDATE defeater SET "
            "defeater_status=?,resolution=?,resolution_artifact_id=?,confirmed_phase_revision_id=?,dt_modified=?"
            " WHERE defeater_id=?"
        ),
        (
            status,
            data["reason"],
            report_id,
            run["current_phase_revision_id"]
            if status == "confirmed"
            else d["confirmed_phase_revision_id"],
            now(),
            d["defeater_id"],
        ),
    )
    return {
        "uuid": d["defeater_uuid"],
        "status": status,
        "regression_required": status == "confirmed",
    }
