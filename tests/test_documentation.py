import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIMARY_DOCS = [
    ROOT / "README.md",
    ROOT / "docs/README.md",
    ROOT / "docs/guides/getting-started.md",
    ROOT / "docs/guides/workflow.md",
    ROOT / "docs/guides/questions-and-assumptions.md",
    ROOT / "docs/guides/evidence-and-claims.md",
    ROOT / "docs/guides/experiments.md",
    ROOT / "docs/guides/final-specification.md",
    ROOT / "docs/guides/resume-and-recovery.md",
    ROOT / "docs/guides/investigator-modes.md",
    ROOT / "docs/reference/cli.md",
    ROOT / "docs/reference/agent-integration.md",
    ROOT / "AGENT_GUIDE.md",
]


def test_primary_documentation_has_a_short_entry_point_and_clear_path():
    readme = (ROOT / "README.md").read_text()
    assert len(readme.splitlines()) <= 130
    for path in PRIMARY_DOCS:
        assert path.is_file() and path.read_text().startswith("# ")
    assert "The Markdown specification is the product" in readme
    assert "docs/guides/getting-started.md" in readme
    assert "docs/guides/final-specification.md" in readme


def test_primary_documentation_links_resolve():
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    failures = []
    for path in [
        ROOT / "README.md",
        ROOT / "AGENT_GUIDE.md",
        ROOT / "AGENTS.md",
        ROOT / "CLAUDE.md",
        ROOT / ".cursor/rules/discovery.mdc",
        *sorted((ROOT / "skills").rglob("*.md")),
        *sorted((ROOT / "docs").rglob("*.md")),
    ]:
        for link in link_pattern.findall(path.read_text()):
            if link.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target_text = link.split("#", 1)[0]
            if not target_text:
                continue
            target = (path.parent / target_text).resolve()
            if not target.exists():
                failures.append(f"{path.relative_to(ROOT)} -> {link}")
    assert not failures, "Broken documentation links:\n" + "\n".join(failures)


def test_primary_reader_facing_docs_keep_the_selected_style():
    for path in PRIMARY_DOCS:
        text = path.read_text()
        assert "—" not in text, path.relative_to(ROOT)
        assert sum(line.startswith("# ") for line in text.splitlines()) == 1


def test_documentation_separates_current_authority_from_history():
    index = (ROOT / "docs/README.md").read_text()
    assert "Historical material" in index
    assert "not current operating instructions" in " ".join(index.lower().split())
    assert "reference/implementation-contract.md" in index
    assert "src/discovery/adapters/sqlite/ddl.sql" in index
