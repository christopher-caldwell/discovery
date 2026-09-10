"""Small synthetic/offline SQLite outbox worker fixture."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).parent


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript((ROOT / "schema.sql").read_text())
    return db


def seed(
    db: sqlite3.Connection, payload: str = "synthetic payload", event_key: str = "synthetic-1"
) -> int:
    cur = db.execute("INSERT INTO jobs(payload) VALUES (?)", (payload,))
    job_id = cur.lastrowid
    db.execute("INSERT INTO outbox(job_id, event_key) VALUES (?, ?)", (job_id, event_key))
    db.commit()
    return int(job_id)


class CrashAfterEffect(RuntimeError):
    """Synthetic crash point used by the reproduction test."""


class Worker:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def run_once(self, crash_after_effect: bool = False) -> bool:
        """Process one event using the fixture's intentionally simple protocol."""
        row = self.db.execute(
            "SELECT id, job_id, event_key FROM outbox "
            "WHERE processed_at IS NULL ORDER BY id LIMIT 1"
        ).fetchone()
        if row is None:
            return False
        self.db.execute("UPDATE outbox SET attempts = attempts + 1 WHERE id = ?", (row["id"],))
        payload = self.db.execute(
            "SELECT payload FROM jobs WHERE id = ?", (row["job_id"],)
        ).fetchone()["payload"]
        # Synthetic side effect: an append-only row, standing in for an external call.
        self.db.execute(
            "INSERT INTO synthetic_effects(event_key, payload) VALUES (?, ?)",
            (row["event_key"], payload),
        )
        if crash_after_effect:
            self.db.commit()
            raise CrashAfterEffect("synthetic crash after side effect")
        self.db.execute(
            "UPDATE outbox SET processed_at = ? WHERE id = ?",
            (datetime.now(UTC).isoformat(), row["id"]),
        )
        self.db.execute("UPDATE jobs SET state = 'done' WHERE id = ?", (row["job_id"],))
        self.db.commit()
        return True


def count_effects(db: sqlite3.Connection, event_key: str = "synthetic-1") -> int:
    return int(
        db.execute(
            "SELECT COUNT(*) FROM synthetic_effects WHERE event_key = ?", (event_key,)
        ).fetchone()[0]
    )
