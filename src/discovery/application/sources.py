import json
import sqlite3
from pathlib import Path

from discovery.adapters.git.repository import baseline
from discovery.adapters.sqlite.records import entity
from discovery.application.claims import invalidate_claim
from discovery.application.investigation import reopen
from discovery.domain.encoding import digest, now
from discovery.domain.errors import require


def write(
    con: sqlite3.Connection, actor: int, name: str, data: dict, prepared: dict, root: Path
) -> dict:
    run = con.execute("SELECT * FROM discovery_run").fetchone()
    require(
        run["current_phase_no"] in (1, 2),
        "WRONG_PHASE",
        "Source maintenance requires Phase 1 or 2.",
    )
    source = con.execute(
        "SELECT * FROM source_repository WHERE baseline_status='active'"
    ).fetchone()
    policy = json.loads(run["config_json"])
    if name == "source.refresh":
        current = baseline(
            Path(source["repository_root"]), root, set(policy["source_excluded_directories"])
        )
        require(
            current == prepared["source"],
            "SOURCE_DRIFT",
            "Source changed during refresh; retry from a stable baseline.",
        )
        require(
            any(current[k] != source[k] for k in ("baseline_revision", "baseline_tree_hash")),
            "INVALID_STATE",
            "Source baseline is already current.",
        )
        con.execute(
            "UPDATE source_repository SET "
            "baseline_status='superseded',drift_status='drifted',dt_modified=? WHERE "
            "source_repository_id=?",
            (now(), source["source_repository_id"]),
        )
        result = entity(con, "source", captured_by_actor_id=actor, **current)
        affected = con.execute(
            "SELECT e.* FROM evidence e JOIN artifact a USING(artifact_id) WHERE "
            "a.source_repository_id=? AND e.evidence_status='active'",
            (source["source_repository_id"],),
        ).fetchall()
        claim_ids = set()
        for e in affected:
            con.execute(
                "UPDATE evidence SET evidence_status='retracted',dt_modified=? WHERE evidence_id=?",
                (now(), e["evidence_id"]),
            )
            con.execute(
                "UPDATE argument SET counter_status='open',dt_modified=? "
                "WHERE resolution_evidence_id=?",
                (now(), e["evidence_id"]),
            )
            claim_ids.update(
                r[0]
                for r in con.execute(
                    "SELECT a.claim_id FROM argument a LEFT JOIN argument_evidence ae "
                    "USING(argument_id) WHERE ae.evidence_id=? OR a.resolution_evidence_id=?",
                    (e["evidence_id"], e["evidence_id"]),
                )
            )
            reopen(con, e["research_lane_id"])
        for cid in claim_ids:
            invalidate_claim(con, cid)
        return {
            **result,
            "retracted_evidence": [e["evidence_uuid"] for e in affected],
            "invalidated_claim_ids": sorted(claim_ids),
        }
    require(
        run["current_phase_no"] == 2, "WRONG_PHASE", "Evidence artifact capture requires Phase 2."
    )
    values = {}
    if data["source_backed"]:
        path = Path(data["file"])
        source_root = Path(source["repository_root"])
        require(
            path.is_relative_to(source_root),
            "SCOPE_MISMATCH",
            "Source artifact must be a file within the source baseline.",
        )
        relative = path.relative_to(source_root)
        require(
            not any(part in policy["source_excluded_directories"] for part in relative.parts[:-1])
            and path.name != ".DS_Store"
            and not path.is_relative_to(root),
            "SCOPE_MISMATCH",
            "Source-backed artifacts must belong to the fingerprinted source tree.",
        )
        current = baseline(source_root, root, set(policy["source_excluded_directories"]))
        require(
            all(current[k] == source[k] for k in ("baseline_revision", "baseline_tree_hash")),
            "SOURCE_DRIFT",
            "Refresh source baseline before capturing evidence.",
        )
        require(
            digest(path.read_bytes()) == prepared["artifact"]["artifact_sha256"],
            "SOURCE_DRIFT",
            "File changed during capture.",
        )
        values = {
            "source_repository_id": source["source_repository_id"],
            "source_revision": source["baseline_revision"],
            "source_locator": str(path.relative_to(source_root)),
        }
    return entity(
        con,
        "artifact",
        artifact_kind="source_snapshot" if values else "external_snapshot",
        media_type="application/octet-stream",
        captured_by_actor_id=actor,
        origin_uri=data["origin_uri"],
        **values,
        **prepared["artifact"],
    )
