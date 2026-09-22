import json
import sqlite3
from collections.abc import Callable
from pathlib import Path
from uuid import UUID, uuid5

from discovery.adapters.filesystem.artifacts import capture
from discovery.adapters.git.repository import baseline
from discovery.adapters.process.sandbox import copy_source
from discovery.adapters.process.sandbox import execute as run_process
from discovery.adapters.sqlite.command_store import CommandStore
from discovery.adapters.sqlite.queries import state
from discovery.adapters.sqlite.records import entity, resolve
from discovery.application import agents
from discovery.domain.encoding import canonical, now
from discovery.domain.errors import require


def write(con: sqlite3.Connection, actor: int, name: str, data: dict, root: Path) -> dict:
    snapshot = state(con, root)
    require(snapshot["run"]["current_phase_no"] == 3, "WRONG_PHASE", "Experiments require Phase 3.")
    if name == "experiment.plan":
        d = resolve(con, "decision", data["decision"])
        require(
            d["decision_status"] in ("proposed", "accepted"),
            "INVALID_STATE",
            "Decision is terminal.",
        )
        require(
            not any(s["observed_drift"] for s in snapshot["sources"]),
            "SOURCE_DRIFT",
            "Refresh source before experiments.",
        )
        return entity(
            con,
            "experiment",
            phase_revision_id=snapshot["phase"]["phase_revision_id"],
            technical_decision_id=d["technical_decision_id"],
            experiment_name=data["name"],
            hypothesis=data["hypothesis"],
            procedure=data["procedure"],
            sandbox_kind="other",
            source_repository_id=snapshot["sources"][0]["source_repository_id"],
            created_by_actor_id=actor,
        )
    e = resolve(con, "experiment", data["ref"])
    if name == "experiment.abort":
        require(
            e["experiment_status"] in ("planned", "running"),
            "INVALID_STATE",
            "Experiment is terminal.",
        )
        con.execute(
            (
                "UPDATE experiment SET "
                "experiment_status='blocked',limitations=?,dt_modified=? WHERE "
                "experiment_id=?"
            ),
            (data["reason"], now(), e["experiment_id"]),
        )
    elif name == "experiment.replace":
        new = resolve(con, "experiment", data["replacement"])
        require(
            e["experiment_status"] in ("failed", "inconclusive", "blocked")
            and not e["superseded_by_experiment_id"],
            "INVALID_STATE",
            "Only failed terminal attempts may be replaced.",
        )
        require(
            new["technical_decision_id"] == e["technical_decision_id"]
            and new["experiment_id"] > e["experiment_id"],
            "SCOPE_MISMATCH",
            "Replacement must be a newer experiment for the same decision.",
        )
        con.execute(
            (
                "UPDATE experiment SET superseded_by_experiment_id=?,dt_modified=?"
                " WHERE experiment_id=?"
            ),
            (new["experiment_id"], now(), e["experiment_id"]),
        )
        for o in con.execute(
            "SELECT proof_obligation_id FROM proof_obligation_experiment WHERE experiment_id=?",
            (e["experiment_id"],),
        ).fetchall():
            con.execute(
                "INSERT OR IGNORE INTO proof_obligation_experiment VALUES (?,?)",
                (o[0], new["experiment_id"]),
            )
            con.execute(
                (
                    "UPDATE proof_obligation SET obligation_status='pending' WHERE "
                    "proof_obligation_id=?"
                ),
                (o[0],),
            )
    elif name == "experiment.finish":
        require(
            e["experiment_status"] == "running" and e["execution_artifact_id"],
            "EXPERIMENT_RESULT_REQUIRED",
            "Run the experiment and capture its result first.",
        )
        if data["outcome"] == "passed":
            require(
                e["execution_exit_code"] == 0,
                "EXPERIMENT_FAILED",
                "Nonzero process result cannot pass.",
            )
            artifact = con.execute(
                "SELECT * FROM artifact WHERE artifact_id=?", (e["execution_artifact_id"],)
            ).fetchone()
            receipt = json.loads((root / artifact["storage_path"]).read_text())
            require(
                receipt.get("included_source_snapshot_unchanged_after_execution", True),
                "SOURCE_DRIFT",
                "The included source snapshot changed during experiment execution.",
            )
        con.execute(
            (
                "UPDATE experiment SET "
                "experiment_status=?,result_summary=?,limitations=?,dt_modified=? "
                "WHERE experiment_id=?"
            ),
            (data["outcome"], data["conclusion"], data["limitations"], now(), e["experiment_id"]),
        )
    return {"uuid": e["experiment_uuid"], "operation": name}


