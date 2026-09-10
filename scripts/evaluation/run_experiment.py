#!/usr/bin/env python3
"""Driver-only experiment handoff from a completed isolated operator session.

Not a daemon or a model-callable broker. The evaluator reviews a request, stops
the operator, then invokes this runner. Discovery still reserves, sandboxes and
records the execution; the child additionally cannot read prior runs or credentials.
"""

import argparse
import json
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

from isolated_run import SYSTEM_READ, recovery_inputs

from discovery.adapters.process.sandbox import execute as sandbox_execute
from discovery.application.experiments import execute
from discovery.application.queries import query


def validate_run_paths(root: Path) -> None:
    # The stopped operator could have left a symlink for the driver to follow.
    # Check BEFORE reservation, source copying or artifact/receipt writes, not
    # just before starting the sandbox child. No concurrent operator is supported.
    if root.is_symlink() or any(p.is_symlink() for p in root.rglob("*")):
        raise ValueError("Selected run contains symlinks; refuse external handoff")


def run(operator: Path, request_file: Path) -> dict:
    operator = operator.resolve()
    manifest = json.loads((operator / "control/manifest.json").read_text())
    if not (operator / "control/result.json").is_file():
        raise ValueError("The operator must finish before an evaluator handoff")
    if (operator / "home/.codex/auth.json").exists():
        raise ValueError("Operator credentials must be cleaned up before handoff")
    work = Path(manifest["work"])
    root = Path(manifest.get("resume_run", work / "run"))
    source = Path(manifest.get("selected_source", work / "source"))
    ticket = Path(manifest.get("selected_ticket", work / "ticket.md"))
    root, source, _ = recovery_inputs(
        SimpleNamespace(resume_run=root, source=source, ticket=ticket)
    )
    validate_run_paths(root)
    if request_file.stat().st_size > 2_000_000:
        raise ValueError("Experiment request exceeds size limit")
    request = json.loads(request_file.read_text())
    if set(request) != {"request_id", "actor", "session_id", "ref", "command", "timeout"}:
        raise ValueError("Only an explicit experiment request is supported")
    actor = request["actor"]
    if set(actor) != {"uuid", "name", "kind"} or actor["kind"] != "model" or not actor["name"]:
        raise ValueError("Use the model author's identity for evaluation work")
    for value in (request["request_id"], request["session_id"], actor["uuid"]):
        UUID(value)
    audit = query(root, "audit.verify")
    if not audit["valid"]:
        raise ValueError("Selected ledger failed audit; do not execute")

    # A filesystem fixture nested inside the evaluator's Git checkout must not
    # acquire that enclosing repository's HEAD merely because the driver sees it.
    previous = os.environ.get("GIT_CEILING_DIRECTORIES")
    os.environ["GIT_CEILING_DIRECTORIES"] = str(source.parent)
    try:

        def restricted_process(box, argv, timeout):
            expected = root / "scratch/experiments"
            if (
                box.is_symlink()
                or not expected.resolve().is_relative_to(root)
                or not box.resolve().is_relative_to(expected)
            ):
                raise ValueError("Unexpected experiment copy path")
            return sandbox_execute(box, argv, timeout, read_roots=[Path(p) for p in SYSTEM_READ])

        return execute(
            root,
            {
                "ref": request["ref"],
                "command_json": json.dumps(request["command"]),
                "timeout": request["timeout"],
            },
            request["request_id"],
            actor,
            request["session_id"],
            process_runner=restricted_process,
        )
    finally:
        if previous is None:
            os.environ.pop("GIT_CEILING_DIRECTORIES", None)
        else:
            os.environ["GIT_CEILING_DIRECTORIES"] = previous


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operator-session", type=Path, required=True)
    parser.add_argument("--request-file", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.operator_session, args.request_file)))
