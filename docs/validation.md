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
