"""Read the shared operator instructions shipped with the installed CLI.

The build bundles AGENT_GUIDE.md and the phase references in this package.
Chat attachments, native agent entry points, and the CLI share those sources.
"""

from importlib.resources import files
from pathlib import Path

TOPICS = (
    "request-vetting",
    "investigation",
    "design-review",
    "evidence-review",
    "confidence",
    "investigators",
)


def read_guide(topic: str | None = None) -> str:
    """Return UTF-8 instructions without opening or creating a Discovery run."""
    if topic is not None and topic not in TOPICS:
        raise ValueError(f"Unknown guide topic: {topic}")
    resource = files("discovery").joinpath("_guide")
    # Editable installs resolve this package to src/, not the wheel's data files.
    # Read the canonical checkout copy there so doc edits are immediately visible.
    checkout = Path(__file__).resolve().parents[2]
    if (
        not resource.joinpath("AGENT_GUIDE.md").is_file()
        and (checkout / "pyproject.toml").is_file()
    ):
        if topic is None:
            return (checkout / "AGENT_GUIDE.md").read_text(encoding="utf-8")
        resource = checkout / "skills" / "discovery"
    if topic is None:
        return resource.joinpath("AGENT_GUIDE.md").read_text(encoding="utf-8")
    return resource.joinpath("references", f"{topic}.md").read_text(encoding="utf-8")
