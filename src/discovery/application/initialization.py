import sqlite3

from discovery.adapters.sqlite.records import entity, insert
from discovery.domain.encoding import canonical, now, uid
from discovery.domain.policy import POLICY


def surfaces(con: sqlite3.Connection, revision: int, actor: int, names: list[str]) -> None:
    for name in names:
        entity(
            con,
            "surface",
            phase_revision_id=revision,
            surface_kind=name,
            surface_name=name,
            created_by_actor_id=actor,
        )


def initialize(
    con: sqlite3.Connection, actor: int, data: dict, artifact: dict, source: dict
) -> dict:
    source_id = insert(
        con, "source_repository", source_repository_uuid=uid(), captured_by_actor_id=actor, **source
    )
    ticket = entity(
        con,
        "artifact",
        artifact_kind="request_assertions",
        media_type="text/plain",
        captured_by_actor_id=actor,
        origin_uri=data["input_uri"],
        **artifact,
    )
    phases = []
    for phase in range(1, 5):
        phases.append(
            insert(
                con,
                "phase_revision",
                phase_revision_uuid=uid(),
                phase_no=phase,
                revision_no=1,
                revision_status="active" if phase == 1 else "pending",
                created_by_actor_id=actor,
            )
        )
    run_uuid = uid()
    insert(
        con,
        "discovery_run",
        discovery_run_uuid=run_uuid,
        run_title=data["title"],
        current_phase_revision_id=phases[0],
        input_artifact_id=ticket["id"],
        config_json=canonical(POLICY),
        dt_created=now(),
        dt_modified=now(),
    )
    surfaces(con, phases[0], actor, POLICY["mandatory_phase1_surfaces"])
    return {
        "run_uuid": run_uuid,
        "phase": 1,
        "revision": 1,
        "input_artifact": ticket,
        "source_repository_id": source_id,
    }
