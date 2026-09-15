# Discovery

Discovery turns a questionable engineering request and its source repository into a
technical specification that another engineer can build from.

The request can be vague, incomplete, contradictory, or simply wrong. A capable model
investigates what the requester means, checks the real project, weighs evidence, tests
ideas when useful, and challenges its recommendation. The CLI keeps that work durable
and prevents important gaps from quietly disappearing.

Discovery stops before implementation. Its job is to determine what should be built
and why.

## Run it

Discovery requires Python 3.11 or newer, SQLite 3.37 or newer, Git on `PATH`, and a
local filesystem. Development and local use run through uv.

```sh
uv sync
uv run discovery --version
```

Discovery is designed for a model investigator. Once the included skill is installed,
give the model the request and source repository:

```text
Run Discovery on /absolute/path/to/request.md against /absolute/path/to/project.
Investigate the request and produce the final technical specification. Do not
implement the target feature.
```

The model handles record IDs, request UUIDs, evidence links, and phase gates. A returning
session begins with the durable resume packet:

```sh
uv run discovery --json --run .discovery/runs/example resume --compact
```

Read [Getting started](docs/guides/getting-started.md) for skill installation, direct CLI use,
and the complete first run guide.

## The workflow

Discovery has four phases:

1. Intent and scope: understand the request, expose ambiguity, and plan focused work.
2. Investigation and evidence: inspect the system, answer research questions, and test
   important claims against evidence.
3. Solution design and validation: compare approaches, choose a design, and prove the
   parts that matter.
4. Adversarial refinement: try to break the recommendation, then revise or regress when
   the challenge succeeds.

Forward movement is sequential. Discovery can return to an earlier phase without
erasing what happened. A corrected run must traverse the affected gates again.

The final export contains:

- `technical-spec.md`, the engineer facing specification
- `discovery-summary.md`, a short result and conditions summary
- `handoff.json`, exact decisions, requirements, and graph relationships
- `evidence-manifest.json`, evidence and artifact provenance

The Markdown specification is the product. The JSON files support machines and audit.

## Concepts worth knowing

The ticket is not truth. Discovery records it as a set of assertions and checks the
claims that matter.

The model judges meaning. Code validates state, required evidence, freshness, process,
and legal phase movement. A passed gate means the required case exists; it does not
mean the conclusion is infallible.

Uncertainty stays visible. Important ambiguity blocks. A safer uncertainty can proceed
under a scoped assumption that records what would invalidate it.

Evidence keeps its job. Source code can establish current behavior. It cannot establish
product intent. A product decision can establish intended behavior. It cannot prove the
current implementation matches it.

Research effort follows consequence. A contextual fact does not need the same challenge
depth as a claim that controls a risky architecture decision. Critical claims receive
an explicit attempt to disprove them.

Experiments use disposable project state. Local databases and synthetic or sanitized
fixtures are allowed. Production credentials and live mutations are not. Read only
provider research happens outside the experiment process and enters the run as evidence.

## Documentation

Start with the [documentation index](docs/README.md). The main guides are:

- [Getting started](docs/guides/getting-started.md)
- [How a Discovery run works](docs/guides/workflow.md)
- [Questions and assumptions](docs/guides/questions-and-assumptions.md)
- [Evidence, claims, and burden of proof](docs/guides/evidence-and-claims.md)
- [Experiments and disposable state](docs/guides/experiments.md)
- [The final technical specification](docs/guides/final-specification.md)
- [Resume, regression, and recovery](docs/guides/resume-and-recovery.md)
- [Investigator modes](docs/guides/investigator-modes.md)
- [CLI reference](docs/reference/cli.md)

Maintainers should also read the
[implementation contract](docs/reference/implementation-contract.md) and
[decision log](docs/reference/decisions.md). Historical design and evaluation records
live under `docs/history/`; they are not current operating instructions.

## Development

```sh
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv build
```

New runs use schema 7. Active runs from schemas 3 through 6 can be upgraded explicitly.
Finalized older runs remain readable. See the [CLI reference](docs/reference/cli.md)
for mutation identity, replay behavior, machine output, and upgrades.
