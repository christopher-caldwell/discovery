import json
import sqlite3
from pathlib import Path

from discovery.adapters.filesystem.artifacts import capture
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
        run["current_phase_no"] in (1, 2) or name == "artifact.capture",
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
            "SELECT e.*,a.artifact_sha256,a.artifact_kind,a.media_type,a.byte_size,"
            "a.storage_path,a.origin_uri,a.source_locator AS artifact_source_locator,"
            "a.metadata_json FROM evidence e JOIN artifact a USING(artifact_id) WHERE "
            "a.source_repository_id=? AND e.evidence_status='active'",
            (source["source_repository_id"],),
        ).fetchall()
        claim_ids = set()
        retracted = []
        revalidated = []
        replacement_artifacts = {}
        for e in affected:
            locator = Path(e["artifact_source_locator"] or "")
            source_path = Path(source["repository_root"]) / locator
            unchanged = bool(
                e["artifact_source_locator"]
                and not locator.is_absolute()
                and ".." not in locator.parts
                and source_path.is_file()
                and not source_path.is_symlink()
                and digest(source_path.read_bytes()) == e["artifact_sha256"]
            )
            if unchanged:
                replacement = replacement_artifacts.get(e["artifact_id"])
                if replacement is None:
                    replacement = entity(
                        con,
                        "artifact",
                        artifact_kind=e["artifact_kind"],
                        artifact_sha256=e["artifact_sha256"],
                        media_type=e["media_type"],
                        byte_size=e["byte_size"],
                        storage_path=e["storage_path"],
                        origin_uri=e["origin_uri"],
                        source_repository_id=result["id"],
                        source_revision=current["baseline_revision"],
                        source_locator=e["artifact_source_locator"],
                        captured_by_actor_id=actor,
                        metadata_json=e["metadata_json"],
                    )
                    con.execute(
                        "INSERT INTO artifact_lineage VALUES (?,?,?)",
                        (replacement["id"], e["artifact_id"], "revalidated_unchanged_source"),
                    )
                    replacement_artifacts[e["artifact_id"]] = replacement
                con.execute(
                    "UPDATE evidence SET artifact_id=?,dt_modified=? WHERE evidence_id=?",
                    (replacement["id"], now(), e["evidence_id"]),
                )
                revalidated.append(e["evidence_uuid"])
                continue
            con.execute(
                "UPDATE evidence SET evidence_status='retracted',dt_modified=? WHERE evidence_id=?",
                (now(), e["evidence_id"]),
            )
            retracted.append(e["evidence_uuid"])
            con.execute(
                "UPDATE defeater SET defeater_status='open',dt_modified=? WHERE defeater_id IN "
                "(SELECT defeater_id FROM defeater_evidence WHERE evidence_id=? "
                "AND relationship='refutes_challenge') AND defeater_status='defeated'",
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
            "retracted_evidence": retracted,
            "revalidated_evidence": revalidated,
            "invalidated_claim_ids": sorted(claim_ids),
        }
    require(
        run["current_phase_no"] in (2, 3, 4),
        "WRONG_PHASE",
        "Evidence artifact capture requires Phases 2–4; use research record in Phase 1.",
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
            digest(path.read_bytes()) == data["content_sha256"],
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
        **capture(root, prepared["content"]),
    )
