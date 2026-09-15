# Design, experiments, adversarial review, and finalization

Global identity/request flags precede each mutation. Read commands need only
`--run` and `--json`. The release remains 0.2.0 during iteration; the current
storage format is schema 7. Active schema 3/4/5/6 runs use explicit `run upgrade`; finalized schema 5/6 runs remain readable.

## Phase 3

1. Propose alternatives with `strategy create --name ... --description ...`.
   Select exactly one with `strategy select ST-001 --reason ...`; reject competing
   candidates explicitly. Replacing a selection requires rejecting it first.
2. Create decisions with `decision create --strategy ST-001 --claim C-001
   --text ... --rationale ... --impact material`. Repeat `--claim` for multiple
   admissible dependencies. Accept/reject each decision with a reason.
3. Add `obligation create --decision D-001 --text ... --impact material --profile
   primary`. Profiles are `primary` and `empirical`; choose the profile based on the
   obligation being proved rather than impact alone. Attach active evidence with `obligation attach-evidence`,
   or a same-decision experiment with `obligation attach-experiment`.
4. Use `obligation satisfy --reason ...` only after evaluating its evidence.
   The CLI checks support. `fail`, `block`, and `not-applicable` preserve explicit
   dispositions; a reason is mandatory. Critical decisions cannot lower their
   proof impact. Unproven and failed obligations block advancement.
5. Create requirements with `requirement create --decision D-001 --need RN-001
   --text ... --acceptance ... --verification ...`. Every answered need and
   accepted decision must be represented. Old rejected alternatives remain
   historical in the structured record.
6. Write an authored technical narrative, then `spec draft --narrative FILE`.
   This compiles structured requirements and backward traceability into immutable
   artifacts. Structured edits stale the draft. `phase advance` enters Phase 4
   only after the design/proof and upstream gates pass.

## Experiments

`experiment plan --decision D-001 --name ... --hypothesis ... --procedure ...`
creates a planned attempt. `experiment exec EXP-001 --command
'["/usr/bin/python3","-c","print(123)"]' --timeout 60` reserves it, copies the
current source into a deterministic scratch directory, executes the exact argv,
and registers a result artifact. No shell is implicit. The copy includes the
baseline's dirty/untracked files and excludes its frozen generated directories.
Symlink targets are materialized inside the disposable tree so common package-manager
links remain usable without retaining a path back to the original project.

Use `--command-file /absolute/command.json` instead of `--command` for multiline
probes. The UTF-8 file contains a JSON argv array; exactly one input is required.
The CLI reads it before reservation and captures the resolved command in its
receipt. Retain the file unchanged for retries; changed input with the same request
is an idempotency conflict. The filename itself is not part of logical identity.
Missing files fail before reservation; malformed JSON, empty executable names,
NUL arguments and invalid UTF-8 are rejected before an attempt starts.

The skill's `scripts/prepare_experiment.py --script probe.py --output command.json`
embeds a readable Python script into argv without shell interpolation. It only
prepares the command file. The eventual sandbox loader preserves cwd, writes the
script under its original basename with exclusive creation, and runs it with
`runpy`; child imports can use the same module. An existing filename is never
overwritten. For scripts already in the source baseline, use ordinary argv
pointing to their relative path instead.

The default executor runs a reviewed command in a disposable copy with a scrubbed
environment. It is the ordinary, platform-neutral path. It does not prevent external
effects, so never use it for untrusted code, production writes, or commands likely to
contact mutation-capable live services. Use disposable local databases and synthetic
or sanitized data only. Production credentials are never an experiment input. A model
may query an explicitly read-only provider outside the subprocess and capture that
result as research evidence; it must not use the experiment runner for live mutations.
Arguments containing the original source path are rejected and source drift is checked
afterward, but those are guardrails rather than confinement. If a safe test environment
does not exist, finish the attempt as blocked and record what is needed.

`--execution-mode restricted` requests the retained macOS Seatbelt adapter. It limits
writes to the copy, denies networking, and never falls back if unavailable. Use it
when an investigation specifically benefits from that stronger local boundary, not
as a prerequisite for ordinary Discovery work.

A result records command, environment, source identity, the exact execution policy
(`sandbox_profile` on new receipts), before/after tree hashes,
stdout/stderr, exit code, timeout, and execution times. Capture uses bounded
pipes, preserving existing project log files. Exceeding 2,000,000 bytes on either
stream stops the process group and records `output_limited: true`, explicit
truncation, and an unsuccessful exit. This bounds captured output, not files the
command itself writes inside the copy. Produced files remain in the scratch copy; capture any additional
output needed as evidence explicitly. `ok:true` means the CLI recorded the result;
inspect `exit_code` before interpreting the experiment.

`experiment finish --outcome passed|failed|inconclusive|blocked --conclusion ...
--limitations ...` records the semantic judgment. A nonzero exit cannot pass.
A zero exit alone never satisfies a proof obligation.

Execution spans two short audited transactions: `experiment.exec` reserves the
attempt; `experiment.record` stores the receipt. The process runs between them.
Retry the exact original request to register an existing receipt; it never
reruns the process. A reservation without a receipt returns
`EXPERIMENT_INTERRUPTED`. Killing the controller can leave its child running;
inspect the scratch directory and stop any surviving attempt before using
`experiment abort`,
plan a new attempt, then `experiment replace --replacement EXP-... --reason ...`.
The old attempt remains historical. Linked obligations return to pending.

