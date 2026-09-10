import json
import sqlite3
from collections.abc import Callable
from pathlib import Path

from discovery.adapters.filesystem.artifacts import ensure_directory
from discovery.adapters.sqlite.audit import envelope, state_hash, verify
from discovery.adapters.sqlite.connection import connect, initialize_schema
from discovery.adapters.sqlite.records import insert
from discovery.domain.encoding import canonical, digest, now, uid, uuid
from discovery.domain.errors import require


class CommandStore:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.path = self.root / "discovery.sqlite"

    def execute(
        self,
        name: str,
        request: str,
        logical: dict,
        actor: dict,
        session: str,
        operation: Callable[[sqlite3.Connection, int], dict],
        *,
        initialize: bool = False,
        guard: Callable[[sqlite3.Connection, bool], None] | None = None,
    ) -> dict:
        request, session = uuid(request), uuid(session)
        actor = {**actor, "uuid": uuid(actor["uuid"])}
        # Session is attribution, not logical input: response-loss retries may use a new session.
        input_hash = digest(canonical({"input": logical, "actor": actor}).encode())
        if initialize:
            ensure_directory(self.root)
        con = connect(self.path, create=initialize)
        try:
            con.execute("BEGIN IMMEDIATE")
            version = con.execute("PRAGMA user_version").fetchone()[0]
            if initialize and version == 0:
                initialize_schema(con)
            else:
                require(
                    version == 5 or (version in (3, 4) and name == "run.upgrade"),
                    "SCHEMA_VERSION_UNSUPPORTED",
                    "Schema 5 required; use run upgrade for schema 3 or 4.",
                )
            exists = con.execute("SELECT * FROM discovery_run").fetchone()
            if exists:
                report = verify(con, self.root)
                require(
                    report["valid"],
                    "AUDIT_INTEGRITY_FAILURE",
                    "Run integrity verification failed.",
                    **report,
                )
            prior = con.execute(
                "SELECT * FROM event_log WHERE command_uuid=?", (request,)
            ).fetchone()
            if guard:
                guard(con, bool(prior))
            if prior:
                require(
                    prior["command_name"] == name and prior["command_input_sha256"] == input_hash,
                    "IDEMPOTENCY_CONFLICT",
                    "Request UUID was already used for different input.",
                )
                result = json.loads(prior["payload_json"])["result"]
                con.rollback()
                return {"result": result, "replayed": True}
            if initialize:
                require(
                    not exists,
                    "RUN_ALREADY_EXISTS",
                    "Run already initialized; use its original request to retry.",
                )
            else:
                require(exists, "RUN_NOT_FOUND", "Database has no run.")
                require(exists["run_status"] == "active", "RUN_NOT_ACTIVE", "Run is not active.")
            prior_actor = con.execute(
                "SELECT * FROM actor WHERE actor_uuid=?", (actor["uuid"],)
            ).fetchone()
            if prior_actor:
                require(
                    prior_actor["actor_kind"] == actor["kind"]
                    and prior_actor["display_name"] == actor["name"],
                    "INVALID_ARGUMENT",
                    "Actor UUID has different identity metadata.",
                )
                actor_id = prior_actor["actor_id"]
            else:
                actor_id = insert(
                    con,
                    "actor",
                    actor_uuid=actor["uuid"],
                    actor_kind=actor["kind"],
                    display_name=actor["name"],
                    dt_created=now(),
                )
            result = operation(con, actor_id)
            phase = con.execute("SELECT current_phase_revision_id FROM discovery_run").fetchone()[0]
            head = con.execute(
                "SELECT * FROM event_log ORDER BY event_log_id DESC LIMIT 1"
            ).fetchone()
            event = {
                "event_log_id": head["event_log_id"] + 1 if head else 1,
                "event_uuid": uid(),
                "event_schema_version": 1,
                "command_uuid": request,
                "command_name": name,
                "command_input_sha256": input_hash,
                "dt_created": now(),
                "actor_id": actor_id,
                "session_uuid": session,
                "phase_revision_id": phase,
                "event_type": name.replace(".", "_"),
                "payload_json": canonical(
                    {"input": logical, "result": result, "state_sha256": state_hash(con)}
                ),
                "previous_event_log_id": head["event_log_id"] if head else None,
                "previous_event_hash": head["event_hash"] if head else None,
            }
            event["event_hash"] = digest(canonical(envelope(con, event)).encode())
            insert(con, "event_log", **event)
            con.commit()
            return {"result": result, "replayed": False}
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()
