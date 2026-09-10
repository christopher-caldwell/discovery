# Discovery CLI — Command and State Contract v1

## 1. Purpose

Discovery is a deterministic workflow controller for high-strength model research. Models perform semantic work; the CLI owns persistence, validation, phase movement, evidence bookkeeping, artifact capture, concurrency guards, and the durable audit trail.

The CLI is designed to work beside Task Ledger and Independent Consensus Review, but neither is a runtime dependency.

The primary invariant is:

> AI evaluates meaning. Code validates state and controls progression.

## 2. Authoritative state model

SQLite relational state is the authoritative current state.

The append-only `event_log` is a tamper-evident command audit trail, not a replay-required event store. Every successful mutating CLI invocation produces exactly one audit event in the same SQLite transaction as its relational mutations.

This deliberately avoids full event sourcing. Historical state remains visible through immutable artifacts, status/supersession relationships, phase revisions, agent reports, and the hash-chained command log without requiring all current state to be reconstructed by replay.

Large or external evidence is stored outside SQLite as immutable content-addressed artifacts. SQLite stores hashes, provenance, locators, and relationships.

## 3. One database per discovery run

Each discovery run owns one SQLite database and one artifact tree.

```text
.discovery/
  runs/
    <run-uuid>/
      discovery.sqlite
      artifacts/
        sha256/
      scratch/
        agents/
        experiments/
      reports/
      exports/
```

A one-database-per-run boundary keeps IDs local, prevents unrelated runs from competing for a writer lock, simplifies backup/export, and makes a discovery package portable.

## 4. SQLite connection policy