def execute(
    root: Path,
    data: dict,
    request: str,
    actor: dict,
    session: str,
    *,
    process_runner: Callable[[Path, list[str], int], dict] | None = None,
) -> dict:
    """Reservation and result registration are separately audited short transactions.

    Replay never reruns the process. A missing receipt requires explicit abort/replacement.
    """
    data = dict(data)
    command_file = data.pop("command_file", None)
    if command_file is not None:
        try:
            data["command_json"] = Path(command_file).read_text(encoding="utf-8")
        except UnicodeError:
            require(False, "INVALID_ARGUMENT", "--command-file must contain UTF-8 JSON.")
    try:
        argv = json.loads(data["command_json"])
    except (ValueError, TypeError):
        argv = None
    require(
        isinstance(argv, list)
        and argv
        and all(isinstance(a, str) and "\x00" not in a for a in argv)
        and argv[0],
        "INVALID_ARGUMENT",
        "Command requires a JSON string array with a nonempty executable and no NUL bytes.",
    )
    require(1 <= data["timeout"] <= 600, "INVALID_ARGUMENT", "Timeout must be 1–600 seconds.")
    if data.get("execution_mode") == "trusted-local":
        data["execution_mode"] = "local"
    data = {**data, "command": argv}
    store = CommandStore(root)

    def reserve(con, aid):
        snapshot = state(con, root)
        e = resolve(con, "experiment", data["ref"])
        require(
            snapshot["run"]["current_phase_no"] == 3, "WRONG_PHASE", "Experiments require Phase 3."
        )
        require(
            e["experiment_status"] == "planned" and not e["execution_uuid"],
            "INVALID_STATE",
            "Experiment already executed/reserved.",
        )
        source = next(
            (
                s
                for s in snapshot["sources"]
                if s["source_repository_id"] == e["source_repository_id"]
            ),
            None,
        )
        require(
            source and not source["observed_drift"], "SOURCE_DRIFT", "Experiment baseline is stale."
        )
        if data.get("execution_mode", "local") == "local":
            original_root = str(Path(source["repository_root"]).resolve())
            require(
                not any(original_root in argument for argument in argv),
                "UNSAFE_EXPERIMENT_COMMAND",
                "Local experiment arguments must not reference the original source path; "
                "use paths inside the disposable working directory.",
            )
        path = root / "scratch" / "experiments" / e["experiment_uuid"] / "source"
        con.execute(
            (
                "UPDATE experiment SET "
                "experiment_status='running',execution_uuid=?,sandbox_path=?,command_json=?,"
                "sandbox_kind='command',dt_modified=?"
                " WHERE experiment_id=?"
            ),
            (request, str(path), canonical(argv), now(), e["experiment_id"]),
        )
        return {
            "uuid": e["experiment_uuid"],
            "id": e["experiment_id"],
            "sandbox": str(path),
            "source": source,
            "excluded": snapshot["policy"]["source_excluded_directories"],
        }

    reserved = store.execute(
        "experiment.exec",
        request,
        data,
        actor,
        session,
        reserve,
        guard=lambda con, replay: agents.guard(con, "experiment.exec", data, actor, replay),
    )
    result = reserved["result"]
    box = Path(result["sandbox"])
    receipt = box.parent / "receipt.json"
    if not reserved["replayed"]:
        source = Path(result["source"]["repository_root"])
        copy_source(source, box, set(result["excluded"]), root)
        current = baseline(source, root, set(result["excluded"]))
        require(
            all(
                current[k] == result["source"][k]
                for k in ("baseline_revision", "baseline_tree_hash")
            ),
            "SOURCE_DRIFT",
            "Source changed during sandbox creation; abort and replace experiment.",
        )
        mode = data.get("execution_mode", "local")
        if process_runner:
            record = process_runner(box, argv, data["timeout"])
        elif mode == "local":
            # Preserve the three-argument adapter seam for focused test adapters.
            record = run_process(box, argv, data["timeout"])
        else:
            record = run_process(
                box,
                argv,
                data["timeout"],
                mode=mode,
            )
        original_after = baseline(source, root, set(result["excluded"]))
        record["included_source_snapshot_unchanged_after_execution"] = all(
            original_after[k] == result["source"][k]
            for k in ("baseline_revision", "baseline_tree_hash")
        )
        record["original_source_after"] = original_after
        record["source_snapshot_scope"] = {
            "excluded_top_level_paths": result["excluded"],
            "limitation": (
                "A post-run comparison cannot detect changes that were restored before capture."
            ),
        }
        if not record["included_source_snapshot_unchanged_after_execution"]:
            record.setdefault("safety_limitations", []).append(
                "The included source snapshot changed during execution"
            )
        # The process cannot write this receipt: it is outside its permitted copy.
        record["source"] = result["source"]
        metadata = capture(root, canonical(record).encode())
        from discovery.adapters.filesystem.artifacts import atomic_write

        atomic_write(receipt, canonical(metadata).encode())
    require(
        receipt.is_file(),
        "EXPERIMENT_INTERRUPTED",
        "Reserved execution has no receipt; inspect, abort, and replace. It will not run twice.",
    )
    metadata = json.loads(receipt.read_text())
    record = json.loads((root / metadata["storage_path"]).read_text())

    def register(con, aid):
        e = resolve(con, "experiment", result["uuid"])
        require(
            e["execution_uuid"] == request and e["experiment_status"] == "running",
            "INVALID_STATE",
            "Execution no longer owns the active experiment.",
        )
        a = entity(
            con,
            "artifact",
            artifact_kind="experiment_result",
            media_type="application/json",
            captured_by_actor_id=aid,
            **metadata,
        )
        con.execute(
            "INSERT INTO experiment_artifact VALUES (?,?,?)", (e["experiment_id"], a["id"], "log")
        )
        con.execute(
            (
                "UPDATE experiment SET "
                "execution_artifact_id=?,execution_exit_code=?,environment_json=?,dt_modified=?"
                " WHERE experiment_id=?"
            ),
            (
                a["id"],
                record["exit_code"],
                canonical(record["environment"]),
                now(),
                e["experiment_id"],
            ),
        )
        return {
            "uuid": e["experiment_uuid"],
            "artifact": a,
            "exit_code": record["exit_code"],
            "timed_out": record["timed_out"],
            "output_limited": record.get("output_limited", False),
            "sandbox": str(box),
        }

    return store.execute(
        "experiment.record",
        str(uuid5(UUID(request), "result")),
        {"execution": request, "receipt": metadata},
        actor,
        session,
        register,
        guard=lambda con, replay: agents.guard(con, "experiment.record", data, actor, replay),
    )
