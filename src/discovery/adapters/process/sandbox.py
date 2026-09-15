"""Disposable local executor with optional macOS Seatbelt containment."""

import json
import os
import platform
import selectors
import shutil
import signal
import subprocess
import time
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

    # Materialize link targets in the disposable tree. This keeps ordinary
    # package-manager links (for example node_modules/.bin) usable without
    # leaving a path that can write back through to the original source.
    shutil.copytree(source, destination, symlinks=False, ignore=ignore)
    for path in destination.rglob("*"):
        require(
            not path.is_symlink(),
            "UNSAFE_SANDBOX_LINK",
            "Source copies with symlinks need an explicit safe fixture.",
        )


def execute(
    sandbox: Path,
    argv: list[str],
    timeout: int,
    *,
    read_roots: list[Path] | None = None,
    mode: str = "local",
) -> dict:
    require(mode in ("local", "restricted", "trusted-local"), "INVALID_ARGUMENT", "Unknown mode.")
    system = platform.system()
    require(
        argv and all(isinstance(a, str) and "\x00" not in a for a in argv),
        "INVALID_ARGUMENT",
        "Command must be a nonempty JSON string array.",
    )
    require(1 <= timeout <= 600, "INVALID_ARGUMENT", "Timeout must be 1–600 seconds.")
    sandbox = sandbox.resolve()
    quote = json.dumps
    # Normal CLI probes retain the documented broad-read behavior. An external
    # evaluation runner can narrow reads while retaining the same offline executor.
    profile = None
    command = argv
    if mode == "restricted":
        require(
            system == "Darwin" and shutil.which("sandbox-exec") is not None,
            "SANDBOX_UNAVAILABLE",
            "Restricted mode requires macOS sandbox-exec; no weaker fallback was used.",
        )
        profile = (
            "(version 1)(deny default)(allow process*)(allow sysctl-read)"
            "(allow signal (target children))"
        )
        if read_roots is None:
            profile += "(allow file-read*)(allow mach-lookup)"
        else:
            roots = [*read_roots, sandbox]
            profile += (
                '(allow file-read-data (literal "/")'
                + "".join(" (subpath " + quote(str(p.resolve())) + ")" for p in roots)
                + ")"
            )
        profile += (
            "(allow file-read-metadata)(allow file-write* (subpath " + quote(str(sandbox)) + "))"
        )
        profile += '(allow file-write-data (literal "/dev/null"))'
        command = ["/usr/bin/sandbox-exec", "-p", profile, *argv]
    env = {
        "PATH": os.defpath,
        "HOME": str(sandbox),
        "TMPDIR": str(sandbox),
        "LANG": "en_US.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    before = baseline(sandbox, sandbox / "__no_run__", set())["baseline_tree_hash"]
    start = now()
    limit = 2_000_000
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    truncated = {"stdout": False, "stderr": False}
    p = subprocess.Popen(
        command,
        cwd=sandbox,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    deadline = time.monotonic() + timeout
    timed_out = output_limited = False
    try:
        with selectors.DefaultSelector() as selector:
            for name, stream in (("stdout", p.stdout), ("stderr", p.stderr)):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, name)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    timed_out = True
                    break
                for key, _ in selector.select(min(remaining, 0.1)):
                    chunk = os.read(key.fd, 65_536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    name = key.data
                    available = limit - len(buffers[name])
                    buffers[name].extend(chunk[:available])
                    if len(chunk) > available:
                        truncated[name] = output_limited = True
                        break
                if output_limited:
                    break
            if not timed_out and not output_limited:
                try:
                    p.wait(timeout=max(0, deadline - time.monotonic()))
                except subprocess.TimeoutExpired:
                    timed_out = True
    finally:
        # Clean up the original process group; independently detached sessions
        # are not guaranteed to remain in this group.
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        p.wait()
        p.stdout.close()
        p.stderr.close()

    def output(name):
        return {
            "text": buffers[name].decode("utf-8", errors="replace"),
            "truncated": truncated[name],
            "captured_bytes": len(buffers[name]),
        }

    return {
        "argv": argv,
        "environment": env,
        "started": start,
        "finished": now(),
        "timeout": timeout,
        "exit_code": p.returncode if p.returncode else (125 if output_limited or timed_out else 0),
        "process_exit_code": p.returncode,
        "output_limited": output_limited,
        "output_limit_bytes_per_stream": limit,
        "timed_out": timed_out,
        "stdout": output("stdout"),
        "stderr": output("stderr"),
        "before_tree": before,
        "after_tree": baseline(sandbox, sandbox / "__no_run__", set())["baseline_tree_hash"],
        "execution_mode": mode,
        "platform": {
            "system": system,
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "adapter": "macos-seatbelt" if mode == "restricted" else "local-process",
        "sandbox_profile": profile,
        "enforced_restrictions": (
            ["network denied", "writes limited to disposable copy"] if mode == "restricted" else []
        ),
        "isolation": (
            "macOS Seatbelt; network denied; writes only to disposable copy"
            + ("; reads restricted to declared roots" if read_roots is not None else "")
            if mode == "restricted"
            else "local process in a disposable copy; no OS security boundary"
        ),
        "safety_limitations": (
            ["Filesystem reads may include credentials"]
            if mode == "restricted" and read_roots is None
            else (
                [
                    "No filesystem, network, credential, process, or service isolation is enforced",
                    "Source preservation and copy changes are checked only after execution",
                ]
                if mode in ("local", "trusted-local")
                else []
            )
        ),
    }
