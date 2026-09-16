---
name: discovery
description: Operate the local Discovery CLI to clarify a request, persist research plans and search provenance, inspect phase gates, or resume a Discovery run. Use when the user asks for Discovery or a durable pre-implementation discovery workflow; ordinary web research does not require it.
metadata:
  version: "0.2.0"
---

# Discovery

This is the optional skill entry point. The complete, agent-neutral workflow lives
in [AGENT_GUIDE.md](../../AGENT_GUIDE.md), not in a provider-specific skill.

When the user asks to install or update Discovery, do not start an investigation.
Read [references/update.md](references/update.md) and follow it using the scope the
user requested.

When asked to run or resume Discovery, resolve the CLI, execute its `guide` command,
and follow the returned instructions through delivery:

1. If this installed skill has an `INSTALLATION.md` note, read it and use the recorded
   absolute Discovery executable. It points to the CLI installed through uv and avoids
   depending on the current application's `PATH`.
2. Otherwise try `discovery` on `PATH`. If it is absent, use `uv tool dir --bin` to
   locate an existing uv-managed `discovery` executable (`discovery.exe` on Windows).
3. In a source checkout, you can use
   `uv run --project /absolute/path/to/discovery discovery` instead.

Verify the selected executable with `--version` and `guide`; retain that resolved
executable or command prefix for all subsequent operations. If a recorded path is
stale, try the other existing locations before reporting the missing installation.
The CLI bundles the core guide and phase-specific references, so an installed skill
does not need the checkout. Installation metadata supplies paths, not workflow rules.

If neither CLI nor checkout is available, report the missing prerequisite. Do not
create substitute SQL or invent an installation URL. Read `discovery --version`
and use the guide from that installation rather than a stale cached skill.

For ordinary work developing Discovery itself, follow the user's task without
starting a Discovery run.
