import json
from pathlib import Path

import pytest

from discovery.cli import main
from discovery.domain.encoding import uid


@pytest.fixture
def run(tmp_path: Path, capsys, request):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.txt").write_text("baseline")
    ticket = tmp_path / "ticket.txt"
    ticket.write_text("The ticket asserts vendor ordering; investigate before relying on it.")
    root = tmp_path / "run"
    actor = uid()

    def call(*args, request=None, expected=0, identity=None):
        argv = [
            "--json",
            "--run",
            str(root),
            "--actor-id",
            identity or actor,
            "--actor-name",
            "Test investigator",
            "--actor-kind",
            "model",
            "--request-id",
            request or uid(),
            *args,
        ]
        status = main(argv)
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert status == expected, output
        assert not captured.err, captured.err
        return output

    initial_request = uid()
    init_args = (
        "run",
        "init",
        "--title",
        "Ordering discovery",
        "--input",
        str(ticket),
        "--source",
        str(source),
        "--subagents",
        getattr(request, "param", "disabled"),
    )
    initial = call(*init_args, request=initial_request)
    return {
        "call": call,
        "root": root,
        "source": source,
        "ticket": ticket,
        "actor": actor,
        "initial_request": initial_request,
        "init_args": init_args,
        "initial": initial,
    }


def question(call, **kwargs):
    return call(
        "question",
        "create",
        "--text",
        "Which ordering guarantee is required?",
        "--rationale",
        "Product owns intended behavior",
        "--authority",
        "product",
        "--authority-confidence",
        "0.8",
        **kwargs,
    )


def ready(run):
    call = run["call"]
    need = call(
        "research-need",
        "create",
        "--text",
        "Verify webhook ordering",
        "--rationale",
        "Correctness depends on it",
        "--impact",
        "material",
    )["result"]
    lane = call(
        "lane",
        "create",
        "--text",
        "Does the vendor guarantee ordering?",
        "--rationale",
        "Verify ticket assertion",
        "--impact",
        "material",
        "--scope",
        "Vendor webhook API",
        "--need",
        need["ref"],
        "--method",
        "official_docs",
        "--surface",
        "vendor_docs",
    )["result"]
    for surface in call("surface", "list")["result"]:
        if surface["research_lane_id"] is None and surface["disposition"] == "pending":
            call(
                "surface",
                "disposition",
                surface["ref"],
                "--disposition",
                "unavailable",
                "--reason",
                "Fixture has no external discovery surfaces",
            )
    review(run)
    return need, lane


def review(run):
    call = run["call"]
    snapshot = call("plan", "snapshot")["result"]
    report = run["root"].parent / "review.txt"
    report.write_text(
        "Reviewed the exact snapshot: needs and lane scope cover the request assertions."
    )
    return call(
        "plan",
        "review",
        "--plan-hash",
        snapshot["plan_sha256"],
        "--outcome",
        "passed",
        "--report",
        str(report),
    )
