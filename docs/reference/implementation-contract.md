# Current implementation contract — Discovery 0.2 / schema 7

This document and runtime schema 7 describe the implemented system. The
[product intent](product-intent.md) governs scope and operator experience. The
[original design package](../history/original-design/) preserves historical context. All four
phases can complete, including finalization.

## Shared agent interface

`AGENT_GUIDE.md` is the generic operating contract. `AGENTS.md`, `CLAUDE.md`, the
Cursor `.mdc` rule, and the optional `SKILL.md` are thin entry points. Detailed
references remain shared. Wheel builds include the core and references; `guide`
reads them without a run, database, provider API, or network request. Plain output
is Markdown; JSON output is the ordinary success envelope with `result.markdown`.

Only state commands require `--run`; guide/version/help do not. `run init` normalizes
an omitted `--subagents` to `disabled`, identical to an explicit disabled mode for
replay identity. Existing stored modes and gate semantics are unchanged. Actor and
request UUIDs remain required for mutations and are managed by the investigating
agent. The agent owns chat-request capture and host tool selection; the CLI does not
launch a model or claim cross-host synchronization.

## Architecture and transaction authority

The CLI parses typed inputs and renders stable JSON. Application modules implement initialization, planning, investigation, claims, sources, and phase transitions. Pure domain policies evaluate phase, lane, and claim state; adapters provide SQLite transactions, immutable artifact capture, and source fingerprints. No ORM, model SDK, generic repository API, or asynchronous framework is required.

Every new mutation uses one `BEGIN IMMEDIATE`, validates schema/integrity/idempotency/current state, applies normalized changes, and appends one event before committing. Actor creation is part of the same transaction. Failed commands, including DDL upgrades, roll back their relational mutations and event. Read queries enable `query_only` and use one SQLite snapshot.

Connections enable foreign keys, WAL, FULL synchronous behavior, recursive triggers, and a five-second busy timeout. Simultaneous WAL bootstrap additionally has a bounded five-second retry because SQLite can return BUSY without invoking the busy handler. This retries connection setup only, before command work. Transaction contention still returns `SQLITE_BUSY` after its timeout; callers retain their request UUID for retries.

Logical input and actor identity determine idempotency, with canonical key ordering and sorted/deduplicated list flags. Session UUID is attribution and can change on a retry. The original result is returned without a new event, even if current workflow state has since changed. File-based commands retain content hashes in logical input; callers must retain those input files to reproduce a request.

## Persistence, artifacts, and upgrade

Schema 7 preserves the handoff tables and schema 5/6 additions, then makes explicit assumptions, authority candidates, custom surfaces, and claim verification methods operational. It adds assumption-to-claim/decision dependencies without rewriting history. Source URI/revision uniqueness permits dirty working-tree snapshots and returns to earlier revisions to share a Git HEAD; exactly one baseline per URI remains active.

Schema 3/4/5/6 runs are not silently migrated. `run upgrade` verifies their existing audit/state, applies additive migrations under the same command transaction, then appends an event. Historical events and artifacts remain byte-identical. Policy stays frozen; its `schema_version` records initialization origin, while SQLite `user_version` reports actual schema. Upgrading a Phase 1 run can stale its plan snapshot because normalized records gain fields. Historical assumptions with no scope/invalidation condition cannot pass the current gate. Historical claims are truthfully marked verification-unavailable until `claim verification` records a method and rationale; that repair is allowed in a later phase but stales the claim, lane, and dependent work, so normal regression/revalidation is required. Finalized historical runs remain readable and immutable.

Artifacts use content-addressed bytes, file/directory fsync, and atomic rename before SQLite metadata registration. A failed command can leave an orphan, which verification reports without deleting.
For `artifact capture`, phase, scope and source validation now precede persistence
inside the command transaction; rejected validation and successful replay do not
write new artifact bytes. `research record` similarly validates phase, surface,
method scope and closure iteration before persisting its report. Later persistence/transaction failures can still leave orphans. Metadata cannot commit ahead of bytes. `artifact capture` saves an attributed snapshot; `--source-backed` additionally records the source baseline, revision, and relative file locator. The file must be inside the fingerprinted source scope and match the captured bytes under the command lock. Search and verification reports are authored reports, not automatically primary or empirical evidence.

