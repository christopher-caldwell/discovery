import sqlite3
import time
from pathlib import Path

from discovery.domain.errors import require


def connect(path: Path, *, create: bool = False, timeout: int = 5000) -> sqlite3.Connection:
    require(create or path.is_file(), "RUN_NOT_FOUND", "Run database does not exist.")
    con = sqlite3.connect(
        path.as_uri() + ("?mode=rwc" if create else "?mode=rw"),
        uri=True,
        isolation_level=None,
        timeout=timeout / 1000,
    )
    con.row_factory = sqlite3.Row
    try:
        con.execute(f"PRAGMA busy_timeout = {int(timeout)}")
        con.execute("PRAGMA foreign_keys = ON")
        enable_wal(con, timeout)
        con.execute("PRAGMA synchronous = FULL")
        con.execute("PRAGMA recursive_triggers = ON")
        require(
            con.execute("PRAGMA foreign_keys").fetchone()[0] == 1,
            "INTERNAL_ERROR",
            "Foreign key enforcement unavailable.",
        )
        return con
    except BaseException:
        con.close()
        raise


def initialize_schema(con: sqlite3.Connection) -> None:
    """Execute DDL within the caller's transaction; executescript would commit it."""
    require(
        not con.execute("SELECT 1 FROM sqlite_master").fetchone(),
        "SCHEMA_VERSION_UNSUPPORTED",
        "Refusing to initialize an existing schema.",
    )
    statement = ""
    for line in Path(__file__).with_name("ddl.sql").read_text().splitlines(True):
        statement += line
        if sqlite3.complete_statement(statement):
            con.execute(statement)
            statement = ""


def enable_wal(con: sqlite3.Connection, timeout: int) -> None:
    """SQLite can bypass its busy handler during concurrent WAL bootstrap."""
    deadline = time.monotonic() + timeout / 1000
    try:
        while True:
            remaining = max(0, int((deadline - time.monotonic()) * 1000))
            con.execute(f"PRAGMA busy_timeout = {min(remaining, 100)}")
            try:
                mode = con.execute("PRAGMA journal_mode = WAL").fetchone()[0]
                require(mode == "wal", "DATABASE_CONFIGURATION_ERROR", "WAL mode is required.")
                return
            except sqlite3.OperationalError as exc:
                busy = getattr(exc, "sqlite_errorcode", 0) & 0xFF == sqlite3.SQLITE_BUSY
                if not busy or time.monotonic() >= deadline:
                    raise
                time.sleep(min(0.01, max(0, deadline - time.monotonic())))
    finally:
        con.execute(f"PRAGMA busy_timeout = {int(timeout)}")


def upgrade_schema(con: sqlite3.Connection) -> None:
    version = con.execute("PRAGMA user_version").fetchone()[0]
    migrations = (["phase2_migration.sql"] if version == 3 else []) + ["completion_migration.sql"]
    script = "\n".join(Path(__file__).with_name(m).read_text() for m in migrations)
    statement = ""
    for line in script.splitlines(True):
        statement += line
        if sqlite3.complete_statement(statement):
            con.execute(statement)
            statement = ""
