import json
import sys
from pathlib import Path

import pytest

from discovery.adapters.process.sandbox import execute


@pytest.mark.parametrize("relative", ["scratch", "scratch/experiments", "artifacts/sha256"])
def test_handoff_rejects_redirected_parent_paths(tmp_path, relative):
    from run_experiment import validate_run_paths

    root = tmp_path / "run"
    link = root / relative
    link.parent.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "preserve"
    sentinel.write_text("original")
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlinks"):
        validate_run_paths(root)
    assert list(outside.iterdir()) == [sentinel]
    assert sentinel.read_text() == "original"


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS Seatbelt integration")
def test_external_probe_runs_but_cannot_read_prior_answers_or_write_source(tmp_path):
    box = tmp_path / "probe"
    box.mkdir()
    private = tmp_path / "old-run.sqlite"
    private.write_text("private prior answer")
    source = tmp_path / "original.py"
    source.write_text("unchanged")
    script = """
import json, pathlib, socket, sqlite3, subprocess
private, source = map(pathlib.Path, __import__('sys').argv[1:])
for access in [lambda: private.read_bytes(), lambda: list(private.parent.iterdir()),
               lambda: source.write_text('changed')]:
    try: access()
    except PermissionError: pass
    else: raise AssertionError('boundary escaped')
link = pathlib.Path('escape'); link.symlink_to(private)
try:
    try: link.read_bytes()
    except PermissionError: pass
    else: raise AssertionError('symlink escaped')
finally: link.unlink()
child = subprocess.run(['/bin/cat', str(private)], capture_output=True)
assert child.returncode != 0 and not child.stdout
try: socket.create_connection(('127.0.0.1', 443), timeout=1)
except PermissionError: pass
else: raise AssertionError('network escaped')
c = sqlite3.connect('probe.sqlite'); c.execute('create table t(x)')
c.execute('insert into t values (42)'); c.commit()
assert c.execute('select x from t').fetchone() == (42,)
print(json.dumps({'probe_ran': True, 'private_reads_denied': True}))
"""
    from isolated_run import SYSTEM_READ

    result = execute(
        box,
        ["/usr/bin/python3", "-c", script, str(private), str(source)],
        15,
        read_roots=[Path(p) for p in SYSTEM_READ],
    )
    assert result["exit_code"] == 0, result
    assert json.loads(result["stdout"]["text"])["probe_ran"]
    assert source.read_text() == "unchanged"
    assert "reads restricted" in result["isolation"]
