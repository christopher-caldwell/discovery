"""Compact recovery preserves reasoning state and identifies omitted payloads."""
# ruff: noqa: F811 -- imported pytest fixtures are requested by parameter name.

import json

from test_completion import designed  # noqa: F401
from test_phase2 import investigation  # noqa: F401
from test_receipt_evidence import execute_receipt


def test_compact_resume_preserves_state_and_full_execution_retrieval(designed, monkeypatch):
    call = designed["call"]
    _, artifact = execute_receipt(designed, monkeypatch)
    before = call("audit", "verify")["result"]
    full = call("resume")["result"]
    compact = call("resume", "--compact")["result"]
    assert compact["context_projection"]["mode"] == "compact"
    for key in full.keys() - {"experiments", "specifications"}:
        assert compact[key] == full[key]
    assert len(compact["experiments"]) == len(full["experiments"])
    for row, original in zip(compact["experiments"], full["experiments"], strict=True):
        assert row == {
            k: v for k, v in original.items() if k not in ("command_json", "environment_json")
        }
    assert compact["experiments"][0]["execution_artifact_id"] == artifact["id"]
    assert compact["investigator_actions"]
    assert (
        call("experiment", "list")["result"][0]["command_json"]
        == full["experiments"][0]["command_json"]
    )
    assert call("audit", "verify")["result"] == before
    assert json.loads(full["experiments"][0]["command_json"]) == ["/usr/bin/true"]
