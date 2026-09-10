# Phase 4 retry with a controlled experiment handoff

The earlier feature run stopped in Phase 3 because macOS rejected applying
Discovery's experiment sandbox inside the evaluator's model sandbox. The main
Codex session already had full access; changing user approval settings would not
remove that independently applied restriction. The user authorized an external
experiment runner while preserving isolation from prior answers.

## Execution boundary

`scripts/evaluation/run_experiment.py` is a driver-only, synchronous handoff. It is
not a daemon or an unrestricted execution service exposed to the model. The
operator session must finish and its temporary credentials must be removed before
the evaluator reviews and executes a specific request. No concurrent operator is
supported during this handoff. The session's saved manifest fixes the selected
ledger, source and original ticket; the runner validates their relationship and
the ledger audit. It rejects symlinks in the selected run before reservation,
source copying or artifact writes. This prevents a stopped operator from leaving
redirected scratch/artifact paths for the outside driver to follow.

The runner calls Discovery's existing experiment application operation. The
operation still reserves execution, copies the source, executes the sandbox and
registers an immutable receipt in audited transactions. A new dependency-injection
parameter lets this caller narrow the process adapter's reads. The normal CLI
continues to use its existing adapter and documented broad-read behavior.

For the handoff, the child can read system runtime roots and its disposable source
copy, write only the copy, and cannot access the network or Mach service lookups.
It cannot read the selected ledger, previous logs, evaluator answers or Codex
credentials. The parent needs ordinary access to the selected ledger to register
results, but never runs the requested probe without the sandbox. An OS failure
remains a failure; there is no unsandboxed fallback.

The regression checks exercise actual SQLite work while denying private-file reads,
directory enumeration, symlink/child-process reads, original-source writes and
network access. Separate tests reject redirected scratch and artifact parents. An
independent code review caught the parent-symlink issue before the actual handoff;
checking only the child working directory would have been too late.

Filesystem fixtures retain their original identity: the driver sets Git's ceiling
at the source parent so visibility of the enclosing evaluator checkout does not
turn an unchanged filesystem fixture into a different Git baseline. This does not
rewrite the ledger or refresh evidence. The environment change is local to the
runner and restored afterward.

## Driver invocation

After a completed isolated session, a reviewed JSON request contains exactly
`request_id`, `actor` (`uuid`, `name`, `kind: model`), `session_id`, `ref`, `command`
(a JSON argv array), and `timeout`. Generate IDs for new work; retain the request
unchanged if recovering its result. The Discovery operation owns replay semantics.

```sh
python3 scripts/evaluation/run_experiment.py \
  --operator-session /absolute/path/to/completed/session \
  --request-file /absolute/path/to/reviewed-experiment-request.json
```

This is an explicit evaluator handoff, not an automatic model-driven four-phase
run. A future automatic dispatcher would need its own authorization, request
validation, concurrency and boundary review; this helper does not provide one.

## Proposal repair and recorded proof

The evaluator authored the repair with full knowledge of the earlier review. A
low-strength fixture author prepared a disposable prototype; it is not a patch to
the target. The new strategy uses targeted composite-key UPSERT, an explicit SQLite
>=3.24 prerequisite, rollback on transaction failure and retirement after cleanup
failure. ST-001/D-001 were rejected; their failed proofs remain historical. New
strategy ST-002/D-002 has its own requirements and proof obligations.

EXP-002/A-040 passed eight cases. Inspection then identified a scope improvement:
that prototype defined an equivalent Receipt type instead of importing the source
type. EXP-003/A-041 passed the strengthened version, with the actual Receipt type
and unchanged DeliveryService. The initial passing receipt remains valid for its
narrower scope; the later experiment supplies the current proof. An attempted
`experiment replace` was rejected because replacement is for failed terminal
attempts, so the added experiment remains a distinct successful test rather than
rewriting its predecessor.

The eight cases cover payload/tenant/reopen behavior, caller injection, associated
concurrent winner payload, trigger/NOT NULL failure classification, a real
reader-lock-induced SQLITE_BUSY at commit with rollback and independent visibility
checks, simulated rollback/close failure retirement, unopenable paths and lifecycle
errors. Both receipts had exit zero, no timeout and no output truncation. They
prove specific local prototype assertions, not deployment universality, production
throughput or crash/power-loss guarantees.

Phase 3's normal gate passed after acceptance and a substantive draft. The run
entered Phase 4 with audit head 124 and no audit failures. A read-only SQLite backup
plus referenced immutable artifacts preserves the exact Phase 4 entry checkpoint.
No target-source file was changed.

## Fresh Phase 4 observation

