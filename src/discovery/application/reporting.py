"""Human-readable, non-final output from the existing audited discovery records."""

from pathlib import Path

from discovery.adapters.filesystem.artifacts import atomic_write
from discovery.application import assessments
from discovery.domain.encoding import canonical, digest
from discovery.domain.errors import require
from discovery.domain.gates import phase_violations


def export_report(root: Path, snapshot: dict, audit: dict) -> dict:
    violations = phase_violations(snapshot)
    packet = {
        "format": "discovery-report-v1",
        "is_final_specification": False,
        "audit_head": audit["head_hash"],
        "audit_event_count": audit["event_count"],
        "audit": audit,
        "gate": {"can_advance": not violations, "violations": violations},
        "confidence": assessments.project(snapshot),
        "state": snapshot,
    }
    encoded = canonical(packet).encode()
    sha = digest(encoded)
    artifacts = {a["artifact_id"]: a for a in snapshot["artifact"]}

    def artifact_label(aid):
        a = artifacts.get(aid)
        return (
            f"[A-{aid:03d}](../../../{a['storage_path']}), SHA-256 {a['artifact_sha256']}"
            if a
            else "No artifact recorded"
        )

    run = snapshot["run"]
    blocking = [
        q
        for q in snapshot["clarification_question"]
        if q["question_status"] == "open" and q["is_blocking"]
    ]
    outcome = (
        "A defensible implementation proposal cannot yet be made because a blocking "
        "decision remains unresolved. Independent recorded facts remain usable."
        if blocking
        else (
            "The recorded work supports continued progression; read the gate prerequisites "
            "and current conclusions below before treating any proposal as ready."
            if violations
            else "The current phase gate is satisfied; this is procedural readiness, not truth."
        )
    )
    lines = [
        "# Discovery investigation report",
        "",
        run["run_title"],
        "",
        f"Run status: **{run['run_status']}**. Phase: {snapshot['phase']['phase_no']}.",
        f"Audit head: `{audit['head_hash']}` ({audit['event_count']} events).",
        f"Audit valid: {audit['valid']}. Orphan artifacts: {len(audit['orphan_artifacts'])}. "
        "Full diagnostics are retained in report.json; orphans are not deleted by export.",
        "",
        "This is a current-state report, not a finalized technical specification or permission "
        "to implement. Exporting it does not complete research or advance a phase.",
        "",
        "## Current outcome and next action",
        "",
        outcome,
        "",
        (
            f"Next action: obtain an authoritative answer to "
            f"Q-{blocking[0]['clarification_question_id']:03d} while preserving useful "
            "investigation that does not depend on it."
            if blocking
            else (
                f"Next action: resolve {violations[0]['code']} — {violations[0]['message']}"
                if violations
                else "Next action: advance exactly one phase when semantic review agrees."
            )
        ),
        "",
        "## Request (assertions to investigate)",
        "",
    ]
    request = artifacts[run["input_artifact_id"]]
    request_text = (root / request["storage_path"]).read_text(encoding="utf-8", errors="replace")
    lines += ["> " + line for line in request_text.splitlines()]
    lines += [
        "",
        artifact_label(run["input_artifact_id"]),
        "",
        assessments.markdown(snapshot),
        "## Unresolved questions",
        "",
    ]
    questions = [q for q in snapshot["clarification_question"] if q["question_status"] == "open"]
    respondents = snapshot["question_respondent"]
    for q in questions:
        lines += [
            f"- Q-{q['clarification_question_id']:03d}: {q['question_text']}",
            f"  Blocking: {bool(q['is_blocking'])}. "
            f"Suggested authority (attributed hypothesis): {q['authority_category']}.",
            f"  Rationale: {q['authority_rationale']}",
        ]
        for candidate in sorted(
            (
                r
                for r in respondents
                if r["clarification_question_id"] == q["clarification_question_id"]
            ),
            key=lambda r: r["respondent_rank"],
        ):
            lines += [
                f"  Candidate {candidate['respondent_rank']}: {candidate['respondent_name']} "
                f"({candidate['respondent_kind']}; identity "
                f"{candidate.get('identity_status', 'known')}; authority confidence "
                f"{candidate['respondent_confidence']}).",
                f"  Candidate rationale: {candidate['rationale']}; support: "
                f"{artifact_label(candidate['supporting_artifact_id'])}.",
            ]
    if not questions:
        lines += ["No open questions recorded. This does not establish that none remain."]
    lines += ["", "## Active assumptions and conditions", ""]
    active_assumptions = [a for a in snapshot["assumption"] if a["assumption_status"] == "active"]
    for assumption in active_assumptions:
        lines += [
            f"- AS-{assumption['assumption_id']:03d} ({assumption['impact']}): "
            f"{assumption['assumption_text']}",
            f"  Scope: {assumption.get('scope') or 'Not recorded'}. "
            f"Why non-blocking: {assumption['justification']}",
            f"  Invalidated or resolved by: "
            f"{assumption.get('invalidation_condition') or 'Not recorded'}.",
        ]
    if not active_assumptions:
        lines += ["No active assumptions recorded."]
    lines += ["", "## Advancement prerequisites", ""]
    lines += [f"- {v['code']}: {v['message']}" for v in violations] or [
        "The current gate allows the next phase. This is not a correctness judgment."
    ]
    lines += ["", "## Research needs and lane answers", ""]
    lines += ["A covered need has planned lane coverage; it is not necessarily answered.", ""]
    for n in snapshot["research_need"]:
        lines += [
            f"- RN-{n['research_need_id']:03d} ({n['need_status']}): {n['need_statement']}",
            f"  Recorded answer: {n.get('answer_text') or 'None'}.",
        ]
    for lane in snapshot["research_lane"]:
        lines += [
            f"- L-{lane['research_lane_id']:03d} ({lane['lane_status']}): {lane['lane_question']}",
            f"  Recorded answer: {lane.get('answer_text') or 'None'}. "
            f"Limitations: {lane.get('limitations') or 'None recorded'}.",
        ]
    lines += ["", "## Recorded research observations", ""]
    lines += ["These are attributed research summaries, not automatically admitted claims.", ""]
    for activity in snapshot["research_activity"]:
        lines += [
            f"- RA-{activity['research_activity_id']:03d}: {activity['result_summary']}",
            f"  Report: {artifact_label(activity['result_artifact_id'])}",
        ]
    lines += ["", "## Registered claims", ""]
    for claim in snapshot["claim"]:
        lines += [
            f"- C-{claim['claim_id']:03d} ({claim['claim_status']}): {claim['claim_statement']}",
            f"  Verification: {claim.get('verification_method', 'legacy unspecified')} "
            f"({claim.get('verification_availability', 'unknown')}); "
            f"{claim.get('verification_rationale') or 'no rationale recorded'}.",
        ]
    if not snapshot["claim"]:
        lines += ["No claims registered for formal evidence evaluation."]
    contrary = [a for a in snapshot["argument"] if a["argument_role"] in ("refutes", "qualifies")]
    lines += ["", "## Contrary and qualifying evidence", ""]
    for argument in contrary:
        lines += [
            f"- ARG-{argument['argument_id']:03d} ({argument['counter_status']}): "
            f"{argument['reasoning']}",
            f"  Limitations: {argument['limitations'] or 'None recorded'}.",
        ]
    if not contrary:
        lines += ["No contrary or qualifying argument has been registered."]
    if snapshot.get("defeater_check"):
        lines += ["", "## Canonical adversarial findings", ""]
        for d in snapshot["defeater"]:
            checks = ", ".join(
                f"CH-{link['adversarial_check_id']:03d}"
                for link in snapshot["defeater_check"]
                if link["defeater_id"] == d["defeater_id"]
            )
            lines += [
                f"- DEF-{d['defeater_id']:03d} ({d['defeater_status']}): {d['challenge']}",
                f"  Checks: {checks}. Resolution: {d['resolution'] or 'None recorded'}.",
            ]
    lines += ["", "## Source observations", ""]
    for source in snapshot["sources"]:
        lines += [
            f"- {source['repository_uri']}: `{source['baseline_revision']}`; "
            f"observed drift: {source['observed_drift']}; "
            f"recorded status: {source['drift_status']}."
        ]
    lines += [
        "",
        "## Report limitations",
        "",
        "The companion report.json preserves the structured snapshot, including answers, "
        "evidence links, verification records and pending work. Artifact paths are relative "
        "to the run directory; keep the run to inspect their bytes. This is not a standalone "
        "evidence archive. Source freshness is observed, not an atomic filesystem snapshot.",
        "",
    ]
    files = {"report.json": encoded, "report.md": "\n".join(lines).encode()}
    bundle_sha = digest(
        canonical({name: digest(content) for name, content in files.items()}).encode()
    )
    folder = root / "exports" / "reports" / bundle_sha
    for path in (root / "exports", root / "exports" / "reports", folder):
        require(not path.is_symlink(), "EXPORT_CONFLICT", "Export path contains a symlink.")
    require(folder.resolve().is_relative_to(root.resolve()), "EXPORT_CONFLICT", "Invalid path.")
    for name, content in files.items():
        path = folder / name
        require(not path.is_symlink(), "EXPORT_CONFLICT", "Export file is a symlink.")
        require(
            not path.exists() or (path.is_file() and path.read_bytes() == content),
            "EXPORT_CONFLICT",
            "Export file already has different content.",
        )
    for name, content in files.items():
        atomic_write(folder / name, content)
    return {
        "directory": str(folder),
        "files": [str(folder / name) for name in files],
        "snapshot_sha256": sha,
        "bundle_sha256": bundle_sha,
        "audit_head": audit["head_hash"],
        "is_final_specification": False,
    }
