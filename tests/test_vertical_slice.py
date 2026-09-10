import json
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest
from conftest import question, ready, review

from discovery.adapters.sqlite.command_store import CommandStore
from discovery.adapters.sqlite.connection import connect
from discovery.domain.encoding import uid
from discovery.domain.errors import DiscoveryError
from discovery.domain.transitions import next_phase, regression_phases


def test_initialization_idempotency_and_reopen(run):
    call = run["call"]
    assert run["initial"]["result"]["phase"] == 1
    assert run["initial"]["result"]["revision"] == 1
    retry = call(*run["init_args"], request=run["initial_request"])
    assert retry["replayed"]
    assert retry["result"] == run["initial"]["result"]
    assert call(*run["init_args"], expected=2)["error"]["code"] == "RUN_ALREADY_EXISTS"
    con = connect(run["root"] / "discovery.sqlite")
    assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert con.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    assert con.execute("PRAGMA synchronous").fetchone()[0] == 2
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert not con.execute("PRAGMA foreign_key_check").fetchall()
    assert all(
        r[5] == 1 for r in con.execute("PRAGMA table_list") if not r[1].startswith("sqlite_")
    )
    con.close()
    result = subprocess.run(
        [sys.executable, "-m", "discovery", "--json", "--run", str(run["root"]), "resume"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    packet = json.loads(result.stdout)["result"]
    assert packet["phase"]["revision_no"] == 1
    assert packet["source_baselines"]
    assert "question create" in packet["legal_next_actions"]
    assert call("audit", "verify")["result"]["event_count"] == 1


def test_question_retry_conflict_and_gate(run):
    call = run["call"]
    request = uid()
    first = question(call, request=request)
    assert question(call, request=request)["result"] == first["result"]
    assert question(call, request=request)["replayed"]
    conflict = call(
        "question",
        "resolve",
        first["result"]["ref"],
        "--answer",
        "Per customer",
        request=request,
        expected=2,
    )
    assert conflict["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    violations = call("phase", "check")["result"]["violations"]
    assert "BLOCKING_QUESTION_OPEN" in {v["code"] for v in violations}
    assert call("phase", "advance", expected=2)["error"]["code"] == "PHASE_GATE_FAILED"
    call("question", "resolve", first["result"]["uuid"], "--answer", "Per customer")
    assert call("question", "list")["result"][0]["question_status"] == "answered"


def test_canonical_input_order_and_atomic_failure(run):
    store = CommandStore(run["root"])
    actor = {"uuid": run["actor"], "name": "Test investigator", "kind": "model"}
    request = uid()

    # Purpose-built command boundary tested independently from the transport.
    def mutation(con, actor_id):
        con.execute("UPDATE discovery_run SET run_title='Changed'")
        return {"changed": True}

    first = store.execute(
        "test.rename", request, {"a": 1, "b": {"x": 2, "y": 3}}, actor, uid(), mutation
    )
    retry = store.execute(
        "test.rename", request, {"b": {"y": 3, "x": 2}, "a": 1}, actor, uid(), mutation
    )
    assert first["result"] == retry["result"] and retry["replayed"]
    with pytest.raises(DiscoveryError, match="different input"):
        store.execute("test.rename", request, {"a": 2}, actor, uid(), mutation)

    def broken(con, actor_id):
        con.execute("UPDATE discovery_run SET run_title='PARTIAL'")
        raise RuntimeError("injected after relational write")

    with pytest.raises(RuntimeError):
        store.execute("test.broken", uid(), {}, actor, uid(), broken)
    assert run["call"]("status")["result"]["title"] == "Changed"
    assert run["call"]("audit", "verify")["result"]["event_count"] == 2


def test_append_failure_rolls_back(run, monkeypatch):
    import discovery.adapters.sqlite.command_store as module

    real = module.insert

    def fail(con, table, **values):
        if table == "event_log":
            raise RuntimeError("append failure")
        return real(con, table, **values)

    monkeypatch.setattr(module, "insert", fail)
    store = CommandStore(run["root"])
    with pytest.raises(RuntimeError):
        store.execute(
            "test",
            uid(),
            {},
            {"uuid": run["actor"], "name": "Test investigator", "kind": "model"},
            uid(),
            lambda con, aid: (con.execute("UPDATE discovery_run SET run_title='partial'"), {})[1],
        )
    assert run["call"]("status")["result"]["title"] == "Ordering discovery"
    assert run["call"]("audit", "verify")["result"]["event_count"] == 1


def test_valid_advance_regress_retraverse(run):
    call = run["call"]
    need, lane = ready(run)
    assert call("phase", "check")["result"]["can_advance"]
    assert call("phase", "advance")["result"]["phase"] == 2
    assert (
        call("phase", "advance", expected=2)["error"]["details"]["violations"][0]["code"]
        == "RESEARCH_NEED_UNANSWERED"
    )
    assert question(call, expected=2)["error"]["code"] == "WRONG_PHASE"
    regress = call(
        "phase",
        "regress",
        "--to",
        "1",
        "--cause",
        "need:" + need["ref"],
        "--reason",
        "Intent needs clarification",
    )
    assert regress["result"]["revision"] == 2
    assert call("lane", "list")["result"][0]["uuid"] == lane["uuid"]
    assert not call("phase", "check")["result"]["can_advance"]
    for s in call("surface", "list")["result"]:
        if s["research_lane_id"] is None and s["disposition"] == "pending":
            call(
                "surface",
                "disposition",
                s["ref"],
                "--disposition",
                "unavailable",
                "--reason",
                "Still unavailable",
            )
    review(run)
    advanced = call("phase", "advance")["result"]
    assert (advanced["phase"], advanced["revision"]) == (2, 2)
    con = connect(run["root"] / "discovery.sqlite")
    rows = con.execute(
        "SELECT phase_no, revision_no, revision_status FROM phase_revision "
        "ORDER BY revision_no,phase_no"
    ).fetchall()
    con.close()
    assert [tuple(r) for r in rows[:4]] == [(p, 1, "invalidated") for p in range(1, 5)]
    assert call("audit", "verify")["result"]["valid"]


def test_transition_rules():
    for phase in range(1, 5):
        assert next_phase(phase) == phase + 1
    with pytest.raises(DiscoveryError):
        next_phase(1, 3)
    for current in range(2, 5):
        for target in range(1, current):
            assert list(regression_phases(current, target)) == list(range(target, 5))
    for current, target in [(1, 1), (2, 2), (2, 3), (4, 0)]:
        with pytest.raises(DiscoveryError):
            regression_phases(current, target)


def test_review_stales_and_source_drift(run):
    call = run["call"]
    ready(run)
    q = question(call)["result"]
    call("question", "resolve", q["ref"], "--answer", "Per customer")
    assert "STALE_REVIEW" in {v["code"] for v in call("phase", "check")["result"]["violations"]}
    review(run)
    assert call("phase", "check")["result"]["can_advance"]
    (run["source"] / "app.txt").write_text("changed")
    assert "SOURCE_DRIFT" in {v["code"] for v in call("phase", "check")["result"]["violations"]}
    call("phase", "advance", expected=2)


def test_surface_search_requires_activity_and_preserves_artifact(run):
    call = run["call"]
    surface = call("surface", "list")["result"][0]
    assert (
        call(
            "surface",
            "disposition",
            surface["ref"],
            "--disposition",
            "searched",
            "--reason",
            "Looked",
            expected=2,
        )["error"]["code"]
        == "SURFACE_ACTIVITY_REQUIRED"
    )
    report = run["root"].parent / "search.txt"
    report.write_text("Ticket asserts ordering; no proof supplied.")
    call(
        "research",
        "record",
        surface["ref"],
        "--query",
        "Read ticket for vendor assertions",
        "--summary",
        "One unverified assertion",
        "--origin-uri",
        run["ticket"].as_uri(),
        "--report",
        str(report),
    )
    call(
        "surface",
        "disposition",
        surface["ref"],
        "--disposition",
        "searched",
        "--reason",
        "Recorded ticket inspection",
    )
    report.unlink()
    assert call("audit", "verify")["result"]["valid"]


def test_lane_dag_and_impact(run):
    call = run["call"]
    need, a = ready(run)
    args = (
        "lane",
        "create",
        "--text",
        "What retries occur?",
        "--rationale",
        "Reliability",
        "--scope",
        "Retry behavior",
        "--need",
        need["ref"],
        "--method",
        "docs",
        "--surface",
        "vendor",
    )
    call(*args, "--impact", "contextual", expected=2)
    b = call(*args, "--impact", "material")["result"]
    call(
        "lane",
        "depends-on",
        a["ref"],
        "--depends-on",
        b["ref"],
        "--reason",
        "Retry affects ordering",
    )
    cycle = call(
        "lane",
        "depends-on",
        b["ref"],
        "--depends-on",
        a["ref"],
        "--reason",
        "Would cycle",
        expected=2,
    )
    assert cycle["error"]["code"] == "LANE_DEPENDENCY_CYCLE"


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE event_log SET payload_json='{}'",
        "DELETE FROM event_log",
        "UPDATE artifact SET origin_uri='changed'",
        "DELETE FROM artifact",
        "UPDATE discovery_run SET config_json='{}'",
    ],
)
def test_immutable_rows(run, sql):
    con = connect(run["root"] / "discovery.sqlite")
    with pytest.raises(sqlite3.IntegrityError):
        con.execute(sql)
    con.close()


@pytest.mark.parametrize(
    "column,value", [("payload_json", "{}"), ("previous_event_hash", "0" * 64)]
)
def test_detect_tampered_chain(run, column, value):
    question(run["call"])
    con = connect(run["root"] / "discovery.sqlite")
    con.execute("DROP TRIGGER prevent_event_log_update")
    con.execute(f"UPDATE event_log SET {column}=? WHERE event_log_id=2", (value,))
    con.close()
    assert run["call"]("audit", "verify", expected=2)["error"]["code"] == "AUDIT_INTEGRITY_FAILURE"


def test_reject_second_root_and_invalid_head(run):
    con = connect(run["root"] / "discovery.sqlite")
    row = dict(con.execute("SELECT * FROM event_log").fetchone())
    row.update(event_log_id=2, event_uuid=uid(), command_uuid=uid(), event_hash="a" * 64)
    from discovery.adapters.sqlite.records import insert

    with pytest.raises(sqlite3.IntegrityError):
        insert(con, "event_log", **row)
    row.update(previous_event_log_id=1, previous_event_hash="b" * 64)
    with pytest.raises(sqlite3.IntegrityError):
        insert(con, "event_log", **row)
    con.close()


def test_detect_unaudited_state_change(run):
    con = connect(run["root"] / "discovery.sqlite")
    con.execute("UPDATE discovery_run SET run_title='direct SQL bypass'")
    con.close()
    assert run["call"]("resume", expected=2)["error"]["code"] == "AUDIT_INTEGRITY_FAILURE"


def test_concurrent_processes_share_request(run):
    request = uid()
    args = [
        sys.executable,
        "-m",
        "discovery",
        "--json",
        "--run",
        str(run["root"]),
        "--request-id",
        request,
        "--actor-id",
        run["actor"],
        "--actor-name",
        "Test investigator",
        "--actor-kind",
        "model",
        "question",
        "create",
        "--text",
        "Concurrent question",
        "--rationale",
        "Test",
        "--authority",
        "product",
        "--authority-confidence",
        "0.5",
    ]

    def invoke(_):
        return subprocess.run(args, capture_output=True, text=True)

    with ThreadPoolExecutor(max_workers=4) as pool:
        outputs = list(pool.map(invoke, range(4)))
    assert all(p.returncode == 0 for p in outputs), [p.stdout + p.stderr for p in outputs]
    results = [json.loads(p.stdout) for p in outputs]
    assert sum(not r["replayed"] for r in results) == 1
    assert run["call"]("audit", "verify")["result"]["event_count"] == 2


def test_busy_timeout_is_deliberate(run):
    path = run["root"] / "discovery.sqlite"
    writer = connect(path)
    competitor = connect(path, timeout=20)
    writer.execute("BEGIN IMMEDIATE")
    try:
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            competitor.execute("BEGIN IMMEDIATE")
        assert competitor.execute("SELECT count(*) FROM discovery_run").fetchone()[0] == 1
    finally:
        writer.rollback()
        writer.close()
        competitor.close()


@pytest.mark.parametrize(
    "args",
    [
        ["phase", "advance", "--to", "3"],
        ["surface", "disposition", "S-001", "--disposition", "skipped"],
        ["question", "create"],
        ["nonsense"],
    ],
)
def test_machine_parse_failures(run, args):
    assert run["call"](*args, expected=2)["error"]["code"] == "INVALID_ARGUMENT"


def test_review_retry_after_plan_changes(run):
    call = run["call"]
    ready(run)
    snap = call("plan", "snapshot")["result"]
    report = run["root"].parent / "review.txt"
    request = uid()
    args = (
        "plan",
        "review",
        "--plan-hash",
        snap["plan_sha256"],
        "--outcome",
        "passed",
        "--report",
        str(report),
    )
    original = call(*args, request=request)
    question(call)
    replay = call(*args, request=request)
    assert replay["replayed"] and replay["result"] == original["result"]
    assert call(*args, expected=2)["error"]["code"] == "STALE_REVIEW"


def test_missing_source_reports_drift(run):
    (run["source"] / "app.txt").unlink()
    run["source"].rmdir()
    assert run["call"]("resume")["result"]["source_baselines"][0]["observed_drift"]


def test_schema_tamper_detected_without_row_changes(run):
    con = connect(run["root"] / "discovery.sqlite")
    con.execute("DROP TRIGGER prevent_event_log_delete")
    con.close()
    run["call"]("audit", "verify", expected=2)


@pytest.mark.parametrize("change", ["delete", "modify"])
def test_artifact_corruption(run, change):
    artifact = next((run["root"] / "artifacts/sha256").iterdir())
    if change == "delete":
        artifact.unlink()
    else:
        artifact.write_text("corrupt")
    run["call"]("audit", "verify", expected=2)


def test_orphan_artifacts_reported_without_deletion(run):
    orphan = run["root"] / "artifacts/sha256" / ("a" * 64)
    orphan.write_text("unreferenced")
    assert run["call"]("audit", "verify")["result"]["orphan_artifacts"] == [
        str(orphan.relative_to(run["root"]))
    ]
    assert orphan.exists()


def test_abrupt_process_exit_rolls_back(run):
    program = """
import os, sqlite3, sys
con = sqlite3.connect(sys.argv[1], isolation_level=None)
con.execute('BEGIN IMMEDIATE')
con.execute("UPDATE discovery_run SET run_title='interrupted'")
os._exit(91)
"""
    process = subprocess.run([sys.executable, "-c", program, str(run["root"] / "discovery.sqlite")])
    assert process.returncode == 91
    assert run["call"]("status")["result"]["title"] == "Ordering discovery"
    assert run["call"]("audit", "verify")["result"]["event_count"] == 1


def test_distinct_simultaneous_writers(run):
    def invoke(index):
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "discovery",
                "--json",
                "--run",
                str(run["root"]),
                "--request-id",
                uid(),
                "--actor-id",
                run["actor"],
                "--actor-name",
                "Test investigator",
                "--actor-kind",
                "model",
                "question",
                "create",
                "--text",
                f"Question {index}",
                "--rationale",
                "Concurrency",
                "--authority",
                "product",
                "--authority-confidence",
                "0.6",
            ],
            capture_output=True,
            text=True,
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        outputs = list(pool.map(invoke, range(8)))
    assert all(p.returncode == 0 for p in outputs), [p.stdout for p in outputs]
    assert len(run["call"]("question", "list")["result"]) == 8
    assert run["call"]("audit", "verify")["result"]["event_count"] == 9