Every CLI process configures the connection before doing application work:

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
PRAGMA busy_timeout = 5000;
```

All mutating commands use `BEGIN IMMEDIATE`.

Rationale:

- WAL permits readers while a writer is active.
- SQLite still permits only one writer, so write transactions must be short.
- `BEGIN IMMEDIATE` prevents a command from reading a state snapshot and then failing later when upgrading to a writer because another process changed the database.
- `synchronous = FULL` favors durability of the ledger over marginal write throughput.
- `busy_timeout` handles brief contention between research agents without custom lock files.

No network filesystem support is assumed for a live WAL database. A completed run can be exported/copied after checkpointing.

## 5. External identity and references

Tables retain numeric internal primary keys plus UUIDs where entities require durable external identity.

Human/model output also renders short run-local references derived from table IDs:

```text
Q-004   clarification_question
RN-003  research_need
L-008   research_lane
A-014   artifact
E-021   evidence
C-019   claim
ARG-007 argument
AR-005  agent_run
D-006   technical_decision
PO-011  proof_obligation
EXP-004 experiment
DEF-003 defeater
SPEC-02 technical_spec_revision
EVT-144 event_log
```

CLI input accepts UUIDs or short references. JSON output always includes UUIDs.

## 6. Command execution protocol

Every mutating command follows the same sequence:

1. Parse and normalize arguments.
2. Resolve the run database.
3. Configure SQLite connection policy.
4. Canonicalize the logical command input.
5. Compute `command_input_sha256`.
6. `BEGIN IMMEDIATE`.
7. Check `command_uuid` for a prior successful invocation.
8. Load current run/phase state inside the write transaction.
9. Run global and command-specific preconditions.
10. Apply all relational mutations.
11. Construct the audit payload including produced IDs and resulting state.
12. Read the current event-log head.
13. Canonicalize the audit envelope and compute its SHA-256 hash.
14. Append exactly one `event_log` row.
15. `COMMIT`.
16. Render the result.

If any step before commit fails, the relational state and audit event both roll back.

### 6.1 Idempotency

Agent/orchestrator callers supply a `command_uuid` / request ID for every mutation.

If the UUID already exists:

- same `command_name` + same `command_input_sha256`: return the recorded result as a successful replay; do not mutate state;
- different command or input hash: return `IDEMPOTENCY_CONFLICT`.

This is especially important when a process loses the command response after SQLite already committed.

One command maps to one audit event in v1. A command can mutate multiple relational rows atomically.

## 7. Event-log hash contract

The CLI computes the event hash over an RFC-8785-style canonical JSON envelope containing at least:

```json
{
  "event_schema_version": 1,
  "event_uuid": "...",
  "command_uuid": "...",
  "command_name": "claim.add",
  "command_input_sha256": "...",
  "dt_created": "...Z",
  "actor_uuid": "...",
  "session_uuid": "...",
  "phase_revision_uuid": "...",
  "event_type": "claim_added",
  "previous_event_hash": "... or null",
  "payload": {}
}
```

`event_hash = SHA256(canonical_envelope_bytes)`.

SQLite triggers enforce that:

- only one root event can exist;
- every non-root event references the current head;
- the supplied previous hash matches the current head;
- event rows cannot be updated or deleted.

`audit verify` independently recomputes the entire chain.

## 8. Artifact write protocol

Artifacts cannot be committed atomically with SQLite because they live on the filesystem. The safe order is:

1. Read/generate artifact into temporary storage.
2. Compute SHA-256 and byte size.
3. Write to the content-addressed artifact path.
4. Flush and atomically rename when a new file is required.
5. Start the SQLite transaction.
6. Insert artifact metadata and all command relationships.
7. Append command event.
8. Commit.

A crash between steps 4 and 8 can leave an unreferenced content-addressed file. This is harmless. `audit verify` reports orphan artifact files; garbage collection is explicit and never automatic.

A database row referring to a missing artifact is considered an integrity failure.

## 9. Agent isolation and leases

An `agent_run` is a logical independent investigator/reviewer.

Each run receives an immutable context artifact generated by the CLI. In overlap mode, replicas receive byte-identical starting context and cannot access sibling reports through the Discovery context commands until their own run is terminal.

### 9.1 Lease contract

`agent start` returns a random lease token. SQLite stores only its SHA-256 hash and expiration time.

Every agent-scoped mutation includes:

```text
--agent-run AR-005
--lease <token>
```

The CLI validates:

- run status is `running`;
- token hash matches;
- lease has not expired;
- entity/lane scope is permitted for that run.

Successful agent mutations extend the lease. `agent heartbeat` exists for long read-only periods.

If a session dies, a new session can reclaim the logical agent after expiry. The original context remains unchanged, preserving reviewer independence.

A failed overlap replica is not silently replaced inside the same consensus group. Starting replacement reviewers creates a new reconciliation cycle/group so requested-versus-completed coverage remains honest.

## 10. Read-only orchestration commands

These never create audit events:

```text
discovery status
discovery next
discovery resume
discovery phase check
discovery lane check <lane>
discovery claim check <claim>
discovery audit verify
discovery show <ref>
discovery list <entity>
```

`--json` produces machine-readable stdout. Human diagnostics go to stderr. Agent mode is non-interactive.

### 10.1 `resume`

Orchestrator resume returns a generated context packet containing:

- run and baseline identity;
- current phase/revision;
- accepted interpretation of intent;
- open/blocking questions;
- active assumptions;
- current research needs and lanes;
- open leads;
- canonical/admissible/contested claims;
- selected implementation strategy and decisions when applicable;
- open proof obligations / experiments;
- open defeaters;
- source drift state;
- exact current gate failures;
- allowed next commands.

`resume --agent-run AR-x --lease ...` returns only that logical investigator's immutable starting context plus its own durable work. It does not expose sibling overlap work.

## 11. Core command families

### Run and integrity

```text
run init
run abandon
status
next
resume
audit verify
audit export
```

### Sources and artifacts

```text
source add
source check
source refresh
artifact capture
artifact derive
```

### Phase 1 — intent and planning

```text
question add
question respondent-add
question answer
question assume
question withdraw
assumption add
assumption discharge
assumption invalidate
need add
need link-source
lane plan
lane link-need
lane depends-on
surface add
surface disposition
research record
plan snapshot
plan review-start
agent start
agent complete
phase check
phase advance
```

### Phase 2 — investigation

```text
lane activate
method add
method disposition
research record
research exec
lead add
lead investigate
lead irrelevant
lead duplicate
lead inaccessible
lead require-human
lead derive-lane
evidence add
evidence retract
evidence supersede
claim add
claim supersede
argument add
argument attach-evidence
argument verify
claim evaluate
agent dispatch
agent start
agent heartbeat
agent complete
consensus reconcile
lane closure-begin
lane check
lane close
need answer
phase check
phase advance
```

### Phase 3 — implementation strategy and proof

```text
strategy add
strategy select
strategy reject
decision add
decision attach-claim
decision accept
decision reject
obligation add
obligation attach-evidence
obligation satisfy
obligation fail
obligation block
obligation not-applicable
experiment plan
experiment start
experiment exec
experiment finish
spec draft
phase check
phase advance
```

### Phase 4 — adversarial refinement

```text
challenge initialize
challenge start
challenge complete
defeater add
defeater attach-claim
defeater attach-decision
defeater attach-evidence
defeater defeat
defeater confirm
defeater accept-contextual-risk
spec revise
assurance calculate
phase check
phase advance
```

### Regression

```text
phase regress --to <1|2|3> --cause <ref> --reason <text>
```

Forward movement never accepts a target argument. `phase advance` means exactly one step. At Phase 4, it means finalization.

## 12. Phase 1 gate: Intent & Scope -> Investigation

`phase advance` from Phase 1 succeeds only when all of the following hold.

### Clarification

- No blocking question is open.
- A blocking question cannot be dispositioned by assumption.
- Every non-blocking question is answered, withdrawn, or has a linked explicit active assumption.
- No active assumption has `critical` impact. A critical uncertainty must be a blocker rather than an assumption.

### Mandatory discovery surfaces

- Every mandatory Phase-1 surface has a terminal disposition.
- `searched` requires at least one linked research activity.
- `unavailable`, `inaccessible`, and `not_applicable` require a non-empty reason.
- `skipped` does not exist.

### Research plan

- Every active research need is linked to at least one lane.
- Every lane is linked to at least one research need.
- Lane dependencies form a DAG.
- Every lane has question, rationale, scope, impact, evidence profile, required methods, and required surfaces.
- No material/critical need disappears through decomposition.

### Semantic coverage review

The CLI builds a canonical Phase-1 plan context artifact. A semantic verifier must complete against that exact artifact with `run_outcome = passed`.

If any plan-affecting command runs afterward, the context hash changes and the prior review becomes stale. Phase advancement fails with `STALE_REVIEW` until the revised plan is challenged again.

## 13. Phase 2 lane lifecycle

```text
planned -> active -> procedurally_exhausted
                   -> blocked
                   -> active (reopened)