The immutable event envelope is hash chained and includes the original result plus a checksum of normalized state and schema definitions/version. Audit verification checks all hashes/predecessors, current state/schema, foreign keys, SQLite integrity, artifact paths/hashes/sizes, and orphan files. This is tamper evidence, not event sourcing, authentication, or proof of semantic truth. A filesystem owner can replace an entire database with another internally consistent chain or backup; detecting that needs an external trusted checkpoint. Full verification on each command is deliberately conservative and may need optimization for large runs.

Canonical encoding is `python-json-sorted-utf8-v1`: UTF-8, sorted keys, compact separators, no NaN/infinities. It does not claim RFC 8785 cross-language equivalence. Actor identity is caller-attributed, not authenticated. Confidence never unlocks a gate.

## Phase 1: intent and planning

Initialization creates P1 r1 active and P2–P4 r1 pending. The immutable baseline surfaces are request, source_code, tests, documentation, issue_history, external_dependencies, and human_authority. Each current Phase 1 surface must terminate with a truthful reason; searched requires actual linked research activity.

Questions default to blocking and record authority category/confidence/rationale as hypotheses. Ranked respondent candidates retain kind, identity-known/unknown status, confidence, rationale, optional source artifact, and submitting actor. `question assume` is allowed only for an open non-blocking, non-critical uncertainty and records scope, justification, and invalidation condition. Withdrawal and reclassification preserve audit history. Resolving an assumed question requires an explicit confirms/contradicts relation. Contradiction invalidates the assumption, reopens linked claims/lanes, and returns linked accepted decisions to proposed; later gates therefore require revalidation or regression. An assumption cannot support a more consequential claim or decision, and critical decisions require an admissible critical claim. Critical or incompletely scoped active assumptions fail the gate.

The initialized Phase-1 surfaces remain mandatory minimums. `surface create` adds a request-tied mandatory planning surface with its reason. Added surfaces participate in plan hashes, gate checks, research recording, resume/export, and Phase-1 regression; they cannot replace baseline surfaces or disappear silently.

Needs trace to the request artifact. Lanes are scoped questions with rationale, impact-aligned profiles, linked needs, required methods, and required surfaces. Dependencies must form a DAG. Need/lane coverage is structurally checked. The semantic reviewer evaluates meaningful coverage against an exact canonical `plan snapshot`, submitting an immutable report through `plan review`. Plan changes stale the review. This is an attributed report import, not an independent agent run or consensus claim.

Phase 1 advancement requires all of these structures, no unresolved questions/invalid assumptions, current source, valid audit, and a passed current semantic review. The initial ticket is an assertion source; copying its bytes into another artifact does not make it factual evidence.

## Phase 2: investigation, leads, and closure

Activate each planned lane. Phase 2 may add needs, lanes, and dependencies for new technical avenues. Meaning changes require explicit regression to Phase 1. `question create --technical` records uncertainty about the answer in Phase 2; omission of that flag still rejects Phase 2 question creation. Questions can be answered in either phase.

Every lead links to an originating activity in the same lane. Terminal dispositions are investigated, irrelevant, duplicate, inaccessible, or requires_human_input, each with a reason. Investigated requires a separate same-lane research activity. Duplicates reference a terminal nonduplicate lead in that lane, preventing cyclic chains and unresolved aliasing. Material/critical human-input leads require blocking questions. There is no skipped state.

Research activities can link a surface and method in the same lane. Optional
`research record --complete-surface REASON` and `--complete-method REASON` combine
recording with searched/completed dispositions in one mutation/event. Method
completion requires an explicit same-lane method in Phase 2 and a current closure
iteration when applicable. Omitted flags preserve prior behavior and request
identity. These operations do not admit claims, close lanes or bypass plan review. Completed methods and searched surfaces require actual activities; unavailable/inaccessible/not_applicable require reasons. Current closure methods must belong to the active closure iteration. Old iterations remain historical and cannot be completed retroactively.

`research capture` is the higher-level Phase-2 path for a saved result that directly
supports one or more same-kind, same-locator observations. One transaction registers
the result artifact, activity, and explicitly classified evidence. It retains precise
provenance and idempotent replay but never creates/evaluates claims, verifies arguments,
closes lanes, or advances a phase. Like lower-level evidence creation, it invalidates
an in-progress closure; it cannot complete a closure method in the same capture.

`research finding` extends that natural action by also creating one proposed claim and
its supporting argument. It leaves argument verification and claim admission explicit,
so bundling persistence does not bundle semantic approval.