def test_failed_init_rolls_back_schema(tmp_path):
    root = tmp_path / "failed"
    store = CommandStore(root)
    actor = {"uuid": uid(), "kind": "model", "name": "Failed initializer"}

    def fail(con, aid):
        raise RuntimeError("after DDL and actor creation")

    with pytest.raises(RuntimeError):
        store.execute("run.init", uid(), {}, actor, uid(), fail, initialize=True)
    con = connect(root / "discovery.sqlite")
    assert not con.execute("SELECT name FROM sqlite_master").fetchall()
    assert con.execute("PRAGMA user_version").fetchone()[0] == 0
    con.close()


def test_regression_from_phase_four_retains_phase_one(run):
    # Arrange future-phase state through the same atomic boundary. No CLI gate bypass exists.
    store = CommandStore(run["root"])
    actor = {"uuid": run["actor"], "name": "Test investigator", "kind": "model"}

    def future_fixture(con, aid):
        con.execute("UPDATE phase_revision SET revision_status='completed' WHERE phase_no<4")
        con.execute("UPDATE phase_revision SET revision_status='active' WHERE phase_no=4")
        con.execute("UPDATE discovery_run SET current_phase_no=4,current_phase_revision_id=4")
        return {"fixture": "future-phase-state"}

    store.execute("test.future_fixture", uid(), {}, actor, uid(), future_fixture)
    result = run["call"](
        "phase", "regress", "--to", "2", "--cause", "artifact:A-001", "--reason", "Evidence defect"
    )["result"]
    assert (result["phase"], result["revision"]) == (2, 2)
    con = connect(run["root"] / "discovery.sqlite")
    assert (
        con.execute("SELECT revision_status FROM phase_revision WHERE phase_no=1").fetchone()[0]
        == "completed"
    )
    assert con.execute("SELECT count(*) FROM phase_revision WHERE revision_no=2").fetchone()[0] == 3
    con.close()
    assert run["call"]("phase", "advance")["result"]["phase"] == 3
    run["call"]("phase", "advance", expected=2)


