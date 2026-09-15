# Installing Discovery for Codex

For the ordinary personal skill, open this checkout in Codex and say “Install this
skill for me.” [AGENTS.md](../../AGENTS.md) selects the native destination and follows
the [shared installation procedure](../guides/agent-installation.md). After installing,
invoke `$discovery` in a fresh task. The remaining sections cover manual CLI and
optional plugin administration.

This is an optional compatibility path for users who prefer installed Codex skills
or a personal plugin. The normal [agent workflow](../guides/getting-started.md)
requires only the CLI and its shared guide. No per-agent installation is required.

The repository's [AGENTS.md](../../AGENTS.md) entry point already routes Discovery
requests to [AGENT_GUIDE.md](../../AGENT_GUIDE.md). The optional skill is another
loader for that same core via `discovery guide`; it owns no separate workflow.
The plugin distributes the skill and does not install the CLI.

## Install the CLI

For development, use the repository environment:

```sh
uv sync
uv run discovery --version
uv run discovery guide
```

To make `discovery` available outside the checkout, install it as a uv tool:

```sh
uv tool install --force /absolute/path/to/discovery
discovery --version
discovery guide
```

Use one installation method. If `discovery` already exists, run `command -v discovery`
and `uv tool list` before replacing it so you know which installation owns the command.

The package release and database schema are separate versions. The current package is
0.2.0 and creates schema 7 runs. Active schema 3 through 6 runs require an explicit
`run upgrade`; finalized schema 5 and 6 runs remain readable.

## Direct skill installation

Use the procedure linked above. It installs the CLI and copies `skills/discovery/`
to the selected personal skill directory, refreshing an existing direct copy when
present. It preserves the previous files outside skill search paths and records the
resolved CLI path in the installed `INSTALLATION.md`. Avoid creating a second copy
in a legacy directory if Codex already discovers Discovery elsewhere.

The source skill can be validated with the Codex skill validator when available:

```sh
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" \
  skills/discovery
```

## Install the optional personal plugin

The repository includes `.codex-plugin/plugin.json` and the source skill. If you use a
personal Codex plugin marketplace, synchronize only those distribution files into the
plugin source, validate it, refresh its cache identity, and reinstall it through the
Codex plugin tooling.

Do not package `.discovery/`, run databases, artifacts, credentials, test caches, or
build output in the plugin. The plugin should contain the manifest and skills only.

The exact personal marketplace path and helper commands depend on the installed Codex
version. Use the current plugin creation documentation rather than copying host specific
paths from an old installation log.

## Verify version alignment

Keep the base package version synchronized across:

```text
pyproject.toml                    project.version
src/discovery/__init__.py        __version__
skills/discovery/SKILL.md        metadata.version
.codex-plugin/plugin.json        version
```

Run the repository checks after installation changes:

```sh
uv run discovery --version
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv build
```

## Keep run data private

Before starting Discovery in a target repository, make sure `.discovery/` is ignored.
A run can contain copied request text, source evidence, experiment output, and a SQLite
database. It belongs to the operator, not in the target package or plugin.

Installing Discovery does not authorize a run, create investigator identities, or alter
the target repository. Initialization happens only when an operator supplies a request,
source path, and run directory.
