# Discovery

Give Discovery an engineering request and a project. Your agent investigates the
request, checks it against the code and available evidence, and writes a technical
specification someone can build from.

The request can be vague or wrong. Discovery keeps the questions, findings, and
reasoning on disk so they survive a new chat or a switch to another agent. It stops
before implementing the feature.

## Install from your agent chat

Open this checkout in Cursor, Claude Code, or Codex and say:

```text
Install this skill for me.
```

The agent installs the CLI through uv and puts the shared skill in its own skill
folder. After installation, use `$discovery` in Codex or `/discovery` in Claude Code
and Cursor. The [installation guide](docs/guides/agent-installation.md) covers the steps
the agent performs.

## Use Discovery

In your agent chat, invoke the skill and give it the work:

```text
Use Discovery to investigate this request against /absolute/path/to/project:

[paste your request here]

Produce the final technical specification. Do not implement the feature.
```

The repository includes an entry file for each agent. All three point to
[AGENT_GUIDE.md](AGENT_GUIDE.md), which owns the workflow. You don't need to
configure each agent or install a plugin.

From another project, give your agent the path to this checkout's
`AGENT_GUIDE.md`, or attach that file to the chat. It tells the agent how to use the
CLI from the checkout. The agent needs local command and file access.

The agent saves your request, creates the run, gathers evidence, and works through
the review gates. One investigator is the default. It asks you when a missing
product decision or unavailable access blocks the work, not for record IDs or
routine setup choices.

## CLI access

Discovery needs Python 3.11 or newer, SQLite 3.37 or newer, Git, and a local
filesystem. These commands use uv.

For direct CLI use, the agent's installation makes `discovery` available. You can
also install it manually:

```sh
uv tool install /absolute/path/to/discovery
discovery --version
```

The installed CLI includes the same guide and its detailed references. In any
agent chat with access to that installation, you can say:

```text
Read the output of `discovery guide`, then use Discovery to investigate
[request] against [project path]. Produce the final technical specification.
```

See [Getting started](docs/guides/getting-started.md) for installation and recovery.

## What you get

A completed run exports:

- `technical-spec.md`: the recommendation, scope, design, and acceptance criteria
- `discovery-summary.md`: the result and remaining conditions
- `handoff.json`: decisions, requirements, and their relationships
- `evidence-manifest.json`: evidence and artifact provenance

The Markdown specification is the product. The supporting records explain why it
says what it says. If the investigation reaches a real blocker, you get an interim
report with the findings and unresolved questions.

To continue in another chat or agent, give it the guide and the run path. It resumes
from the saved state. Keep the run directory; its artifacts support the exported
specification.

## How it works

Discovery moves through intent and scope, investigation, solution design, and
adversarial review. A failed premise can send the work back to an earlier phase.
The agent judges the evidence; the CLI checks required records, freshness, and
legal transitions. Passing a gate does not make a conclusion infallible.

Experiments use disposable project copies and local test data. Discovery does not
launch models or keep a chat running after its host stops.

Read the [workflow guide](docs/guides/workflow.md), the
[specification guide](docs/guides/final-specification.md), or the
[documentation index](docs/README.md) for more detail.

## Development

```sh
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv build
```

The code separates CLI parsing, application operations, domain rules, and storage
adapters. See the [implementation contract](docs/reference/implementation-contract.md)
for those boundaries and the [agent integration guide](docs/reference/agent-integration.md)
for the shared instructions and entry files.
