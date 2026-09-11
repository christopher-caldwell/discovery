import json
import sqlite3
from pathlib import Path

from discovery.domain.encoding import canonical, digest

TABLES = (
    "actor source_repository artifact artifact_lineage discovery_run phase_revision "
    "clarification_question question_respondent assumption research_need research_lane "
    "research_lane_need research_lane_dependency research_surface "
    "research_method research_activity "
    "lead agent_run evidence claim argument argument_evidence agent_claim_position "
    "implementation_strategy technical_decision technical_decision_claim proof_obligation "
    "proof_obligation_evidence experiment proof_obligation_experiment experiment_artifact "
    "adversarial_check defeater defeater_evidence defeater_claim defeater_decision "
    "technical_spec_revision assurance_score"
).split()


def state_hash(con: sqlite3.Connection) -> str:
    tables = TABLES + (
        ["defeater_check", "conclusion_assessment"]
        if con.execute("PRAGMA user_version").fetchone()[0] >= 6
        else []
    )
    state = {
        table: sorted((dict(r) for r in con.execute(f"SELECT * FROM {table}")), key=canonical)
        for table in tables
    }
    state["schema"] = [
        dict(r)
        for r in con.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name")
    ]
    state["schema_version"] = con.execute("PRAGMA user_version").fetchone()[0]
    return digest(canonical(state).encode())


def envelope(con: sqlite3.Connection, row: dict) -> dict:
    actor = con.execute(
        "SELECT actor_uuid FROM actor WHERE actor_id=?", (row["actor_id"],)
    ).fetchone()
    phase = con.execute(
        "SELECT phase_revision_uuid FROM phase_revision WHERE phase_revision_id=?",
        (row["phase_revision_id"],),
    ).fetchone()
    keys = (
        "event_schema_version",
        "event_uuid",
        "command_uuid",
        "command_name",
        "command_input_sha256",
        "dt_created",
        "session_uuid",
        "event_type",
        "previous_event_hash",
    )
    return {
        **{key: row[key] for key in keys},
        "actor_uuid": actor[0] if actor else None,
        "phase_revision_uuid": phase[0] if phase else None,
        "payload": json.loads(row["payload_json"]),
    }


def verify(con: sqlite3.Connection, root: Path) -> dict:
    failures = []
    if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        failures.append("SQLite integrity check failed")
    if con.execute("PRAGMA foreign_key_check").fetchall():
        failures.append("Foreign key violations")
    previous_id, previous_hash, last_payload = None, None, None
    count = 0
    for raw in con.execute("SELECT * FROM event_log ORDER BY event_log_id"):
        row = dict(raw)
        count += 1
        if (
            row["previous_event_log_id"] != previous_id
            or row["previous_event_hash"] != previous_hash
        ):
            failures.append(f"Invalid predecessor at event {row['event_log_id']}")
        try:
            env = envelope(con, row)
            if canonical(env["payload"]) != row["payload_json"]:
                failures.append(f"Noncanonical payload at event {row['event_log_id']}")
            if digest(canonical(env).encode()) != row["event_hash"]:
                failures.append(f"Hash mismatch at event {row['event_log_id']}")
            last_payload = env["payload"]
        except (ValueError, TypeError):
            failures.append(f"Invalid envelope at event {row['event_log_id']}")
        previous_id, previous_hash = row["event_log_id"], row["event_hash"]
    if not count:
        failures.append("Missing root event")
    if not isinstance(last_payload, dict) or last_payload.get("state_sha256") != state_hash(con):
        failures.append("Current relational state differs from committed audit head")
    referenced = set()
    for row in con.execute("SELECT * FROM artifact"):
        expected = f"artifacts/sha256/{row['artifact_sha256']}"
        path = root / expected
        referenced.add(expected)
        if row["storage_path"] != expected or path.is_symlink() or not path.is_file():
            failures.append(f"Missing or invalid artifact {row['artifact_id']}")
        elif (
            digest(path.read_bytes()) != row["artifact_sha256"]
            or path.stat().st_size != row["byte_size"]
        ):
            failures.append(f"Artifact hash/size mismatch {row['artifact_id']}")
    orphans = sorted(
        str(p.relative_to(root))
        for p in (root / "artifacts/sha256").glob("*")
        if str(p.relative_to(root)) not in referenced
    )
    return {
        "valid": not failures,
        "event_count": count,
        "head_hash": previous_hash,
        "failures": failures,
        "orphan_artifacts": orphans,
    }
