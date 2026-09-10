# Discovery System Design Package

This package collects the current first-pass design work for the Discovery CLI/skill that is intended to sit upstream of Task Ledger and Independent Consensus Review.

## Current direction

The system accepts a potentially vague or incorrect written specification, establishes intent and blocking ambiguities, performs structured evidence-backed research, develops and experimentally validates implementation strategies against the source code, then adversarially challenges the resulting technical answer before producing a technical specification and assurance score.

Progress is constrained to four semantic phases:

1. **Intent & Scope**
2. **Investigation & Evidence**
3. **Solution Design & Experimental Validation**
4. **Adversarial Refinement**

Forward movement must be sequential. Regression may target any earlier phase, after which every later phase must be traversed again.

## Core invariants

- The model performs semantic reasoning; deterministic CLI code owns persistence, validation, phase movement, IDs, and audit writes.
- SQLite normalized state is authoritative; the immutable hash-chained event log is a command/audit history rather than a replay-required event-sourcing system.
- Ambiguity defaults to blocking when the model is unsure.
- Blocking and non-blocking questions are distinct; non-blocking ambiguity requires an explicit recorded assumption.
- Respondent targeting records an authority category first, then ranked likely people/groups as hypotheses.
- Phase 1 has mandatory discovery surfaces. Each must be `searched`, `unavailable`, `inaccessible`, or `not_applicable`; there is no generic `skip`.
- Research is claim-centric: artifacts preserve sources, evidence records observations, claims state propositions, arguments explain support, and defeaters record reasons the conclusion may be wrong.
- Confidence scores never unlock workflow gates.
- Research lanes close only when their protocol is complete, all eligible leads are dispositioned, and a closure sweep produces no new material leads. This is called `procedurally exhausted`, not absolutely exhaustive.
- New technical avenues expand Phase 2. New uncertainty about the meaning of the request regresses to Phase 1.
- Subagents support two modes: partitioned research for speed and overlapping isolated research for independent convergence/omission detection.
- Consensus is not verification. Agreement, evidence admissibility, and unresolved defeaters are separate dimensions.
- A unique minority finding becomes a lead; failure by other agents to discover it is not a vote against it.
- Phase 3 may use disposable Git worktrees, copied/local databases, test harnesses, and other temporary artifacts to prove implementation strategies without modifying the real working source tree.
- Phase 4 explicitly attempts to falsify important claims and design decisions. Material/critical open defeaters block finalization.
- The final technical specification should trace important decisions back through claims, arguments, evidence, artifacts, research needs, and ultimately the incoming request.

## SQLite-specific choices

The DDL follows the supplied `db_financial_tracker` house style where practical: singular tables, entity-specific numeric IDs, explicit named constraints, leading commas, table-level primary keys, and explicit indexes.

SQLite adaptations include:

- `STRICT` tables.
- `INTEGER` surrogate primary keys instead of PostgreSQL identity/smallint variants.
- UUIDs and timestamps stored as `TEXT` and generated/normalized by the CLI.
- JSON stored as validated canonical `TEXT`.
- booleans represented as integer values constrained to `0/1`.
- `WITHOUT ROWID` only for appropriate pure composite-key junction tables.
- foreign keys enabled per CLI connection.
- `dt_modified` maintained by application transactions rather than generated per-table SQLite triggers.

## Mutation/CLI direction

Mutating commands are designed around a single atomic SQLite transaction using `BEGIN IMMEDIATE`:

1. validate command and current state;
2. validate request idempotency;
3. perform normalized state changes;
4. append one immutable audit event;
5. commit.

Agent-scoped writes use expiring leases. Mutating commands use request UUIDs/input hashes so retries cannot duplicate state.

The CLI should preserve Task Ledger-style ergonomics where applicable: machine-readable `--json`, stable nonzero error codes, diagnostics on stderr, resumability, and no mandatory interactive behavior in agent mode.

## Files

### `schema/discovery_ddl_v1.sql`
Initial SQLite schema pass.

### `schema/discovery_ddl_v2.sql`
Current schema revision after the CLI/state-machine design pass. **Use this as the current schema reference.**

### `specs/discovery_cli_contract_v1.md`
Current command, transaction, phase-gate, lease, idempotency, regression, research-lane, experiment, and audit contract.

### `references/independent-consensus-audit-reference.zip`
The older Independent Consensus Audit supplied as a reference point. It is not normative; useful ideas should continue to be evolved or discarded as Discovery is dogfooded.

## Recommended next implementation slice

Implement the smallest end-to-end path first:

`run init -> status/resume -> question/research-need/lane creation -> phase check -> audit verify`

This tests persistence, transactionality, idempotency, audit integrity, and phase gating before implementing the entire research workflow.
