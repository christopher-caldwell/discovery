import sqlite3
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
        con.execute("PRAGMA journal_mode = WAL")
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
