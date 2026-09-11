import copy
import json
from pathlib import Path

import pytest
from conftest import question
from test_completion import challenges, designed, draft  # noqa: F401
from test_phase2 import investigation  # noqa: F401

from discovery.application import assessments, specification
from discovery.domain.encoding import uid
from discovery.domain.errors import DiscoveryError


def unresolved():
    return {
        "conclusions": [
            {
                "conclusion": "Retries meet the production delivery objective",
                "scope": "Provided repository only; no production measurements",
                "disposition": "unresolved",
                "support_level": "unassessed",
                "supporting_evidence": [],
                "contrary_evidence": [],
                "limitations": ["Local mock tests do not measure production reliability"],
                "unknowns": ["Production latency and failure distributions"],
                "rationale": "Available observations cannot establish the objective",
                "would_change_with": ["Representative production measurements"],
            }
        ],
    }


def snapshot(run):
    return run["call"]("spec", "snapshot")["result"]


def test_unresolved_assessment_is_durable_replayable_and_does_not_advance(run):
    call = run["call"]
    question(call)
    before = call("phase", "check")["result"]
    path = run["root"].parent / "assessment.json"
    path.write_text(json.dumps(unresolved()))
    request = uid()
    first = call("assessment", "record", "--file", str(path), request=request)
    replay = call("assessment", "record", "--file", str(path), request=request)
    assert replay["replayed"] and replay["result"] == first["result"]
    result = call("report", "export")["result"]
    packet = json.loads((Path(result["directory"]) / "report.json").read_text())
    assessment = packet["confidence"]
    assert assessment["status"] == "current"
    assert assessment["score"] is None
    assert assessment["latest"]["conclusions"][0]["support_rating"] is None
    assert len(assessment["open_questions"]) == 1
    assert call("phase", "check")["result"] == before
    assert call("report", "export")["result"] == result
    assert call("audit", "verify")["result"]["valid"]
    call("question", "resolve", "Q-001", "--answer", "Product requires per-key ordering")
    assert assessments.project(snapshot(run))["status"] == "stale"


def test_support_checks_references_without_claiming_semantic_verification(run):
    state = snapshot(run)
    state["evidence"] = [{"evidence_id": 1, "evidence_status": "active"}]
    payload = unresolved()
    item = payload["conclusions"][0]
    item.update(disposition="supported", support_level="strong", supporting_evidence=["E-001"])
    assert assessments.validate(payload, state) == payload
    state["evidence"][0]["evidence_status"] = "retracted"
    with pytest.raises(DiscoveryError, match="active E-NNN"):
        assessments.validate(payload, state)
    item["supporting_evidence"] = ["E-999"]
    with pytest.raises(DiscoveryError, match="active E-NNN"):
        assessments.validate(payload, state)
    item.update(disposition="unresolved", support_level="strong", supporting_evidence=[])
    with pytest.raises(DiscoveryError, match="unassessed"):
        assessments.validate(payload, state)


def test_assessment_freshness_tracks_evidence_and_narrative_not_its_own_storage(run):
    state = snapshot(run)
    before = assessments.fingerprint(state)
    state["conclusion_assessment"] = [{"arbitrary": "new assessment"}]
    state["artifact"].append({"artifact_id": 999, "artifact_sha256": "new report bytes"})
    assert assessments.fingerprint(state) == before
    changed = copy.deepcopy(state)
    changed["sources"][0]["observed_drift"] = True
    assert assessments.fingerprint(changed) != before
    changed = copy.deepcopy(state)
    changed["evidence"].append({"evidence_id": 1, "evidence_status": "active"})
    assert assessments.fingerprint(changed) != before
    state["technical_spec_revision"] = [{"narrative_artifact_id": 999}]
    assert assessments.fingerprint(state) != before
    bound = assessments.fingerprint(state)
    state["technical_spec_revision"][0].update(spec_status="final", bundle_json="new export")
    assert assessments.fingerprint(state) == bound


def test_final_export_never_infers_confidence_from_assurance(run):
    state = snapshot(run)
    packet = specification.prepare(run["root"], state, b"No conclusion assessed", final=True)
    # prepare captures bytes; inspect generated handoff via its artifact receipt.
    handoff = packet["files"]["handoff.json"]
    assert handoff
    assert assessments.project(state)["status"] == "not_assessed"
    assert b"not_assessed" in (run["root"] / handoff["storage_path"]).read_bytes()


def test_assessment_survives_real_finalization_without_claiming_review(designed):  # noqa: F811
    call = designed["call"]
    draft(designed)
    call("phase", "advance")
    challenges(designed)
    path = designed["root"].parent / "assessment.json"
    payload = unresolved()
    item = payload["conclusions"][0]
    item.update(
        conclusion="Fixture's scoped source observation",
        disposition="supported",
        support_level="limited",
        supporting_evidence=["E-001"],
    )
    path.write_text(json.dumps(payload))
    call("assessment", "record", "--file", str(path))
    assert call("assessment", "list")["result"]["status"] == "current"
    call("phase", "advance")
    assessment = call("assessment", "list")["result"]
    assert assessment["status"] == "current"
    assert "does not establish independent review" in assessment["meaning"]
    assert assessment["latest"]["conclusions"][0]["support_rating"] == 1


def test_changed_narrative_export_is_stale_before_database_write(run):
    path = run["root"].parent / "assessment.json"
    path.write_text(json.dumps(unresolved()))
    run["call"]("assessment", "record", "--file", str(path))
    current = snapshot(run)
    assert assessments.project(current)["status"] == "current"
    prepared = specification.prepare(run["root"], current, b"Changed technical proposal")
    handoff = json.loads(
        (run["root"] / prepared["files"]["handoff.json"]["storage_path"]).read_text()
    )
    assert handoff["confidence"]["status"] == "stale"


def test_report_leads_with_readable_assessment_and_explicit_staleness(run):
    call = run["call"]
    path = run["root"].parent / "assessment.json"
    path.write_text(json.dumps(unresolved()))
    call("assessment", "record", "--file", str(path))
    report = call("report", "export")["result"]
    text = (Path(report["directory"]) / "report.md").read_text()
    assert text.count("## Conclusion confidence") == 1
    assert "## Confidence and limitations" not in text
    assert "support: unassessed; no rating assigned" in text
    assert "(None)" not in text
    assert "Supporting evidence: None recorded" in text
    assert "Contrary evidence: None recorded" in text
    assert text.index("## Conclusion confidence") < text.index("## Unresolved questions")
    question(call)
    report = call("report", "export")["result"]
    stale = (Path(report["directory"]) / "report.md").read_text()
    assert "**Stale assessment:" in stale
    assert "historical, not current confidence" in stale
