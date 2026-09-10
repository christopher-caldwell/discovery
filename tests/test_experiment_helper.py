import json
import subprocess
import sys
from pathlib import Path


def test_prepare_script_preserves_bytes_imports_and_refuses_overwrite(tmp_path):
    helper = Path(__file__).parents[1] / "skills/discovery/scripts/prepare_experiment.py"
    probe = tmp_path / "probe.py"
    content = """from pathlib import Path
VALUE = "quotes '\\"; $(not_shell); `literal`"
if __name__ == '__main__':
    import subprocess, sys
    subprocess.run([sys.executable, '-c', 'from probe import VALUE; print(VALUE)'], check=True)
    Path('observed.txt').write_text(VALUE)
"""
    probe.write_text(content)
    command_file = tmp_path / "command.json"
    prepared = subprocess.run(
        [
            sys.executable,
            str(helper),
            "--script",
            str(probe),
            "--output",
            str(command_file),
            "--python",
            sys.executable,
        ],
        capture_output=True,
        text=True,
    )
    assert prepared.returncode == 0, prepared.stderr
    assert not (tmp_path / "observed.txt").exists()
    sandbox = tmp_path / "copy"
    sandbox.mkdir()
    argv = json.loads(command_file.read_text())
    executed = subprocess.run(argv, cwd=sandbox, capture_output=True, text=True)
    assert executed.returncode == 0, executed.stderr
    assert (sandbox / "probe.py").read_text() == content
    assert "$(not_shell); `literal`" in executed.stdout
    (sandbox / "probe.py").write_text("project-owned")
    retry = subprocess.run(argv, cwd=sandbox, capture_output=True, text=True)
    assert retry.returncode != 0 and "FileExistsError" in retry.stderr
    assert (sandbox / "probe.py").read_text() == "project-owned"
