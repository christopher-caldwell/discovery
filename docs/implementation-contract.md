# Current implementation contract — milestone 1

This document and runtime schema 3 describe the implemented system. The original package is retained unchanged as a historical handoff and future architectural target. Unsupported later-phase operations are not silently approximated.

## Architecture and mutation ownership

- `cli.py` owns parsing, transport normalization, output, and exit codes.
- `application/commands.py` prepares immutable external inputs and dispatches use cases. Initialization, planning, and phase transitions are separate small modules. Queries build resume and status projections.
- `domain/` contains pure transition rules, gate policies, errors, canonical encoding, and policy defaults. It has no SQLite, filesystem, subprocess, or CLI dependency.
- SQLite adapters expose a command transaction boundary and purpose-specific snapshots, plus internal SQL insertion/reference helpers. They are not a public generic repository API. SQL in application use cases stays explicit and parameterized.
- Filesystem and Git adapters capture immutable bytes and source fingerprints. No shell or experiment execution adapter is exposed yet.

Each successful new mutation opens one `BEGIN IMMEDIATE`, checks integrity and idempotency, loads current state, verifies command preconditions, changes normalized rows, computes a state checksum, appends one audit event, and commits. Actor creation is inside the same transaction. Any exception, including interrupts, rolls back. DDL initialization also runs inside this boundary without `executescript`, because that API can implicitly commit a pending transaction.

Read commands enable `query_only` and use a single read transaction, so resume cannot combine different SQLite revisions. Connection setup enables foreign keys, WAL, synchronous FULL, a 5000ms busy timeout, and recursive triggers. Run-level source observation is external to SQLite's snapshot.

## Persistence and audit

All handoff v2 tables remain available, with STRICT typing and explicit constraints/indexes. Most are intentionally unexposed. Schema 3 removes destructive initialization, adds a singleton run index, and protects run identity, request linkage, subagent selection, and policy from updates. Versions other than 3 are rejected; there is no implicit migration or reset command.

The request and research results are content-addressed artifacts. Writes use a same-directory temporary file, fsync, atomic rename, and directory fsync before metadata registration. Generated review context is captured before its command transaction, then checked against the exact current context under the write lock. A failed command can leave an orphan file, which verification reports without deleting. Metadata must never commit before its referenced bytes exist.

Events use the supplied UUID-based canonical envelope. Payload contains logical input, original command result, and a checksum of normalized relational state plus SQLite schema definitions/version. Events are immutable and chained to the current head; triggers prohibit a second root, forks, updates, and deletes. The current state checksum detects unaudited data changes, dropped triggers, and tail deletion that changes state. It is a checksum, not a replay projection: only current state is serialized and hashed, not stored in each event.

Verification recomputes all event hashes, links, SQLite integrity, foreign keys, current state/schema checksum, and artifact size/hash/path. It cannot prove semantic truth, authenticate a claimed human identity, prevent a filesystem owner from rewriting the entire database and chain, or detect replacement with an internally consistent older backup without an external trusted checkpoint. Actor/session attribution is recorded, not an authentication system. Entire-run verification on each mutation favors correctness for this small slice; large-run optimization is deferred.

Canonical format `python-json-sorted-utf8-v1` uses sorted keys, compact separators, UTF-8, and rejects NaN/infinities. It is deterministic for this Python CLI but does not claim full RFC 8785 interoperability. The resolved policy freezes this encoding/version. Request hashing includes command name (checked separately), normalized input and actor identity. Session UUID is excluded, allowing response-loss retries from a new session. Input-file paths/content hashes are part of logical input where recorded; callers must retain file inputs to reproduce a request. CLI lane list options are deduplicated and sorted; different reference spellings are not promised to be equivalent idempotency inputs.

## Phase 1 and review

Initialization creates P1 r1 active and P2–P4 r1 pending. The default immutable baseline surfaces are request, source_code, tests, documentation, issue_history, external_dependencies, and human_authority. This list was unspecified in the handoff and is now explicit policy. Custom Phase 1 surface creation and policy overrides are deferred; lanes can declare their own required surfaces.

