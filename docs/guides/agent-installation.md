# Install Discovery from an agent chat

Open the Discovery checkout in your agent and say:

```text
Install this skill for me.
```

To refresh the CLI and the current host's skill later, say:

```text
Update Discovery from this checkout.
```

To refresh every host where Discovery is already installed on the same machine, say:

```text
Update Discovery from this checkout for every installed host.
```

The native entry file selects the destination and invocation syntax for that agent.
The agent carries out the procedure below. This is a local skill installation with
a shared uv-managed CLI; there is no custom installer or marketplace requirement.

## Instructions for the installing agent

### 1. Resolve the source and prerequisites

Use the Discovery checkout the user opened or explicitly supplied. For an update
requested from an installed skill, use the source path in its `INSTALLATION.md` when
that checkout still exists. Resolve its
absolute path and confirm `pyproject.toml` identifies `discovery-cli`, and that
`AGENT_GUIDE.md` and `skills/discovery/SKILL.md` exist. Do not infer a package source
from the bare name `discovery` on a registry. If working from a link without a local
checkout, obtain that specific user-supplied repository first.

Use the host's normal file and shell tools. Run `uv --version` and check Git is
available. If uv is absent, install it using the
[official uv instructions](https://docs.astral.sh/uv/getting-started/installation/)
for the host platform within its permission rules. Locate the resulting executable
and use its absolute path if the running app has not inherited the new command path.
Let uv obtain a supported Python when needed; do not modify the project's environment
to install a global CLI. Report a concrete missing prerequisite only if you cannot
resolve it with the access available.

### 2. Install the CLI through uv

Inspect `uv tool list` and any existing `discovery` executable before replacement.
Install from this checkout, using its actual absolute path:

```sh
uv tool install /absolute/path/to/discovery
uv tool dir --bin
```

This installs a persistent, isolated CLI environment. It includes the generic guide
and detailed references, so the installation does not depend on keeping the checkout.
Do not use `--editable` for the normal personal installation.

For an existing installation of this project's `discovery-cli`, refresh it from the
requested checkout even if the version string is unchanged:

```sh
uv tool install --force --reinstall /absolute/path/to/discovery
```

Use `--force` only after identifying the existing executable as this Discovery tool.
If the name belongs to a different program, explain the collision rather than replacing
it. The same uv tool installation serves all three agents on the same host; do not
create a different Python environment per agent. Install on the machine where the
agent actually executes commands, which can differ from the UI machine in remote use.

Resolve `discovery` inside the directory returned by `uv tool dir --bin` (on Windows,
use `discovery.exe`). Invoke that absolute executable for verification. A successful
install must not depend on the current shell having a freshly updated `PATH`.

### 3. Bundle the shared skill in the native destination

Use the destination specified by the current ecosystem's entry file. Default to a
personal installation, unless the user asked for a project or custom scope. Copy the
contents of `skills/discovery/` into that destination, including its `SKILL.md`,
`references/`, `scripts/`, and optional `agents/` metadata. Copy files using the host's
file tools or a directory-copy operation; no provider-specific rewrite of the
workflow is needed. Do not install the repository root, `.git`, `.venv`, run data,
or build output as skill resources.

Inspect the destination first. For an existing Discovery skill, preserve its previous
contents in a backup outside all scanned skill roots before refreshing it. Preserve
local additions separately rather than silently dropping them or retaining obsolete
workflow instructions. If it is a symlink, inspect its target and replace the link
when appropriate; do not overwrite a different checkout through it. Do not replace
an unrelated skill that happens to use the same name.

Avoid duplicate Discovery entries in the selected application's search paths. Refresh
an existing direct installation when possible. Do not modify another application's
skills or managed plugin caches merely to hide a duplicate; identify any remaining
conflict in the result. Backups inside a skills directory can themselves be discovered,
so keep them elsewhere.

An ordinary install or update changes only the current host's skill directory. When
the user explicitly requests every installed host, inspect the normal Codex, Claude
Code, and Cursor locations and refresh only existing directories whose `SKILL.md`
declares `name: discovery`. Do not create missing host installations as part of an
update.

Add an `INSTALLATION.md` note inside the installed skill directory, not the source
checkout. Record the resolved CLI executable path, uv executable path, source checkout
and commit if available, whether the source had local changes, and reported CLI/schema
versions. This is local installation metadata, not a second workflow. It lets future
sessions call the uv-managed executable even when their `PATH` differs. Do not record
credentials or tokens.

### 4. Verify the installation without starting an investigation

From a directory outside the checkout, run the installed executable by absolute path:

```sh
/absolute/uv-bin/discovery --version
/absolute/uv-bin/discovery --json guide
/absolute/uv-bin/discovery guide --topic investigation
```

Replace the example executable path with the actual path; use native process argument
arrays or proper shell quoting for paths containing spaces. Confirm successful results,
not just that the process started. Compare `result.markdown` from the guide with this
checkout's `AGENT_GUIDE.md`, and the topic output with its source reference. A version
match alone does not establish that the latest guide was installed.

Compare the installed `SKILL.md` with its source and confirm its companion folders and
`INSTALLATION.md` note are present. Do not create a test run or modify a target project
just to prove installation. Do not start the discovery workflow unless also requested.

Report every skill directory refreshed, any host location that was absent, the CLI
path, verification result, and the native
invocation (`$discovery` in Codex; `/discovery` for direct Claude Code and Cursor skills).
If the current session still has a cached skill, tell the user to open a new session.
Distinguish file/CLI verification from observing the skill in the host UI; do not claim
UI discovery or a live invocation was tested unless it was.

## Ecosystem references

- [Codex skills](https://learn.chatgpt.com/docs/build-skills) describes local skill locations and explicit invocation.
- [Claude Code skills](https://code.claude.com/docs/en/skills) describes personal and project skills and slash commands.
- [Cursor Agent Skills](https://cursor.com/docs/skills) describes local skill discovery and invocation.
- [uv tools](https://docs.astral.sh/uv/concepts/tools/) describes persistent tool environments and executable locations.
