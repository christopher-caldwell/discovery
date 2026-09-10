import json
import sqlite3
from pathlib import Path

from discovery.adapters.git.repository import baseline
from discovery.domain.encoding import canonical, digest
from discovery.domain.errors import DiscoveryError

PLAN_TABLES = (
    "clarification_question",
    "question_respondent",
    "assumption",
    "research_need",
    "research_lane",
    "research_lane_need",
    "research_lane_dependency",
    "research_surface",
    "research_method",
    "research_activity",
)


def plan(con: sqlite3.Connection) -> dict:
    run = dict(con.execute("SELECT * FROM discovery_run").fetchone())
    return {
        "run_uuid": run["discovery_run_uuid"],
        "phase_revision_id": run["current_phase_revision_id"],
        "input_artifact_id": run["input_artifact_id"],
        "policy": json.loads(run["config_json"]),
        **{
            t: sorted((dict(r) for r in con.execute(f"SELECT * FROM {t}")), key=canonical)
            for t in PLAN_TABLES
        },
    }


def state(con: sqlite3.Connection, root: Path) -> dict:
    result = plan(con)
    result["run"] = dict(con.execute("SELECT * FROM discovery_run").fetchone())
    result["phase"] = dict(
        con.execute(
            "SELECT * FROM phase_revision WHERE phase_revision_id=?",
            (result["run"]["current_phase_revision_id"],),
        ).fetchone()
    )
    for table in (
        "phase_revision",
        "lead",
        "claim",
        "proof_obligation",
        "defeater",
        "implementation_strategy",
        "technical_decision",
        "experiment",
    ):
        result[table] = [dict(r) for r in con.execute(f"SELECT * FROM {table}")]
    result["plan_sha256"] = digest(canonical(plan(con)).encode())
    result["reviews"] = [
        dict(r)
        for r in con.execute(
            "SELECT ar.*, a.artifact_sha256 FROM agent_run ar JOIN artifact a ON "
            "a.artifact_id=ar.context_artifact_id "
            "WHERE ar.run_role='semantic_verifier' AND ar.run_status='completed' AND "
            "ar.run_outcome='passed'"
        )
    ]
    result["sources"] = []
    for row in con.execute("SELECT * FROM source_repository WHERE baseline_status='active'"):
        source = dict(row)
        try:
            current = baseline(
                Path(source["repository_root"]),
                root,
                set(result["policy"]["source_excluded_directories"]),
            )
            source["observed_drift"] = any(
                current[k] != source[k] for k in ("baseline_revision", "baseline_tree_hash")
            )
        except (OSError, DiscoveryError):
            source["observed_drift"] = True
        result["sources"].append(source)
    return result
