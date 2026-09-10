# Taskledger request-vetting evaluation — September 10, 2026

This exercise examined how Discovery handles a flawed feature request and a simple
source question. Completion was not the success criterion. Both produced useful
answers while exposing differences between authored findings and durable workflow
state. Neither Taskledger implementation nor a target database was changed.

## Setup and controls

A lighter agent (gpt-5.6-terra, low) inspected Taskledger and authored two tickets
plus a separate evaluator key. Independent operator contexts received one ticket,
the Discovery skill and a frozen source copy, with instructions not to read the
key or sibling outputs. This was cooperative separation, not filesystem isolation.
The root evaluator inspected the key and source independently; it did not supply
answers to operators during the initial runs.

The source snapshot includes 69 tracked/nonignored working-tree files, including
existing edits. Original HEAD was `6c93944f471d52b04e2a595497d87ae237991179`; the
snapshot has its own empty Git root and uses Discovery's content-derived baseline.
This preserves current work without attributing dirty bytes to that commit.
Discovery baseline was `b28e790`, release 0.2.0, schema 5.

The complex case had an eight-minute/65-command limit; the simple case had a
four-minute/35-command limit. These are experimental bounds, not product defaults.
Every operator CLI invocation was captured by an evaluation-only recorder, with
arguments, output, error, elapsed command time and persistent mutation identity.
Source reads/model reasoning were not individually timed. Token totals were not
available and were not estimated from text size.

## Cases and observations

### Feature ticket

The request proposed a launch-wave preview with routine/complex worker advice and
expected all eligible tasks in a valid plan to be suitable for one parallel wave.
It left recommendation ownership and persistence/freshness behavior unresolved.

The operator challenged the premise using actual plan/eligibility code and current
orchestration guidance. Taskledger eligibility does not compare prospective write
sets or establish parallel safety. It also separated worker complexity from parallel
independence and advice from assignment/worktree/token creation.

The operator identified three blocking questions: whether to change the existing
parallel-safety policy, who supplies and approves assessments (including UNKNOWN),
and whether resume should show recomputed advice, a durable reviewed wave, or both.
Its proposed API, persistence and tests were explicitly conditional. This was useful
scope exploration, but not a product-approved or formally proven design.

It also found details beyond the planted issues: two rejected routine submissions
force complex, plan fingerprints omit lifecycle state, and preflight can reconcile
state. A preview behind that preflight is not automatically mutation-free. These
are supported by static source inspection, not executed runtime experiments.

The run remained in Phase 1 with three questions and a findings review. It recorded
three needs, three planned lanes and five research activities. Audit integrity
verified 23 events. Seven orphan files remained from seven rejected artifact calls.
The operator's script repeated the deterministic phase error instead of stopping;
this is an operator failure as well as an opportunity for clearer CLI behavior.

### Simple source question

The request asked how `project resume` differs from `project recover`, including
preflight and usage. The operator correctly traced both preflight paths: resume's
shared dispatcher call and recover's internal call. It distinguished compact,
cursor-based refresh from self-contained recovery, including `not_modified` and
new/lost session context. The evaluator checked these against CLI/service definitions
and the current Taskledger skill. No runtime execution was needed for that scope.

The operator delivered a concise source explanation, but reached its command limit
in Phase 2 before claim admission or lane closure. Seven generic planning surfaces,
separate research/disposition records, plan review, and repeated planning/lane
recording consumed workflow effort. The answer does not naturally call for an
implementation strategy. Forcing Phases 3–4 would manufacture work beyond the ask.

## Measured effort

| Measurement | Simple | Complex |
| --- | ---: | ---: |
| Recorded CLI invocations | 35 | 46 |
| Help calls | 6 | 8 |
| First-to-last CLI interval | 150.3 s | 238.6 s |
| Time inside CLI processes | 2.44 s | 3.34 s |
| CLI stdout bytes | 33,651 | 50,749 |
| Nonzero exits | 1 | 8 |