Creating a critical claim provisions one primary `falsification` method for its lane.
This makes the obligation visible before closure rather than discovering it at the
gate. `claim challenge` is the task-oriented completion path: one transaction captures
the falsification report, activity, observations, evidence, and a supporting,
refuting, or qualifying argument, and completes that method. It does not verify the
argument, evaluate or admit the claim, close the lane, or advance the phase. Replays
return the original result without duplicate records.

`lane closure-begin` requires an active lane with no pending leads and instantiates the
run policy's impact-proportional methods. Contextual lanes review evidence gaps;
material lanes add contradiction search; critical lanes add terminology and
relationship snowballing. New leads, evidence, arguments, method requirements,
dependency changes, or explicit reopen invalidate closure. Affected lanes and
transitive dependents reopen; prior answers remain rather than being erased.

Closure requires terminal surfaces/primary methods/current closure methods, no pending leads, closed dependencies, and deterministic admissibility or terminal rejection of material/critical claims. Reevaluate claims after the fresh sweep. A known material/critical answer requires an admissible same-lane claim at least as consequential as the lane. A material/critical UNKNOWN requires a linked blocking question; procedural closure may succeed while phase advancement stays blocked. When that question is answered, its linked lanes reopen to incorporate the answer.

`research-need answer` requires all covering lanes to be procedurally exhausted. Phase 2 advancement rechecks needs, lane closure, material claims and evidence profiles, questions, source freshness, and audit integrity. A successful transition enters Phase 3; no implementation strategy or final-spec result is implied.

## Claims and counterevidence

`evidence create` records a primary, secondary, or empirical classification, immutable artifact reference, locator, observation, and extraction actor. Classification remains a semantic responsibility. Claims distinguish current behavior, vendor capability, constraints, and intended behavior. Claim impact cannot be below its lane's floor in this release.

Arguments link active same-lane evidence with support, refutation, or qualification, plus reasoning and explicit limitations. `argument verify` records a passed/failed/inconclusive judgment and immutable report. Arguments are submitted with their evidence set; revised reasoning/evidence requires a new argument. Failed or inconclusive arguments remain visible.

`claim evaluate` is the only admission path. It returns status and violations; command success does not itself mean admissibility. All admissions require a passed supporting argument with active artifact-backed evidence. Material profiles additionally require primary/direct evidence and the current contradiction sweep; critical profiles add explicit falsification. Each claim selects inspection, analysis, authoritative record, test, or experiment with a rationale, availability, and limitations. An authoritative-record claim requires primary evidence; a test/experiment claim requires empirical evidence. Required but unavailable verification leaves the claim proposed. Impact cannot be lowered to evade these checks. Unsupported claims remain proposed, countered claims remain contested.

The small kind/method policy rejects obvious category errors: product intent requires
an authoritative record, while current runtime behavior cannot be established by an
authority document alone. Vendor capabilities accept authoritative records, analysis,
or empirical checks; constraints retain the broad method set because their origin
varies. This structural floor complements rather than replaces semantic review.

Every contrary or qualifying argument needs an evidenced disposition before admission, regardless of supporting argument count. `argument resolve-counter` retains the original argument and links distinct active same-lane resolution evidence with a reason. A duplicate evidence ID or copied artifact bytes cannot resolve themselves. Retraction of supporting or resolving evidence invalidates admission and closure. No vote or confidence value overrides contrary evidence.

## Source refresh and resume

The fingerprint records file contents, modes, symlink targets without following links, and Git HEAD when available. It includes untracked/ignored files except the frozen excluded directories (`.git`, `.discovery`, `.venv`, `__pycache__`, `.pytest_cache`, `.ruff_cache`), `.DS_Store`, and the run directory. Reserved paths cannot supply source-backed evidence. Filesystem-only sources use a content-derived revision. Source scans are not atomic against concurrent external edits; no final-spec freshness guarantee is claimed yet.

Status/resume/gates observe drift without rewriting baseline history. `source refresh
--reason` creates a new baseline and compares each active source-backed artifact with
its recorded locator. Matching bytes gain an explicit validation artifact linked to
the original and remain active. Changed or missing bytes retract only affected
evidence and invalidate dependent claims, lanes, answers, decisions, and spec work.
External snapshots and unrelated lanes survive. When provenance is insufficient for
precise comparison, refresh uses the conservative changed path.

