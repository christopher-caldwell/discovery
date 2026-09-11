import json
import sqlite3
from pathlib import Path

import pytest

from discovery.adapters.filesystem.artifacts import capture
from discovery.adapters.sqlite import command_store
from discovery.adapters.sqlite.audit import state_hash, verify
from discovery.adapters.sqlite.connection import connect
from discovery.adapters.sqlite.records import entity
from discovery.application import commands
from discovery.application.queries import query
from discovery.domain.encoding import uid
from discovery.domain.errors import DiscoveryError
from discovery.domain.policy import POLICY


@pytest.fixture(params=[3, 4, 5])
def legacy(tmp_path, monkeypatch, request):
    version, seed = (request.param, None) if isinstance(request.param, int) else request.param
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
            if version == 3
            else "ALTER TABLE technical_spec_revision ADD COLUMN"
            if version == 4
            else "CREATE TABLE defeater_check"
        )[0]
    )
    schema += f"PRAGMA user_version = {version};\n"

    def old_schema(con):
        statement = ""
        for line in schema.splitlines(True):
            statement += line
            if sqlite3.complete_statement(statement):
                con.execute(statement)
                statement = ""

    original_initialize = commands.initialize

    def historical_initialize(con, aid, data, artifact, source):
        result = original_initialize(con, aid, data, artifact, source)
        if seed:
            # Seed historical schema-5 records before the initial audited commit.
            # This fixture tests storage compatibility, not completion gates.
            phase = con.execute("SELECT current_phase_revision_id FROM discovery_run").fetchone()[0]
            metadata = capture(root, b"Legacy compiled specification")
            a = entity(
                con,
                "artifact",
                artifact_kind="spec_export",
                media_type="text/markdown",
                captured_by_actor_id=aid,
                **metadata,
            )
            spec = entity(
                con,
                "spec",
                phase_revision_id=phase,
                revision_no=1,
                spec_status="final" if seed == "finalized" else "draft",
                artifact_id=a["id"],
                scoring_model="structural-coverage-v1",
                created_by_actor_id=aid,
                bundle_json=json.dumps({"technical-spec.md": {**a, **metadata}}),
            )
            if seed == "finalized":
                con.execute("UPDATE discovery_run SET run_status='finalized'")
            else:
                check = entity(
                    con,
                    "challenge",
                    phase_revision_id=phase,
                    technical_spec_revision_id=spec["id"],
                    check_category="correctness",
                    check_name="Legacy check",
                    scope="Legacy spec",
                    created_by_actor_id=aid,
                )
                entity(
                    con,
                    "defeater",
                    phase_revision_id=phase,
                    adversarial_check_id=check["id"],
                    challenge="Legacy canonical concern",
                    impact="material",
                    created_by_actor_id=aid,
                )
        return result

    with monkeypatch.context() as patch:
        patch.setattr(commands, "initialize", historical_initialize)
        patch.setattr(command_store, "initialize_schema", old_schema)
        patch.setitem(POLICY, "schema_version", version)
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
    return root, actor, version


def test_explicit_upgrade_preserves_history_and_replays(legacy):
    root, actor, version = legacy
    before = query(root, "audit.verify")
    if version < 5:
        with pytest.raises(DiscoveryError, match="run upgrade"):
            query(root, "resume")
    else:
        assert query(root, "resume")["title"] == "Legacy"
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
    assert (
        "structure_sha256"
        in {r[1] for r in con.execute("PRAGMA table_info(technical_spec_revision)")}
    ) == (version == 5)
    assert not con.execute("SELECT 1 FROM sqlite_master WHERE name='defeater_check'").fetchone()
    assert not con.execute(
        "SELECT 1 FROM sqlite_master WHERE name='conclusion_assessment'"
    ).fetchone()
    assert verify(con, root)["valid"]
    con.close()


@pytest.mark.parametrize("legacy", [(5, "with-defeater")], indirect=True)
def test_schema5_upgrade_backfills_owner_without_rewriting_defeater(legacy):
    root, actor, _ = legacy
    with connect(root / "discovery.sqlite") as con:
        before = dict(con.execute("SELECT * FROM defeater").fetchone())
        old_head = verify(con, root)["head_hash"]
    commands.execute(root, "run.upgrade", {}, uid(), actor, uid())
    with connect(root / "discovery.sqlite") as con:
        assert dict(con.execute("SELECT * FROM defeater").fetchone()) == before
        link = dict(con.execute("SELECT * FROM defeater_check").fetchone())
        assert link == {
            "defeater_id": before["defeater_id"],
            "adversarial_check_id": before["adversarial_check_id"],
            "link_reason": "Original owning check",
            "linked_by_actor_id": before["created_by_actor_id"],
            "dt_created": before["dt_created"],
        }
        assert con.execute("PRAGMA user_version").fetchone()[0] == 6
        assert (
            con.execute(
                "SELECT previous_event_hash FROM event_log ORDER BY event_log_id DESC"
            ).fetchone()[0]
            == old_head
        )
        assert verify(con, root)["valid"]


@pytest.mark.parametrize("legacy", [(5, "finalized")], indirect=True)
def test_finalized_schema5_remains_readable_auditable_and_exportable(legacy):
    root, actor, _ = legacy
    with connect(root / "discovery.sqlite") as con:
        before = state_hash(con)
        head = verify(con, root)
    assert query(root, "resume")["status"] == "finalized"
    assert query(root, "audit.verify")["valid"]
    spec = query(root, "spec.export")
    assert (
        Path(spec["directory"]) / "technical-spec.md"
    ).read_bytes() == b"Legacy compiled specification"
    assert query(root, "report.export")["is_final_specification"] is False
    with pytest.raises(DiscoveryError) as error:
        commands.execute(root, "run.upgrade", {}, uid(), actor, uid())
    assert error.value.code == "RUN_NOT_ACTIVE"
    with connect(root / "discovery.sqlite") as con:
        assert con.execute("PRAGMA user_version").fetchone()[0] == 5
        assert state_hash(con) == before
        assert verify(con, root) == head
