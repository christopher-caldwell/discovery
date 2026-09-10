import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from discovery.domain.errors import DiscoveryError


def canonical(value: object) -> str:
    """Versioned Python JSON encoding, not a claim of full RFC 8785 compliance."""
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def uid() -> str:
    return str(uuid4())


def uuid(value: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise DiscoveryError("INVALID_ARGUMENT", "Expected a UUID.") from exc


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
