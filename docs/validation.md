# Milestone 1 validation

Validated locally on 2026-09-10 with CPython 3.13.7. No live services, model calls, or source-mutating experiments were used.

- `uv run pytest -q`: **47 passed**.
- `uv run ruff check src tests`: passed.
- `uv run ruff format --check src tests`: passed.
- `uv build`: source distribution and wheel built successfully.
- Installed the wheel into an isolated environment with no development/runtime dependencies, then ran initialization, the same initialization retry, status, resume, phase check, and audit verification: **six commands passed**. This exercises the packaged DDL outside the editable installation.
- `git diff --cached --check`: passed.

Tests cover initialization and rollback of DDL, repeat initialization safety, canonical input ordering, conflicting request reuse, original-result replay, review replay after later edits, relational write failures, audit append failures, process restart, abrupt process exit before commit, foreign keys, STRICT tables, WAL/FULL configuration, and deliberate writer contention.

Integrity tests cover append-only rows, policy immutability, second roots, invalid predecessor hashes, changed payloads, unaudited relational edits, removed protection triggers, missing/modified artifacts, and orphan reporting without deletion.

Workflow tests cover default blocking questions, answer resolution, surface search provenance, stale semantic reviews, source drift/unavailability, need/lane coverage, impact preservation, dependency cycles, required method/surface/scope/evidence-profile records, critical assumptions, illegal skips, real 1→2 advancement, 2→1 regression and re-entry, and future-phase regression mechanics using explicit test fixtures. Regression also proves that the run's original policy survives changed application defaults.

Concurrency tests use simultaneous OS processes: four callers retry one request, eight distinct writers append to one chain, and four callers initialize one run. Each scenario preserves a single logical result per request and a valid event chain.

Self-review found and fixed three issues during implementation:

1. Pre-transaction review freshness checking could reject an otherwise valid idempotent replay after a plan edit. Freshness now gates new execution under the write lock; successful requests replay their original result.
2. Event hashes alone missed schema-protection changes. The committed-state checksum now includes schema definitions and version as well as normalized data.
3. Regression initially referenced application default surfaces. It now uses the run's frozen policy; source-directory exclusions are frozen there too.

At the end of the original slice, not yet claimed as tested or implemented: full 2→3→4→finalized traversal; leased-agent expiry/reclaim; overlap report isolation; evidence admissibility and lane closure; disposable experiments; adversarial defeaters; source refresh/migration; filesystem power-loss behavior; or adversarial replacement of an entire database. These are explicit later-slice boundaries, not passing placeholder checks.

## Installation follow-up

Added a synchronized CLI/skill/plugin release contract and side-effect-free JSON
`--version` command. The suite now has **50 passing tests**. Both distribution
validators pass. The active pip-owned editable executable and module report
0.1.0/schema 3; package metadata matches. Direct and cached skill contents match
the checkout. `codex plugin list --marketplace personal --json` confirms
`discovery@personal` installed and enabled. See the installation guide for exact
locations and future refresh commands.


## Phase 2 release — 0.2.0 / schema 4

`uv run pytest -q`: **69 passed**. This includes the original transaction, audit,
restart, and concurrent-process tests plus real Phase 2 traversal, scoped
research provenance, closure retries, lead dispositions, UNKNOWN blockers,
impact-based admissibility, minority counterevidence, counterargument recovery,
source drift/refresh, idempotent refresh, and schema-3 migration rollback.

A lighter subagent created the disposable webhook fixture in
`tests/fixtures/phase2`. Its late-retry bug is intentional: the fixture's separate
test run yields one pass and one expected failure. Those toy tests are excluded
from the main suite. Evidence files are clearly fabricated offline inputs, not
verified statements about a real vendor. The subagent's first CLI walkthrough
exposed an UNKNOWN need-answer bypass; a regression test now rejects it.

Leased agents, Phase 3 feasibility, Phase 4 synthesis/finalization, and production
project validation remain outside this release. Model-authored verification
reports do not establish semantic correctness by themselves.

Ruff lint and formatting checks, both skill/plugin validators, and source/wheel
builds passed. The isolated wheel reports 0.2.0/schema 4 and contains the migration
resource. The refreshed system editable package metadata and both CLI entry
points agree. Direct and installed cached skills match the checkout, and the
personal marketplace reports Discovery installed and enabled.


## Four-phase completion iteration — release unchanged at 0.2.0, schema 5

The full suite passed **84 tests**. The new coverage includes complete
1→2→3→4→finalized traversal, immutable final replay and export, draft/checklist
staleness, final compilation rollback on changed adversarial context, evidenced
defeaters and explicit regression, proof links, real macOS sandbox execution,
original-source write denial, offline network denial, timeout result capture and interrupted execution with
no duplicate process, replacement attempts, lease expiry/reclaim/stale tokens,
private replica context, unique findings, failed-replica denominator retention,
and overlap requirements in both Phases 2 and 4. Both schema 3 and schema 4
migration paths preserve history; injected upgrade failures roll back schema and
audit together.

The sandbox positive test runs actual system Python, writes only the copied
fixture, captures results, and satisfies a linked proof obligation. No external
vendor or production environment is used. Skills/plugin validation, Ruff checks,
and wheel/source builds passed. The base package, CLI, and plugin release remain
0.2.0 at the user's request; schema identity is checked separately.

Remaining validation: real-project research quality, long-running experiment
resource usage, large ledgers, and sandbox adapters for other operating systems.
The CLI's actor attribution and isolated context are cooperative boundaries, not
protection from a filesystem owner. Freeform narratives and reports still require
actual semantic scrutiny; procedural success does not establish technical truth.


## Bounded output and reusable cold fixture

The full suite passed **88 tests**; Ruff, skill/plugin validators, and source/wheel
builds passed. Direct and cached skills were refreshed; base release stays 0.2.0.
Targeted sandbox/completion tests passed (13 tests), including a real SIGKILL of
the controller after the child started. The original request retry reported
`EXPERIMENT_INTERRUPTED`, retained one invocation, and allowed explicit
abort/replacement with valid audit history. The test cleaned up its surviving
child; automatic cleanup after controller death is not claimed. Separate stdout
and stderr flood tests enforce the 2,000,000-byte limit, while a source-log test
proves capture preserves existing stdout.log/stderr.log files and source hashes.

A lighter agent built `tests/fixtures/outbox_worker`; a separate lighter agent
inspected it without the sibling oracle. Its three unittest checks produced one
pass and two intentional expected failures. The cold evaluator identified both
the duplicate effect after crash/retry and committed attempt count contradicting
a test's rollback expectation. It also retained the unresolved retry versus
quarantine policy as a blocking human question. These match the original oracle, but root review found an attribution error in
both: the ticket never explicitly requires the attempt counter to roll back.
The oracle now distinguishes that extra test assumption; the cold report remains
unchanged as evidence of the evaluator's limitation.
It additionally flagged untested concurrent-worker behavior, without claiming a
concurrency reproduction. The fixture simulates a side effect in SQLite and an
injected crash, not a real external service or process-kill durability test.

The bounded Discovery smoke recorded 15 audited events, two blocking questions,
two needs, and two scoped lanes. Audit verification passed without orphan
artifacts. It stopped in Phase 1 with unresolved questions, pending surfaces,
and no semantic plan review. Initial source drift was recorded through refresh.
The local report is `.discovery/outbox-cold-report.md`; the durable run is
`.discovery/outbox-cold-check`. Subsequent repository commits change its Git
baseline, so resuming must inspect drift. This exercise validates honest blockers
and useful findings, not four-phase semantic quality. Future checks should reuse
this fixture or a real project rather than multiply synthetic environments.