```

`superseded` is terminal.

### 13.1 Leads

Every eligible lead must end in one of:

```text
investigated
irrelevant(reason)
duplicate(of)
inaccessible(reason)
requires_human_input(question)
```

There is no skipped state.

A `requires_human_input` lead that materially affects intent may require regression to Phase 1.

### 13.2 Closure iterations

`lane closure-begin` increments `closure_iteration` and creates the configured mandatory closure methods for that iteration.

The default material/critical closure set is:

1. terminology / synonym expansion;
2. relationship and reference snowballing;
3. explicit contradiction search;
4. claim/evidence gap sweep.

If a new eligible lead is added after closure has begun, the lane becomes active and its previous closure attempt is stale. Before the lane can close, a fresh closure iteration must be completed.

`lane close` requires:

- lane is active;
- no pending lead exists;
- all mandatory surfaces are terminal;
- all mandatory primary methods are terminal;
- all mandatory closure methods in the current closure iteration are terminal;
- all material/critical claims in scope are admissible, rejected, or superseded;
- no material/critical contested claim remains;
- evidence-profile requirements are satisfied for every admissible material/critical claim;
- any unresolved unknown is explicitly represented as a question/assumption/limitation rather than silently inferred.

A lane may close with answer `UNKNOWN` if its search protocol is procedurally exhausted. If that unknown is implementation-blocking, Phase 2 still cannot advance.

## 14. Claim admissibility

Confidence values never unlock workflow transitions.

A claim is evaluated from:

```text
claim_kind + impact -> evidence profile
```

Profiles are versioned policy, resolved into the run configuration at initialization.

The CLI checks structure, not semantic truth. Semantic verification is represented by passed argument verification records.

Typical material profile requirements:

- atomic claim statement;
- at least one supporting argument;
- supporting evidence with immutable artifact provenance;
- primary/direct evidence when reasonably obtainable;
- semantic verifier passed the claim/evidence argument;
- contradiction search completed;
- independent corroboration when the profile requires it;
- no unresolved material counterevidence;
- limitations recorded.

Critical profiles additionally require explicit falsification/challenge and empirical verification when applicable.

`claim evaluate` is the only command permitted to set `claim_status = admissible`.

## 15. Overlap consensus

Consensus is an assurance signal, not a truth gate.

All requested replica `agent_run` rows are created before work begins. Their status preserves the actual requested denominator even when some fail.

Reconciliation distinguishes:

```text
support
refute
not_seen
```

`not_seen` is not a vote against a claim.

Agreement labels are descriptive only:

```text
unanimous
strong_agreement
majority
minority
isolated
```

A unique finding generates a lead for reconciliation rather than being discarded below quorum.

Any credible evidence-backed material/critical contradiction keeps the canonical claim contested regardless of vote count.

A reconciler gets a context artifact containing only terminal replica outputs. It produces canonical claim positions through CLI commands and completes with an outcome. Phase 2 cannot advance if an overlap group lacks completed reconciliation or has unresolved unique/material findings.

## 16. Phase 2 gate: Investigation -> Solution Design

Phase 2 can advance only when:

- all research needs are answered or superseded;
- all non-superseded lanes are procedurally exhausted;
- no pending lead exists;
- no blocking question exists;
- all material/critical claims are admissible, rejected, or superseded;
- no material/critical contested claim remains;
- every applicable overlap group is terminal and reconciled;
- all active source baselines report `drift_status = current`;
- `audit verify` reports no structural integrity failure.

## 17. Phase 3 experiment boundary

Source repositories are read-only by default.

Experiments may:

- read/execute source;
- run tests/builds/static analysis;
- inspect databases;
- modify explicitly declared local/sandbox databases;
- generate scratch programs/harnesses;
- invoke local services;
- create disposable copies of artifacts.

If a proof obligation truly requires source modification, the CLI may create a disposable detached Git worktree or full scratch copy pinned to the discovery baseline. Modification of the user's original working tree is never permitted by an experiment command.

Every experiment captures:

- baseline/environment identity;
- hypothesis;
- procedure;
- exact command/query inputs;
- stdout/stderr or equivalent result artifact;
- before/after snapshots where relevant;
- result status;
- limitations;
- resulting evidence.

External side effects are not considered transactionally atomic with SQLite. Experiment commands therefore use deterministic sandbox paths and explicit planned/running/terminal state so interrupted work can be inspected and recovered.

## 18. Proof obligations

Every accepted material/critical technical decision must have at least one proof obligation.

A proof obligation is satisfied only through `obligation satisfy`, after the CLI confirms it has linked evidence and/or a linked passed experiment satisfying its configured profile.

`not_applicable` requires a reason.

`failed` or `blocked` obligations prevent Phase 3 advancement.

## 19. Phase 3 gate: Solution Design -> Adversarial Refinement

Phase 3 can advance only when:

- exactly one implementation strategy is selected;
- no material/critical strategy remains ambiguously `candidate` when it represents a genuine competing option;
- every material/critical decision is accepted, rejected, or superseded;
- every accepted material/critical decision traces to at least one admissible claim or explicitly recorded assumption/constraint;
- every accepted material/critical decision has proof obligations;
- every required proof obligation is satisfied or explicitly not applicable;
- no linked experiment is planned, running, blocked, failed, or inconclusive for an accepted material/critical decision;
- source baselines are current;
- a draft technical specification has been compiled from the structured state;
- `audit verify` passes.

The Phase-3 draft is the immutable baseline challenged during Phase 4.

## 20. Phase 4 adversarial checks

Phase 4 initializes a configured checklist against the exact Phase-3 draft spec revision.

Default mandatory categories:

1. intent and acceptance-criteria alignment;
2. correctness and invariants;
3. data integrity / persistence / migration effects;
4. concurrency, transactions, ordering, and race conditions;
5. failure modes, retries, idempotency, and partial completion;
6. security and privacy;
7. integration / compatibility / dependency behavior;
8. performance, capacity, and scalability where relevant;
9. operability, observability, deployment, rollback, and recovery;
10. testability and verification feasibility;
11. maintainability / architectural fit / unnecessary complexity;
12. evidence freshness, provenance, and source drift.

Every category must be dispositioned as:

```text
completed_no_finding
completed_findings
not_applicable(reason)
unavailable(reason)
inaccessible(reason)
```

There is no skipped state.

A `completed_findings` check must create at least one linked defeater.

## 21. Defeaters and regression

A defeater challenges one or more claims and/or technical decisions and links to evidence supporting or refuting the challenge.

Statuses:

```text
open
defeated
confirmed
accepted
inconclusive
superseded
```

Rules:

- material/critical `open`, `confirmed`, or `inconclusive` defeaters block finalization;
- a confirmed material/critical defeater requires regression;
- `accepted` is allowed automatically only for contextual findings;
- accepting material/critical risk requires a human actor and explicit rationale if this capability is enabled later;
- a defeated challenge must have evidence supporting its resolution.

`phase regress` is always explicit. Defeater confirmation does not silently move the phase.

### 21.1 Regression semantics

Forward:

```text
1 -> 2 -> 3 -> 4 -> finalized
```

Backward:

```text
current -> any earlier phase
```

Regression invalidates phase-completion revisions from the target phase through the former current phase and creates a new active revision of the target phase.

Knowledge is not deleted merely because its originating phase revision was invalidated. Claims, evidence, lanes, decisions, and artifacts remain until explicitly reopened, contested, rejected, or superseded. Phase revision IDs represent creation provenance, not automatic object validity.

This prevents one bad Phase-4 assumption from erasing unrelated valid Phase-2 research.

A regression automatically supersedes all non-historical technical-spec revisions that depended on the invalidated traversal.

## 22. Phase 4 gate and finalization

Phase 4 finalizes only when:

- all mandatory adversarial checks are terminal;
- their target spec hash still matches the current Phase-3 draft baseline or current reviewed revision as required by policy;
- all material/critical defeaters are defeated or superseded;
- no confirmed/inconclusive material or critical defeater remains;
- required overlap challengers/reconciliation are complete when overlap mode is enabled;
- source baselines are current;
- the final technical spec validates all structured references;
- assurance dimensions have been calculated by code;
- `audit verify` passes.

`phase advance` at Phase 4:

1. compiles final spec;
2. calculates assurance scores;
3. marks the spec final;
4. completes Phase 4;
5. marks `discovery_run.run_status = finalized`;
6. appends the finalization audit event.

## 23. Assurance scoring

Scores are assurance indicators, not probabilities.

Default dimensions:

```text
intent
research_coverage
evidence_strength
implementation_validation
adversarial_resilience
```

Each score is deterministic from a versioned rubric stored with the run.

The overall score is the minimum dimension rather than an average:

```text
overall = min(dimensions)
```

This prevents four strong dimensions from hiding one dangerous weakness.

Scores never override phase gates.

## 24. Source drift

Each source repository baseline is explicit and immutable as historical provenance.

`source check` compares the active baseline with current repository state.

If it changed materially:

```text
drift_status = drifted
```

Phase advancement is blocked until the change is dispositioned.

`source refresh` does not rewrite the old baseline. It supersedes the old baseline row and creates a new active baseline row. Existing artifacts continue to point to the baseline under which they were captured.

The model/CLI then determine which evidence, claims, experiments, or decisions must be refreshed.

## 25. Default policy snapshot

At `run init`, the CLI resolves defaults plus repository-specific configuration into one canonical immutable policy snapshot stored with the run.

It includes at least:

```text
policy_version
schema_version
mandatory_phase1_surfaces
closure_methods_by_impact
evidence_profiles
subagent_mode
agent_count
agent_lease_duration
phase4_challenge_categories
assurance_scoring_model
experiment_safety_policy
```

A later CLI release does not silently change the rules of an in-progress run.

V1 treats the resolved run policy as immutable after Phase 1 begins. Policy mutation can be added later if real usage requires it.

## 26. Stable error contract

Machine errors use a stable envelope:

```json
{
  "ok": false,
  "error": {
    "code": "PHASE_GATE_FAILED",
    "message": "Phase 2 cannot advance.",
    "details": {
      "violations": []
    }
  }
}
```

Initial stable codes:

```text
INVALID_ARGUMENT
RUN_NOT_FOUND
RUN_NOT_ACTIVE
WRONG_PHASE
INVALID_TRANSITION
PHASE_GATE_FAILED
BLOCKING_QUESTION_OPEN
REQUIRED_SURFACE_PENDING
REQUIRED_METHOD_PENDING
RESEARCH_NEED_UNCOVERED
LANE_HAS_OPEN_LEADS
LANE_CLOSURE_STALE
CLAIM_NOT_ADMISSIBLE
ARGUMENT_NOT_VERIFIED
CONSENSUS_INCOMPLETE
PROOF_OBLIGATION_OPEN
DEFEATER_OPEN
SOURCE_DRIFT
STALE_REVIEW
AGENT_LEASE_REQUIRED
AGENT_LEASE_INVALID
AGENT_LEASE_EXPIRED
IDEMPOTENCY_CONFLICT
SQLITE_BUSY
ARTIFACT_HASH_MISMATCH
AUDIT_INTEGRITY_FAILURE
INTERNAL_ERROR
```

Exit-code families should remain coarse and stable; semantic details live in JSON error codes.

## 27. Implementation architecture

Use Python to stay compatible with the existing Task Ledger tool family and because SQLite, filesystem hashing, subprocess control, and Git orchestration are all straightforward in the standard runtime.

Keep transport, workflow policy, and infrastructure separated:

```text
src/discovery/
  cli/
    commands.py
    render.py

  application/
    commands/
    queries/
    ports.py

  domain/
    gates/
    policies/
    refs.py
    errors.py

  adapters/
    sqlite/
      connection.py
      command_store.py
      queries.py
      ddl.sql
    filesystem/
      artifacts.py
    git/
      repository.py
    shell/
      experiments.py

  services/
    context_builder.py
    audit_verifier.py
    scoring.py
