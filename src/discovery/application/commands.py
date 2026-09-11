import json
import sqlite3
from pathlib import Path

from discovery.adapters.filesystem.artifacts import capture
from discovery.adapters.git.repository import baseline
from discovery.adapters.sqlite.command_store import CommandStore
from discovery.adapters.sqlite.connection import upgrade_schema
from discovery.application import (
    adversarial,
    agents,
    assessments,
    claims,
    design,
    experiments,
    investigation,
    sources,
    specification,
)
from discovery.application.initialization import initialize
from discovery.application.phases import transition
from discovery.application.planning import write
from discovery.application.queries import query
from discovery.domain.encoding import canonical, digest
from discovery.domain.errors import require
from discovery.domain.policy import POLICY


def execute(root: Path, name: str, data: dict, request: str, actor: dict, session: str) -> dict:
    root = root.resolve()
    data = dict(data)
    prepared = {}
    if name == "experiment.exec":
        return experiments.execute(root, data, request, actor, session)
    if name == "run.init":
        path = Path(data.pop("input")).resolve()
        content = path.read_bytes()
        require(content.strip(), "INVALID_ARGUMENT", "Request file must not be empty.")
        data["input_uri"] = path.as_uri()
        data["input_sha256"] = digest(content)
        source_root = Path(data["source"]).resolve()
        data["source"] = str(source_root)
        prepared["source"] = baseline(source_root, root, set(POLICY["source_excluded_directories"]))
        prepared["artifact"] = capture(root, content)
    elif name in (
        "research.record",
        "plan.review",
        "argument.verify",
        "challenge.complete",
        "defeater.defeat",
        "agent.complete",
        "agent.finding",
        "group.reconcile",
    ):
        path = Path(data.pop("report")).resolve()
        content = path.read_bytes()
        require(content.strip(), "INVALID_ARGUMENT", "Report must not be empty.")
        data["report_sha256"] = digest(content)
        if name == "research.record":
            prepared["content"] = content
        else:
            prepared["artifact"] = capture(root, content)
        if name == "plan.review":
            snapshot = query(root, "plan.snapshot")
            prepared["context"] = capture(root, canonical(snapshot["context"]).encode())
    elif name == "assessment.record":
        try:
            data["assessment"] = json.loads(Path(data.pop("file")).read_text())
        except (ValueError, UnicodeError) as exc:
            require(False, "INVALID_ARGUMENT", f"Assessment must be valid UTF-8 JSON: {exc}")
    elif name == "artifact.capture":
        path = Path(data["file"]).resolve()
        data["file"] = str(path)
        content = path.read_bytes()
        data["content_sha256"] = digest(content)
        prepared["content"] = content
    elif name == "source.refresh":
        snapshot = query(root, "resume")
        source = snapshot["source_baselines"][0]
        prepared["source"] = baseline(
            Path(source["repository_root"]),
            root,
            set(snapshot["policy"]["source_excluded_directories"]),
        )
        data["baseline"] = prepared["source"]
    if name in ("spec.draft", "spec.revise"):
        snapshot = query(root, "spec.snapshot")
        narrative = Path(data.pop("narrative")).read_bytes()
        require(narrative.strip(), "INVALID_ARGUMENT", "Technical narrative must not be empty.")
        data["narrative_sha256"] = digest(narrative)
        prepared = specification.prepare(root, snapshot, narrative)
    elif name == "phase.advance":
        snapshot = query(root, "spec.snapshot")
        if snapshot["phase"]["phase_no"] == 4:
            prepared = specification.prepare(
                root, snapshot, specification.final_narrative(snapshot, root), final=True
            )
    store = CommandStore(root)

    def operation(con: sqlite3.Connection, aid: int) -> dict:
        if name == "run.init":
            return initialize(con, aid, data, prepared["artifact"], prepared["source"])
        if name == "run.upgrade":
            require(
                con.execute("PRAGMA user_version").fetchone()[0] in (3, 4, 5),
                "INVALID_STATE",
                "Run already uses schema 6.",
            )
            upgrade_schema(con)
            return {"schema_version": 6}
        if name == "assessment.record":
            return assessments.record(con, aid, data["assessment"], root)
        if name.startswith(("agent.", "group.", "finding.")):
            return agents.write(con, aid, name, data, prepared, root)
        if name.startswith(("strategy.", "decision.", "obligation.", "requirement.")):
            return design.write(con, aid, name, data, root)
        if name.startswith("experiment."):
            return experiments.write(con, aid, name, data, root)
        if name.startswith(("challenge.", "defeater.")):
            return adversarial.write(con, aid, name, data, prepared, root)
        if name in ("spec.draft", "spec.revise"):
            return specification.compile_spec(con, aid, prepared, root)
        if name in ("artifact.capture", "source.refresh"):
            return sources.write(con, aid, name, data, prepared, root)
        if name.startswith(("evidence.", "claim.", "argument.")):
            return claims.write(con, aid, name, data, prepared, root)
        phase = con.execute("SELECT current_phase_no FROM discovery_run").fetchone()[0]
        if (
            name
            in ("lane.activate", "lane.reopen", "lane.closure-begin", "lane.close", "need.answer")
            or name.startswith(("lead.", "method."))
            or (phase == 2 and name in ("surface.disposition", "research.record"))
        ):
            return investigation.write(con, aid, name, data, prepared, root)
        if name.startswith("phase."):
            return transition(con, aid, name, data, root, prepared)
        return write(con, aid, name, data, prepared, root)

    return store.execute(
        name,
        request,
        data,
        actor,
        session,
        operation,
        initialize=name == "run.init",
        guard=lambda con, replay: agents.guard(con, name, data, actor, replay),
    )
