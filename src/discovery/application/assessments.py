"""Attributed conclusion support, deliberately separate from procedural assurance."""

import json
import sqlite3
from pathlib import Path

from discovery.adapters.sqlite.queries import state
from discovery.adapters.sqlite.records import insert
from discovery.domain.encoding import canonical, digest, uid
from discovery.domain.errors import require

LEVELS = {"unassessed": None, "limited": 1, "moderate": 2, "strong": 3}
FIELDS = {
    "conclusion",
    "scope",
    "disposition",
    "support_level",
    "supporting_evidence",
    "contrary_evidence",
    "limitations",
    "unknowns",
    "rationale",
    "would_change_with",
}
MEANING = (
    "Model or human attributed judgment: ordinal support ratings 1=limited, 2=moderate, "
    "3=strong, null=unassessed. Not a probability, calibrated confidence, or procedural score. "
    "Validation checks structure and references, not semantic truth. "
    "Finalization does not establish independent review of this assessment."
)


def fingerprint(snapshot: dict, *, narrative_sha256: str | None = None) -> str:
    # Export/draft bookkeeping and recording this assessment cannot invalidate itself.
    excluded = {
        "artifact",
        "conclusion_assessment",
        "technical_spec_revision",
        "assurance_score",
        "run",
        "phase",
        "phase_revision",
        "plan_sha256",
    }
    contents = {k: v for k, v in snapshot.items() if k not in excluded}
    specs = snapshot.get("technical_spec_revision", [])
    artifacts = {a["artifact_id"]: a for a in snapshot.get("artifact", [])}
    narrative_id = specs[-1].get("narrative_artifact_id") if specs else None
    contents["narrative_sha256"] = narrative_sha256 or artifacts.get(narrative_id, {}).get(
        "artifact_sha256"
    )
    contents["run_uuid"] = snapshot["run"]["discovery_run_uuid"]
    contents["phase_revision_id"] = snapshot["phase"]["phase_revision_id"]
    return digest(canonical(contents).encode())


def validate(payload: dict, snapshot: dict) -> dict:
    require(
        isinstance(payload, dict) and set(payload) == {"conclusions"},
        "INVALID_ARGUMENT",
        "Assessment requires exactly a conclusions array.",
    )
    conclusions = payload["conclusions"]
    require(
        isinstance(conclusions, list) and 0 < len(conclusions) <= 50,
        "INVALID_ARGUMENT",
        "Provide between 1 and 50 conclusions.",
    )
    evidence = {f"E-{e['evidence_id']:03d}": e for e in snapshot["evidence"]}
    for item in conclusions:
        require(
            isinstance(item, dict) and set(item) == FIELDS,
            "INVALID_ARGUMENT",
            "Each conclusion must contain the documented assessment fields.",
        )
        for field in ("conclusion", "scope", "rationale"):
            require(
                isinstance(item[field], str) and item[field].strip(),
                "INVALID_ARGUMENT",
                f"{field} must be nonempty text.",
            )
        require(
            isinstance(item["disposition"], str)
            and item["disposition"] in ("supported", "refuted", "conditional", "unresolved"),
            "INVALID_ARGUMENT",
            "Invalid conclusion disposition.",
        )
        require(
            isinstance(item["support_level"], str) and item["support_level"] in LEVELS,
            "INVALID_ARGUMENT",
            "Invalid support_level.",
        )
        for field in (
            "supporting_evidence",
            "contrary_evidence",
            "limitations",
            "unknowns",
            "would_change_with",
        ):
            values = item[field]
            require(
                isinstance(values, list) and all(isinstance(v, str) and v.strip() for v in values),
                "INVALID_ARGUMENT",
                f"{field} must be an array of nonempty strings.",
            )
            require(
                len(values) == len(set(values)), "INVALID_ARGUMENT", f"Duplicate {field} entries."
            )
        require(
            item["limitations"] and item["would_change_with"],
            "INVALID_ARGUMENT",
            "Each conclusion needs limitations and conditions that would change it.",
        )
        for ref in item["supporting_evidence"] + item["contrary_evidence"]:
            require(
                ref in evidence and evidence[ref]["evidence_status"] == "active",
                "ASSESSMENT_EVIDENCE_INVALID",
                f"Evidence must be an active E-NNN reference: {ref}",
            )
        require(
            not set(item["supporting_evidence"]) & set(item["contrary_evidence"]),
            "INVALID_ARGUMENT",
            "One evidence reference cannot both support and contradict the same proposition.",
        )
        if item["disposition"] == "unresolved":
            require(
                item["unknowns"] and item["support_level"] == "unassessed",
                "INVALID_ARGUMENT",
                "An unresolved proposition requires unknowns and unassessed support.",
            )
        else:
            required = (
                "contrary_evidence" if item["disposition"] == "refuted" else "supporting_evidence"
            )
            require(
                item[required] and item["support_level"] != "unassessed",
                "INVALID_ARGUMENT",
                f"Assessed {item['disposition']} requires {required} and a support level.",
            )
        if item["disposition"] == "conditional":
            require(
                item["unknowns"],
                "INVALID_ARGUMENT",
                "Conditional conclusions must state unresolved conditions.",
            )
    return payload


