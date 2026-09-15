from pathlib import Path

from discovery.adapters.process.sandbox import copy_source


def test_copy_source_materializes_links_inside_disposable_tree(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    target = source / "tool.js"
    target.write_text("original")
    (source / "tool-link").symlink_to("tool.js")

    destination = tmp_path / "scratch" / "source"
    copy_source(source, destination, set(), tmp_path / "run")

    copied_link = destination / "tool-link"
    assert copied_link.read_text() == "original"
    assert not copied_link.is_symlink()

    copied_link.write_text("changed only in disposable tree")
    assert target.read_text() == "original"