`phase4-review-1` receives only the selected durable state, source and ticket in a
fresh isolated process. Prior conversations, loose outcomes and evaluator material
remain denied. It reviews twelve configured categories against the exact draft.
Its predeclared bound is 600 seconds / 90 CLI invocations, reserving the last minute
for delivery. It may finalize only if the evidence withstands the review; a material
defeater requires normal regression. New experiments require another stopped-session
handoff. This is an independent review of an informed repair, not a cold repeat.

Raw requests, receipts, operator manifests and results remain under
`.discovery/scenario-campaign/`. The informed fixtures and driver logs are under
`evaluator/phase4-retry-fixtures/`; the fresh review is under
`sessions/phase4-review-1/`. The completed first-review outcome follows.


## First Phase 4 result: a material finding and real regression

The fresh reviewer finished in 514.818 seconds. All twelve categories received
substantive reports. It confirmed one root schema defect: `IF NOT EXISTS` accepts
an existing NOCASE key and can violate exact tenant identity. It distinguished
this static conditional counterexample from an executed failure. It preserved the
valid scope of the eight passing tests rather than treating their coverage gap as
proof that those executions failed.

The CLI required separate per-category finding links, so the reviewer created
DEF-001 through DEF-007, explicitly labeling six as category projections of the
same defect. They are one issue, not seven confirmations. This is a concrete
workflow/data-shape concern for subsequent tuning: cross-category relevance should
not require duplicating the canonical defect. No quorum inference is justified.

The reviewer confirmed those records, regressed to Phase 3 revision 2, failed the
overstated tenant-preservation proof, and planned EXP-004 with a new blocked proof
obligation. Its scoped reports and request remain captured; it neither implemented
a target change nor attempted another nested sandbox. This is the first fresh
model observation in this campaign of an actual Phase 4-to-3 transition caused by
a semantic defect. The repair and forward retraversal are recorded below.

Session usage was 2,167,363 cumulative input tokens (2,068,352 cached) and 14,542
output tokens. These are session counters, not newly generated token counts.


## Revised schema proposal and forward retraversal

A low-strength fixture author extended the disposable prototype. Root inspection
strengthened the constructor/close double-fault test to inspect the actual failed
instance and verify that later calls reject its retired connection; an assignment
that never returned would not have proved handle retirement. EXP-004/A-062 then
ran 19 named cases successfully under the restricted runner, without timeout or
truncation. Eight cases rerun the prior behavioral suite against the revised facade;
eleven cover schema compatibility, exact-case keys, concurrent initialization,
missing reads/count after reopen, and additional runtime/error branches.

D-003 explicitly proposes a dedicated SQLite file and schema validation under an
initialization transaction. It rejects incompatible declarations and additional
noninternal objects, and rolls back rejected logical changes. Tests cover the
reviewer's NOCASE example and preserve its schema/rows. The narrative distinguishes
logical preservation from byte-identical files, simulated version checks from old
runtime execution, and deliberate fault injection from supported external mutation.
The dedicated-file boundary is a proposal, not an invented requester fact.

The evaluator repaired the proof obligations and resolved the seven category
records using the new empirical evidence. It retained the original valid finding
and superseded draft. SPEC-002 passed the normal Phase 3 gate and entered Phase 4
revision 2. `phase4-review-2` is a fresh isolated reviewer of that exact new draft;
it has no previous conversation or loose outcome, but can inspect selected durable
history as intended by session recovery.

Two additional source-flow frictions surfaced while recording the repair:

- A real experiment receipt could not be registered directly as empirical evidence
  because its `origin_uri` was absent. The evaluator recaptured its exact immutable
  bytes with the original receipt-file URI (A-064/E-012), explicitly identifying it
  as the same execution rather than independent corroboration.
- Reattaching an already-linked experiment returned a raw database UNIQUE error.
  The existing link was preserved; the evaluator resumed without another attachment.

These are operation-level observations, independent of whether the proposal passes
review. The generated second draft is about 145 KB including structured history;
its usefulness and retrieval cost should not be inferred from gate completion.


## Source changes motivated by the handoff

The evidence registry now accepts a receipt without a separate origin URI only
when it is an `experiment_result` tied to a registered execution. A kind label
alone is insufficient. Failed executions can provide empirical observations;
accepting their provenance does not establish that a proposed claim is true.
Existing request-assertion and copied-request protections remain enforced. This
also supports old registered receipts without changing schema or rewriting them.

Repeated evidence/experiment attachments now succeed without changing the existing
obligation status, explanation or timestamp. Scope and active-evidence checks still
run first. New attachments still invalidate the prior proof disposition. Ten
focused tests cover genuine and forged receipt associations, failed execution
observations, repeated requests/links, full state preservation and invalid scope.
The isolated second reviewer runs a frozen copy from before these two changes;
its outcome therefore does not measure their effect on model behavior.


