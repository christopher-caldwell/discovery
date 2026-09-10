import os
import tempfile
from pathlib import Path

from discovery.domain.encoding import digest
from discovery.domain.errors import require


def ensure_directory(path: Path) -> None:
    """Persist newly created directory entries as well as the eventual artifact bytes."""
    if path.is_dir():
        return
    ensure_directory(path.parent)
    path.mkdir(exist_ok=True)
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def capture(root: Path, data: bytes) -> dict:
    sha = digest(data)
    relative = Path("artifacts/sha256") / sha
    path = root / relative
    ensure_directory(path.parent)
    if path.exists():
        require(path.read_bytes() == data, "ARTIFACT_HASH_MISMATCH", "Stored artifact is corrupt.")
    else:
        fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".pending-")
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, path)
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
    return {"artifact_sha256": sha, "byte_size": len(data), "storage_path": str(relative)}
