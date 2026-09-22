import sys

import pytest

from discovery.adapters.process.sandbox import execute

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="macOS Seatbelt adapter")


def test_capture_preserves_project_log_files(tmp_path):
    for name in ("stdout.log", "stderr.log"):
        (tmp_path / name).write_text("project-owned content")
    result = execute(
        tmp_path,
        ["/usr/bin/python3", "-c", 'import sys; print("out"); print("err",file=sys.stderr)'],
        10,
        mode="restricted",
    )
    assert result["exit_code"] == 0
    assert result["stdout"]["text"] == "out\n" and result["stderr"]["text"].endswith("err\n")
    assert result["before_tree"] == result["after_tree"]
    for name in ("stdout.log", "stderr.log"):
        assert (tmp_path / name).read_text() == "project-owned content"


@pytest.mark.parametrize("stream", [1, 2])
def test_output_limit_stops_noisy_process_without_log_files(tmp_path, stream):
    result = execute(
        tmp_path,
        ["/usr/bin/python3", "-c", f'import os\nwhile True: os.write({stream},b"x"*65536)'],
        10,
        mode="restricted",
    )
    assert result["output_limited"] and result["exit_code"] != 0 and not result["timed_out"]
    output = result["stdout" if stream == 1 else "stderr"]
    assert output["truncated"] and output["captured_bytes"] == 2_000_000
    assert not (tmp_path / "stdout.log").exists() and not (tmp_path / "stderr.log").exists()


def test_sandbox_can_terminate_own_child(tmp_path):
    code = """import subprocess, signal
child = subprocess.Popen(['/usr/bin/python3', '-c', 'import time; time.sleep(20)'])
child.terminate()
assert child.wait(timeout=3) == -signal.SIGTERM
print('child terminated')
"""
    result = execute(tmp_path, ["/usr/bin/python3", "-c", code], 8, mode="restricted")
    assert result["exit_code"] == 0, result["stderr"]
    assert "child terminated" in result["stdout"]["text"]
    assert not result["timed_out"]


def test_sandbox_cannot_signal_unrelated_owned_process(tmp_path):
    import subprocess

    unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"])
    try:
        code = f"""import os, signal
try:
    os.kill({unrelated.pid}, signal.SIGTERM)
except PermissionError:
    print('unrelated signal denied')
else:
    raise AssertionError('sandbox signalled unrelated process')
"""
        result = execute(tmp_path, ["/usr/bin/python3", "-c", code], 8, mode="restricted")
        assert result["exit_code"] == 0, result["stderr"]
        assert "unrelated signal denied" in result["stdout"]["text"]
        assert unrelated.poll() is None
    finally:
        unrelated.kill()
        unrelated.wait(timeout=5)
