# Installing Discovery as an AI Orchestrated Tool

Discovery follows the Taskledger installation workflow described in
`task_ledger/docs/AI_ORCHESTRATED_TOOL_INSTALLATION.md`: a deterministic CLI,
a direct Codex skill, a personal marketplace plugin, and private per-project
runtime state. Leased investigators receive per-run identities and immutable
contexts; installation does not create global worker profiles.

## Installation surfaces

| Surface | Versioned source | Installed location | Responsibility |
| --- | --- | --- | --- |
| CLI | `src/discovery/`, `pyproject.toml` | Active Python or existing uv tool environment | Own state, invariants, transactions, and JSON responses |
| Direct skill | `skills/discovery/` | `${CODEX_HOME:-$HOME/.codex}/skills/discovery/` | Guide the primary model through supported commands |
| Plugin source | `.codex-plugin/`, `skills/` | `$HOME/plugins/discovery/` | Distribute the skill through `discovery@personal` |
| Marketplace entry | Managed by plugin-creator helpers | `$HOME/.agents/plugins/marketplace.json` | Discover and enable the personal plugin |
| Runtime state | Created by an authorized `discovery run init` | `<source>/.discovery/runs/<uuid>/` by convention | One SQLite database and immutable artifacts per run |

The plugin wraps the skill; it does not install the Python CLI. Install and verify
them separately. Copy only the manifest and skills into the plugin source.
Never package run databases, artifacts, credentials, or `.discovery/` as plugin
content. No MCP server, app, or worker-profile manifest is declared.

## Current installation on this machine

Verified on 2026-09-10:

```text
source checkout:
  /Users/christophercaldwell/Code/projects/discovery

active executable:
  /Library/Frameworks/Python.framework/Versions/3.13/bin/discovery

Python package:
  discovery-cli 0.2.0, editable, pointing at the checkout above

direct skill:
  /Users/christophercaldwell/.codex/skills/discovery

personal marketplace:
  /Users/christophercaldwell/.agents/plugins/marketplace.json

personal plugin source:
  /Users/christophercaldwell/plugins/discovery

installed plugin cache:
  /Users/christophercaldwell/.codex/plugins/cache/personal/discovery/0.2.0+codex.20260910173432

plugin identifier:
  discovery@personal (installed and enabled)
```

No worker profiles or consuming-project discovery runs were created by this
installation. The cache suffix changes on subsequent refreshes.

## Version invariant

Keep the base release synchronized:

```text
pyproject.toml                 project.version
src/discovery/__init__.py       __version__
skills/discovery/SKILL.md       metadata.version
.codex-plugin/plugin.json      version
```

The current release is `0.2.0`; its SQLite schema is version `5`. Release version
and schema version are different contracts. Existing schema versions other than
3 are rejected, never reset. A local plugin cache suffix such as
`+codex.20260910162056` changes cache identity, not CLI or database semantics.

`tests/test_installation.py` verifies the base-version invariant and installed
Python metadata, plus side-effect-free JSON version output without a run path.

## 1. Inspect before installing

From the checkout:

```sh
git status --short
python3 --version
command -v discovery || true
which -a discovery || true
python3 -m pip show discovery-cli || true
uv tool list
```

Identify the installation that owns the executable first on PATH. Update that
installation instead of creating a competing one. Repeated identical entries
from `which -a` can reflect repeated PATH directories, not separate installs.

## 2. Install the CLI

For the current editable development installation:

```sh
python3 -m pip install --editable /absolute/path/to/discovery
```

For a regular source installation use `python3 -m pip install --upgrade
/absolute/path/to/discovery`. If uv already owns the active tool, use
`uv tool install --force /absolute/path/to/discovery` instead. Do not run all
three alternatives.

Verify the active executable and its owning interpreter:

```sh
discovery --version
python3 -m discovery --version
python3 -m pip show discovery-cli
```

For this pip-owned installation the two version commands must return:

```json
{"ok":true,"result":{"schema_version":5,"version":"0.2.0"}}
```

For a uv-owned installation, run the module/metadata checks with that tool
environment's interpreter, not an unrelated system Python. `--version` creates
no runtime state and does not require `--run`.

## 3. Validate and synchronize the direct skill

From the source checkout:

```sh
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" skills/discovery
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills/discovery"
rsync -a --delete skills/discovery/ "${CODEX_HOME:-$HOME/.codex}/skills/discovery/"
cmp skills/discovery/SKILL.md "${CODEX_HOME:-$HOME/.codex}/skills/discovery/SKILL.md"
```

The source skill owns this destination. Inspect any existing local modifications
before synchronizing an installation maintained by someone else. `--delete`
removes obsolete distribution files, so keep project-specific customizations in
the consuming repository, not this installed copy.

## 4. Create or refresh the personal plugin

Validate the existing marketplace name before making changes:

```sh
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/plugin-creator/scripts/read_marketplace_name.py"
```

On this machine the result is `personal`. For a first installation only, when
the plugin source/entry do not exist, use the official scaffold helper:

```sh
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/plugin-creator/scripts/create_basic_plugin.py" discovery --with-skills --with-marketplace
```

Then synchronize from the checkout, validate, and refresh:

```sh
rsync -a --delete .codex-plugin/ "$HOME/plugins/discovery/.codex-plugin/"
rsync -a --delete skills/ "$HOME/plugins/discovery/skills/"
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/plugin-creator/scripts/validate_plugin.py" "$HOME/plugins/discovery"
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py" "$HOME/plugins/discovery"
codex plugin add discovery@personal
codex plugin list --marketplace personal --json
```

Use the validated marketplace name if it differs from `personal`. Do not edit
`marketplace.json` or the installed plugin cache by hand. On later updates skip
the first-time scaffold; the cachebuster helper replaces one suffix while the
versioned source manifest retains the base release.

The final plugin list must show `installed: true`, `enabled: true`, and the
expected source directory. Compare the cached skill to the checkout using the
actual cache root returned by `codex plugin add`.

## 5. Prepare a consuming project only when requested

Before initializing an actual discovery run, ensure `.discovery/` is ignored.
Inspect and preserve existing `.gitignore` contents rather than blindly appending
duplicate entries. Then use the [README workflow](../README.md#start-a-run).

Discovery initialization captures a request and a source baseline, and creates
its own private state. It does not change a Git branch or implement source code,
so Taskledger's exact-branch approval mechanism does not apply. Existing user
authorization controls whether to initialize a run. Installation alone is not a
request to begin research in every repository.

The skill asks about subagents for a new run when that preference is missing.
Disabled, partitioned, and overlap modes are implemented. Workers receive
isolated contexts and leased identities; no global worker profiles are installed.

## 6. Verify and hand off

```sh
discovery --version
python3 -m discovery --version
cmp skills/discovery/SKILL.md "${CODEX_HOME:-$HOME/.codex}/skills/discovery/SKILL.md"
codex plugin list --marketplace personal --json
uv run pytest -q
uv run ruff check src tests
uv run ruff format --check src tests
```

The prior Phase 2 installation passed **69 tests**, both skill/plugin validators, and
all executable, package-metadata, direct-copy, and cached-copy checks. The
personal plugin list showed Discovery installed/enabled and retained Taskledger.

Start a new Codex task to pick up the installed skill/plugin snapshot. A suitable
first request is: “Use the Discovery skill and run `discovery --version`; do not
initialize a run.” The installer can verify files and plugin registration in the
current task but cannot prove fresh-task skill selection until that task starts.

During iteration, retain the base release number (currently 0.2.0). Schema revisions
identify actual storage changes and require explicit upgrades. The plugin helper
refreshes cache metadata without incrementing the base release.
