import sqlite3
from pathlib import Path

from discovery.adapters.sqlite.queries import state
from discovery.adapters.sqlite.records import entity, resolve
from discovery.application.investigation import active_lane, reopen
from discovery.domain.encoding import now
from discovery.domain.errors import require
from discovery.domain.investigation import claim_violations


def invalidate_claim(con: sqlite3.Connection, claim_id: int) -> None:
    claim = con.execute("SELECT * FROM claim WHERE claim_id=?", (claim_id,)).fetchone()
    if claim["claim_status"] not in ("rejected", "superseded"):
        con.execute(
            "UPDATE claim SET claim_status='proposed',dt_modified=? WHERE claim_id=?",
            (now(), claim_id),
        )
    reopen(con, claim["research_lane_id"])


def write(
    con: sqlite3.Connection, actor: int, name: str, data: dict, prepared: dict, root: Path
) -> dict:
    run = con.execute("SELECT * FROM discovery_run").fetchone()
    require(
        run["current_phase_no"] == 2 or name in ("evidence.create", "evidence.retract"),
        "WRONG_PHASE",
        "Claim/evidence work requires Phase 2.",
    )
    if name == "evidence.create":
        lane = active_lane(con, data["lane"])
        artifact = resolve(con, "artifact", data["artifact"])
        require(
            artifact["artifact_kind"] != "request_assertions",
            "ASSERTION_NOT_EVIDENCE",
            "The incoming request is not verified factual evidence.",
        )
        require(
            artifact["origin_uri"],
            "EVIDENCE_PROVENANCE_REQUIRED",
            "Evidence requires an artifact with explicit source provenance.",
        )
        request_hash = con.execute(
            "SELECT artifact_sha256 FROM artifact WHERE artifact_id=?", (run["input_artifact_id"],)
        ).fetchone()[0]
        require(
            artifact["artifact_sha256"] != request_hash,
            "ASSERTION_NOT_EVIDENCE",
            "Recapturing the same request bytes does not turn assertions into evidence.",
        )
        result = entity(
            con,
            "evidence",
            research_lane_id=lane["research_lane_id"],
            artifact_id=artifact["artifact_id"],
            evidence_kind=data["kind"],
            source_locator=data["locator"],
            observation=data["observation"],
            extracted_by_actor_id=actor,
        )
        if run["current_phase_no"] == 2:
            reopen(con, lane["research_lane_id"])
        return result
    if name == "evidence.retract":
        evidence = resolve(con, "evidence", data["ref"])
        require(evidence["evidence_status"] == "active", "INVALID_STATE", "Evidence is not active.")
        con.execute(
            "UPDATE evidence SET evidence_status='retracted',dt_modified=? WHERE evidence_id=?",
            (now(), evidence["evidence_id"]),
        )
        con.execute(
            "UPDATE defeater SET defeater_status='open',dt_modified=? WHERE defeater_id IN "
            "(SELECT defeater_id FROM defeater_evidence WHERE evidence_id=? "
            "AND relationship='refutes_challenge') AND defeater_status='defeated'",
            (now(), evidence["evidence_id"]),
        )
        con.execute(
            "UPDATE argument SET counter_status='open',dt_modified=? "
            "WHERE resolution_evidence_id=?",
            (now(), evidence["evidence_id"]),
        )
        for row in con.execute(
            "SELECT DISTINCT a.claim_id FROM argument a LEFT JOIN argument_evidence ae "
            "USING(argument_id) WHERE ae.evidence_id=? OR a.resolution_evidence_id=?",
            (evidence["evidence_id"], evidence["evidence_id"]),
        ).fetchall():
            invalidate_claim(con, row[0])
        reopen(con, evidence["research_lane_id"])
        return {"uuid": evidence["evidence_uuid"], "status": "retracted"}
    if name == "claim.create":
        lane = active_lane(con, data["lane"])
        rank = {"contextual": 0, "material": 1, "critical": 2}
        require(
            rank[data["impact"]] >= rank[lane["impact"]],
            "CLAIM_IMPACT_TOO_LOW",
            "Claim impact must meet its lane's impact floor.",
        )
        claim = entity(
            con,
            "claim",
            phase_revision_id=run["current_phase_revision_id"],
            research_lane_id=lane["research_lane_id"],
            claim_kind=data["kind"],
            claim_statement=data["text"],
            impact=data["impact"],
            is_canonical=1,
            created_by_actor_id=actor,
        )
        reopen(con, lane["research_lane_id"])
        return claim
    if name in ("claim.evaluate", "claim.reject"):
        claim = resolve(con, "claim", data["ref"])
        require(
            claim["claim_status"] not in ("rejected", "superseded"),
            "INVALID_STATE",
            "Claim is terminal; create a revised claim.",
        )
        if name == "claim.reject":
            status = "rejected"
            reopen(con, claim["research_lane_id"])
            failures = []
        else:
            failures = claim_violations(state(con, root), claim)
            status = (
                "contested"
                if any(f["code"] == "COUNTEREVIDENCE_OPEN" for f in failures)
                else ("proposed" if failures else "admissible")
            )
        if status != "admissible" and claim["claim_status"] == "admissible":
            reopen(con, claim["research_lane_id"])
        con.execute(
            "UPDATE claim SET claim_status=?,dt_modified=? WHERE claim_id=?",
            (status, now(), claim["claim_id"]),
        )
        return {"uuid": claim["claim_uuid"], "status": status, "violations": failures}
    if name == "argument.create":
        claim = resolve(con, "claim", data["claim"])
        require(
            claim["claim_status"] not in ("rejected", "superseded"),
            "INVALID_STATE",
            "Claim is terminal.",
        )
        evidence = [resolve(con, "evidence", ref) for ref in data["evidence"]]
        require(
            all(
                e["evidence_status"] == "active"
                and e["research_lane_id"] == claim["research_lane_id"]
                for e in evidence
            ),
            "SCOPE_MISMATCH",
            "Evidence must be active and belong to the claim's lane.",
        )
        result = entity(
            con,
            "argument",
            claim_id=claim["claim_id"],
            argument_role=data["role"],
            reasoning=data["reasoning"],
            limitations=data["limitations"],
            created_by_actor_id=actor,
        )
        for e in evidence:
            con.execute(
                "INSERT INTO argument_evidence VALUES (?,?)", (result["id"], e["evidence_id"])
            )
        invalidate_claim(con, claim["claim_id"])
        if data["role"] in ("refutes", "qualifies"):
            con.execute(
                "UPDATE claim SET claim_status='contested' WHERE claim_id=?", (claim["claim_id"],)
            )
        return result
    if name in ("argument.verify", "argument.resolve-counter"):
        argument = resolve(con, "argument", data["ref"])
        require(
            argument["verification_status"] == "pending"
            if name == "argument.verify"
            else argument["counter_status"] == "open",
            "INVALID_STATE",
            "Argument already dispositioned; record a new argument for revised reasoning.",
        )
        if name == "argument.verify":
            report = entity(
                con,
                "artifact",
                artifact_kind="argument_verification",
                media_type="text/plain",
                captured_by_actor_id=actor,
                **prepared["artifact"],
            )
            con.execute(
                "UPDATE argument SET "
                "verification_status=?,verified_by_actor_id=?,dt_verified=?,"
                "verification_artifact_id=?,dt_modified=? WHERE argument_id=?",
                (data["outcome"], actor, now(), report["id"], now(), argument["argument_id"]),
            )
        else:
            require(
                argument["argument_role"] in ("refutes", "qualifies"),
                "INVALID_ARGUMENT",
                "Only counterarguments need this disposition.",
            )
            evidence = resolve(con, "evidence", data["evidence_ref"])
            claim = con.execute(
                "SELECT * FROM claim WHERE claim_id=?", (argument["claim_id"],)
            ).fetchone()
            require(
                evidence["evidence_status"] == "active"
                and evidence["research_lane_id"] == claim["research_lane_id"],
                "SCOPE_MISMATCH",
                "Resolution needs active same-lane evidence.",
            )
            require(
                not con.execute(
                    "SELECT 1 FROM argument_evidence WHERE argument_id=? AND evidence_id=?",
                    (argument["argument_id"], evidence["evidence_id"]),
                ).fetchone(),
                "RESOLUTION_EVIDENCE_REQUIRED",
                "Use separate evidence to resolve the challenge.",
            )
            counter_hashes = {
                r[0]
                for r in con.execute(
                    "SELECT art.artifact_sha256 FROM argument_evidence ae "
                    "JOIN evidence e USING(evidence_id) JOIN artifact art USING(artifact_id) "
                    "WHERE ae.argument_id=?",
                    (argument["argument_id"],),
                )
            }
            resolution_hash = con.execute(
                "SELECT artifact_sha256 FROM artifact WHERE artifact_id=?",
                (evidence["artifact_id"],),
            ).fetchone()[0]
            require(
                resolution_hash not in counter_hashes,
                "RESOLUTION_EVIDENCE_REQUIRED",
                "Copying the same counterevidence does not resolve it; provide distinct evidence.",
            )
            con.execute(
                "UPDATE argument SET "
                "counter_status='resolved',resolution_evidence_id=?,"
                "resolution_reason=?,dt_modified=? WHERE argument_id=?",
                (evidence["evidence_id"], data["reason"], now(), argument["argument_id"]),
            )
        invalidate_claim(con, argument["claim_id"])
        return {"uuid": argument["argument_uuid"], "operation": name}
    raise AssertionError(name)