## Phase 4

`challenge initialize` instantiates the frozen categories against the exact
current draft. For each check, submit `challenge complete CH-001 --disposition
completed_no_finding|completed_findings|not_applicable|unavailable|inaccessible
--reason ... --report FILE`. Reports must reflect actual adversarial work.
`completed_findings` requires at least one linked defeater.

When one substantive report genuinely covers several categories, use `challenge
review --check CH-001 --check CH-002 ...` to bind that report and disposition to all
of them in one transaction. This reduces duplicate bookkeeping; each category still
needs a specific reasoned treatment in the report, and finding dispositions still
require linked defeaters.

Use `defeater create --check CH-001 --claim C-001` or `--decision D-001`, with
`--evidence-ref E-001 --text ... --impact ...`. New proof/challenge evidence can be
captured in Phases 3 and 4 without reopening unrelated Phase 2 claims. Changes to
existing supporting evidence still invalidate dependent knowledge.

`defeater confirm --reason ...` records a successful attack and requires explicit
`phase regress --to 1|2|3 --cause defeater:DEF-001 --reason ...` before repair.
`defeater defeat --evidence-ref E-002 --reason ... --report FILE` requires distinct,
active resolution evidence. Retraction of that evidence reopens the defeater.
Only contextual findings may use `accept-contextual-risk`; majority agreement
never disposes a material challenge.

`spec revise --narrative FILE` compiles a new review target. Every configured check
must be completed against that new revision. Earlier reports and defeaters remain
visible. Source drift requires regression to Phase 2 (or Phase 1) for refresh and
revalidation; it cannot be waived at finalization.

`assurance calculate` reports deterministic coverage indicators, not probabilities.
The overall value is the minimum dimension. N/A or unavailable checks and proofs
reduce demonstrated coverage. Scores never override gates. `phase advance` in
Phase 4 recompiles the final package, records scores, completes the phase, and
finalizes the run atomically. Further mutations are rejected.

`spec export` materializes the latest immutable package under
`<run>/exports/<spec-uuid>/`: `technical-spec.md`, `discovery-summary.md`,
`evidence-manifest.json`, and `handoff.json`. It is safe to repeat and refuses
conflicting existing files. It does not create tasks in Taskledger.

The renderer owns the sole top-level heading in `technical-spec.md`; a leading H1 in
the authored narrative is removed as redundant. The Markdown specification is the
primary implementation artifact, while JSON files retain exhaustive machine state.

## Leased investigators

Initialize with `--subagents partitioned|overlap` only when requested. The CLI
manages state and context; the calling assistant launches the actual agents.
Partitioned groups have one investigator per lane. Overlap groups have 2–8
replicas. In Phase 2 use `group dispatch --lane L-001 --count 2`; in Phase 4 omit
`--lane` to target the current draft. All replicas exist before work begins and
share the exact immutable starting context.

Give every replica an actor UUID distinct from the orchestrator and other replicas,
and a fresh random lease (at least 32
characters). `--lease TOKEN agent start AR-001` registers only the token's hash.
Use `--agent-run AR-001 --lease TOKEN resume` for isolated context and own findings.
Unscoped reads/writes by an active isolated actor are rejected. This is a
cooperative CLI context boundary, not authentication against a filesystem owner
or a caller deliberately inventing another actor identity.

An investigator submits `--lease TOKEN agent finding AR-001 --position
support|refute|not_seen|unique --text ... --impact ... --origin-uri ... --report
FILE`, optionally with `--claim` or `--decision`. Phase 4 positions are challenges
(`refute`/`unique`) or `not_seen`. Finish with `agent complete --outcome
findings|no_findings|passed|inconclusive --report FILE`. All writes validate and
extend ownership. `agent heartbeat` renews read-heavy work; `agent reclaim` needs
expiry and a new token, and permanently rejects the old token. Lease authorization also precedes replay;
an expired or replaced token cannot retrieve a prior scoped command result.

The orchestrator uses `finding reconcile --reason ...` only after every requested
replica completes. Substantive findings automatically create leads (Phase 2) or
evidenced defeaters (Phase 4, with `--check CH-...`). Refutation of a canonical
claim makes it contested regardless of supporting counts. Imported investigator
reports are secondary evidence requiring canonical verification and corroboration.
`not_seen` is recorded without becoming a negative vote.

Finally use `group reconcile --reason ... --report FILE`. Failed replicas cannot
silently disappear: `group supersede` preserves the requested denominator, and a
new group must complete. Enabled runs require reconciled groups in both Phase 2
and Phase 4. No confidence score or vote overrides evidence or defeater gates.

## Reporting without a final specification

Use `discovery --json --run /path/to/run report export` when research is blocked or
a bounded question has useful observations but has not completed specification
gates. It exports current records, questions, source freshness and unfinished work
without changing run state. The report labels authored observations separately from
registered claims and leaves conclusion confidence unassessed. It is not a shortcut
to a final technical specification or a standalone archive of artifact bytes.


One defect can be linked to several current checks without duplicate records; see
[canonical findings](../reference/canonical-defeaters.md). Optional conclusion assessments are
attributed support ratings, separate from procedural assurance. Use
`assessment record --file FILE` and `assessment list`; see the
[assessment guide](../../skills/discovery/references/confidence.md).
