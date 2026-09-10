import sqlite3
from pathlib import Path

from discovery.adapters.sqlite.queries import state
from discovery.adapters.sqlite.records import insert, resolve
from discovery.application.initialization import surfaces
from discovery.domain.encoding import now, uid
from discovery.domain.errors import require
from discovery.domain.gates import phase_violations
from discovery.domain.transitions import next_phase, regression_phases


def transition(
    con: sqlite3.Connection,
    actor: int,
    name: str,
    data: dict,
    root: Path,
    prepared: dict | None = None,
) -> dict:
    snapshot = state(con, root)
    current = snapshot["phase"]
    pid, number = current["phase_revision_id"], current["phase_no"]
    if name == "phase.advance":
        target = next_phase(number)
        failures = phase_violations(snapshot)
        require(not failures, "PHASE_GATE_FAILED", "Phase cannot advance.", violations=failures)
        con.execute(
            "UPDATE phase_revision SET revision_status='completed', dt_completed=?, dt_modified=? "
            "WHERE phase_revision_id=?",
            (now(), now(), pid),
        )
        if number == 4:
            from discovery.application.specification import compile_spec

            spec = compile_spec(con, actor, prepared, root, final=True)
            con.execute("UPDATE discovery_run SET run_status='finalized',dt_modified=?", (now(),))
            return {"phase": 4, "status": "finalized", "spec": spec}
        pending = con.execute(
            "SELECT * FROM phase_revision WHERE phase_no=? AND revision_status='pending' "
            "ORDER BY revision_no DESC LIMIT 1",
            (target,),
        ).fetchone()
        require(pending is not None, "INVALID_TRANSITION", "Next pending revision is missing.")
        new = pending["phase_revision_id"]
        con.execute(
            "UPDATE phase_revision SET revision_status='active', dt_modified=? WHERE "
            "phase_revision_id=?",
            (now(), new),
        )
    else:
        target = data["to"]
        affected = regression_phases(number, target)
        # A cause must resolve to durable knowledge; free prose alone is not a reference.
        kind, ref = data["cause"].split(":", 1)
        require(
            kind
            in (
                "question",
                "need",
                "lane",
                "artifact",
                "defeater",
                "decision",
                "claim",
                "obligation",
                "experiment",
            ),
            "INVALID_ARGUMENT",
            "Unsupported regression cause kind.",
        )
        resolve(con, kind, ref)
        old = con.execute(
            "SELECT phase_revision_id FROM phase_revision WHERE phase_no>=? "
            "AND revision_status IN ('active','pending','completed')",
            (target,),
        ).fetchall()
        con.execute(
            "UPDATE phase_revision SET revision_status='invalidated', dt_modified=? "
            "WHERE phase_no>=? AND revision_status IN ('active','pending','completed')",
            (now(), target),
        )
        new = None
        for phase in affected:
            revision = con.execute(
                "SELECT max(revision_no)+1 FROM phase_revision WHERE phase_no=?", (phase,)
            ).fetchone()[0]
            created = insert(
                con,
                "phase_revision",
                phase_revision_uuid=uid(),
                phase_no=phase,
                revision_no=revision,
                revision_status="active" if phase == target else "pending",
                regression_reason=data["reason"],
                created_by_actor_id=actor,
            )
            if phase == target:
                new = created
        for row in old:
            con.execute(
                "UPDATE phase_revision SET invalidated_by_phase_revision_id=? WHERE "
                "phase_revision_id=?",
                (new, row[0]),
            )
        con.execute(
            "UPDATE technical_spec_revision SET spec_status='superseded' WHERE "
            "spec_status<>'superseded'"
        )
        if target == 1:
            surfaces(con, new, actor, snapshot["policy"]["mandatory_phase1_surfaces"])
    con.execute(
        "UPDATE discovery_run SET current_phase_no=?, current_phase_revision_id=?, dt_modified=?",
        (target, new, now()),
    )
    revision = con.execute(
        "SELECT revision_no, phase_revision_uuid FROM phase_revision WHERE phase_revision_id=?",
        (new,),
    ).fetchone()
    return {"phase": target, "revision": revision[0], "phase_revision_uuid": revision[1]}
