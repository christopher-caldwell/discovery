# Synthetic full-workflow evaluation — 2026-09-10

This evaluation reuses the disposable outbox fixture under an explicitly synthetic
policy. It is an assisted model-led exercise, not a real business discovery run
or an autonomous quality benchmark. Low-cost agents prepared the environment,
operated Discovery, and generated probes; the root reviewer inspected evidence.

Environment: `.discovery/full-evaluation/0dab38f2-37f7-485f-b7c9-04ff3069bdae/`.
The source has an independent Git baseline and the original ticket is retained.
`scenario-policy.md` supplies model-generated exercise policy with explicit
provenance: local SQLite effects only, unchanged schema, ambiguous outcomes stop
for review. It is not attributed to a human. The sibling `run/` holds durable
Discovery state. All fixture copies and execution artifacts are disposable.

## Findings so far

The operator passed Phases 1–3 and entered Phase 4. Root review found material
semantic gaps despite structural acceptance: hardcoded crash-success output,
unchecked intermediate state, unspecified quarantine/restart behavior, and absent
atomic job completion. Discovery recorded confirmed defeaters, regressed to Phase
3, and reopened proof obligations without erasing previous attempts.

Later prototypes exposed inherited test state, incomplete crash boundaries, and
using a lock-holder instead of a second worker. Generic adversarial reports were
also insufficient. These are failures of model-authored proof interpretation,
not evidence that a procedural assurance score measures technical correctness.
Two initial experiments failed due command quoting and remained in history.
Readable scripts launched with structured argv avoided that harness problem.

A separate lighter agent produced a fourth probe with fresh databases, shared
processing code in both child and parent, abrupt exits before and after commit,
controlled two-worker contention, and complete legacy before/after snapshots.
Root inspected the script. Independent `/usr/bin/python3` validation passed five
cases. Python 3.9 lacks structured SQLite error codes, so the probe explicitly
reports its locked-message diagnostic fallback; newer runtimes require SQLITE_BUSY.

## Final outcome

The run completed all four phases and finalized after three regressions from
Phase 4 to Phase 3. Final audit: **178 events, valid, zero integrity failures**.
Six orphan artifact files are reported and retained; these are unregistered files,
not missing committed evidence. Audit validity does not mean an empty orphan list.

Seven experiment attempts remain in history: two quoting failures, four earlier
passing but semantically insufficient probes, and EXP-007 with the final five-case
probe. The root reviewer checked that the immutable receipt embeds the exact v4
script, reports all five asserted cases, has exit 0, empty stderr, no timeout and
no output truncation. The frozen source remained unchanged with no drift.

The final narrative explicitly includes atomic job completion, the oldest-row
stop-for-review mechanism and caller responsibility, synthetic policy provenance,
which historical proof interpretations were rejected, and remaining limits.
Twelve fresh category-specific root reviews replaced the earlier generic review
approach: eleven completed without an additional finding in the stated scope;
performance was recorded as unavailable because no representative workload exists.
The resulting **92 procedural coverage score is not a correctness probability**.

Final exports are under
`run/exports/6d664f38-5236-4c27-8c28-c430eb10055b/` within the environment:
`technical-spec.md`, `discovery-summary.md`, `evidence-manifest.json`, `handoff.json`.
The handoff is marked final and contains requirements and traceability. The local
`completion.json` records finalization/export/audit responses; root command
transcripts and per-category reviews are preserved under `run/reports/`.

## What this suggests improving next

1. Make empirical review demand explicit assertion-to-claim mapping. An exit code,
   hardcoded success message, or inherited fixture state must not satisfy a proof.
2. Guide agents to readable experiment files and structured argv, avoiding fragile
   inline shell quoting. Capturing an exact script should be straightforward.
3. Make category-specific attack and observation reporting clearer. Generic reports
   can currently satisfy structural gates even when their semantic content is weak.
4. Keep independent review for consequential conclusions. This exercise needed
   concrete root interventions; it does not show that a low-cost operator can
   reliably validate its own proofs without supervision.

No Discovery implementation or release version changed for this evaluation.
Further synthetic environments are lower priority than observing a real request.
The final prototype is still a disposable experiment: no production integration,
caller-loop test, high-load test, power-loss test or external-effect guarantee is
claimed. These limitations are carried in the final specification, not hidden by
phase completion.
