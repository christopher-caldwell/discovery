# Refinement iteration: findings, confidence and investigation cost

This iteration follows [the Phase 4 campaign](phase4-retry.md). Its purpose is to
improve the discovery process from observed behavior, not certify a proposed
implementation. Release remains 0.2.0; active storage moves explicitly to schema 6.
Historical finalized schema 5 runs remain readable and are not rewritten.

## Changes prompted by the earlier campaign

The same underlying design defect had been repeated across seven or eight review
categories. A canonical defeater can now link multiple checks within one exact
draft and traversal. It has one confirmation, resolution and gate consequence;
category links are not independent corroboration. Historical owner associations
are backfilled without merging distinct old findings or inventing new judgments.

Procedural assurance previously reached 100 while conclusion confidence was still
absent. Attributed conclusion assessments now preserve each proposition, its scope,
evidence and counterevidence references, unknowns, limitations, rationale and what
would change it. Support is ordinal (limited/moderate/strong), not a probability.
Unresolved propositions remain unassessed. Substantive state changes stale an old
assessment. Structural validation cannot establish semantic truth or independent
review of these ratings.

Repeated recovery loaded embedded execution scripts and export bundles. Optional
`resume --compact` omits those payloads and identifies how to retrieve their exact
records. Historical final-run recovery shrank from 291,331 to 126,447 bytes with
identical gate results. The skill loads phase-specific instructions when needed.
This measurement concerns serialized context size, not overall model cost.

## Same-input simple explanation comparison

All three sessions used the same fixture, ticket, prompt and configured
`gpt-5.6-terra` xhigh model. Each had a fresh isolated home, frozen runtime and
read-only source; prior answers and evaluator artifacts were outside its read
boundary. The baseline froze commit b1490e1; candidates froze the development
changes. The candidate repeat did not receive the first candidate's ledger or log.

| Session | Seconds | Input tokens (includes cached) | Cached input | Output tokens |
| --- | ---: | ---: | ---: | ---: |
| simple-cost-baseline-1 | 177.7 | 296,927 | 257,792 | 8,349 |
| simple-cost-candidate-1 | 150.9 | 237,660 | 206,464 | 4,301 |
| simple-cost-candidate-2 | 161.9 | 212,913 | 195,328 | 4,347 |

Each correctly explained first-call local acceptance, payload and attempt count,
and distinguished these from remote delivery or distributed exactly-once claims.
Both candidate sessions ran the existing two tests and an additional in-memory
call-count probe. All exported interim reports in Phase 1 without inventing an
implementation plan or relaxing advancement gates. Baseline recorded seven
research activities; candidates recorded four each. All source/runtime integrity
checks matched and audits were valid (8/5/5 events, no orphan artifacts).

Candidates used about 20–28% fewer input tokens and 9–15% less elapsed time than
this baseline. One baseline and two candidates cannot isolate causality or establish
stable savings. Cached inputs and model variability matter. These remain minutes
and substantial cumulative context for a small question; the result supports a
narrow improvement, not completion of proportionality work.

## Missing operational evidence

`confidence-unavailable-1` correctly left production delivery attainment and the
necessary/sufficient implementation change unresolved, with no invented score.
It recorded two blocking questions, scoped the passing local tests accurately,
and did not turn missing production evidence into proof of production failure.
Assessment recording, export and audit succeeded (11 events, no orphans).

The 240-second harness cutoff occurred before outcome.md or a final model response.
No usage event was emitted, so token usage is unavailable rather than zero. The
saved report is real evidence; this was not successful end-to-end delivery.
Inspection found avoidable final-state reads and surface bookkeeping before final
delivery, plus a recovered shell heredoc failure inside the isolated environment.

The report also buried conclusions, printed unassessed support as Python `None`,
and duplicated confidence headings. Rendering now puts conclusions after the
request, explicitly describes absent ratings/references, and prominently labels
stale judgments. The skill now calls for early interim delivery once the answer or
blocking boundary is established, preserving unfinished surfaces as pending.

The confidence guide contains a production-reliability example similar to this
fixture. This run tests use of that documented pattern, not generalization to an
unseen domain or calibrated confidence accuracy.

The fresh repeat `confidence-unavailable-3` completed in 207.0 seconds with
279,558 input tokens (235,520 cached) and 5,933 output tokens. It delivered both
outcome.md and an interim report, left unfinished planning surfaces pending, and
recorded three unresolved propositions without fabricated Phase 2 evidence. Its
single compound blocking question retained the owner/evidence gaps. Audit: 7
valid events, no orphans; frozen inputs/runtime unchanged. This supports the
early-delivery route in one repeat, not a deterministic time-budget guarantee.

