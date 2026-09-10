#!/usr/bin/env python3
"""Prepare JSON argv for a readable Python probe; never execute the probe here."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--python", default="/usr/bin/python3", help="Sandbox interpreter path")
    args = parser.parse_args()
    script = args.script.read_text(encoding="utf-8")
    name = args.script.name
    if args.script.suffix != ".py":
        parser.error("Use a .py script; the copied file keeps its original basename.")
    # Exclusive creation protects files already present in the copied project.
    # Keep cwd unchanged so probes can read the source and child processes can
    # import this same module instead of an independently reimplemented helper.
    loader = (
        "from pathlib import Path\nimport runpy\n"
        f'with Path({name!r}).open("x", encoding="utf-8") as output:\n'
        f"    output.write({script!r})\n"
        f'runpy.run_path({name!r}, run_name="__main__")\n'
    )
    with args.output.open("x", encoding="utf-8") as output:
        json.dump([args.python, "-c", loader], output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(args.output)


if __name__ == "__main__":
    main()