def record(con: sqlite3.Connection, actor: int, payload: dict, root: Path) -> dict:
    snapshot = state(con, root)
    validate(payload, snapshot)
    identifier = uid()
    numeric = insert(
        con,
        "conclusion_assessment",
        assessment_uuid=identifier,
        created_by_actor_id=actor,
        phase_revision_id=snapshot["phase"]["phase_revision_id"],
        snapshot_sha256=fingerprint(snapshot),
        assessment_json=canonical(payload),
    )
    return {"id": numeric, "uuid": identifier, "ref": f"CA-{numeric:03d}"}


def project(snapshot: dict, *, narrative_sha256: str | None = None) -> dict:
    current_hash = fingerprint(snapshot, narrative_sha256=narrative_sha256)
    records = []
    for row in sorted(snapshot.get("conclusion_assessment", []), key=lambda r: r["assessment_id"]):
        payload = json.loads(row["assessment_json"])
        records.append(
            {
                "ref": f"CA-{row['assessment_id']:03d}",
                "created_by_actor_id": row["created_by_actor_id"],
                "snapshot_sha256": row["snapshot_sha256"],
                "status": "current" if row["snapshot_sha256"] == current_hash else "stale",
                "conclusions": [
                    {**item, "support_rating": LEVELS[item["support_level"]]}
                    for item in payload["conclusions"]
                ],
            }
        )
    latest = records[-1] if records else None
    return {
        "status": latest["status"] if latest else "not_assessed",
        "score": None,
        "meaning": MEANING,
        "latest": latest,
        "history": records,
        "open_questions": [
            q for q in snapshot["clarification_question"] if q["question_status"] == "open"
        ],
        "confirmed_defeaters": [
            d for d in snapshot["defeater"] if d["defeater_status"] == "confirmed"
        ],
    }


def markdown(snapshot: dict, *, narrative_sha256: str | None = None) -> str:
    assessment = project(snapshot, narrative_sha256=narrative_sha256)
    text = "## Conclusion confidence\n\n" + MEANING + "\n\n"
    text += f"Assessment status: **{assessment['status']}**. No aggregate score is assigned.\n\n"
    if assessment["status"] == "stale":
        text += (
            "**Stale assessment: the investigation has changed. "
            "The judgments below are historical, not current confidence.**\n\n"
        )
    if assessment["latest"]:
        for item in assessment["latest"]["conclusions"]:
            text += f"### {item['conclusion']}\n\n"
            support = (
                "unassessed; no rating assigned"
                if item["support_rating"] is None
                else f"{item['support_level']} (ordinal rating {item['support_rating']})"
            )
            text += f"Disposition: {item['disposition']}; support: {support}.\n\n"
            for field in (
                "scope",
                "rationale",
                "supporting_evidence",
                "contrary_evidence",
                "limitations",
                "unknowns",
                "would_change_with",
            ):
                value = item[field]
                rendered = (
                    (", ".join(value) or "None recorded") if isinstance(value, list) else value
                )
                text += f"{field.replace('_', ' ').capitalize()}: {rendered}\n\n"
    text += (
        f"Recorded open questions: {len(assessment['open_questions'])}; "
        f"confirmed defeaters: {len(assessment['confirmed_defeaters'])}.\n\n"
    )
    return text
