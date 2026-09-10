import sqlite3
from pathlib import Path

import pytest

from discovery.adapters.sqlite import command_store
from discovery.adapters.sqlite.audit import verify
from discovery.adapters.sqlite.connection import connect
from discovery.application import commands
from discovery.application.queries import query
from discovery.domain.encoding import uid
from discovery.domain.errors import DiscoveryError
from discovery.domain.policy import POLICY


@pytest.fixture(params=[3, 4])
def legacy(tmp_path, monkeypatch, request):
    source = tmp_path / "source"
    source.mkdir()
    ticket = tmp_path / "ticket.txt"
    ticket.write_text("Legacy request assertions")
    root = tmp_path / "run"
    actor = {"uuid": uid(), "name": "Legacy actor", "kind": "model"}
    schema = (
        Path(command_store.__file__)
        .with_name("ddl.sql")
        .read_text()
        .split(
            "ALTER TABLE research_lane ADD COLUMN"
            if request.param == 3
            else "ALTER TABLE technical_spec_revision ADD COLUMN"
        )[0]
    )
    schema += f"PRAGMA user_version = {request.param};\n"

    def old_schema(con):
        statement = ""
        for line in schema.splitlines(True):
            statement += line
            if sqlite3.complete_statement(statement):
                con.execute(statement)
                statement = ""

    with monkeypatch.context() as patch:
        patch.setattr(command_store, "initialize_schema", old_schema)
        patch.setitem(POLICY, "schema_version", request.param)
        patch.setitem(POLICY, "policy_version", "milestone-1")
        commands.execute(
            root,
            "run.init",
            {
                "input": str(ticket),
                "source": str(source),
                "subagents": "disabled",
                "title": "Legacy",
            },
            uid(),
            actor,
            uid(),
        )
    return root, actor, request.param


def test_explicit_upgrade_preserves_history_and_replays(legacy):
    root, actor, version = legacy
    before = query(root, "audit.verify")
    with pytest.raises(DiscoveryError, match="run upgrade"):
        query(root, "resume")
    request = uid()
    first = commands.execute(root, "run.upgrade", {}, request, actor, uid())
    replay = commands.execute(root, "run.upgrade", {}, request, actor, uid())
    assert replay["replayed"] and replay["result"] == first["result"]
    after = query(root, "audit.verify")
    assert after["valid"] and after["event_count"] == before["event_count"] + 1
    assert query(root, "resume")["title"] == "Legacy"
    assert query(root, "resume")["policy"]["schema_version"] == version
    con = connect(root / "discovery.sqlite")
    assert (
        con.execute("SELECT event_hash FROM event_log WHERE event_log_id=1").fetchone()[0]
        == before["head_hash"]
    )
    con.close()


def test_failed_upgrade_rolls_back_schema_and_audit(legacy, monkeypatch):
    root, actor, version = legacy
    original = commands.upgrade_schema

    def broken(con):
        original(con)
        raise RuntimeError("injected after DDL")

    monkeypatch.setattr(commands, "upgrade_schema", broken)
    with pytest.raises(RuntimeError):
        commands.execute(root, "run.upgrade", {}, uid(), actor, uid())
    con = connect(root / "discovery.sqlite")
    assert con.execute("PRAGMA user_version").fetchone()[0] == version
    assert "structure_sha256" not in {
        r[1] for r in con.execute("PRAGMA table_info(technical_spec_revision)")
    }
    assert verify(con, root)["valid"]
    con.close()
