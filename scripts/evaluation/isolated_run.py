#!/usr/bin/env python3
"""Evaluation-only macOS process isolation. Never resumes an existing Codex session."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
import tomllib
from pathlib import Path

SYSTEM_READ = [
    "/usr",
    "/bin",
    "/sbin",
    "/System",
    "/Library/Frameworks/Python.framework",
    "/Library/Developer/CommandLineTools",
    "/private/etc",
    "/private/var/db/timezone",
    "/dev",
]
DISABLED = [
    "apps",
    "plugins",
    "remote_plugin",
    "browser_use",
    "browser_use_external",
    "computer_use",
    "in_app_browser",
    "in_app_chat",
    "in_app_local_automation",
    "hooks",
    "memories",
    "multi_agent",
    "multi_agent_v2",
    "skill_search",
    "skill_mcp_dependency_install",
    "shell_snapshot",
    "workspace_dependencies",
]
EXCLUDED = {
    ".git",
    ".discovery",
    ".codex",
    ".agents",
    ".venv",
    "node_modules",
    "tickets",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".understand-anything",
}


def profile(read_roots: list[Path], writable: list[Path]) -> str:
    # Metadata access permits stat, not directory enumeration or file contents.
    reads = "".join(f" (subpath {json.dumps(str(p.resolve()))})" for p in read_roots)
    writes = "".join(f" (subpath {json.dumps(str(p.resolve()))})" for p in writable)
    return f"""(version 1)
(deny default)
(allow process-exec process-fork sysctl-read file-read-metadata)
(allow signal (target self))
(allow file-read-data (literal "/"){reads})
(allow file-write*{writes} (subpath "/dev"))
(allow network-outbound (remote tcp "*:443") (remote udp "*:53")
 (literal "/private/var/run/mDNSResponder"))
(deny network-outbound (remote ip "localhost:*"))
(allow mach-lookup
 (global-name "com.apple.system.notification_center")
 (global-name "com.apple.system.logger")
 (global-name "com.apple.system.opendirectoryd.libinfo")
 (global-name "com.apple.networkd")
 (global-name "com.apple.mDNSResponder")
 (global-name "com.apple.SystemConfiguration.configd")
 (global-name "com.apple.trustd.agent"))
"""


def copy_source(source: Path, dest: Path) -> list[str]:
    omissions = []

    # No symlinks: a checked-in link can expose another run, home, or evaluator key.
    def ignore(directory: str, names: list[str]) -> list[str]:
        excluded = [n for n in names if n in EXCLUDED or (Path(directory) / n).is_symlink()]
        omissions.extend(str((Path(directory) / n).relative_to(source)) for n in excluded)
        return excluded

    shutil.copytree(source, dest, ignore=ignore)
    return omissions


def boundary(profile_path: Path, command: list[str], env: dict[str, str], cwd: Path, **kwargs):
    return subprocess.run(
        ["/usr/bin/sandbox-exec", "-f", str(profile_path), *command], env=env, cwd=cwd, **kwargs
    )


def probe(
    profile_path: Path,
    env: dict[str, str],
    work: Path,
    denied: list[Path],
    source: Path | None = None,
    ticket: Path | None = None,
    resume_run: Path | None = None,
) -> dict:
    allowed = work / "allowed-sentinel.txt"
    allowed.write_text("allowed")
    selected = {
        "source": str(source or work / "source"),
        "ticket": str(ticket or work / "ticket.md"),
        "resume_run": str(resume_run) if resume_run else None,
    }
    # Probe direct open, directory listing, descendant shell, symlink, and write.
    script = """import os, pathlib, subprocess, sys, json
p=pathlib.Path(sys.argv[1]); assert p.read_text() == 'allowed'
selected=json.loads(sys.argv[2])
source=pathlib.Path(selected['source']); ticket=pathlib.Path(selected['ticket'])
assert source.is_dir(); list(source.iterdir()); ticket.read_bytes()
if selected['resume_run']:
 run=pathlib.Path(selected['resume_run'])
 (run/'discovery.sqlite').open('rb').close()
 check=run/('isolation-probe-'+str(os.getpid()))
 with check.open('x') as f: f.write('run writable')
 assert check.read_text() == 'run writable'; check.unlink()
