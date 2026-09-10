import os
import subprocess
from pathlib import Path

from discovery.domain.encoding import canonical, digest
from discovery.domain.errors import require


def baseline(root: Path, run_root: Path, excluded: set[str]) -> dict:
    require(root.is_dir(), "INVALID_ARGUMENT", "Source root must be a directory.")
    require(
        root != run_root and not root.is_relative_to(run_root),
        "INVALID_ARGUMENT",
        "Source cannot be inside the run directory.",
    )
    files = []
    for directory, dirs, names in os.walk(root, followlinks=False):
        parent = Path(directory)
        dirs[:] = sorted(d for d in dirs if d not in excluded and parent / d != run_root)
        for name in sorted(names + [d for d in dirs if (parent / d).is_symlink()]):
            path = parent / name
            if name == ".DS_Store":
                continue
            content = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
            files.append([str(path.relative_to(root)), digest(content), path.lstat().st_mode])
    tree = digest(canonical(files).encode())
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    revision = result.stdout.strip() if result.returncode == 0 else "filesystem:" + tree
    return {
        "repository_kind": "git" if result.returncode == 0 else "filesystem",
        "repository_uri": root.as_uri(),
        "repository_root": str(root),
        "baseline_revision": revision,
        "baseline_tree_hash": tree,
    }
