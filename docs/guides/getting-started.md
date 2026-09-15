# Getting started

Discovery runs locally through uv. It does not need a server, model provider SDK, or
external database. A run consists of one SQLite database plus immutable artifacts in a
directory you choose.

## Requirements

- Python 3.11 or newer
- SQLite 3.37 or newer with JSON support
- Git available on `PATH`
- uv
- a local filesystem for the run directory

Do not place an active run on a network filesystem. SQLite uses WAL mode, and copying
only the main database file is not a valid backup of a live run.

## Install the project

From the repository root:

```sh
uv sync
uv run discovery --version
```

The version command returns a JSON envelope with the CLI version and current schema.
For an editable system installation or Codex plugin setup, use the
[Codex installation guide](../reference/codex-installation.md).

## Use Discovery through a model investigator

The normal operator experience is a request to a capable model with the Discovery
skill installed:

```text
Run Discovery on /absolute/path/to/request.md against /absolute/path/to/project.
Investigate the request and produce the final technical specification. Do not
implement the target feature.
```

Choose `disabled`, `partitioned`, or `overlap` investigators when it matters. If no mode
was supplied, the model asks once. Most runs should use `disabled`.

The model reads the request and project, decides what evidence means, and writes the
technical recommendation. The CLI stores its work, checks required evidence and
freshness, and controls phase movement. The operator should not need to manage record
IDs or understand the schema.

The remaining command examples explain what the model is operating and support direct
CLI use or troubleshooting.

## Prepare the request

Put the request in a plain text or Markdown file. Preserve the original wording. Do not
rewrite a weak ticket before initialization, because its ambiguity and incorrect
premises are part of what Discovery needs to inspect.

Choose the real source repository as `--source`. Discovery reads that project and may
copy it into disposable experiment state, but it does not implement the requested
feature there.

Keep run data under `.discovery/` and ignore that directory in the target repository.
A common layout is:

```text
project/
  .discovery/
    requests/
      request.md
    runs/
      <run id>/
  src/
  tests/
```

## Initialize a run

Every mutation carries a request UUID and an actor identity. The request UUID belongs
to one logical command. Generate a new value for each new mutation. Reuse the same
value only when retrying the exact same command after an uncertain response.

```sh
uv run discovery --json --run /absolute/project/.discovery/runs/example \
  --request-id 10000000-0000-4000-8000-000000000001 \
  --actor-id 20000000-0000-4000-8000-000000000001 \
  --actor-name 'Discovery investigator' \
  --actor-kind model \
  run init \
  --title 'Investigate webhook ordering' \
  --input /absolute/project/.discovery/requests/request.md \
  --source /absolute/project \
  --subagents disabled
```

Use `disabled` unless the operator deliberately chooses `partitioned` or `overlap`.
Those modes record isolated investigator assignments. Discovery does not launch models
by itself.

Initialization captures the request and source baseline. It refuses to replace an
existing run directory.

## Read the run before changing it

```sh
uv run discovery --json --run /absolute/project/.discovery/runs/example resume --compact
```

The compact packet is the normal starting point for a new model session. It includes:

- the interpreted request state and current phase
- blocking questions and active assumptions
- respondent hypotheses
- research needs, lanes, dependencies, and open leads
- important claims and contrary evidence
- source drift
- design obligations or open defeaters in later phases
- current gate failures and useful next actions

Use ordinary `resume` when you need the larger record. Use focused list commands when
you need one entity type.

## Begin with intent, not implementation

Phase 1 asks whether the request means what it appears to mean. Inspect the ticket,
source, tests, documentation, issue history, external dependencies, and human authority.
These are minimum surfaces. Add another surface when the project reveals one, such as an
architecture decision record or deployment configuration.

Create blocking questions for ambiguity that could materially change the outcome. Use a
nonblocking question and explicit assumption only when continuing is genuinely safe.
Then create focused research needs and lanes. Review the plan before advancing.

The detailed sequence is in [How a Discovery run works](workflow.md). For command
syntax, run:

```sh
uv run discovery --run /absolute/path/to/run <family> <action> --help
```

## Know what success looks like

A successful run does not end with a database or a score. It exports an implementation
ready `technical-spec.md` supported by machine readable traceability. Read
[The final technical specification](final-specification.md) before drafting one. It
sets the quality bar for the work that precedes it.