```

Do not create generic CRUD repositories for every table. Persistence functions should serve application operations/gates directly. For example, `evaluate_phase_two_gate()` may issue the purpose-built queries it needs rather than forcing every query through `ClaimRepository.getAll()` abstractions.

## 28. Mutation ownership

Model-authored scratch files are temporary only.

The only supported way to create durable Discovery state is through CLI commands. This includes:

- importing an agent report;
- capturing evidence;
- recording search activity;
- adding claims;
- dispositioning surfaces;
- changing statuses;
- moving phases;
- generating final specs.

The CLI itself is the only writer to `discovery.sqlite` and the durable artifact tree.

## 29. Testing requirements before dogfooding

Minimum test suite:

### Database

- fresh schema creation;
- `PRAGMA integrity_check`;
- `PRAGMA foreign_key_check`;
- append-only trigger tests;
- event root/head/hash linkage tests;
- immutable artifact/activity tests.

### Idempotency

- duplicate successful command returns same result;
- same request UUID with different input rejects;
- simulated response loss followed by retry creates one logical mutation.

### Phase state machine

- no forward skip;
- all backwards targets allowed;
- every gate failure class tested;
- regression invalidates phase revisions without deleting evidence;
- complete 1 -> 2 -> 3 -> 4 -> finalized happy path.

### Lane fixpoint

- pending lead prevents closure;
- closure iteration completes;
- new lead invalidates closure attempt;
- second closure iteration can succeed;
- UNKNOWN answer can close procedurally but still create a blocker.

### Agents

- invalid/expired lease rejects mutations;
- reclaim after expiry;
- overlap contexts are identical;
- sibling reports unavailable to active overlap agent;
- failed reviewer remains in requested denominator;
- unique finding becomes a lead.

### Claims

- confidence alone cannot admit a claim;
- insufficient evidence fails profile;
- verified evidence can admit;
- material contradiction makes claim contested;
- `not_seen` is not counted as refute.

### Phase 3/4

- unsatisfied proof obligation blocks;
- original source tree remains unchanged after sandbox experiments;
- mandatory challenge cannot be skipped;
- confirmed material defeater blocks finalization;
- contextual accepted risk is retained in spec/score;
- stale source blocks advancement.

### Concurrency

Run multiple OS processes writing research activities/evidence against different lanes. Confirm:

- writes serialize correctly;
- readers remain available under WAL;
- no event-chain fork occurs;
- busy timeout/retry behavior is deterministic;
- no lost updates occur in gate-changing operations.

## 30. Deliberate v1 non-goals

Do not build yet:

- full event sourcing/replay projections;
- distributed/network SQLite writers;
- generalized workflow engine;
- RDF/SACM/PROV serialization;
- Bayesian probability claims;
- automatic human messaging;
- production-database mutation;
- automatic deletion of historical artifacts;
- silent auto-regression;
- model-controlled phase transitions.

These can be reconsidered only after dogfooding exposes a concrete need.