Resume includes `research_activities` and `research_reports` so captured observations
and their immutable artifact paths survive a session change without relying on chat.
These are attributed research records, not admitted claims or independent corroboration.
Resume also projects normalized questions, needs, lanes, leads, claims, proof
obligations, defeaters, source observations, frozen policy, gate failures, a short list
of meaningful investigator actions, lower-level legal command families, and five
recent event headers. No event replay is used. Scoped investigator resume exposes
immutable starting context and only its own findings. Detailed records remain
available on demand. Pagination and large-context budgeting remain deferred.

## Phases 3–4 and isolated investigators

[The completion workflow](../guides/completion-workflow.md) defines the supported commands. Design gates recheck upstream research, exactly one strategy, decision/claim links, impact-preserving proof obligations, experiment results, requirement/need coverage, and an exact structured-state draft hash. Narrative is authored; relational references are validated by code. Authored prose is not automatically semantically verified.

Experiments always use a disposable copied baseline. Ordinary `local` mode is the
portable default for reviewed commands. It uses a scrubbed environment and copied
working directory but is not a security boundary; obvious arguments containing the
original source path are rejected, while commands that may reach credentials,
networks, or real services remain out of scope. The experiment subprocess may use
disposable local databases and synthetic or sanitized fixtures, but it is never
authorized to mutate a live service or live data. Read-only provider calls are made
through a separately configured read-only research provider outside the subprocess;
their returned material can then be captured as evidence. A hypothesis that requires
a live mutation is recorded as blocked. These are operating rules, not capabilities a
portable copied directory can enforce. Optional `restricted` mode uses macOS
Seatbelt with copy-only writes and no network and never falls back when requested.
Receipts preserve mode, adapter, limitations, copy changes, and before/after source
fingerprints. A changed included-source snapshot prevents a passing disposition.
Reservation and receipt registration remain separate audited transactions, and
interrupted attempts never rerun implicitly.

Phase 4 checks bind to both spec revision and phase revision. Confirmed defeaters require explicit regression before repair. Material risks cannot be accepted by vote. Resolution evidence must remain active; retracting it reopens the challenge. Finalization recompiles structured/narrative exports, rechecks both structured and adversarial snapshots under the write lock, registers deterministic assurance dimensions, and marks the run finalized in one transaction. Export materializes already committed artifacts without creating another logical mutation.

`challenge review` may apply one substantive report to multiple current checks in one
transaction. It does not weaken per-category dispositions or defeater requirements;
it removes duplicate artifact and command ceremony when the analysis is genuinely
shared.

The specification renderer owns the single top-level title in `technical-spec.md`.
If an authored narrative begins with an H1, that heading is treated as redundant and
removed from the rendered body. Machine traceability remains in the JSON artifacts;
the Markdown document remains the canonical engineer-facing result.

Investigators operate on immutable context and private finding/report rows. Lease tokens are caller-generated random secrets; only hashes enter the database or audit trail. Replicas require distinct actor identities, and scoped writes check token, expiry, actor, group, phase, and lane. This is cooperative isolation through the CLI, not authentication against a filesystem owner. All requested replicas must finish before reconciliation. Unique findings become leads/defeaters, and refutations contest claims independently of counts. Failed groups require explicit supersession and new groups.

## Remaining extensions

Large-context pagination and direct Taskledger ingestion remain extensions. Stronger
execution containment may be added only for a concrete investigation need; it is not
a product completion requirement. The exported handoff contains structured
requirements, assumptions, uncertainty, and traceability. Real-project semantic
validation remains the important next proving ground.

## Non-final investigation reports

`report export` is an audit-verified read projection available at every phase. It
materializes `report.md` and `report.json` under a content-addressed export directory,
including the request, open questions, attributed research summaries, claim statuses,
source observations and unmet gates. It does not mutate the ledger, advance phases,
finalize a spec or infer a numeric confidence score. The JSON preserves the full
structured snapshot. Artifact references still require the original run directory.
Repeated exports of unchanged state are identical; observed source drift creates a
distinct report even when the audit head is unchanged. Conflicting files and symlinks
are rejected. `spec export` continues to require a compiled specification.

`status`, `resume` and `phase check` explicitly expose interim reporting
availability separately from advancement gates. An unmet phase gate does not
prevent `report export`; the report preserves unfinished work and does not imply
verified conclusions. This is an existing export capability made discoverable,
not a separate answer-only completion state.


Schema 6 added shared finding/check associations and durable, attributed conclusion
assessments. Schema 7 adds the realignment records described above. Finalized schema
5/6 records remain readable without history rewrites.
Conclusion assessment validation checks shape, references and freshness; it does
not certify the model judgment or turn ordinal support into a probability.
