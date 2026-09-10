# Current implementation contract — Discovery 0.2

This document and runtime schema 5 describe the implemented system. The unchanged `discovery-design-package/` is the historical handoff and future architectural target. All four phases can complete, including finalization; see the completion workflow for operating details.

## Architecture and transaction authority

The CLI parses typed inputs and renders stable JSON. Application modules implement initialization, planning, investigation, claims, sources, and phase transitions. Pure domain policies evaluate phase, lane, and claim state; adapters provide SQLite transactions, immutable artifact capture, and source fingerprints. No ORM, model SDK, generic repository API, or asynchronous framework is required.

Every new mutation uses one `BEGIN IMMEDIATE`, validates schema/integrity/idempotency/current state, applies normalized changes, and appends one event before committing. Actor creation is part of the same transaction. Failed commands, including DDL upgrades, roll back their relational mutations and event. Read queries enable `query_only` and use one SQLite snapshot.

Connections enable foreign keys, WAL, FULL synchronous behavior, recursive triggers, and a five-second busy timeout. Simultaneous WAL bootstrap additionally has a bounded five-second retry because SQLite can return BUSY without invoking the busy handler. This retries connection setup only, before command work. Transaction contention still returns `SQLITE_BUSY` after its timeout; callers retain their request UUID for retries.

Logical input and actor identity determine idempotency, with canonical key ordering and sorted/deduplicated list flags. Session UUID is attribution and can change on a retry. The original result is returned without a new event, even if current workflow state has since changed. File-based commands retain content hashes in logical input; callers must retain those input files to reproduce a request.

## Persistence, artifacts, and upgrade

Schema 5 preserves the handoff tables and adds normalized lane closure state, lane answers/limitations/question linkage, need answers, verification-report linkage, and counterargument resolutions. It relaxes source URI/revision uniqueness: dirty working-tree snapshots and returns to earlier revisions can share a Git HEAD. Exactly one baseline per URI remains active. New fields have explicit checks and foreign keys where applicable.

Schema 3/4 runs are not silently migrated. `run upgrade` verifies their existing audit/state, applies the additive migration under the same command transaction, then appends an event. Historical events and artifacts remain byte-identical. Policy stays frozen; its `schema_version` records the initialization policy's origin, while SQLite `user_version` reports the actual current schema. Upgrading a Phase 1 run can stale its plan snapshot because normalized records now have additional fields. Other old schema versions remain unsupported.

Artifacts use content-addressed bytes, file/directory fsync, and atomic rename before SQLite metadata registration. A failed command can leave an orphan, which verification reports without deleting. Metadata cannot commit ahead of bytes. `artifact capture` saves an attributed snapshot; `--source-backed` additionally records the source baseline, revision, and relative file locator. The file must be inside the fingerprinted source scope and match the captured bytes under the command lock. Search and verification reports are authored reports, not automatically primary or empirical evidence.

The immutable event envelope is hash chained and includes the original result plus a checksum of normalized state and schema definitions/version. Audit verification checks all hashes/predecessors, current state/schema, foreign keys, SQLite integrity, artifact paths/hashes/sizes, and orphan files. This is tamper evidence, not event sourcing, authentication, or proof of semantic truth. A filesystem owner can replace an entire database with another internally consistent chain or backup; detecting that needs an external trusted checkpoint. Full verification on each command is deliberately conservative and may need optimization for large runs.

Canonical encoding is `python-json-sorted-utf8-v1`: UTF-8, sorted keys, compact separators, no NaN/infinities. It does not claim RFC 8785 cross-language equivalence. Actor identity is caller-attributed, not authenticated. Confidence never unlocks a gate.

## Phase 1: intent and planning

Initialization creates P1 r1 active and P2–P4 r1 pending. The immutable baseline surfaces are request, source_code, tests, documentation, issue_history, external_dependencies, and human_authority. Each current Phase 1 surface must terminate with a truthful reason; searched requires actual linked research activity.

Questions default to blocking and record authority category/confidence/rationale as hypotheses. Answer resolution records the submitting actor. Explicit assumption and withdrawal commands remain deferred; there is no shortcut for open non-blocking questions. Critical active assumptions fail the gate.

Needs trace to the request artifact. Lanes are scoped questions with rationale, impact-aligned profiles, linked needs, required methods, and required surfaces. Dependencies must form a DAG. Need/lane coverage is structurally checked. The semantic reviewer evaluates meaningful coverage against an exact canonical `plan snapshot`, submitting an immutable report through `plan review`. Plan changes stale the review. This is an attributed report import, not an independent agent run or consensus claim.

Phase 1 advancement requires all of these structures, no unresolved questions/invalid assumptions, current source, valid audit, and a passed current semantic review. The initial ticket is an assertion source; copying its bytes into another artifact does not make it factual evidence.

## Phase 2: investigation, leads, and closure

Activate each planned lane. Phase 2 may add needs, lanes, and dependencies for new technical avenues. Meaning changes require explicit regression to Phase 1. `question create --technical` records uncertainty about the answer in Phase 2; omission of that flag still rejects Phase 2 question creation. Questions can be answered in either phase.

Every lead links to an originating activity in the same lane. Terminal dispositions are investigated, irrelevant, duplicate, inaccessible, or requires_human_input, each with a reason. Investigated requires a separate same-lane research activity. Duplicates reference a terminal nonduplicate lead in that lane, preventing cyclic chains and unresolved aliasing. Material/critical human-input leads require blocking questions. There is no skipped state.

Research activities can link a surface and method in the same lane. Completed methods and searched surfaces require actual activities; unavailable/inaccessible/not_applicable require reasons. Current closure methods must belong to the active closure iteration. Old iterations remain historical and cannot be completed retroactively.

