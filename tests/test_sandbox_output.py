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
    )
    assert result["output_limited"] and result["exit_code"] != 0 and not result["timed_out"]
    output = result["stdout" if stream == 1 else "stderr"]
    assert output["truncated"] and output["captured_bytes"] == 2_000_000
    assert not (tmp_path / "stdout.log").exists() and not (tmp_path / "stderr.log").exists()
