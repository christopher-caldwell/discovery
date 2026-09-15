# Discovery entry point for Codex

## Install or update the skill

Treat “install this skill”, “install Discovery”, or “update Discovery” as a request
to install it for Codex. Follow the
[shared installation procedure](docs/guides/agent-installation.md) yourself, using the current checkout
as the source. It covers uv, the CLI, bundling the skill, and verification. An
installation request does not start a Discovery investigation.

Install the shared `skills/discovery/` folder as the personal `discovery` skill.
Default to `~/.agents/skills/discovery/`, which makes `$discovery` available across
projects. If this Codex installation already loads a direct Discovery skill from
`${CODEX_HOME:-$HOME/.codex}/skills/discovery/`, refresh that existing location
instead of creating a duplicate. Honor a user-requested project or custom location.
Keep `agents/openai.yaml` with the skill for Codex display metadata.

After verification, tell the user to invoke `$discovery` in a new task. If it has not
appeared, reload/restart Codex. Do not claim the current task has refreshed its cached
skill unless you can observe that. Use the native skill/plugin UI to identify any
older plugin copy; never edit plugin cache files to perform a direct skill install.

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