results=[]
for q in [source/'isolation-write-probe', ticket]:
 try:
  flags=os.O_WRONLY if q == ticket else os.O_WRONLY|os.O_CREAT|os.O_EXCL
  fd=os.open(q, flags); os.close(fd)
  if q != ticket: q.unlink()
  raise AssertionError('write escaped: '+str(q))
 except PermissionError: pass
for x in sys.argv[3:]:
 q=pathlib.Path(x)
 try: q.read_bytes(); raise AssertionError('read escaped: '+x)
 except PermissionError: pass
 try: list(q.parent.iterdir()); raise AssertionError('listing escaped: '+x)
 except PermissionError: pass
 r=subprocess.run(['/bin/cat',x],capture_output=True)
 assert r.returncode != 0 and not r.stdout, x
 link=p.parent/'escape-link'; link.symlink_to(q)
 try:
  try: link.read_bytes(); raise AssertionError('symlink escaped: '+x)
  except PermissionError: pass
 finally: link.unlink()
 results.append({'path':x,'read_denied':True,'listing_denied':True,'child_denied':True,'symlink_denied':True})
print(json.dumps(results))
"""
    r = boundary(
        profile_path,
        [env["EVAL_PYTHON"], "-c", script, str(allowed), json.dumps(selected), *map(str, denied)],
        env,
        work,
        capture_output=True,
        text=True,
    )
    if r.returncode:
        raise RuntimeError(f"Isolation probe failed: {r.stderr or r.stdout}")
    return {"passed": True, "checks": json.loads(r.stdout)}


def prepare(args) -> tuple[Path, dict]:
    root = args.run_dir.resolve()
    root.mkdir(parents=True, exist_ok=False)
    try:
        return prepare_created(args, root)
    except BaseException:
        (root / "home/.codex/auth.json").unlink(missing_ok=True)
        raise


def recovery_inputs(args) -> tuple[Path, Path, Path]:
    run, source, ticket = args.resume_run.resolve(), args.source.resolve(), args.ticket.resolve()
    if not source.is_dir() or not ticket.is_file():
        raise ValueError("Recovery needs existing source and ticket")
    # Broad/overlapping grants could reveal old chats or make frozen source writable.
    if any(
        a.is_relative_to(b) or b.is_relative_to(a)
        for a, b in ((run, source), (run, ticket), (source, ticket))
    ):
        raise ValueError("Recovery run, source, and ticket must be separate paths")
    with sqlite3.connect(f"{(run / 'discovery.sqlite').as_uri()}?mode=ro", uri=True) as db:
        roots = {
            Path(row[0]).resolve()
            for row in db.execute(
                "SELECT repository_root FROM source_repository WHERE repository_root IS NOT NULL"
            )
        }
        if roots != {source}:
            raise ValueError("--source must match the selected ledger's sole recorded source")
        original_hashes = {
            row[0]
            for row in db.execute(
                "SELECT a.artifact_sha256 FROM discovery_run r "
                "JOIN artifact a ON a.artifact_id = r.input_artifact_id"
            )
        }
        if original_hashes != {hashlib.sha256(ticket.read_bytes()).hexdigest()}:
            raise ValueError("--ticket must match the ledger's immutable input")
    if any(p.is_symlink() for p in source.rglob("*")):
        raise ValueError("Recovery source contains symlinks; refuse an ambiguous read grant")
    return run, source, ticket


def selected_integrity(source: Path, ticket: Path) -> dict:
    return {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [ticket, *sorted(source.rglob("*"))]
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    }


def audit_snapshot(sb: Path, env: dict, work: Path, run: Path, output: Path) -> None:
    result = boundary(
        sb,
        ["discovery", "--json", "--run", str(run), "audit", "verify"],
        env,
        work,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output.write_text(
        json.dumps(
            {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr},
            indent=2,
        )
    )


def prepare_created(args, root: Path) -> tuple[Path, dict]:
    work, home, control = root / "work", root / "home", root / "control"
    for p in (work, home, control, home / ".codex", home / "tmp"):
        p.mkdir(exist_ok=True)
    resume_run = None
    if getattr(args, "resume_run", None):
        resume_run, source, ticket = recovery_inputs(args)
        if any(
            root.is_relative_to(p) or p.is_relative_to(root) for p in (resume_run, source, ticket)
        ):
            raise ValueError(
                "Fresh session directory must be separate from selected durable inputs"
            )
        omissions = []
    else:
        source, ticket = work / "source", work / "ticket.md"
        omissions = copy_source(args.source.resolve(), source)
        shutil.copyfile(args.ticket, ticket)
    shutil.copyfile(args.prompt, work / "request.txt")
    repo = Path(__file__).resolve().parents[2]
    package = root / "package"
    package.mkdir()
    shutil.copytree(repo / "src", package / "src", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copyfile(repo / "pyproject.toml", package / "pyproject.toml")
    venv = root / "runtime"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, capture_output=True)
    subprocess.run(
        [
            shutil.which("uv") or "uv",
            "pip",
            "install",
            "--python",
            str(venv / "bin/python"),
            "--no-deps",
            str(package),
        ],
        check=True,
        capture_output=True,
    )
    shutil.rmtree(package)
    shutil.copytree(repo / "skills/discovery", home / ".codex/skills/discovery")
    # Export public trust certificates only; never expose login keychains.
    certificates = b""
    for keychain in (
        "/System/Library/Keychains/SystemRootCertificates.keychain",
        "/Library/Keychains/System.keychain",
    ):
        certs = subprocess.run(
            ["/usr/bin/security", "find-certificate", "-a", "-p", keychain],
            capture_output=True,
            check=True,
        )
        certificates += certs.stdout
    (home / "trust.pem").write_bytes(certificates)
    original_home = Path.home() / ".codex"
    config = tomllib.loads((original_home / "config.toml").read_text())
    # Preserve configured operator default; never choose or override a model.
    safe_config = {
        k: config[k]
        for k in ("model", "model_provider", "model_reasoning_effort", "service_tier")
        if k in config
    }
    if safe_config.get("model_provider", "openai") != "openai":
        raise RuntimeError("Custom providers require a separately reviewed transport configuration")
    lines = [f"{k} = {json.dumps(v)}" for k, v in safe_config.items()]
    lines += [
        'web_search = "live"',
        'cli_auth_credentials_store = "file"',
        "[features]",
        *[f"{k} = false" for k in DISABLED],
    ]
    (home / ".codex/config.toml").write_text("\n".join(lines) + "\n")
    auth = original_home / "auth.json"
    if not auth.is_file():
        raise RuntimeError("File-backed Codex authentication required; keychain access is denied")
    shutil.copyfile(auth, home / ".codex/auth.json")
    (home / ".codex/auth.json").chmod(0o600)
    codex = Path(shutil.which("codex") or "codex").resolve()
    python = (venv / "bin/python").resolve()
    env = {
        "HOME": str(home),
        "CODEX_HOME": str(home / ".codex"),
        "TMPDIR": str(home / "tmp"),
        "PATH": f"{venv}/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "LANG": "en_US.UTF-8",
        "SSL_CERT_FILE": str(home / "trust.pem"),
        "EVAL_PYTHON": str(venv / "bin/python"),
    }
    read = [Path(p) for p in SYSTEM_READ] + [work, home, venv, codex.parent, python.parent.parent]
    writable = [work, home]
    if resume_run:
        read.extend([resume_run, source, ticket])
        writable.append(resume_run)
    sb = control / "boundary.sb"
    sb.write_text(
        profile(read, writable)
        + f"\n(deny file-write* (subpath {json.dumps(str(source))}) "
        + f"(subpath {json.dumps(str(home / '.codex/skills'))}) "
        + f"(literal {json.dumps(str(ticket))}))\n"
    )
    sentinels = []
    for name in ("evaluator-key", "sibling-run", "old-discovery", "codex-history"):
        p = control / name / "sentinel.txt"
        p.parent.mkdir()
        p.write_text(os.urandom(32).hex())
        sentinels.append(p)
    # Real private roots are probed as well; temporary sentinels are never answers.
    sentinels += args.deny_probe
    if resume_run:
        # A known old prompt always exists in campaign sessions; other old answers
        # and reports are denied even if they were not written by that operator.
        old_work = resume_run.parent
        candidates = [old_work / name for name in ("request.txt", "outcome.md", "answer.md")]
        candidates.append(old_work.parent / "control/events.jsonl")
        sentinels.extend(p for p in candidates if p.is_file())
        if not any(p.is_file() for p in candidates):
            raise ValueError("Recovery requires an existing old-chat/report denial probe")
    result = probe(sb, env, work, sentinels, source, ticket, resume_run)
    if resume_run:
        audit_snapshot(sb, env, work, resume_run, control / "audit-before.json")
    (control / "isolation-check.json").write_text(json.dumps(result, indent=2))
    smoke = boundary(
        sb,
        [str(codex), "exec", "--strict-config", "--help"],
        env,
        work,
        capture_output=True,
        text=True,
    )
    if smoke.returncode:
        raise RuntimeError(f"Codex startup probe failed: {smoke.stderr}")
    command = [
        str(codex),
        "exec",
        "--strict-config",
        "--ignore-rules",
        "--ephemeral",
        "--dangerously-bypass-approvals-and-sandbox",
        "--skip-git-repo-check",
        "--json",
        "-C",
        str(work),
        "-o",
        str(work / "answer.md"),
        "-",
    ]
    manifest = {
        "command": command,
        "env": env,
        "profile": str(sb),
        "work": str(work),
        "omissions": omissions,
        "integrity_before": integrity(root),
        "configured_defaults": safe_config,
        "timeout_seconds": args.timeout,
        "source": str(args.source.resolve()),
        "isolation": result,
        "limitations": [
            "File metadata stat is allowed, contents and directory listings are allowlisted.",
            "HTTPS is allowed for model and public research; localhost and app IPC are denied.",
            "Run-local Codex auth is readable inside the process and removed after execution.",
        ],
    }
    if resume_run:
        manifest.update(
            {
                "resume_run": str(resume_run),
                "selected_source": str(source),
                "selected_ticket": str(ticket),
                "selected_integrity_before": selected_integrity(source, ticket),
            }
        )
    (control / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return root, manifest


def integrity(root: Path) -> dict:
    result = {}
    for relative in (
        "work/source",
        "work/ticket.md",
        "work/request.txt",
        "home/.codex/skills",
        "runtime/lib",
    ):
        path = root / relative
        files = [path] if path.is_file() else sorted(path.rglob("*"))
        result[relative] = {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
        }
    return result


def execute(root: Path, manifest: dict) -> None:
    control, work = root / "control", Path(manifest["work"])
    start = time.monotonic()
    timed_out = False
    try:
        with (control / "events.jsonl").open("w") as out, (control / "stderr.log").open("w") as err:
            process = subprocess.Popen(
                ["/usr/bin/sandbox-exec", "-f", manifest["profile"], *manifest["command"]],
                cwd=work,
                env=manifest["env"],
                stdin=subprocess.PIPE,
                stdout=out,
                stderr=err,
                start_new_session=True,
            )
            try:
                process.communicate(
                    (work / "request.txt").read_bytes(), timeout=manifest["timeout_seconds"]
                )
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
        usage = []
        for line in (control / "events.jsonl").read_text().splitlines():
            try:
                event = json.loads(line)
                if "usage" in event:
                    usage.append(event["usage"])
            except json.JSONDecodeError:
                pass
        result = {
            "exit_code": process.returncode,
            "timed_out": timed_out,
            "elapsed_seconds": time.monotonic() - start,
            "usage_events": usage,
            "integrity_after": integrity(root),
        }
        if manifest.get("resume_run"):
            result["selected_integrity_after"] = selected_integrity(
                Path(manifest["selected_source"]), Path(manifest["selected_ticket"])
            )
            audit_snapshot(
                Path(manifest["profile"]),
                manifest["env"],
                work,
                Path(manifest["resume_run"]),
                control / "audit-after.json",
            )
        (control / "result.json").write_text(json.dumps(result, indent=2))
        print(
            json.dumps(
                {
                    k: v
                    for k, v in result.items()
                    if k not in ("integrity_after", "selected_integrity_after")
                }
            )
        )
    finally:
        (root / "home/.codex/auth.json").unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Sanitized source tree only; no previous answers or evaluator keys",
    )
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--ticket", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True, help="Must not already exist")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--deny-probe", type=Path, action="append", default=[])
    parser.add_argument(
        "--resume-run",
        type=Path,
        help="Continue only this durable Discovery ledger in a fresh model session",
    )
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    root, manifest = prepare(args)
    if args.prepare_only:
        # Auth must not linger in prepared runs. Execute requires fresh preparation.
        (root / "home/.codex/auth.json").unlink(missing_ok=True)
        print(json.dumps({"prepared": str(root), "isolation_passed": True}))
    else:
        execute(root, manifest)


if __name__ == "__main__":
    main()
