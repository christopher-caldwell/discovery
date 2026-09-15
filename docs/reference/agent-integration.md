# Agent integration

Discovery separates the operating contract from the host that loads it. Maintain
workflow behavior once in [AGENT_GUIDE.md](../../AGENT_GUIDE.md). Agent entry points
route to it and describe installation in their own ecosystem; they must not fork
phase rules, defaults, or completion criteria.

## Instruction layout

| File | Role |
| --- | --- |
| [AGENT_GUIDE.md](../../AGENT_GUIDE.md) | Generic core: bootstrap, ownership, request capture, recovery, phase workflow, and delivery |
| [AGENTS.md](../../AGENTS.md) | Codex workspace entry point |
| [CLAUDE.md](../../CLAUDE.md) | Claude Code workspace entry point |
| [.cursor/rules/discovery.mdc](../../.cursor/rules/discovery.mdc) | Cursor project rule; Markdown with rule frontmatter |
| [skills/discovery/SKILL.md](../../skills/discovery/SKILL.md) | Optional skill entry point that reads the core through the CLI |
| `skills/discovery/references/*.md` | Detailed shared procedures, loaded by phase or task |
| `src/discovery/guide.py` | Read-only access to the bundled core and references |

Codex loads project instructions from `AGENTS.md`; no `CODEX.md` fallback configuration
is needed. See the [official Codex instructions documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
Claude Code loads `CLAUDE.md`; see its [memory documentation](https://code.claude.com/docs/en/memory).
Cursor project rules use `.mdc` files under `.cursor/rules/`; a plain `CURSOR.md` file
would not establish the same native loading contract. See the
[Cursor rules documentation](https://cursor.com/docs/rules).

The small Cursor rule uses `alwaysApply: true` to make routing available in every
chat. Its body still limits the workflow to Discovery requests. The entry files do
not turn ordinary development of this repository into an investigation.

## Installation through the agent

“Install this skill” in the Discovery checkout is sufficient. Each native entry
file selects its ecosystem's destination and command syntax, then directs the agent
through the [shared installation procedure](../guides/agent-installation.md).
The agent installs the CLI with `uv tool install` and copies the shared skill bundle
into the selected native skill directory. There is no installer program or new
marketplace metadata involved in this path.

The default is a personal skill: `$discovery` in Codex, `/discovery` in Claude Code,
and `/discovery` in Cursor. Existing direct installations are refreshed rather than
duplicated; prior contents are backed up outside scanned skill roots. The installed
skill gets a local `INSTALLATION.md` note recording the resolved executable and source.
The shared skill loader uses this note when an app's command path differs. Neither
this note nor ecosystem-specific installation language duplicates the core workflow.

Installation verifies CLI and guide output outside the checkout without starting a
Discovery run. The agent reports native UI discovery separately when it can observe
it. A current chat can retain an older skill snapshot until a new session starts.

## Use from any project

The checked-in native entry points apply when the Discovery checkout is the agent's
workspace. They do not install global rules or affect every project on the machine.
For work in another repository, supply the absolute path to `AGENT_GUIDE.md`, attach
that file, or ask the agent to read `discovery guide`. This requires no separate
configuration for Cursor, Claude, or Codex.

A team that wants persistent native routing in another repository can reuse the thin
entry points and the core file there. Merge the routing text into any existing
`AGENTS.md` or `CLAUDE.md` rather than replacing project instructions. Preserve the
relative layout or use the installed `discovery guide` fallback. Copying those files
is optional; the ordinary chat workflow does not require it.

## Runtime contract

Every supported host needs local command execution and file access. Research uses
the host's existing capabilities; Discovery has no dependency on a tool named
`exec`, `web`, a particular question widget, or a provider API. Unavailable external
sources must remain visible as limitations. Native tool permissions still apply.

`discovery guide` prints the core as Markdown. `discovery --json guide` returns it
under `result.markdown`. `discovery guide --topic TOPIC` reads one detailed reference;
`guide --help` lists valid topics. No guide invocation creates or opens a run. A
source checkout can use `uv run --project /absolute/discovery discovery` as the
prefix for every command, even while investigating another source repository.

The CLI defaults `run init --subagents` to `disabled`. Additional investigator modes
remain explicit, and a requested mode must not silently fall back. Host-specific
worker launching is outside the CLI; assignments and findings use the same durable
protocol regardless of host. The generic guide owns the stopping and resumption rules.

Switching hosts does not create a new run. The receiving agent loads the same core,
reads `resume --compact`, follows artifact references, and uses its own actor/session
identity for new actions. Exact uncertain retries retain the original mutation's
actor, request UUID, and logical input. The source/run files must be accessible to
the receiving host; this is shared local state, not cloud synchronization.

## Packaging and updates

The wheel build includes `AGENT_GUIDE.md` and the detailed references under
`discovery/_guide/`. It copies the canonical files at build time; do not check in or
edit a second generated guide. Editable development reads the originals from the
checkout, while a wheel installation reads only its packaged resources.

The optional skill/plugin contains a loader, not a separate workflow. Its CLI
installation must expose `guide`. Older installations with the same base version may
predate that command; check capability with `discovery guide`, not version alone.
Rebuild/reinstall the CLI after updating the shared guide to distribute those changes.
No runtime network fetch is needed to read installed instructions.

After editing the core, references, or entry points, check links and run:

```sh
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv build
```

For distribution verification, install the built wheel in a fresh environment outside
the checkout. Verify plain/JSON guide output and every reference topic, then initialize
and resume a disposable run without `--subagents`. This catches packages that work only
because the repository's Markdown files happen to exist beside an editable install.

The native file conventions are documented by their providers. CLI and packaging
tests establish the shared runtime contract; they do not prove that every model will
follow every instruction or that every host setting permits execution.
