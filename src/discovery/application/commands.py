import sqlite3
from pathlib import Path

from discovery.adapters.filesystem.artifacts import capture
from discovery.adapters.git.repository import baseline
from discovery.adapters.sqlite.command_store import CommandStore
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
    if name == "run.init":
        require(
            data["subagents"] == "disabled",
            "FEATURE_NOT_IMPLEMENTED",
            "Subagent execution is deferred; this slice supports explicit disabled mode only.",
        )
        path = Path(data.pop("input")).resolve()
        content = path.read_bytes()
        require(content.strip(), "INVALID_ARGUMENT", "Request file must not be empty.")
        data["input_uri"] = path.as_uri()
        data["input_sha256"] = digest(content)
        source_root = Path(data["source"]).resolve()
        data["source"] = str(source_root)
        prepared["source"] = baseline(source_root, root, set(POLICY["source_excluded_directories"]))
        prepared["artifact"] = capture(root, content)
    elif name in ("research.record", "plan.review"):
        path = Path(data.pop("report")).resolve()
        content = path.read_bytes()
        require(content.strip(), "INVALID_ARGUMENT", "Report must not be empty.")
        data["report_sha256"] = digest(content)
        prepared["artifact"] = capture(root, content)
        if name == "plan.review":
            snapshot = query(root, "plan.snapshot")
            prepared["context"] = capture(root, canonical(snapshot["context"]).encode())
    store = CommandStore(root)

    def operation(con: sqlite3.Connection, aid: int) -> dict:
        if name == "run.init":
            return initialize(con, aid, data, prepared["artifact"], prepared["source"])
        if name.startswith("phase."):
            return transition(con, aid, name, data, root)
        return write(con, aid, name, data, prepared)

    return store.execute(
        name, request, data, actor, session, operation, initialize=name == "run.init"
    )
