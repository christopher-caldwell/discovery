# Getting started

The normal interface is your agent chat. Supply the request and the real source
project; the agent owns request capture, CLI calls, record IDs, evidence, and delivery.
The same instructions work with any agent that can read Markdown, execute local
commands, and read/write files.

## Ask the agent to install it

Open this checkout in Cursor, Claude Code, or Codex and say “Install this skill for
me.” The native entry file tells the agent to install the CLI through uv, copy the
shared skill into its own ecosystem, and verify both. See the
[installation procedure](agent-installation.md) for those agent-facing instructions.

Personal installation is the default. Afterward, invoke `$discovery` in Codex or
`/discovery` in Claude Code and Cursor from any project on that host. No custom
installer, marketplace setup, or separate workflow configuration is required.
If the current session has an older skill cached, open a fresh session after install.
The installed skill records the CLI path so it can work even if the app's `PATH`
differs from the installing shell.

## From a Discovery checkout

Open the checkout in Cursor, Claude Code, or Codex. The checked-in entry files route
Discovery requests to [AGENT_GUIDE.md](../../AGENT_GUIDE.md). Ask:

```text
Use Discovery to investigate this request against /absolute/path/to/project:
[paste the request]
Produce the final technical specification without implementing the feature.
```

When working in another project, add the absolute path to this checkout's
`AGENT_GUIDE.md` to that prompt, or attach it. Agent rule files apply to the workspace
where they live; they do not configure unrelated projects globally.

The shared guide tells the agent to use
`uv run --project /absolute/path/to/discovery discovery` when the CLI is not installed.
The `--project` path identifies the Discovery tool checkout. The `--source` path used
when initializing identifies the project being investigated. They need not be the same.
An unqualified `uv run discovery` is appropriate only in the Discovery checkout.

No agent plugin, separate model credentials, provider SDK, MCP server, or external
database is required. Use the agent's existing research tools when external evidence
is needed; unavailable tools remain explicit research limitations.

## Manual CLI installation

Requirements:

- Python 3.11 or newer and SQLite 3.37 or newer with JSON support
- Git on `PATH`
- uv for the installation commands below
- a local filesystem for active runs

From the Discovery checkout, verify the development environment:

```sh
uv sync
uv run discovery --version
uv run discovery guide
```

For use outside the checkout, install the tool:

```sh
uv tool install /absolute/path/to/discovery
discovery --version
discovery guide
```

If your shell cannot find `discovery`, use the explicit checkout command above. Inspect `command -v discovery` and
`uv tool list` before replacing an existing installation. For a refreshed local
installation, use `uv tool install --force /absolute/path/to/discovery` after verifying
the source. Agents may inherit a different `PATH` from your terminal; using the
checkout command avoids relying on it.

The wheel includes the core guide and all named operating references. Read the guide
as plain Markdown with `discovery guide`, or use `discovery --json guide` for a JSON
`result.markdown` field. Use `discovery guide --help` to list reference topics. These
commands work without creating a run or touching a source repository.

## Give the agent the work

With the CLI installed, use this prompt from any project:

```text
Read `discovery guide`, then investigate this request against [project path]:
[paste the request]
Produce the final technical specification. Do not implement the feature.
```

A request file is also accepted, but not required from the user. The agent preserves
chat wording in a file before initialization, with interpretation recorded separately.
It selects `disabled` investigators by default without a setup question. Explicitly
request `partitioned` or `overlap` only when separate sessions are wanted and the
host can launch them. Discovery stores that work but does not launch models itself.

The agent continues through all four phases. Questions concern actual missing intent,
authority, access, or consequential scope choices. Routine internal bookkeeping and
phase transitions do not need human approval beyond the host's permission rules.

## Continue in another agent

Save the run path the agent reports. In a new chat, say:

```text
Read `discovery guide` and resume /absolute/project/.discovery/runs/[run id].
Continue to the final technical specification, preserving existing findings.
```

The agent begins with:

```sh
discovery --json --run /absolute/project/.discovery/runs/[run-id] resume --compact
```

Recovery includes blockers, assumptions, research reports, contrary evidence, current
gates, and next actions. The new investigator uses its own actor/session identity;
the durable run remains the same. Reuse the earlier actor and request only for an
exact uncertain mutation retry, never to impersonate a prior investigator.

If no path is given, the agent inspects candidate runs and selects a clearly matching
one. Ambiguous matches need a focused question, not a new run that loses prior work.
See [Resume and recovery](resume-and-recovery.md) for source drift and interrupted work.

## Files and delivery

By default, the agent keeps requests, reports, and runs under the source's `.discovery/`
directory and ensures it is ignored by Git before capturing the baseline. No tracked
agent configuration needs to be added to the target project. A typical layout is:

```text
project/
  .discovery/
    requests/<uuid>.md
    runs/<uuid>/
  src/
  tests/
```

Keep the run directory. Do not place active SQLite state on a network filesystem or
back up a live WAL database by copying only its main file.

A final result links `technical-spec.md` and the supporting exports. A blocked result
links an interim report and explains exactly what is missing. A stopped chat leaves
unfinished work; the CLI does not schedule a background continuation. Read
[The final technical specification](final-specification.md) for the quality bar.

For manual inspection, command syntax, mutation identity, and machine output, use the
[CLI reference](../reference/cli.md). Optional native entry points and skill packaging
are described in [Agent integration](../reference/agent-integration.md).