Question creation defaults to blocking. Authority category, confidence, and rationale are recorded as a hypothesis; answering records the submitting actor. This slice provides answer resolution only, with no assume/withdraw shortcut. Active critical assumptions, if present in future state, fail the domain gate.

Every need captures request-artifact provenance and impact. Every lane requires a question, rationale, scope, impact-aligned evidence profile, methods, surfaces, and linked needs. Dependency insertion rejects cycles; the gate independently checks the entire dependency DAG. Need/lane graph coverage is structural, while a semantic reviewer judges meaningful coverage.

Phase 1 advancement requires no open questions, no invalid/critical assumptions, all baseline surfaces terminal with activity/reasons, complete need/lane coverage, valid lane structure and dependencies, current source observation, intact audit, and a passed semantic review of the exact canonical plan context. An empty research plan still requires the reviewer's explicit semantic judgment; code cannot infer whether a request needs research.

`plan review` is an atomic attributed report import. It creates a terminal `semantic_verifier` record referencing immutable context and report artifacts. It is not a running agent or an independent-review claim. No agent-scoped commands are available, and no lease token is accepted. Leases, reclaim, partitioned work, and overlap isolation will be introduced together rather than exposing agent writes without ownership enforcement.

## Transitions, regression, and future phases

`phase advance` accepts no target. The domain transition rule is 1 → 2 → 3 → 4 → finalized, but this milestone enables only the 1 → 2 edge. Any later gate includes `PHASE_NOT_IMPLEMENTED`, including empty later-phase state. Tests cover later regression mechanics with explicitly arranged future-phase fixtures, not a public gate bypass.

Regression accepts any earlier phase and a durable cause reference. It invalidates current traversal revisions from the target through phase 4, creates the target's next revision active and later revisions pending, and records invalidation links. Earlier unaffected phases remain intact. Existing knowledge and creation provenance are preserved. Non-historical technical specs are superseded. Returning to Phase 1 creates fresh mandatory surface records and requires a fresh review. Returning through later phases never skips intermediate gates.

Future Phase 2 work must enforce lead dispositions and closure iterations, reopening on new material leads, and UNKNOWN without pretending epistemic certainty. New uncertainty about request meaning requires explicit regression. Evidence supports/refutes/qualifies arguments; confidence cannot admit a claim.

Future Phase 3 work must isolate source modifications in disposable worktrees/copies and capture exact procedures/results/limitations for proof obligations. No experiment commands run today. Future Phase 4 must target the actual draft, record evidenced defeaters, block unresolved material/critical challenges, and require explicit regression for confirmed material/critical defeaters. There is no finalization or renderer shortcut today.

## Baseline and resume limits

Initialization records Git HEAD when available and a content/mode fingerprint of the specified source directory, including untracked/ignored files except reserved generated directories. Filesystem sources without a commit use a content-addressed revision. Symlink targets are hashed without following links. Source files are only read; Git only runs `rev-parse`.

The excluded directories are `.git`, `.discovery`, `.venv`, `__pycache__`, `.pytest_cache`, and `.ruff_cache`, plus `.DS_Store` files and the exact run directory. Do not place relevant source only in these reserved paths. Large generated directories elsewhere are included and can be expensive. Submodule worktree contents are included; `.git` directory metadata is not treated as source.

Status/resume/gates compare the baseline with current files and report observed drift without mutating historical baseline rows. Missing source counts as drift. Refresh and narrow evidence invalidation are deferred; drift blocks forward progress. A filesystem scan is not an atomic snapshot of a concurrently edited source tree, so this slice does not claim final-spec freshness guarantees.

Resume reads normalized state and at most five event headers, not event replay. It returns request provenance, phase/revision, answered/open questions, assumptions, needs/lanes, leads, claims, proof obligations, defeaters, source observations, gate failures, and next actions. It is an orchestrator view; no isolated agent-context endpoint exists yet. Large-run pagination/context budgeting is deferred.
