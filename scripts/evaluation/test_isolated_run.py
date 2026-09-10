import importlib.util
import json
import sys
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "isolated_run", Path(__file__).with_name("isolated_run.py")
)
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)


def test_copy_exclusions_and_symlinks_are_reported(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    (source / "code.py").write_text("source")
    (source / ".discovery").mkdir()
    (source / "tickets").mkdir()
    (source / "escape").symlink_to("/Users")
    omitted = harness.copy_source(source, tmp_path / "output")
    assert set(omitted) == {".discovery", "tickets", "escape"}
    assert [p.name for p in (tmp_path / "output").iterdir()] == ["code.py"]


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS Seatbelt integration")
def test_process_boundary_and_frozen_inputs(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    (work / "source").mkdir()
    (work / "ticket.md").write_text("ticket")
    hidden = tmp_path / "hidden"
    hidden.mkdir()
    sentinel = hidden / "answers.txt"
    sentinel.write_text("private answer")
    policy = harness.profile(
        [Path(p) for p in harness.SYSTEM_READ]
        + [work, Path(sys.executable).resolve().parent.parent],
        [work],
    )
    policy += (
        f"(deny file-write* (subpath {json.dumps(str(work / 'source'))}) "
        f"(literal {json.dumps(str(work / 'ticket.md'))}))"
    )
    sb = tmp_path / "boundary.sb"
    sb.write_text(policy)
    env = {
        "EVAL_PYTHON": str(Path(sys.executable).resolve()),
        "PATH": "/usr/bin:/bin",
        "HOME": str(work),
    }
    assert harness.probe(sb, env, work, [sentinel])["passed"]
    # Local services and app automation are unavailable through the same boundary.
    command = [
        str(Path(sys.executable).resolve()),
        "-c",
        'import socket; s=socket.socket(); s.connect(("127.0.0.1",443))',
    ]
    r = harness.boundary(sb, command, env, work, capture_output=True, text=True)
    assert r.returncode != 0
    assert "Operation not permitted" in r.stderr
    git = harness.boundary(
        sb, ["/usr/bin/git", "--version"], env, work, capture_output=True, text=True
    )
    assert git.returncode == 0, git.stderr


def test_existing_run_is_not_cleaned_up_and_new_failure_cleans_only_owned_auth(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace

    existing = tmp_path / "existing"
    auth = existing / "home/.codex/auth.json"
    auth.parent.mkdir(parents=True)
    auth.write_text("test sentinel, not a credential")
    with pytest.raises(FileExistsError):
        harness.prepare(SimpleNamespace(run_dir=existing))
    assert auth.read_text() == "test sentinel, not a credential"

    fresh = tmp_path / "fresh"

    def fail_after_copy(args, root):
        path = root / "home/.codex/auth.json"
        path.parent.mkdir(parents=True)
        path.write_text("new test sentinel")
        raise RuntimeError("injected preparation failure")

    monkeypatch.setattr(harness, "prepare_created", fail_after_copy)
    with pytest.raises(RuntimeError, match="injected"):
        harness.prepare(SimpleNamespace(run_dir=fresh))
    assert not (fresh / "home/.codex/auth.json").exists()
    assert auth.exists()
