import sqlite3
from pathlib import Path

from discovery.adapters.sqlite.queries import state
from discovery.adapters.sqlite.records import entity, resolve
from discovery.domain.completion import obligation_supported
from discovery.domain.encoding import now
from discovery.domain.errors import require

RANK = {"contextual": 0, "material": 1, "critical": 2}


def write(con: sqlite3.Connection, actor: int, name: str, data: dict, root: Path) -> dict:
    run = con.execute("SELECT * FROM discovery_run").fetchone()
    require(run["current_phase_no"] == 3, "WRONG_PHASE", "Design edits require Phase 3.")
    pid = run["current_phase_revision_id"]
    if name == "strategy.create":
        return entity(
            con,
            "strategy",
            phase_revision_id=pid,
            strategy_name=data["name"],
            strategy_description=data["description"],
            created_by_actor_id=actor,
        )
    if name in ("strategy.select", "strategy.reject"):
        s = resolve(con, "strategy", data["ref"])
        require(
            s["strategy_status"] in ("candidate", "selected"),
            "INVALID_STATE",
            "Strategy is terminal.",
        )
        if name == "strategy.select":
            require(
                not con.execute(
                    (
                        "SELECT 1 FROM implementation_strategy WHERE "
                        "strategy_status='selected' AND implementation_strategy_id<>?"
                    ),
                    (s["implementation_strategy_id"],),
                ).fetchone(),
                "STRATEGY_ALREADY_SELECTED",
                "Reject the former selection before replacing it.",
            )
        status = "selected" if name.endswith("select") else "rejected"
        con.execute(
            (
                "UPDATE implementation_strategy SET "
                "strategy_status=?,dt_modified=? WHERE "
                "implementation_strategy_id=?"
            ),
            (status, now(), s["implementation_strategy_id"]),
        )
        return {"uuid": s["implementation_strategy_uuid"], "status": status}
    if name == "decision.create":
        s = resolve(con, "strategy", data["strategy"])
        require(
            s["strategy_status"] in ("candidate", "selected"),
            "INVALID_STATE",
            "Strategy is terminal.",
        )
        claims = [resolve(con, "claim", r) for r in data["claims"]]
        require(
            all(c["claim_status"] == "admissible" for c in claims),
            "DECISION_TRACE_REQUIRED",
            "Link admissible claims.",
        )
        d = entity(
            con,
            "decision",
            phase_revision_id=pid,
            implementation_strategy_id=s["implementation_strategy_id"],
            decision_statement=data["text"],
            rationale=data["rationale"],
            impact=data["impact"],
            created_by_actor_id=actor,
        )
        for c in claims:
            con.execute(
                "INSERT INTO technical_decision_claim VALUES (?,?,?)",
                (d["id"], c["claim_id"], "depends_on"),
            )
        return d
    if name in ("decision.accept", "decision.reject"):
        d = resolve(con, "decision", data["ref"])
        require(
            d["decision_status"] in ("proposed", "accepted"),
            "INVALID_STATE",
            "Decision is terminal.",
        )
        status = "accepted" if name.endswith("accept") else "rejected"
        con.execute(
            (
                "UPDATE technical_decision SET decision_status=?,dt_modified=? "
                "WHERE technical_decision_id=?"
            ),
            (status, now(), d["technical_decision_id"]),
        )
        return {"uuid": d["technical_decision_uuid"], "status": status}
    if name == "requirement.create":
        d, n = resolve(con, "decision", data["decision"]), resolve(con, "need", data["need"])
        require(
            d["decision_status"] in ("proposed", "accepted") and n["need_status"] == "answered",
            "INVALID_STATE",
            "Link an active decision and answered need.",
        )
        return entity(
            con,
            "requirement",
            technical_decision_id=d["technical_decision_id"],
            research_need_id=n["research_need_id"],
            requirement_text=data["text"],
            acceptance_criteria=data["acceptance"],
            verification_plan=data["verification"],
            created_by_actor_id=actor,
        )
    if name == "obligation.create":
        d = resolve(con, "decision", data["decision"])
        require(
            d["decision_status"] in ("proposed", "accepted"),
            "INVALID_STATE",
            "Decision is terminal.",
        )
        require(
            RANK[data["impact"]] >= RANK[d["impact"]],
            "IMPACT_TOO_LOW",
            "Proof must meet decision impact.",
        )
        return entity(
            con,
            "obligation",
            technical_decision_id=d["technical_decision_id"],
            obligation_description=data["text"],
            impact=data["impact"],
            evidence_profile="empirical" if data["impact"] == "critical" else data["profile"],
        )
    if name.startswith("obligation."):
        o = resolve(con, "obligation", data["ref"])
        oid = o["proof_obligation_id"]
        if name == "obligation.attach-evidence":
            e = resolve(con, "evidence", data["evidence_ref"])
            require(e["evidence_status"] == "active", "INVALID_STATE", "Evidence must be active.")
            con.execute(
                "INSERT INTO proof_obligation_evidence VALUES (?,?,?)",
                (oid, e["evidence_id"], "supports"),
            )
            status = "pending"
        elif name == "obligation.attach-experiment":
            e = resolve(con, "experiment", data["experiment"])
            require(
                e["technical_decision_id"] == o["technical_decision_id"],
                "SCOPE_MISMATCH",
                "Experiment must concern the same decision.",
            )
            con.execute(
                "INSERT INTO proof_obligation_experiment VALUES (?,?)", (oid, e["experiment_id"])
            )
            status = "pending"
        else:
            status = {
                "obligation.satisfy": "satisfied",
                "obligation.fail": "failed",
                "obligation.block": "blocked",
                "obligation.not-applicable": "not_applicable",
            }[name]
            if status == "satisfied":
                require(
                    obligation_supported(state(con, root), o),
                    "PROOF_UNSATISFIED",
                    "Required primary/empirical evidence or passed experiment missing.",
                )
        con.execute(
            (
                "UPDATE proof_obligation SET "
                "obligation_status=?,disposition_reason=?,dt_modified=? WHERE "
                "proof_obligation_id=?"
            ),
            (status, data.get("reason", "Evidence changed; reevaluate"), now(), oid),
        )
        return {"uuid": o["proof_obligation_uuid"], "status": status}
    raise AssertionError(name)