def test_concurrent_initialization(run):
    root = run["root"].parent / "concurrent-init"
    request = uid()
    args = [
        sys.executable,
        "-m",
        "discovery",
        "--json",
        "--run",
        str(root),
        "--request-id",
        request,
        "--actor-id",
        run["actor"],
        "--actor-name",
        "Test investigator",
        "--actor-kind",
        "model",
        *run["init_args"],
    ]
    with ThreadPoolExecutor(max_workers=4) as pool:
        outputs = list(
            pool.map(lambda _: subprocess.run(args, capture_output=True, text=True), range(4))
        )
    assert all(p.returncode == 0 for p in outputs), [p.stdout + p.stderr for p in outputs]
    assert sum(not json.loads(p.stdout)["replayed"] for p in outputs) == 1


def test_regression_uses_original_policy(run, monkeypatch):
    from discovery.domain.policy import POLICY

    need, _ = ready(run)
    run["call"]("phase", "advance")
    original = list(POLICY["mandatory_phase1_surfaces"])
    monkeypatch.setitem(POLICY, "mandatory_phase1_surfaces", ["future_default"])
    run["call"](
        "phase",
        "regress",
        "--to",
        "1",
        "--cause",
        "need:" + need["ref"],
        "--reason",
        "Recheck scope",
    )
    current = [
        s["surface_name"]
        for s in run["call"]("surface", "list")["result"]
        if s["disposition"] == "pending" and s["research_lane_id"] is None
    ]
    assert sorted(current) == sorted(original)
