import argparse
import json
import math
import sqlite3
import sys
from pathlib import Path

from discovery import __version__
from discovery.application.commands import execute
from discovery.application.queries import query
from discovery.domain.encoding import canonical, uid, uuid
from discovery.domain.errors import DiscoveryError


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise DiscoveryError("INVALID_ARGUMENT", message)


def text(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("Value must not be empty.")
    return value.strip()


def confidence(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or not 0 <= number <= 1:
        raise argparse.ArgumentTypeError("Confidence must be between 0 and 1.")
    return number


def parser() -> Parser:
    p = Parser(description="Discovery: durable intent, investigation, and evidence.")
    p.add_argument(
        "--version",
        action="version",
        version=canonical({"ok": True, "result": {"version": __version__, "schema_version": 4}}),
    )
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--run", required=True, type=Path, help="Run directory containing discovery.sqlite"
    )
    p.add_argument("--request-id", type=uuid)
    p.add_argument("--actor-id", type=uuid)
    p.add_argument("--actor-name", type=text)
    p.add_argument("--actor-kind", choices=["human", "model", "system"])
    p.add_argument("--session-id", type=uuid)
    families = p.add_subparsers(dest="family", required=True)
    for simple in ("status", "resume"):
        families.add_parser(simple).set_defaults(command=simple)
    for family, operations in {
        "run": ["init", "upgrade"],
        "question": ["create", "list", "resolve"],
        "research-need": ["create", "list", "answer"],
        "lane": [
            "create",
            "list",
            "depends-on",
            "activate",
            "reopen",
            "closure-begin",
            "close",
            "check",
        ],
        "lead": ["create", "list", "disposition"],
        "method": ["create", "list", "disposition"],
        "artifact": ["capture", "list"],
        "evidence": ["create", "list", "retract"],
        "claim": ["create", "list", "check", "evaluate", "reject"],
        "argument": ["create", "list", "verify", "resolve-counter"],
        "source": ["refresh", "list"],
        "surface": ["list", "disposition"],
        "research": ["record", "list"],
        "plan": ["snapshot", "review"],
        "phase": ["check", "advance", "regress"],
        "audit": ["verify"],
    }.items():
        group = families.add_parser(family).add_subparsers(dest="action", required=True)
        for operation in operations:
            cmd = group.add_parser(operation)
            name = ("need" if family == "research-need" else family) + "." + operation
            if name == "research.list":
                name = "activity.list"
            cmd.set_defaults(command=name)
            phase2_arguments(cmd, name)
            if name == "run.init":
                cmd.add_argument("--title", required=True, type=text)
                cmd.add_argument("--input", required=True)
                cmd.add_argument("--source", required=True)
                cmd.add_argument(
                    "--subagents", required=True, choices=["disabled", "partitioned", "overlap"]
                )
            if name in ("question.create", "need.create", "lane.create"):
                cmd.add_argument("--text", required=True, type=text)
                cmd.add_argument("--rationale", required=True, type=text)
            if name == "question.create":
                cmd.add_argument("--non-blocking", action="store_true")
                cmd.add_argument(
                    "--technical",
                    action="store_true",
                    help="Phase 2 technical uncertainty; intent ambiguity requires regression.",
                )
                cmd.add_argument("--authority", required=True, type=text)
                cmd.add_argument("--authority-confidence", required=True, type=confidence)
            if name in ("need.create", "lane.create"):
                cmd.add_argument(
                    "--impact", required=True, choices=["contextual", "material", "critical"]
                )
            if name == "lane.create":
                cmd.add_argument("--scope", required=True, type=text)
                cmd.add_argument("--need", dest="needs", action="append", required=True, type=text)
                cmd.add_argument(
                    "--method", dest="methods", action="append", required=True, type=text
                )
                cmd.add_argument(
                    "--surface", dest="surfaces", action="append", required=True, type=text
                )
            if name in (
                "question.resolve",
                "surface.disposition",
                "research.record",
                "lane.depends-on",
            ):
                cmd.add_argument("ref", type=text)
            if name == "question.resolve":
                cmd.add_argument("--answer", required=True, type=text)
            if name == "lane.depends-on":
                cmd.add_argument("--depends-on", required=True, type=text)
                cmd.add_argument("--reason", required=True, type=text)
            if name == "surface.disposition":
                cmd.add_argument(
                    "--disposition",
                    required=True,
                    choices=["searched", "unavailable", "inaccessible", "not_applicable"],
                )
                cmd.add_argument("--reason", required=True, type=text)
            if name == "research.record":
                cmd.add_argument("--method", type=text)
                cmd.add_argument("--query", required=True, type=text)
                cmd.add_argument("--summary", required=True, type=text)
                cmd.add_argument("--origin-uri", required=True, type=text)
            if name in ("research.record", "plan.review"):
                cmd.add_argument("--report", required=True)
            if name == "plan.review":
                cmd.add_argument("--plan-hash", required=True, type=text)
                cmd.add_argument(
                    "--outcome", required=True, choices=["passed", "findings", "inconclusive"]
                )
            if name == "phase.regress":
                cmd.add_argument("--to", required=True, type=int, choices=[1, 2, 3])
                cmd.add_argument(
                    "--cause", required=True, type=text, help="kind:ref, e.g. question:Q-001"
                )
                cmd.add_argument("--reason", required=True, type=text)
    return p


def phase2_arguments(cmd: Parser, name: str) -> None:
    with_ref = {
        "lane.activate",
        "lane.reopen",
        "lane.closure-begin",
        "lane.close",
        "lane.check",
        "need.answer",
        "lead.disposition",
        "method.disposition",
        "claim.check",
        "claim.evaluate",
        "claim.reject",
        "evidence.retract",
        "argument.verify",
        "argument.resolve-counter",
    }
    if name in with_ref:
        cmd.add_argument("ref", type=text)
    if name in {"lead.create", "method.create", "evidence.create", "claim.create"}:
        cmd.add_argument("--lane", required=True, type=text)
    if name in {
        "lane.reopen",
        "source.refresh",
        "claim.reject",
        "evidence.retract",
        "argument.resolve-counter",
        "lead.disposition",
        "method.disposition",
    }:
        cmd.add_argument("--reason", required=True, type=text)
    if name in {"lane.close", "need.answer"}:
        cmd.add_argument("--answer", required=True, type=text)
    if name == "lane.close":
        cmd.add_argument("--limitations", required=True, type=text)
        cmd.add_argument("--question", type=text)
    if name == "lead.create":
        cmd.add_argument("--activity", required=True, type=text)
    if name in {"lead.create", "claim.create"}:
        cmd.add_argument("--text", required=True, type=text)
        cmd.add_argument("--impact", required=True, choices=["contextual", "material", "critical"])
    if name == "lead.disposition":
        cmd.add_argument(
            "--disposition",
            required=True,
            choices=[
                "investigated",
                "irrelevant",
                "duplicate",
                "inaccessible",
                "requires_human_input",
            ],
        )
        cmd.add_argument("--activity", type=text)
        cmd.add_argument("--duplicate-of", type=text)
        cmd.add_argument("--question", type=text)
    if name == "method.create":
        cmd.add_argument("--name", required=True, type=text)
    if name == "method.disposition":
        cmd.add_argument(
            "--disposition",
            required=True,
            choices=["completed", "unavailable", "inaccessible", "not_applicable"],
        )
    if name == "artifact.capture":
        cmd.add_argument("--file", required=True, type=text)
        cmd.add_argument("--origin-uri", required=True, type=text)
        cmd.add_argument("--source-backed", action="store_true")
    if name == "evidence.create":
        cmd.add_argument("--artifact", required=True, type=text)
        cmd.add_argument("--kind", required=True, choices=["primary", "secondary", "empirical"])
        cmd.add_argument("--locator", required=True, type=text)
        cmd.add_argument("--observation", required=True, type=text)
    if name == "claim.create":
        cmd.add_argument(
            "--kind",
            required=True,
            choices=["current_behavior", "vendor_capability", "constraint", "intended_behavior"],
        )
    if name == "argument.create":
        cmd.add_argument("--claim", required=True, type=text)
        cmd.add_argument("--role", required=True, choices=["supports", "refutes", "qualifies"])
        cmd.add_argument("--evidence", required=True, action="append", type=text)
        cmd.add_argument("--reasoning", required=True, type=text)
        cmd.add_argument("--limitations", required=True, type=text)
    if name == "argument.verify":
        cmd.add_argument("--outcome", required=True, choices=["passed", "failed", "inconclusive"])
        cmd.add_argument("--report", required=True, type=text)
    if name == "argument.resolve-counter":
        cmd.add_argument("--evidence-ref", required=True, type=text)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    machine = "--json" in args
    # Make --json safe anywhere; all other global options precede the command.
    if machine:
        args = ["--json"] + [a for a in args if a != "--json"]
    try:
        ns = vars(parser().parse_args(args))
        name = ns.pop("command")
        root = ns.pop("run").resolve()
        for key in ("json", "family", "action"):
            ns.pop(key, None)
        request = ns.pop("request_id")
        actor = {
            "uuid": ns.pop("actor_id"),
            "name": ns.pop("actor_name"),
            "kind": ns.pop("actor_kind"),
        }
        session = ns.pop("session_id") or uid()
        readonly = name in (
            "status",
            "resume",
            "lane.check",
            "claim.check",
            "phase.check",
            "audit.verify",
            "plan.snapshot",
        ) or name.endswith(".list")
        if readonly:
            result = query(root, name, ns.get("ref"))
            if name == "audit.verify" and not result["valid"]:
                raise DiscoveryError(
                    "AUDIT_INTEGRITY_FAILURE", "Audit verification failed.", **result
                )
            output = {"ok": True, "result": result}
        else:
            if not request or not all(actor.values()):
                raise DiscoveryError(
                    "INVALID_ARGUMENT",
                    "Mutations require --request-id, --actor-id, --actor-name, and --actor-kind.",
                )
            if name == "phase.regress" and ":" not in ns["cause"]:
                raise DiscoveryError("INVALID_ARGUMENT", "Cause must use kind:ref syntax.")
            if not ns.get("technical"):
                ns.pop("technical", None)
            if ns.get("method") is None:
                ns.pop("method", None)
            for key in ("needs", "methods", "surfaces", "evidence"):
                if key in ns:
                    ns[key] = sorted(set(ns[key]))
            output = {"ok": True, **execute(root, name, ns, request, actor, session)}
        print(canonical(output) if machine else json.dumps(output, indent=2, ensure_ascii=False))
        return 0
    except DiscoveryError as exc:
        output = {
            "ok": False,
            "error": {"code": exc.code, "message": str(exc), "details": exc.details},
        }
        code = 2
    except sqlite3.Error as exc:
        busy = getattr(exc, "sqlite_errorcode", 0) & 0xFF in (
            sqlite3.SQLITE_BUSY,
            sqlite3.SQLITE_LOCKED,
        )
        error = "SQLITE_BUSY" if busy else "DATABASE_ERROR"
        output = {"ok": False, "error": {"code": error, "message": str(exc), "details": {}}}
        code = 3
    except OSError as exc:
        output = {"ok": False, "error": {"code": "IO_ERROR", "message": str(exc), "details": {}}}
        code = 3
    except Exception as exc:
        print(f"Unexpected error: {type(exc).__name__}: {exc}", file=sys.stderr)
        output = {
            "ok": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Unexpected internal error.",
                "details": {},
            },
        }
        code = 4
    print(canonical(output), file=sys.stdout if machine else sys.stderr)
    return code
