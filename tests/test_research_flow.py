from test_phase2 import investigation  # noqa: F401

from discovery.domain.encoding import uid


def record_args(env, surface):
    report = env["root"].parent / "research.txt"
    report.write_text(
        "Inspected the contract and the caller: the implementation disagrees. "
        "Owner decision is unresolved."
    )
    return (
        "research",
        "record",
        surface,
        "--query",
        "Compare contract with caller",
        "--summary",
        "Contract and implementation disagree; owner decision unresolved",
        "--origin-uri",
        report.as_uri(),
        "--report",
        str(report),
    )


def test_planning_record_completes_surface_and_resumes_provenance(run):
    call = run["call"]
    surface = call("surface", "list")["result"][0]
    before = call("audit", "verify")["result"]["event_count"]
    request = uid()
    args = (
        *record_args(run, surface["ref"]),
        "--complete-surface",
        "Inspected request and traced its premise",
    )
    result = call(*args, request=request)
    assert call("audit", "verify")["result"]["event_count"] == before + 1
    assert call(*args, request=request)["replayed"]
    state = call("resume")["result"]
    activity = state["research_activities"][0]
    report = next(
        a for a in state["research_reports"] if a["artifact_id"] == activity["result_artifact_id"]
    )
    assert "Owner decision is unresolved" in (run["root"] / report["storage_path"]).read_text()
    assert activity["research_activity_id"] == result["result"]["id"]
    assert state["claims"] == []
    assert not state["gate"]["can_advance"]
    assert call("surface", "list")["result"][0]["disposition"] == "searched"
    assert (
        call(*args, "--complete-method", "No linked method", expected=2)["error"]["code"]
        == "INVALID_ARGUMENT"
    )


def test_lane_record_completes_linked_work_atomically_and_replays(investigation):  # noqa: F811
    env = investigation
    call = env["call"]
    method = call("method", "list")["result"][0]
    request = uid()
    args = (
        *record_args(env, env["surface"]["ref"]),
        "--method",
        method["ref"],
        "--complete-surface",
        "Source inspected",
        "--complete-method",
        "Contract compared with caller",
    )
    before = call("audit", "verify")["result"]["event_count"]
    first = call(*args, request=request)
    assert call("audit", "verify")["result"]["event_count"] == before + 1
    assert call("method", "list")["result"][0]["disposition"] == "completed"
    surface = next(
        s for s in call("surface", "list")["result"] if s["ref"] == env["surface"]["ref"]
    )
    assert surface["disposition"] == "searched"
    activity = call("research", "list")["result"][0]
    assert activity["research_method_id"] == method["research_method_id"]
    audit = call("audit", "verify")["result"]
    replay = call(*args, request=request)
    assert replay["replayed"] and replay["result"] == first["result"]
    assert call("audit", "verify")["result"] == audit
    assert not call("phase", "check")["result"]["can_advance"]


def test_stale_closure_completion_rolls_back_without_capture(investigation):  # noqa: F811
    env = investigation
    call = env["call"]
    call("lane", "closure-begin", env["lane"]["ref"])
    old = next(m for m in call("method", "list")["result"] if m["method_category"] == "closure")
    call("lane", "closure-begin", env["lane"]["ref"])
    before = call("audit", "verify")["result"]
    args = (
        *record_args(env, env["surface"]["ref"]),
        "--method",
        old["ref"],
        "--complete-surface",
        "Attempted closure",
        "--complete-method",
        "Attempted closure",
    )
    assert call(*args, expected=2)["error"]["code"] == "LANE_CLOSURE_STALE"
    assert call("audit", "verify")["result"] == before
    assert call("research", "list")["result"] == []


def test_completion_is_opt_in_and_phase_one_rejects_method_completion(run):
    call = run["call"]
    surface = call("surface", "list")["result"][0]
    args = record_args(run, surface["ref"])
    call(*args)
    assert call("surface", "list")["result"][0]["disposition"] == "pending"
    before = call("audit", "verify")["result"]
    assert (
        call(*args, "--method", "M-001", "--complete-method", "Wrong phase", expected=2)["error"][
            "code"
        ]
        == "WRONG_PHASE"
    )
    assert call("audit", "verify")["result"] == before