`lane closure-begin` requires an active lane with no pending leads, increments its iteration, and instantiates the run policy's terminology, snowballing, contradiction, and evidence-gap methods. New leads, evidence, arguments, method requirements, dependency changes, or explicit reopen invalidate closure. Affected lanes and transitive dependents reopen; prior need answers become covered, and previously admissible claims become proposed pending reevaluation. Historical answers remain present with their nonterminal status, rather than being erased.

Closure requires terminal surfaces/primary methods/current closure methods, no pending leads, closed dependencies, and deterministic admissibility or terminal rejection of material/critical claims. Reevaluate claims after the fresh sweep. A known material/critical answer requires an admissible same-lane claim at least as consequential as the lane. A material/critical UNKNOWN requires a linked blocking question; procedural closure may succeed while phase advancement stays blocked. When that question is answered, its linked lanes reopen to incorporate the answer.

`research-need answer` requires all covering lanes to be procedurally exhausted. Phase 2 advancement rechecks needs, lane closure, material claims and evidence profiles, questions, source freshness, and audit integrity. A successful transition enters Phase 3; no implementation strategy or final-spec result is implied.

## Claims and counterevidence

`evidence create` records a primary, secondary, or empirical classification, immutable artifact reference, locator, observation, and extraction actor. Classification remains a semantic responsibility. Claims distinguish current behavior, vendor capability, constraints, and intended behavior. Claim impact cannot be below its lane's floor in this release.

Arguments link active same-lane evidence with support, refutation, or qualification, plus reasoning and explicit limitations. `argument verify` records a passed/failed/inconclusive judgment and immutable report. Arguments are submitted with their evidence set; revised reasoning/evidence requires a new argument. Failed or inconclusive arguments remain visible.

`claim evaluate` is the only admission path. It returns status and violations; command success does not itself mean admissibility. All admissions require a passed supporting argument with active artifact-backed evidence. Material profiles additionally require primary/direct evidence and the current contradiction sweep. Critical profiles also require empirical evidence and completed falsification/empirical-verification methods. Unsupported claims remain proposed, countered claims remain contested. Rejection is an explicit attributed semantic disposition with a reason; it cannot supply a known lane answer.

Every contrary or qualifying argument needs an evidenced disposition before admission, regardless of supporting argument count. `argument resolve-counter` retains the original argument and links distinct active same-lane resolution evidence with a reason. A duplicate evidence ID or copied artifact bytes cannot resolve themselves. Retraction of supporting or resolving evidence invalidates admission and closure. No vote or confidence value overrides contrary evidence.

## Source refresh and resume

The fingerprint records file contents, modes, symlink targets without following links, and Git HEAD when available. It includes untracked/ignored files except the frozen excluded directories (`.git`, `.discovery`, `.venv`, `__pycache__`, `.pytest_cache`, `.ruff_cache`), `.DS_Store`, and the run directory. Reserved paths cannot supply source-backed evidence. Filesystem-only sources use a content-derived revision. Source scans are not atomic against concurrent external edits; no final-spec freshness guarantee is claimed yet.

Status/resume/gates observe drift without rewriting baseline history. `source refresh --reason` creates a new baseline and retracts active evidence captured from the old baseline, invalidating affected claims/lanes/need answers and transitive lane dependents. External snapshots and unrelated lanes survive. The scope is one source baseline, not individual changed lines; this conservative first version avoids a full run restart without silently blessing stale source evidence. Replacing source evidence and recording new arguments is explicit.

Resume projects normalized questions, needs, lanes, leads, claims, proof obligations, defeaters, source observations, frozen policy, gate failures, next command families, and five recent event headers. No event replay is used. Scoped investigator resume exposes immutable starting context and only its own findings. Entity lists and lane/claim checks expose detailed current state. Pagination and large-context budgeting remain deferred.

## Phases 3–4 and isolated investigators

[The completion workflow](completion-workflow.md) defines the supported commands. Design gates recheck upstream research, exactly one strategy, decision/claim links, impact-preserving proof obligations, experiment results, requirement/need coverage, and an exact structured-state draft hash. Narrative is authored; relational references are validated by code. Authored prose is not automatically semantically verified.

Experiments use a copied baseline and macOS Seatbelt with filesystem reads, copy-only writes, and no network. There is no unsandboxed fallback, credential-read isolation, or production database support. Reservation and receipt registration are separately audited transactions around execution; interrupted attempts never rerun implicitly. Existing source bytes remain untouched. Source scans are not atomic snapshots of a concurrently changing filesystem.

Phase 4 checks bind to both spec revision and phase revision. Confirmed defeaters require explicit regression before repair. Material risks cannot be accepted by vote. Resolution evidence must remain active; retracting it reopens the challenge. Finalization recompiles structured/narrative exports, rechecks both structured and adversarial snapshots under the write lock, registers deterministic assurance dimensions, and marks the run finalized in one transaction. Export materializes already committed artifacts without creating another logical mutation.

Investigators operate on immutable context and private finding/report rows. Lease tokens are caller-generated random secrets; only hashes enter the database or audit trail. Replicas require distinct actor identities, and scoped writes check token, expiry, actor, group, phase, and lane. This is cooperative isolation through the CLI, not authentication against a filesystem owner. All requested replicas must finish before reconciliation. Unique findings become leads/defeaters, and refutations contest claims independently of counts. Failed groups require explicit supersession and new groups.

## Remaining extensions

Explicit assumption/withdrawal conveniences, custom Phase 1 surface commands, richer profile policies, Linux/Windows experiment adapters, large-context pagination, and direct Taskledger ingestion remain extensions. The exported handoff contains structured requirements and traceability. These do not prevent current four-phase traversal. Real-project semantic validation is still needed.
