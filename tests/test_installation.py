import json
import subprocess
import sys
import tomllib
from importlib.metadata import version
from pathlib import Path

import pytest

from discovery import __version__


@pytest.mark.parametrize("options", [["--version"], ["--json", "--version"]])
def test_version_without_run_has_json_envelope(options, tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "discovery", *options],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0 and not result.stderr
    assert json.loads(result.stdout) == {
        "ok": True,
        "result": {"version": __version__, "schema_version": 7},
    }
    assert not list(tmp_path.iterdir())


def test_distribution_versions_agree():
    root = Path(__file__).resolve().parents[1]
    project = tomllib.loads((root / "pyproject.toml").read_text())
    plugin = json.loads((root / ".codex-plugin/plugin.json").read_text())
    skill = (root / "skills/discovery/SKILL.md").read_text().split("---", 2)[1]
    skill_version = next(
        line.split(":", 1)[1].strip().strip('"')
        for line in skill.splitlines()
        if line.strip().startswith("version:")
    )
    assert project["project"]["version"] == plugin["version"] == skill_version == __version__
    assert version("discovery-cli") == __version__
