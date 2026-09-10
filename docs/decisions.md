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
