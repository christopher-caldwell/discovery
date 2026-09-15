# Implementation decisions

## 001 — Safe schema initialization (schema 3)

**Previous:** Handoff DDL v2 disables foreign keys, drops every table, then recreates the schema.

**Problem:** Executing that script against an existing run destroys history. Python `executescript` can also commit a pending transaction, breaking atomic run initialization.

**Evidence/reasoning:** Direct inspection of both DDL versions and the [Python sqlite3 transaction documentation](https://docs.python.org/3/library/sqlite3.html#transaction-control). SQLite supports transactional DDL under an explicit transaction; [BEGIN IMMEDIATE](https://www.sqlite.org/lang_transaction.html) reserves the writer before reading command state.

**Decision:** Preserve v2 table definitions, remove teardown and connection-level pragmas from the runtime DDL, execute complete SQL statements under the command transaction, keep foreign keys enabled, add one-run and immutable-policy protection, and set user_version=3.

**Compatibility:** Original files remain untouched reference material. Existing v1/v2 databases are rejected rather than modified. A future migration must explicitly establish the checksum/policy contract.

## 002 — Versioned canonical JSON

**Previous:** The contract calls the envelope “RFC-8785-style” without selecting exact numeric/Unicode serialization semantics.

**Problem:** Python's standard JSON serializer is deterministic with sorted keys but is not an RFC 8785 implementation.

**Decision:** Explicitly version Python sorted compact UTF-8 JSON, reject nonfinite numbers, and avoid an unsupported interoperability claim. Confidence is typed at the CLI boundary; scores never gate transitions.

**Compatibility:** Consumers must implement this exact encoding to reproduce v1 hashes. A future cross-language RFC 8785 switch requires a new encoding/event version, never silent rehashing.

## 003 — Check committed state as well as event hashes

**Previous:** Hash verification checks the immutable event chain, while relational state is authoritative.

**Problem:** A direct SQL edit can change operational state without modifying any event. A dropped protection trigger also leaves event hashes valid.

**Decision:** Include a checksum of all normalized tables and schema definitions/version in each committed event payload; compare the current database to the head on verification. No state replay and no full-state snapshots are introduced.

**Compatibility:** Additional payload field is permitted by the envelope contract. This is tamper evidence, not authentication or protection against complete database replacement. Full verification is intentionally conservative for milestone-sized databases.

## 004 — Complete Phase 1 support; later gates fail closed

**Previous:** The milestone lists core planning and transition commands; the target contract also requires surface evidence and a semantic plan review.

**Problem:** Exposing advance with only questions/lanes would either make 1 → 2 impossible or omit mandatory gates. Implementing all later phases would exceed the requested thin slice.

**Decision:** Add minimal surface dispositions, immutable research reports/activities, plan snapshots, and synchronous attributed semantic-review import. Implement the actual Phase 1 gate. Later phases explicitly return PHASE_NOT_IMPLEMENTED. Leased/subagent execution, assumption commands, claim admissibility, experiments, and finalization remain unavailable.

**Compatibility:** Subagent mode must be explicitly selected; only disabled succeeds. Imported semantic reviews do not claim isolation or independent verification. Future agent commands must enforce leases before any agent-scoped write is exposed.

## 005 — Explicit baseline surfaces and conservative drift

**Previous:** Mandatory surfaces and baseline drift are required, but the baseline surface list and dirty/untracked working-tree semantics were unspecified.

**Decision:** Freeze seven Phase 1 surface categories in policy. Capture request bytes separately from a source fingerprint that includes files, executable modes, symlinks, and Git HEAD when available. Ignore explicitly reserved generated paths. Compare the source at status/gate time; block on drift until refresh is implemented.

**Compatibility:** Defaults are immutable for an initialized run. Custom policy/surface expansion and targeted refresh need later commands. Source scans are not atomic against concurrent external edits.

## 006 — Regression includes pre-created pending revisions

**Previous:** The contract describes invalidating completed traversal revisions through the former current phase, while the request's example creates new later pending revisions.

**Problem:** Initialization pre-creates all four revisions. Leaving old pending rows would produce ambiguous next revisions after regression.

**Decision:** Invalidate the current traversal from the target through phase 4, then create one new revision per affected phase. Preserve earlier phases and knowledge rows; refresh Phase 1 surfaces when returning to intent.

**Compatibility:** This realizes the user's pending-revision example and avoids automatic knowledge invalidation. Historical revision numbers remain monotonic and never reused.


## 007 — Phase 2 schema migration and frozen policy

Release 0.2 adds schema 4 with closure attempts, lane/need answers, counterargument resolution, and verification artifacts. Existing schema-3 runs require explicit `run upgrade`. Migration and its audit event share the command transaction; old events and frozen run policy remain unchanged. Fresh runs use the Phase 2 policy. The handoff SQL remains preserved as design history.

## 008 — Evidence and answer gates

Claims require active artifact-backed evidence with provenance, passed supporting arguments, and impact-specific closure methods. Material claims need primary or empirical evidence; critical claims additionally need empirical verification and falsification. These are procedural checks: the model remains responsible for semantic relevance and truthful interpretation. Request assertions, including byte-identical recaptures, cannot become evidence. Known material lane answers require admissible same-lane claims. Material UNKNOWN answers require blocking human questions; this also applies to research-need answers and UNKNOWN-prefixed explanatory text.

Counterarguments remain visible regardless of supporting-argument count. Resolution requires distinct evidence and a reason. Retraction reopens the counterargument for fresh resolution, invalidates affected claims, and reopens dependent lanes. Earlier dispositions remain in the audit history.

## 009 — Source refresh and closure freshness

Source refresh conservatively retracts all evidence backed by the previous repository baseline while preserving external evidence. Multiple baselines may share a Git revision because dirty trees and return visits are valid; only one baseline per URI may be active. New evidence, leads, dependency changes, and relevant question answers invalidate closure. Closure retries create new method records rather than overwrite historical attempts.

## 010 — Bounded WAL initialization retry

Concurrent first-time connections can receive SQLITE_BUSY from WAL setup despite a busy timeout. SQLite documents that the [busy handler may be bypassed to avoid deadlock](https://www.sqlite.org/c3ref/busy_handler.html). Initialization now retries only WAL setup within a bounded deadline, preserving the configured timeout afterward. Logical mutations retain their existing transaction and idempotency behavior.


## 011 — Complete traversal without a release-number bump

The user requested continued development without ceremonial version bumps. The
base release remains 0.2.0. Schema 5 adds structured requirements, draft freshness,
experiment receipts, resolution provenance, and investigator groups/findings.
Schema 3/4 upgrades are explicit transactional migrations preserving historical
policy and events. New specs identify the structural-coverage-v1 rubric and store
its full score details; historical runs retain their initialization policy origin.

## 012 — Experiment reservation and offline execution

The handoff calls for short command transactions and recoverable external effects.
A subprocess cannot share SQLite atomicity. `experiment.exec` therefore reserves
one attempt, executes outside the write transaction, and uses a deterministic
second request to register its receipt. These are two named audited mutations.
A missing receipt is interrupted/unknown, never implicit permission to rerun.
Explicit abort/replacement retains failures and resets linked proof obligations.

The first executor uses the host's macOS Seatbelt facility: default deny,
filesystem reads, writes only within a copied baseline, and no networking. It has
no unsandboxed fallback and rejects symlink-bearing copies. It does not provide
credential-read isolation. Runtime testing showed that narrower read allowlists
could abort the system Python launcher; allowing reads preserves the required
source-write boundary while supporting installed runtimes. Other OS adapters are
future extensions. The macOS sandbox facility is deprecated as an application
API; the adapter is isolated for replacement. Runtime probes test actual behavior.
[Apple's sandbox overview](https://developer.apple.com/library/archive/documentation/Security/Conceptual/AppSandboxDesignGuide/AboutAppSandbox/AboutAppSandbox.html)
describes OS-level restrictions; [Python's subprocess documentation](https://docs.python.org/3/library/subprocess.html)
documents process sessions, timeouts, and execution mechanics.

## 013 — Isolated findings and caller-owned lease secrets

Rather than expose mutable canonical rows to workers, investigators submit private
finding/report rows against immutable context. All requested replicas are created
up front, and all must finish before import/reconciliation. Imported refutations
contest claims and every substantive unique finding creates follow-up work.
Failed groups need explicit replacement, preserving the requested denominator.

The caller supplies a fresh random lease secret; only its hash enters relational
state or audit payloads. This avoids persisting a generated token inside the
idempotent result/event envelope. Expiry, actor, phase/group, and lane checks apply
to scoped writes; reclaim rotates the token. Distinct actors are required for
replicas. This is cooperative context isolation, not filesystem-owner security or
identity authentication. CLI orchestration is implemented; model spawning remains
with the assistant and its available agent tools.

## 014 — Structured finalization and adversarial freshness

Drafts combine authored narrative with structured requirements and complete
backward traceability. Structured-state edits stale drafts; revised drafts require
fresh adversarial checks. Finalization compares both design and adversarial
snapshots under its write transaction so a concurrently changed review cannot
produce a stale final artifact. Material defeaters cannot be accepted by majority;
confirmation requires regression before evidenced repair. Retraction reopens a
previously defeated challenge.

Assurance values measure procedural coverage, not truth probabilities. Overall
assurance is the minimum dimension; unavailable/N/A work reduces demonstrated
coverage. No score bypasses a gate. Exports materialize committed immutable
artifacts and refuse conflicting files; they do not submit tasks to another tool.


## 015 — Bounded capture and actual controller-crash recovery

Experiment capture uses separate bounded pipe buffers instead of log files inside
the source copy. This preserves project files named stdout.log/stderr.log and
prevents unbounded capture files. Exceeding either stream's 2,000,000-byte limit
stops the original process group and prevents a passed result. This is not a disk
quota for program-created files or guaranteed cleanup of detached sessions.

A real SIGKILL test now interrupts the CLI after its child starts. Retrying the
same request preserves the single execution and reports interruption. Controller
death can leave the child running, so recovery instructions require inspection
and cleanup before abort/replacement. No release or schema bump is needed.


## 016 — File-based experiment input and evidence review guidance

The full evaluation lost attempts to inline quoting and accepted inadequate
assertions as proof. `experiment exec --command-file` reads UTF-8 JSON argv before
reservation; the resolved bytes retain normal request identity and receipt
capture. Existing inline commands remain compatible. A skill helper prepares
readable Python probes without executing them or overwriting project filenames.

The skill now asks reviewers to map claims to actual assertions/observations and
record category-specific adversarial work. These are semantic review guidance,
not a purported automatic proof checker or new schema gate. No release/schema
bump is required for this additive input path.


## 017 — Child-only signalling discovered by real test-runner execution

The full Boilerman experiment returned exit 0 and 41 passing tests, but its nested
Vitest stderr reported EPERM and a timeout terminating the fork worker. The outer
process's success did not establish clean runtime behavior. The sandbox now adds
`(allow signal (target children))`, following the restricted rule also present in
the host's Apple-provided `/System/Library/Sandbox/Profiles/darwin-container-base.sb`
and `com.apple.WindowServer.sb`. It does not grant unrestricted signal permission.

Actual subprocess tests verify own-child termination and denial of signalling an
unrelated test-owned process. Existing network/write-boundary tests still pass.
New receipts include the exact `sandbox_profile` so policy changes remain visible
while release 0.2.0 is still being developed. A repeated real Boilerman experiment
then ran 41 tests without worker-cleanup stderr. The earlier receipt is retained
and classified inconclusive, rather than rewritten as success.


## 018 — Non-final reports and capture validation from request-vetting runs

Two Taskledger cases produced useful research but could not export through the
final-spec path. `report export` now materializes an explicitly non-final audited
snapshot and readable summary without relaxing any gate or inventing confidence.
Research observations remain attributed reports; formal claim statuses remain
visible. The report includes need answers, artifact links and orphan diagnostics.

Repeated Phase 1 capture mistakes created seven orphan files. Artifact capture now
retains input bytes in memory for identity, then validates phase/scope/source inside
the transaction before persisting them. Replay still returns its original result
even after regression. Other artifact-producing commands and late commit failures
can still create orphans; the change does not claim universal orphan prevention.

The simple case also exposed workflow cost and an absent answer-only completion
route. Those need further evaluation, not an untested relaxation of evidence gates.
Base version and schema remain unchanged.


## 019 — Reduce research bookkeeping while preserving proof gates

The Taskledger evaluation used separate mutations to record searches and mark the
same work completed. `research record` now accepts explicit surface/method completion
reasons and applies those linked updates atomically with the activity. Method scope,
active closure checks, claim admission and phase gates remain unchanged. Report
bytes are persisted only after validating the activity target. Omitted flags retain
the previous logical request shape for replay compatibility.

Resume now exposes attributed research activities and their artifact metadata. It
does not promote a rich Phase 1 narrative into formally evaluated claims. The skill
now checks governing product contracts alongside implementation, separates intended
and observed behavior, and defers detailed design when owner decisions control it.
These semantic checks remain attributed model work, not a keyword-based code gate.

A deterministic replay of the simple evaluation used 31 rather than 35 CLI calls
with the same unfinished research status. It is not evidence of a cold-model speedup
or a calibrated confidence score. No release/schema increment is needed.

## 020 — Product realignment and schema 7

The original contract included explicit assumptions, ranked respondent hypotheses,
and investigator-added Phase-1 surfaces, but the operating path never exposed them.
Schema 7 activates those existing concepts and adds scoped invalidation conditions,
attributed authority candidates, and dependency links from assumptions to claims and
decisions. Invalidating an assumption makes linked claims/lanes and accepted decisions
stale; it never deletes history or silently regresses a phase.
Assumption impact must meet the impact of every linked conclusion, and a critical
decision requires an admissible critical claim. Resolving an assumed question now
requires the caller to declare confirmation or contradiction; contradiction applies
the dependent-invalidation path in the same transaction.

Claim admission no longer derives every verification requirement from impact alone.
Impact retains evidence and challenge floors. The investigator also selects a narrow
verification method—inspection, analysis, authoritative record, test, or experiment—
and records why it applies and whether it is available. Authoritative records require
primary evidence; tests and experiments require empirical evidence. Critical claims
still require falsification, but an intent claim is not forced through an irrelevant
runtime experiment.

The method vocabulary follows NASA's
[product-verification guidance](https://www.nasa.gov/reference/5-3-product-verification/),
which separates analysis, inspection, demonstration, and test. The CLI records and
checks the chosen category; an attributed reviewer still owns semantic applicability.

`research capture` bundles one saved result, its activity, and explicitly classified
observations in one transaction. It does not create/admit claims, verify arguments,
complete closure, or advance a phase. New captured evidence invalidates an active
closure sweep, matching lower-level evidence creation. Lower-level commands remain
available.

Restricted experiments retain macOS Seatbelt and never fall back. Trusted-local is a
separate explicit macOS/Linux mode for reviewed commands in disposable copies. Its
receipt says that no OS security boundary is enforced and records post-run source
comparison with its exclusions and detection limitations. It also attests the host
platform and adapter and rejects unsupported operating systems. This improves
portability without claiming a copied directory is a sandbox. A hardened Linux
sandbox and Windows execution remain outside this pass.

Python's [subprocess documentation](https://docs.python.org/3/library/subprocess.html)
defines execution controls such as working directory and environment; those controls
are not represented here as confinement. Likewise, a Git
[linked worktree](https://git-scm.com/docs/git-worktree) shares repository state, so
worktree structure alone would not establish an isolation boundary.

Compatibility is explicit: active schema 3–6 runs upgrade transactionally; finalized
schema 5/6 runs remain readable and immutable. Migrated claim verification is marked
unavailable rather than inventing a method result, and old unscoped assumptions block
until repaired. Release remains 0.2.0 because this is continued development, not a
release-numbering exercise.

## 021 — Restore the investigator as the primary product experience

The current [product intent](product-intent.md) makes the boundary explicit: the model
owns meaning and the CLI preserves consequential guardrails. Existing normalized
state, artifacts, idempotency, audit history, four phases, regression, evidence graphs,
and investigator reconciliation remain because they support durable trust.

The ordinary workflow now hides avoidable bookkeeping. `plan review` binds to the
current snapshot without requiring a copied hash. `research finding` can atomically
record one result, its observations, a proposed claim, and its supporting argument,
while leaving semantic verification and admission explicit. Closure methods scale
with consequence rather than imposing four identical sweeps on every lane.

Source refresh revalidates unchanged source-backed artifacts by exact locator and
content hash and retracts only changed or missing dependencies. The final technical
specification no longer embeds raw state JSON; exact records remain in the machine
handoff and evidence manifest.

Ordinary experiments now default to portable local execution in a disposable copy.
The macOS Seatbelt adapter remains an optional `restricted` mode and never falls back.
Discovery does not make a cross-platform security sandbox part of its product
completion standard.

## 022 — Make critical challenges planned work and protect the final artifact

Critical claims now provision their lane's primary falsification method when created.
Older active runs receive the same obligation before closure begins. A generic search
activity cannot satisfy it: each critical claim requires a falsification activity whose
captured evidence is linked to an argument about that exact claim.

`claim challenge` is the ordinary investigator-facing operation for this work. It
atomically records the saved report, activity, observations, evidence, argument, and
method completion, while leaving argument verification, claim evaluation, lane closure,
and phase advancement explicit. This removes ID-oriented wiring without combining
semantic judgments or weakening replay and audit guarantees.

The specification renderer now owns exactly one top-level title. A leading authored H1
is removed from the rendered body, while the authored narrative remains preserved as
its immutable source artifact. This keeps the engineer-facing specification polished
without altering machine traceability.

Experiment policy uses “sandbox” in the practical product sense: work happens in a
disposable project/state copy, including disposable local databases. This is not a
claim of universal process confinement. Experiment subprocesses are not authorized to
mutate live services or use production credentials. Explicitly read-only provider
research remains outside the subprocess and may be captured as evidence; a hypothesis
that requires a live mutation is blocked until a safe fixture exists.
