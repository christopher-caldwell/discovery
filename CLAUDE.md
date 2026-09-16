# Discovery entry point for Claude Code

## Install or update the skill

Treat “install this skill”, “install Discovery”, or “update Discovery” as a request
to install it for Claude Code. Follow the
[shared installation procedure](docs/guides/agent-installation.md) yourself, using the current checkout
as the source. It covers uv, the CLI, bundling the skill, and verification. An
installation request does not start a Discovery investigation.

“Update Discovery” refreshes the shared uv tool and this Claude Code skill. If the
user says “update Discovery for every installed host,” also refresh matching Codex
and Cursor skill directories that already exist. Do not create a new host installation
unless the user asks for it. When updating from an installed skill instead of an open
checkout, use the source recorded in its `INSTALLATION.md`.

Install the shared `skills/discovery/` folder at
`~/.claude/skills/discovery/` as a personal skill, available across projects. If
`CLAUDE_CONFIG_DIR` is set, use its `skills/discovery/` directory. Honor an explicit
project installation by using `<project>/.claude/skills/discovery/` instead.
Preserve the shared `name: discovery` and `description` frontmatter; no separate
`.claude/commands/` file is needed.

After verification, tell the user to invoke `/discovery` in a fresh Claude Code
session. This is a direct skill install, so the command is `/discovery`, not a
plugin namespace. Only package a Claude plugin or add a marketplace if the user
specifically asks for that distribution method.

## Run Discovery

When the user asks to run or resume Discovery, read [AGENT_GUIDE.md](AGENT_GUIDE.md)
and follow it through delivery. It contains the shared workflow, defaults, recovery,
and stopping rules. Do not maintain a separate workflow in this entry file.

If the guide is not present locally, run `discovery guide` to read the installed
copy. In a Discovery checkout, use
`uv run --project /absolute/path/to/discovery discovery guide` and keep that command
prefix for subsequent operations. If neither is available, report the missing CLI
or checkout rather than guessing an installation source.

For ordinary work developing or documenting Discovery itself, perform the user's
task normally. These instructions do not request a Discovery run for every edit.
