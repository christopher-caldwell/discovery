import json
import sqlite3
from pathlib import Path

from discovery.adapters.filesystem.artifacts import capture
from discovery.adapters.sqlite.queries import state
from discovery.adapters.sqlite.records import entity
from discovery.domain.completion import (
    assurance,
    current_spec,
    design_violations,
    review_hash,
    structure,
    structure_hash,
)
from discovery.domain.encoding import canonical
from discovery.domain.errors import require


def prepare(root: Path, snapshot: dict, narrative: bytes, *, final: bool = False) -> dict:
    contents = structure(snapshot)
    report = assurance(snapshot) if final else None
    artifacts = {a["artifact_id"]: a for a in snapshot["artifact"]}
    manifest = {
        "sources": snapshot["sources"],
        "evidence": snapshot["evidence"],
        "artifacts": [
            a
            for a in artifacts.values()
            if a["artifact_kind"] not in ("spec_export", "technical_narrative")
        ],
        "experiment_artifacts": snapshot["experiment_artifact"],
        "proof_evidence": snapshot["proof_obligation_evidence"],
        "proof_experiments": snapshot["proof_obligation_experiment"],
        "defeater_evidence": snapshot["defeater_evidence"],
        "arguments": snapshot["argument"],
        "argument_evidence": snapshot["argument_evidence"],
    }
    text = "# " + snapshot["run"]["run_title"] + "\n\n" + narrative.decode("utf-8") + "\n\n"
    text += "## Structured technical requirements\n\n"
    for r in snapshot["technical_requirement"]:
        text += (
            f"- REQ-{r['technical_requirement_id']:03d}: {r['requirement_text']} "
            f"(D-{r['technical_decision_id']:03d}, RN-{r['research_need_id']:03d})\n"
            f"  Acceptance: {r['acceptance_criteria']}\n"
            f"  Verification: {r['verification_plan']}\n"
        )
    text += (
        "\n## Structured discovery record\n\n```json\n" + json.dumps(contents, indent=2) + "\n```\n"
    )
    text += (
        "\n## Limitations and adversarial record\n\n```json\n"
        + json.dumps(
            {
                "checks": snapshot["adversarial_check"],
                "defeaters": snapshot["defeater"],
                "assurance": report,
            },
            indent=2,
        )
        + "\n```\n"
    )
    handoff = {
        "format": "discovery-handoff-v1",
        "run_uuid": snapshot["run"]["discovery_run_uuid"],
        "final": final,
        "requirements": snapshot["technical_requirement"],
        "decisions": snapshot["technical_decision"],
        "proof_obligations": snapshot["proof_obligation"],
        "traceability": contents,
        "assurance": report,
    }
    files = {
        "technical-spec.md": text.encode(),
        "evidence-manifest.json": canonical(manifest).encode(),
        "handoff.json": canonical(handoff).encode(),
        "discovery-summary.md": (
            "# Discovery summary\n\n"
            + ("Finalized" if final else "Draft")
            + "\n\n"
            + canonical(
                {
                    "assurance": report,
                    "limitations": [
                        c["disposition_reason"]
                        for c in snapshot["adversarial_check"]
                        if not c["check_status"].startswith("completed")
                    ],
                }
            )
        ).encode(),
    }
    return {
        "structure_sha256": structure_hash(snapshot),
        "review_sha256": review_hash(snapshot),
        "narrative": capture(root, narrative),
        "files": {name: capture(root, content) for name, content in files.items()},
        "scores": report,
    }


def compile_spec(
    con: sqlite3.Connection, actor: int, prepared: dict, root: Path, *, final: bool = False
) -> dict:
    snapshot = state(con, root)
    require(
        prepared["structure_sha256"] == structure_hash(snapshot),
        "SPEC_STALE",
        "Structured state changed during compilation.",
    )
    if final:
        require(
            prepared["review_sha256"] == review_hash(snapshot),
            "SPEC_STALE",
            "Adversarial state changed during final compilation.",
        )
    if not final:
        require(
            snapshot["phase"]["phase_no"] in (3, 4), "WRONG_PHASE", "Drafts require Phase 3 or 4."
        )
        failures = design_violations(snapshot, draft=False)
        require(
            not failures,
            "SPEC_INCOMPLETE",
            "Resolve design/proof gates first.",
            violations=failures,
        )
    narrative = entity(
        con,
        "artifact",
        artifact_kind="technical_narrative",
        media_type="text/markdown",
        captured_by_actor_id=actor,
        **prepared["narrative"],
    )
    bundle = {}
    for filename, metadata in prepared["files"].items():
        a = entity(
            con,
            "artifact",
            artifact_kind="spec_export",
            media_type="application/json" if filename.endswith(".json") else "text/markdown",
            captured_by_actor_id=actor,
            **metadata,
        )
        bundle[filename] = {**a, **metadata}
    con.execute(
        "UPDATE technical_spec_revision SET spec_status='superseded' WHERE"
        " spec_status<>'superseded'"
    )
    revision = con.execute(
        "SELECT coalesce(max(revision_no),0)+1 FROM technical_spec_revision"
    ).fetchone()[0]
    result = entity(
        con,
        "spec",
        phase_revision_id=snapshot["phase"]["phase_revision_id"],
        revision_no=revision,
        spec_status="final" if final else "draft",
        artifact_id=bundle["technical-spec.md"]["id"],
        narrative_artifact_id=narrative["id"],
        structure_sha256=prepared["structure_sha256"],
        bundle_json=canonical(bundle),
        scoring_model="structural-coverage-v1",
        overall_assurance_score=prepared["scores"]["overall"] if final else None,
        created_by_actor_id=actor,
    )
    if final:
        for dimension, score in prepared["scores"]["dimensions"].items():
            con.execute(
                "INSERT INTO assurance_score VALUES (?,?,?,?)",
                (result["id"], dimension, score, canonical(prepared["scores"])),
            )
    return {**result, "revision": revision, "files": bundle, "assurance": prepared["scores"]}


def final_narrative(snapshot: dict, root: Path) -> bytes:
    spec = current_spec(snapshot)
    require(spec is not None, "SPEC_REQUIRED", "Draft required before finalization.")
    a = next(a for a in snapshot["artifact"] if a["artifact_id"] == spec["narrative_artifact_id"])
    return (root / a["storage_path"]).read_bytes()