The intervals exclude some initial reading and final writing. Output bytes are not
token usage. One run of each case cannot establish typical latency or comparative
model efficiency. The useful signal is that process execution was a small fraction
of elapsed operator time; optimizing SQLite alone would not address this sample's
workflow cost. Both operators tried `spec export`; both received SPEC_REQUIRED.

## Changes justified by the evidence

1. Added `report export`: a non-final Markdown report and full structured snapshot
   available without a compiled specification. It preserves questions, attributed
   research observations, claim statuses, source observations and unmet gates.
   It neither finalizes the run nor supplies an invented numeric confidence score.
2. Moved `artifact capture` persistence after phase/scope/source validation under
   the command transaction. Rejected validation and successful replay no longer
   write new artifact bytes. Existing orphans remain preserved; later I/O or commit
   failures can still leave orphans.
3. Added legal-phase guidance to capture help and the skill, plus guidance to inspect
   deterministic errors before continuing dependent batches. Added report guidance
   for blocked and explanation-only investigations without claiming formal closure.

Both existing runs exported through the new command without advancement. Their
original audit heads remained unchanged, and original gate restrictions remained.
Targeted tests cover unresolved questions, absent confidence, unchanged ledger,
repeat exports, source drift at the same audit head, conflicting/symlink output,
rejected captures without orphans, and capture replay after regression. After the final report review, **103 tests passed in 46.45 seconds**. Ruff lint and
format checks, package build and skill/plugin validators passed. Installed skill
copies match the checkout. Base version remains 0.2.0 and schema remains 5.

## Post-change review

Both operators inspected the new exports using separate logs, preserving the original
measurement transcripts. Review found omitted need answers, non-clickable artifact
references, and missing orphan diagnostics. The report now includes need answers,
clickable captured-report links and the full audit result, explicitly distinguishing
covered needs from answered ones. Rendered bundle hashes prevent a changed renderer
from colliding with an older export of the same structured snapshot.

After the evaluator key was unsealed, the complex operator identified a substantive
miss: it had not inspected PS-051/052 in the product specification, which explicitly
reserves selection/prioritization to the orchestrator. Its original proposal reached
a compatible general direction through the skill, but “selected first-wave IDs”
needed to be explicitly orchestrator-supplied. This remains recorded in the
retrospective; the original proposal was not retroactively rewritten. The operator
also noted premature emphasis on persisted assessments before the owner chose an
ephemeral versus durable outcome. These are semantic findings, not fixed by report
export or a passing audit.

## What remains to learn

- The simple case still lacks a formally complete answer-only route. Interim export
  solves delivery friction, not research closure or proportionality. Evaluate a
  few more simple cases before choosing smaller policies or a distinct outcome.
- Confidence in conclusions is still distinct from procedural coverage. Operators
  used scoped qualitative judgments; the new export explicitly leaves a numeric
  score unassessed. A calibrated confidence model was not established here.
- Phase 1 observations retain source locators in reports, but are not admitted
  Phase 2 claims. The authored complex proposal is richer than its normalized state.
  Test whether later investigators can recover the reasoning and qualifications.
- Failed calls are visible in evaluation transcripts, not successful-mutation audit
  events. Ordinary-run diagnostic retention deserves separate evaluation; audit
  validity alone cannot reveal command friction or semantic misses.
- The complex operator developed substantial conditional design while questions
  remained open. Compare its usefulness against a shorter blocked report rather
  than assuming additional detail always improves the outcome.

## Local evidence

All raw artifacts are under `.discovery/taskledger-vetting/`:

- `input/`: exact tickets; `evaluator/expectations.md`: the separate evaluation key.
- `evaluator/source-manifest.json` and `source-status.txt`: source provenance.
- `simple/` and `complex/`: outcome, operator notes, immutable runs and command logs.
- `evaluator/metrics.json`: counts/timing; `*-post-change.json`: report verification.

This is a process-evaluation record, not a claim that two successful answers prove
Discovery reliably vets arbitrary requirements.
