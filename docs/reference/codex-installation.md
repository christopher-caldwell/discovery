# Installing Discovery for Codex

Discovery has two parts: the Python CLI that owns workflow state and the Codex skill
that teaches a model how to operate it. Install and verify both from the same checkout.
The optional plugin is another way to distribute the skill. It does not install the CLI.

## Install the CLI

For development, use the repository environment:

```sh
uv sync
uv run discovery --version
```

To make `discovery` available outside the checkout, install it as a uv tool:

```sh
uv tool install --force /absolute/path/to/discovery
discovery --version
```

Use one installation method. If `discovery` already exists, run `command -v discovery`
and `uv tool list` before replacing it so you know which installation owns the command.

The package release and database schema are separate versions. The current package is
0.2.0 and creates schema 7 runs. Active schema 3 through 6 runs require an explicit
`run upgrade`; finalized schema 5 and 6 runs remain readable.

## Install the Codex skill directly

The versioned skill lives in `skills/discovery/`. Copy it to the personal Codex skill
directory:

```sh
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills/discovery"
rsync -a --delete skills/discovery/ \
  "${CODEX_HOME:-$HOME/.codex}/skills/discovery/"
```

Inspect an existing destination before using `--delete`. Keep project specific changes
outside the installed copy so a refresh does not erase them.

Validate the source and installed copies when the Codex skill validator is available:

```sh
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" \
  skills/discovery
cmp skills/discovery/SKILL.md \
  "${CODEX_HOME:-$HOME/.codex}/skills/discovery/SKILL.md"
```

Start a new Codex task after refreshing the skill. Existing tasks may retain the skill
snapshot they started with.

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
