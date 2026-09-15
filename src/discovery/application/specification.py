import sqlite3
from pathlib import Path

from discovery.adapters.filesystem.artifacts import capture
from discovery.adapters.sqlite.queries import state
from discovery.adapters.sqlite.records import entity
from discovery.application import assessments
from discovery.domain.completion import (
    assurance,
    current_spec,
    design_violations,
    review_hash,
    structure,
    structure_hash,
)
from discovery.domain.encoding import canonical, digest
from discovery.domain.errors import require


def prepare(root: Path, snapshot: dict, narrative: bytes, *, final: bool = False) -> dict:
    contents = structure(snapshot)
    report = assurance(snapshot) if final else None
    confidence = assessments.project(snapshot, narrative_sha256=digest(narrative))
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
        "assumption_claims": snapshot.get("assumption_claim", []),
        "assumption_decisions": snapshot.get("assumption_decision", []),
    }
    if "defeater_check" in snapshot:
        manifest["defeater_checks"] = snapshot["defeater_check"]
    narrative_text = narrative.decode("utf-8").lstrip()
    # The renderer owns the document title. Accept an authored H1 for convenience,
    # but remove it from the body so the product artifact has exactly one title.
    if narrative_text.startswith("# "):
        _, separator, narrative_text = narrative_text.partition("\n")
        narrative_text = narrative_text.lstrip() if separator else ""
    text = "# " + snapshot["run"]["run_title"] + "\n\n" + narrative_text + "\n\n"
    text += assessments.markdown(snapshot, narrative_sha256=digest(narrative))
    text += "## Assumptions and conditional conclusions\n\n"
    active_assumptions = [a for a in snapshot["assumption"] if a["assumption_status"] == "active"]
    if active_assumptions:
        for assumption in active_assumptions:
            linked_claims = [
                f"C-{link['claim_id']:03d}"
                for link in snapshot.get("assumption_claim", [])
                if link["assumption_id"] == assumption["assumption_id"]
            ]
            linked_decisions = [
                f"D-{link['technical_decision_id']:03d}"
                for link in snapshot.get("assumption_decision", [])
                if link["assumption_id"] == assumption["assumption_id"]
            ]
            dependencies = ", ".join(linked_claims + linked_decisions) or "none recorded"
            text += (
                f"- AS-{assumption['assumption_id']:03d} ({assumption['impact']}): "
                f"{assumption['assumption_text']}\n"
                f"  Scope: {assumption.get('scope') or 'Not recorded'}. "
                f"Invalidates when: {assumption.get('invalidation_condition') or 'Not recorded'}. "
                f"Dependent claims/decisions: {dependencies}.\n"
            )
    else:
        text += "No active assumptions.\n"
    text += "\n"
    text += "## Structured technical requirements\n\n"
    decisions = {d["technical_decision_id"]: d for d in snapshot["technical_decision"]}
    groups = {}
    for requirement in snapshot["technical_requirement"]:
        status = decisions[requirement["technical_decision_id"]]["decision_status"]
        groups.setdefault(status, []).append(requirement)
    headings = {
        "accepted": "Current accepted decisions",
        "proposed": "Proposed decisions — not accepted",
        "rejected": "Historical rejected decisions — not current acceptance work",
    }
    for status in sorted(groups, key=lambda value: (value != "accepted", value)):
        text += f"### {headings.get(status, 'Decision status: ' + status)}\n\n"
        for r in groups[status]:
            text += (
                f"- REQ-{r['technical_requirement_id']:03d}: {r['requirement_text']} "
                f"(D-{r['technical_decision_id']:03d}, RN-{r['research_need_id']:03d}; {status})\n"
                f"  Acceptance: {r['acceptance_criteria']}\n"
                f"  Verification: {r['verification_plan']}\n"
            )
        text += "\n"
    text += "\n## Validation performed\n\n"
    if snapshot["experiment"]:
        for experiment in snapshot["experiment"]:
            receipt = artifacts.get(experiment["execution_artifact_id"])
            receipt_text = (
                f"A-{receipt['artifact_id']:03d}, sha256 {receipt['artifact_sha256']}, "
                f"run-relative `{receipt['storage_path']}`"
                if receipt
                else "no execution receipt"
            )
            text += (
                f"- EXP-{experiment['experiment_id']:03d} — "
                f"{experiment['experiment_name']}: {experiment['experiment_status']}. "
                f"Result: {experiment['result_summary'] or 'not yet interpreted'}. "
                f"Receipt: {receipt_text}.\n"
            )
            if experiment["limitations"]:
                text += f"  Limitations: {experiment['limitations']}\n"
    else:
        text += "No experiment was required for this proposal.\n"

    text += "\n## Adversarial findings and remaining risks\n\n"
    if snapshot["defeater"]:
        for defeater in snapshot["defeater"]:
            text += (
                f"- DEF-{defeater['defeater_id']:03d} "
                f"({defeater['defeater_status']}, {defeater['impact']}): "
                f"{defeater['challenge']}\n"
            )
    else:
        text += "No defeaters are recorded. Review coverage is listed in the machine handoff.\n"
    incomplete = [
        check
        for check in snapshot["adversarial_check"]
        if not check["check_status"].startswith("completed")
    ]
    for check in incomplete:
        text += (
            f"- CH-{check['adversarial_check_id']:03d} ({check['check_status']}): "
            f"{check['check_name']} — {check['disposition_reason'] or 'not yet dispositioned'}\n"
        )

    text += (
        "\n## Traceability and audit material\n\n"
        "The readable specification intentionally omits raw ledger state and execution payloads. "
        "Exact requirements, decisions, graph relationships, experiment commands, review checks, "
        "and procedural assurance remain in [handoff.json](handoff.json). Artifact hashes and "
        "run-relative locations remain in [evidence-manifest.json](evidence-manifest.json). "
        "Paths resolve relative to the original Discovery run directory. Procedural coverage is "
        "supporting audit information, not a probability that this proposal is correct.\n"
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
        "confidence": confidence,
    }
    if "defeater_check" in snapshot:
        handoff["defeater_checks"] = snapshot["defeater_check"]
    files = {
        "technical-spec.md": text.encode(),
        "evidence-manifest.json": canonical(manifest).encode(),
        "handoff.json": canonical(handoff).encode(),
        "discovery-summary.md": (
            "# Discovery summary\n\n"
            + (
                "Finalized technical recommendation."
                if final
                else "Draft technical recommendation."
            )
            + "\n\nRead [technical-spec.md](technical-spec.md) for the engineering answer. "
            "Read [handoff.json](handoff.json) only when exact machine traceability is needed.\n\n"
            + "## Current conditions\n\n"
            + (
                "\n".join(
                    f"- AS-{a['assumption_id']:03d}: {a['assumption_text']}"
                    for a in active_assumptions
                )
                if active_assumptions
                else "- No active assumptions."
            )
            + "\n\n## Remaining review limits\n\n"
            + (
                "\n".join(
                    f"- {c['check_name']}: {c['disposition_reason'] or c['check_status']}"
                    for c in incomplete
                )
                if incomplete
                else "- No incomplete adversarial checks."
            )
            + "\n\nConclusion confidence is explained in the technical specification; "
            "procedural scores, when present, are retained in the machine handoff.\n"
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
