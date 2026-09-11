#!/usr/bin/env python3
"""Summarize retained model events without interpreting investigation quality."""

import argparse
import json
from pathlib import Path


def summarize(root: Path) -> dict:
    control = root / "control"
    manifest = json.loads((control / "manifest.json").read_text())
    result_path = control / "result.json"
    result = json.loads(result_path.read_text()) if result_path.exists() else {}
    events = []
    incomplete_lines = 0
    for line in (control / "events.jsonl").read_text().splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            incomplete_lines += 1
    commands = [
        e["item"]
        for e in events
        if e.get("type") == "item.completed"
        and e.get("item", {}).get("type") == "command_execution"
    ]
    envelopes = []
    for command in commands:
        for line in command.get("aggregated_output", "").splitlines():
            try:
                value = json.loads(line)
            except ValueError:
                continue
            if (
                isinstance(value, dict)
                and "ok" in value
                and ("result" in value or "error" in value)
            ):
                envelopes.append(value)
    return {
        "run": root.name,
        "completed": bool(result),
        "elapsed_seconds": result.get("elapsed_seconds"),
        "exit_code": result.get("exit_code"),
        "timed_out": result.get("timed_out"),
        "model": manifest["configured_defaults"],
        "usage_events": result.get("usage_events", []),
        "timing": result.get("timing"),
        "shell_commands": len(commands),
        "nonzero_shell_commands": sum(bool(c.get("exit_code")) for c in commands),
        "observed_json_envelopes": len(envelopes),
        "cli_errors": [v["error"] for v in envelopes if not v["ok"]],
        "captured_shell_output_bytes": sum(
            len(c.get("aggregated_output", "").encode()) for c in commands
        ),
        "incomplete_event_lines": incomplete_lines,
        "isolation_passed": manifest["isolation"]["passed"],
        "frozen_inputs_unchanged": (
            manifest["integrity_before"] == result["integrity_after"]
            if "integrity_after" in result
            else None
        ),
        "outcome_exists": (root / "work/outcome.md").exists(),
        "final_message_exists": (root / "work/answer.md").exists(),
        "limitations": [
            "Shell commands may contain multiple CLI calls or helper scripts.",
            "JSON envelopes omit text help/version calls and may include printed prior results; "
            "they are observations, not an exact CLI invocation count.",
            "Captured tool output can be truncated by the model runtime.",
            "Missing usage at timeout is unavailable, not zero tokens.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summaries = [
        summarize(p.parent)
        for p in sorted(args.runs.glob("*/control"))
        if (p / "events.jsonl").exists()
    ]
    args.output.write_text(json.dumps(summaries, indent=2) + "\n")
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
