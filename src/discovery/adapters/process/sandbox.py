"""Offline macOS Seatbelt executor. No unsandboxed fallback."""

import json
import os
import shutil
import signal
import subprocess
from pathlib import Path

from discovery.adapters.git.repository import baseline
from discovery.domain.encoding import now
from discovery.domain.errors import require


def copy_source(source: Path, destination: Path, excluded: set[str], run: Path) -> None:
    require(
        not destination.exists(),
        "SANDBOX_EXISTS",
        "Inspect existing sandbox; it is never overwritten.",
    )
    destination.parent.mkdir(parents=True, exist_ok=True)

    def ignore(directory, names):
        return [
            n
            for n in names
            if n in excluded or n == ".DS_Store" or (Path(directory) / n).resolve() == run
        ]

    shutil.copytree(source, destination, symlinks=True, ignore=ignore)
    for path in destination.rglob("*"):
        require(
            not path.is_symlink(),
            "UNSAFE_SANDBOX_LINK",
            "Source copies with symlinks need an explicit safe fixture.",
        )


def execute(sandbox: Path, argv: list[str], timeout: int) -> dict:
    require(
        shutil.which("sandbox-exec") is not None,
        "SANDBOX_UNAVAILABLE",
        "macOS sandbox-exec required; no unsandboxed fallback.",
    )
    require(
        argv and all(isinstance(a, str) and "\x00" not in a for a in argv),
        "INVALID_ARGUMENT",
        "Command must be a nonempty JSON string array.",
    )
    require(1 <= timeout <= 600, "INVALID_ARGUMENT", "Timeout must be 1–600 seconds.")
    sandbox = sandbox.resolve()
    quote = json.dumps
    # The original tree may be read, but all writes are confined to the copy.
    # OS runtimes require broad read access; this is not credential-read isolation.
    profile = (
        "(version 1)(deny default)(allow process*)(allow sysctl-read)"
        "(allow mach-lookup)(allow file-read*)"
    )
    profile += "(allow file-read-metadata)(allow file-write* (subpath " + quote(str(sandbox)) + "))"
    profile += '(allow file-write-data (literal "/dev/null"))'
    env = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
        "HOME": str(sandbox),
        "TMPDIR": str(sandbox),
        "LANG": "en_US.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    before = baseline(sandbox, sandbox / "__no_run__", set())["baseline_tree_hash"]
    start = now()
    with (
        (sandbox / "stdout.log").open("wb") as stdout,
        (sandbox / "stderr.log").open("wb") as stderr,
    ):
        p = subprocess.Popen(
            ["/usr/bin/sandbox-exec", "-p", profile, *argv],
            cwd=sandbox,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )
        timed_out = False
        try:
            p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            # Kill descendant processes even if the direct child exited successfully.
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            p.wait()

    def read_log(name):
        path = sandbox / name
        with path.open("rb") as f:
            content = f.read(2_000_000)
        return {
            "text": content.decode("utf-8", errors="replace"),
            "truncated": path.stat().st_size > len(content),
        }

    return {
        "argv": argv,
        "environment": env,
        "started": start,
        "finished": now(),
        "timeout": timeout,
        "exit_code": p.returncode,
        "timed_out": timed_out,
        "stdout": read_log("stdout.log"),
        "stderr": read_log("stderr.log"),
        "before_tree": before,
        "after_tree": baseline(sandbox, sandbox / "__no_run__", set())["baseline_tree_hash"],
        "isolation": "macOS Seatbelt; network denied; writes only to disposable copy",
    }