## Fresh canonical finding review and external observation

`canonical-review-3` resumed a copy of the earlier pre-review Phase 4 checkpoint,
not the repaired/finalized run. It finished in 451.4 seconds: 1,149,069 input tokens
(1,074,688 cached), 12,611 output tokens. It found a constructor cleanup exception
that bypasses the promised StoreError boundary, created one DEF-001, linked six
categories, completed all twelve scoped category reports, confirmed the finding
and regressed to Phase 3. The model did not implement a target fix.

It assigned strong ordinal support to the narrow static finding, separately left
whole-implementation readiness unresolved, and prepared an exact external probe.
The audit had 156 valid events with no orphans. Runtime and selected source/ticket
hashes matched. The old review report was explicitly denied by direct, directory,
child-process and symlink read probes. This observed use of the link model is
stronger than a structural unit test, but is still one review of a seeded design.

After the model stopped and its credentials were removed, the evaluator inspected
and executed its exact command through the restricted Discovery experiment runner.
The embedded prototype matched the captured artifact. EXP-004 / A-064 exited 1
without timeout or truncation: the injected cleanup OperationalError escaped,
the original error remained in implicit context, and the connection field was
cleared. That corroborates the static counterexample under injected wrapper faults;
it does not establish physical IO behavior or production occurrence. The experiment
was recorded as failed, not a passing proof. No target source changed.

The new receipt/finish made CA-001 stale, as intended. The post-probe report labels
it historical rather than silently upgrading its rating; audit159 remains valid
with no orphans. This disposable proposal remains in Phase 3 with a confirmed
finding and unresolved proof. Repairing this target proposal is not the objective
of this CLI implementation iteration.

The fresh review did not rediscover earlier schema/input-boundary counterexamples
in the same old draft. Its category limitations were explicit, but twelve completed
categories do not establish exhaustive challenge. Evidence-review guidance now
asks reviewers to compare accepted inputs and starting states with examined cases,
trace downstream special meanings, and distinguish an actual scope exclusion from
an unvalidated assumption. A separately seeded focused repeat tests that guidance;
it must not be presented as a blind full-workflow repeat.

## Evaluation setup corrections

A detached checkpoint initially failed setup because the harness assumed prior
session reports remained beside the run. Explicit real denial probes now support
that layout; relative probe paths are normalized before sandbox entry. Both setup
failures were preserved, and neither started a model. The resumed review still
requires an actual denied old-report read; isolation was not relaxed.
A later confidence repeat setup used an incorrect ticket path supplied by the
evaluator; it was corrected before another fresh session was launched. This was
an evaluator invocation error, not a Discovery behavior observation.

## Additional invariant checks

Review of the new links found that direct and imported defeater creation could
still attach to a completed no-finding check. Both paths now require a pending
check for new findings; exact-request replay remains valid after completion.
Rejection tests compare snapshots and audits to establish that no mutation occurs.

Schema migration also exposed an old `== 5` condition in the investigator write
guard. Under schema 6 it allowed an active isolated investigator to omit its scope
and write canonical state. The guard now covers supported later schemas. A focused
regression verifies rejection without changes to state or audit. Other schema
comparisons were inspected for this mistake. Read isolation, scope validation and
transaction tests remain separate from claims about model research quality.

## Implementation verification

The integrated suite passed **152 tests** across the application, isolation harness
and restricted experiment runner. Ruff checks and formatting passed; the skill
validator passed. Direct skill, personal plugin source and installed plugin skill
were byte-compared with the checkout. Active executable reports release0.2.0,
schema6. No base release version was incremented. Raw ledgers and test sessions
remain ignored and are not committed.

## Evidence locations

Raw, ignored evidence lives under `.discovery/scenario-campaign/`:

- `sessions/simple-cost-baseline-1`, `simple-cost-candidate-1`, `simple-cost-candidate-2`
- `sessions/confidence-unavailable-1` and subsequent separately named repeats
- `sessions/canonical-review-1`, `canonical-review-2` (setup failures), `canonical-review-3`
- `evaluator/iteration-2/cold-results.json`, `context-size.json`, prompts and frozen baseline

Session manifests preserve frozen inputs and isolation checks; result files preserve
elapsed time, available usage and integrity. Reports and audit receipts live in
their respective session or selected run. These artifacts are not distributed by
committing this summary.
