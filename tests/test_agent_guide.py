"""Agent bootstrap must work without a run or a particular agent installation."""

import json
from pathlib import Path

import pytest

from discovery.cli import main
from discovery.guide import TOPICS, read_guide

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("topic", [None, *TOPICS])
@pytest.mark.parametrize("machine", [False, True])
def test_guide_from_unrelated_directory_matches_canonical_source(
    topic, machine, tmp_path, capsys, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    argv = ["guide"]
    if topic:
        argv += ["--topic", topic]
    if machine:
        argv += ["--json"]
    assert main(argv) == 0
    captured = capsys.readouterr()
    assert not captured.err
    markdown = json.loads(captured.out)["result"]["markdown"] if machine else captured.out
    source = (
        ROOT / "AGENT_GUIDE.md"
        if topic is None
        else (ROOT / "skills/discovery/references" / f"{topic}.md")
    )
    assert markdown == source.read_text(encoding="utf-8")
    assert not list(tmp_path.iterdir())


def test_guide_does_not_open_supplied_run(tmp_path, capsys):
    run_path = tmp_path / "absent"
    assert main(["--run", str(run_path), "guide"]) == 0
    assert capsys.readouterr().out == read_guide()
    assert not run_path.exists()


def test_invalid_topic_returns_argument_error_without_creating_state(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["--json", "guide", "--topic", "../../secrets"]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["error"]["code"] == "INVALID_ARGUMENT"
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("argv", [["status"], ["resume", "--compact"], ["question", "list"]])
def test_state_commands_still_require_run(argv, capsys):
    assert main(["--json", *argv]) == 2
    assert json.loads(capsys.readouterr().out)["error"]["code"] == "INVALID_ARGUMENT"


def test_command_help_does_not_require_run(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["run", "init", "--help"])
    assert exit_info.value.code == 0
    assert "--source" in capsys.readouterr().out


def test_omitted_mode_replays_explicit_disabled_initialization(run):
    # Initialization is durable; a default must not create a different retry identity.
    args = list(run["init_args"])
    index = args.index("--subagents")
    del args[index : index + 2]
    result = run["call"](*args, request=run["initial_request"])
    assert result["replayed"] is True
    assert result["result"] == run["initial"]["result"]


def test_new_investigator_can_resume_existing_run_without_reinitializing(run):
    from discovery.domain.encoding import uid

    original = run["call"]("resume", "--compact")["result"]
    resumed = run["call"]("resume", "--compact", identity=uid())["result"]
    assert resumed == original
    assert run["call"]("audit", "verify")["result"]["valid"]