## Second Phase 4 result: filename interpretation

`phase4-review-2` completed all twelve categories in 472.012 seconds and found a
new material boundary error. Passing `Path("./:memory:")` directly to SQLite loses
the dot prefix and selects its private in-memory database. The proposal claimed
local-file persistence but did not constrain or normalize this input. Schema
validation does not prove that the database is backed by the requested disk file.
The reviewer separated this static deduction from the valid 19-test receipt and
from the repaired NOCASE issue. Eight category records (DEF-008–DEF-015) represent
one root filename issue. It regressed to Phase 3 revision 3 and requested EXP-005.

The disposable repair anchors Path inputs to absolute filesystem names and retains
SQLite's uri=False semantics. EXP-005/A-092 executed 25 tests: one explicitly
reproduced the old data-loss/private-database behavior, and the revised cases
preserved disk-backed special filenames while retaining the earlier 19 assertions.
Root inspection corrected a fixture count expectation where relative and absolute
names intentionally addressed the same file. That correction occurred before
execution and is not an observed failed experiment.

A follow-up EXP-006 strengthens the path matrix to check original payload, reopen
and independent-handle duplicate behavior for every sampled accepted path. The
first passing execution remains recorded with its narrower coverage. This is
additional proof work, not replacement of a failed receipt. The scope remains a
proposed optional backend; no target-source implementation was performed.

Second-session counters: 1,282,614 cumulative input tokens (1,198,848 cached),
13,064 output tokens. The first two reviews' runtime and repeated context reads
remain a proportionality concern even though each produced a concrete finding.


## Current stopping point and rendering repair

EXP-006/A-094 passed 27 tests, including the full accepted-path matrix. D-004 and its
empirical proof extend the proposal with explicit Path-only absolute filesystem
semantics. The evaluator resolved the filename finding by repair, retained the
valid old counterexample, and passed the normal gate into Phase 4 revision 3 with
SPEC-003. E-014 was registered directly from A-094 using the new receipt-provenance
support; no recapture was needed.

The third independent session, `phase4-review-3`, stopped after 106.852 seconds with
an account usage-limit error. It did not finish a review or deliver an outcome.
No usage counters were returned. All twelve categories for the newest draft remain
incomplete. **The run is active in Phase 4; it is not finalized.** No further model
retry or usage-credit redemption was attempted. An evaluator-authored interruption
note is kept separately in the session control directory.

All three sessions preserved selected source/ticket and frozen runtime/skill hashes;
all temporary auth files were removed. Their final audits were valid with no orphan
artifacts: 160 events after review 1, 227 after review 2, and 259 after review 3.
Raw state is sufficient for a fresh selected-ledger continuation when model capacity
is available. The exact pending draft can be exported with `spec export`; its
bundle is under `run/exports/3a6e7e7d-01ce-4b9f-926e-7029e800196d/`.

Independent output inspection found that 157 KB (about 60%) of the 260 KB Markdown draft
consisted of embedded historical experiment commands. The requirements section also
presented rejected D-001 requirements beside current ones without status labels.
The Markdown renderer now summarizes execution payloads with receipt references and
links to the full handoff/manifest, and groups requirements by decision status.
Missing receipts are explicitly distinguished from successful execution. The
structured handoff, manifest, structure hash and review hash remain unchanged.

A controlled comparison rendered the same snapshot and narrative using the old and
new code in evaluator-only directories. Markdown decreased from 260,089 to 101,902 bytes
(60.8%); handoff and manifest bytes/hashes were identical, as were structure/review
hashes. This is a rendering measurement, not a demonstrated reduction in model token
usage or proof of document usability. The exact pending draft was not rewritten;
the new rendering preview is separate from the independent review target.
Comparison data is retained under `evaluator/spec-render-comparison/`. The two
rendering regressions also verify rejected-history labeling, missing receipts,
retained exact commands and command-sensitive structure hashes.

Remaining process work includes cross-category canonical findings without duplicate
defect records, numeric conclusion-confidence semantics, proportional investigation
cost, and a completed independent review of SPEC-003. This campaign supplies
concrete findings and repairs, not a claim that every scenario is proven.


## Verification of source changes

The final combined project and evaluation-harness suite passed **129 tests**.
Ruff lint and formatting checks passed. Version remains 0.2.0 and schema remains 5.
Raw evaluator fixtures, logs and ledgers are not committed; source, regression tests
and this analysis are retained in the repository. The pending independent review
can resume from the selected run without replaying either earlier model session.
