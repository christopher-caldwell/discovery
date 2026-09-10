"""Registered execution provenance and repeated proof attachments."""
# ruff: noqa: F811 -- imported pytest fixtures are requested by parameter name.

import pytest
from test_completion import designed, plan_experiment  # noqa: F401
from test_phase2 import investigation  # noqa: F401

from discovery.adapters.sqlite.connection import connect
from discovery.adapters.sqlite.records import entity
from discovery.application import claims, experiments
from discovery.domain.encoding import uid
from discovery.domain.errors import DiscoveryError


def execute_receipt(env, monkeypatch, exit_code=0):
    def process(box, argv, timeout):
        return {
            "argv": argv,
            "environment": {},
            "exit_code": exit_code,
            "timed_out": False,
            "stdout": {"text": "Observed result from injected test process adapter"},
        }

    monkeypatch.setattr(experiments, "run_process", process)
    experiment = plan_experiment(env)
    result = env["call"]("experiment", "exec", experiment["ref"], "--command", '["/usr/bin/true"]')[
        "result"
    ]
    return experiment, result["artifact"]


def extract(env, artifact, expected=0):
    return env["call"](
        "evidence",
        "create",
        "--lane",
        env["lane"]["ref"],
        "--artifact",
        artifact["ref"],
        "--kind",
        "empirical",
        "--locator",
        "$.exit_code and $.stdout.text",
        "--observation",
        "The registered process returned its recorded result",
        expected=expected,
    )


@pytest.mark.parametrize("exit_code", [0, 1])
def test_registered_receipt_without_origin_is_empirical_evidence(designed, monkeypatch, exit_code):
    env = designed
    experiment, artifact = execute_receipt(env, monkeypatch, exit_code)
    call = env["call"]
    call(
        "experiment",
        "finish",
        experiment["ref"],
        "--outcome",
        "passed" if exit_code == 0 else "failed",
        "--conclusion",
        "Observed adapter result",
        "--limitations",
        "Synthetic adapter only",
    )
    with connect(env["root"] / "discovery.sqlite") as db:
        assert (
            db.execute(
                "SELECT origin_uri FROM artifact WHERE artifact_id=?", (artifact["id"],)
            ).fetchone()[0]
            is None
        )
    result = extract(env, artifact)["result"]
    with connect(env["root"] / "discovery.sqlite") as db:
        evidence = db.execute(
            "SELECT * FROM evidence WHERE evidence_id=?", (result["id"],)
        ).fetchone()
        assert evidence["artifact_id"] == artifact["id"]
    assert call("audit", "verify")["result"]["valid"]


@pytest.mark.parametrize("alteration", ["unlinked", "no_execution", "wrong_kind", "request_bytes"])
def test_receipt_provenance_is_not_a_kind_only_or_request_bypass(designed, monkeypatch, alteration):
    env = designed
    _, artifact = execute_receipt(env, monkeypatch)
    # Exercise the application guard directly with synthetic rows. The outer
    # command store separately rejects unaudited mutations, and artifact updates
    # are forbidden; create a new artifact rather than modifying the receipt.
    with connect(env["root"] / "discovery.sqlite") as db:
        values = dict(
            db.execute("SELECT * FROM artifact WHERE artifact_id=?", (artifact["id"],)).fetchone()
        )
        for key in ("artifact_id", "artifact_uuid", "dt_created"):
            values.pop(key)
        if alteration == "wrong_kind":
            values["artifact_kind"] = "external_snapshot"
        elif alteration == "request_bytes":
            values["artifact_sha256"] = db.execute(
                "SELECT a.artifact_sha256 FROM discovery_run r "
                "JOIN artifact a ON a.artifact_id=r.input_artifact_id"
            ).fetchone()[0]
        synthetic = entity(db, "artifact", **values)
        if alteration != "unlinked":
            db.execute("UPDATE experiment SET execution_artifact_id=?", (synthetic["id"],))
        if alteration == "no_execution":
            db.execute("UPDATE experiment SET execution_uuid=NULL")
        data = {
            "lane": env["lane"]["ref"],
            "artifact": synthetic["ref"],
            "kind": "empirical",
            "locator": "$.exit_code",
            "observation": "Synthetic",
        }
        with pytest.raises(DiscoveryError) as caught:
            claims.write(
                db, values["captured_by_actor_id"], "evidence.create", data, {}, env["root"]
            )
        expected = (
            "ASSERTION_NOT_EVIDENCE"
            if alteration == "request_bytes"
            else "EVIDENCE_PROVENANCE_REQUIRED"
        )
        assert caught.value.code == expected


def obligation_state(env):
    with connect(env["root"] / "discovery.sqlite") as db:
        return dict(
            db.execute(
                "SELECT * FROM proof_obligation WHERE proof_obligation_id=?",
                (env["obligation"]["id"],),
            ).fetchone()
        )


@pytest.mark.parametrize("kind", ["evidence", "experiment"])
def test_repeated_attachment_preserves_full_obligation_state(designed, monkeypatch, kind):
    env = designed
    call = env["call"]
    if kind == "evidence":
        args = (
            "obligation",
            "attach-evidence",
            env["obligation"]["ref"],
            "--evidence-ref",
            env["evidence"]["ref"],
        )
    else:
        experiment, _ = execute_receipt(env, monkeypatch)
        args = (
            "obligation",
            "attach-experiment",
            env["obligation"]["ref"],
            "--experiment",
            experiment["ref"],
        )
        call(*args)
        call(
            "obligation",
            "satisfy",
            env["obligation"]["ref"],
            "--reason",
            "Existing primary evidence still supports this obligation",
        )
    before = obligation_state(env)
    assert before["obligation_status"] == "satisfied"
    request = uid()
    assert call(*args, request=request)["result"]["status"] == "satisfied"
    assert call(*args, request=request)["replayed"]
    assert call(*args)["result"]["status"] == "satisfied"
    assert obligation_state(env) == before
    with connect(env["root"] / "discovery.sqlite") as db:
        table = "proof_obligation_" + kind
        assert (
            db.execute(
                f"SELECT COUNT(*) FROM {table} WHERE proof_obligation_id=?",
                (env["obligation"]["id"],),
            ).fetchone()[0]
            == 1
        )
    assert call("audit", "verify")["result"]["valid"]


def test_duplicate_evidence_attachment_still_rejects_retracted_evidence(designed):
    env = designed
    call = env["call"]
    call("evidence", "retract", env["evidence"]["ref"], "--reason", "Fixture retracted")
    before = obligation_state(env)
    result = call(
        "obligation",
        "attach-evidence",
        env["obligation"]["ref"],
        "--evidence-ref",
        env["evidence"]["ref"],
        expected=2,
    )
    assert result["error"]["code"] == "INVALID_STATE"
    assert obligation_state(env) == before


def test_attachment_still_rejects_other_decision_experiment(designed):
    env = designed
    call = env["call"]
    other = call(
        "decision",
        "create",
        "--strategy",
        call("strategy", "list")["result"][0]["ref"],
        "--claim",
        env["claim"]["ref"],
        "--text",
        "Different decision",
        "--rationale",
        "Independent scope",
        "--impact",
        "material",
    )["result"]
    experiment = plan_experiment({**env, "decision": other})
    before = obligation_state(env)
    result = call(
        "obligation",
        "attach-experiment",
        env["obligation"]["ref"],
        "--experiment",
        experiment["ref"],
        expected=2,
    )
    assert result["error"]["code"] == "SCOPE_MISMATCH"
    assert obligation_state(env) == before
