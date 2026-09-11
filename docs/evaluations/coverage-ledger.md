# Scenario coverage ledger

Companion to [the scenario specifications](scenario-specs.md). This distinguishes
existing executable safeguards from observed investigation quality. Test names
below identify narrowly scoped assertions, not proof of the full scenario.

| Scenario | Existing executable evidence | Model investigation evidence before this campaign | Remaining observation |
| --- | --- | --- | --- |
| S01 simple answer | `test_blocked_report_preserves_questions_without_advancement_or_scoring` | Taskledger answer correct; 35-call bound reached before closure | Isolated repeats; proportionality still unresolved |
| S02 vague ask/authority | `test_question_retry_conflict_and_gate` | Three questions in Taskledger flawed ticket | Fresh vague ask and quality of authority hypothesis |
| S03 false premise | `test_request_copy_is_still_an_assertion` | Caught eligibility premise; missed explicit PS-051/052 contract | Repeat after source-selection guidance change |
| S04 contradiction | Questions block; meaning changes require Phase 1 | Preview/preflight side effects noticed in Taskledger | Dedicated contradiction and owner-reply variant |
| S05 already satisfied | Interim report can export without spec | Not established by prior Taskledger runs | Fresh local behavior ticket |
| S06 focused lanes | `test_gate_rejects_structurally_invalid_plans`, `test_review_stales_and_source_drift` | Needs/lanes created in Taskledger | Independently assess coverage, omissions and irrelevant lanes |
| S07 missing technical evidence | `test_material_unknown_closes_but_blocks_phase`, `test_unknown_need_cannot_bypass_blocking_question` | Missing owner answers observed; unavailable technical evidence not demonstrated | Fresh production-SLO question on local fixture |
| S08 conflicting sources | `test_contradiction_not_outvoted` | Source/skill used, decisive product doc missed | Model must find and preserve source disagreement |
| S09 closure lead | `test_new_lead_invalidates_closure_and_answers`, `test_closure_retry_and_historical_method_rejection` | Earlier fixture work; not a fresh campaign observation | New lead must change investigator behavior, not just state |
| S10 copied/weak evidence | `test_secondary_evidence_cannot_admit_material_claim`, `test_copied_counterevidence_cannot_resolve_itself` | Not independently established for misleading prose | Classifications are model judgments; test that limit |
| S11 complex proposal | `test_complete_traversal_exports_and_final_replay` | Boilerman full traversal, but repair-oriented; Taskledger conditional design | Working-repo feature proposal with owner inputs |
| S12 isolated probe | `test_experiment_isolation_replay_and_proof`, `test_experiment_cannot_write_original_or_use_network` | Boilerman scratch probes exposed executor issues | Probe relevance/strength for a proposed feature |
| S13 challenge depth | `test_draft_staleness_and_revised_checklist` | Boilerman challenge reports | Fresh concrete attacks; generic reports can satisfy structure |
| S14 regress/retraverse | `test_valid_advance_regress_retraverse`, `test_transition_rules`, `test_regression_from_phase_four_retains_phase_one`, `test_defeater_requires_regression_and_distinct_resolution` | Earlier full evaluation includes refinement | Model chooses appropriate regression for semantic defect |
| S15 fresh recovery | `test_initialization_idempotency_and_reopen`, `test_planning_record_completes_surface_and_resumes_provenance` | Resume projection improved after Taskledger review | Fresh model with only permitted run state, no chat |
| S16 drift | `test_source_refresh_retracts_source_evidence_only`, `test_retraction_blocks_previously_closed_lane` | Earlier source-refresh exercises | Fresh operator handles changed assumption in proposal |
| S17 collaborators | `test_overlap_isolation_reconciliation_and_no_token_leak`, `test_failed_replica_preserves_denominator`, `test_overlap_gates_in_both_investigation_and_adversarial_phases` | Prior scoped investigator exercises | Semantic minority objection and start preference behavior |
| S18 recovery/integrity | `test_concurrent_processes_share_request`, `test_killed_cli_reservation_recovers_without_duplicate_execution`, `test_detect_unaudited_state_change`, `test_artifact_corruption` | Earlier killed-controller and audit work | Keep technical checks separate from model conclusions |
| S19 document/confidence | `test_interim_report_includes_answered_need_and_resolvable_artifact_links` | Operator export reviews prompted report fixes | Numeric conclusion confidence absent; fresh reader review |
| S20 proportionality | Evaluation recorder; no CLI model-token quota | 35 calls simple, 46 flawed; 31-call replay reused answers | Independent repeats and measured model usage |

Historical details: [Taskledger evaluation](../taskledger-vetting-evaluation.md),
[Boilerman evaluation](../boilerman-full-evaluation.md). The current campaign must
append its own results with artifacts and limitations; these older observations
must not be relabeled as new isolated experiments.

## Campaign update

See [the retained campaign findings](isolated-campaign.md) for exact run names,
controls, source checks and metrics. These assessments are limited to the supplied
inputs, not estimates of general reliability.

| Observable | Assessment | Evidence |
| --- | --- | --- |
| S01 correct bounded source explanation | demonstrated on this input | All Taskledger simple runs recorded the correct preflight distinction; the final variant delivered outcome/export |
| S01/S20 timely completion | contradicted under this bound | Four Taskledger simple sessions reached 240 seconds; the final one delivered artifacts before cutoff |
| S02 missing authority | partially_demonstrated | Blocked cases preserved questions and owner hypotheses; a fully vague initial ask was not run |
| S03 false premise and governing contract | demonstrated on this input | Both launch-wave runs cited product rules and rejected eligibility ⇒ parallel safety |
| S04 contradictory requirements | partially_demonstrated | Product/ticket conflict retained; controlled owner-reply continuation not run |
| S05 already satisfied | demonstrated on this input | Small fixture confirmed existing local behavior, proposed no target change, exported in 192 seconds |
| S06 focused plan | partially_demonstrated | Blocked runs recorded differing needs/lanes; no independent proof of comprehensive semantic coverage |
| S07 useful cannot-answer outcome | demonstrated for explicit missing evidence | Both SLO runs separated local acceptance from production guarantees and remained blocked |
| S07 Phase 2 UNKNOWN operator path | not_exercised by model | Runs stopped in Phase 1; structural test exercises the later-phase rule |
| S08 source disagreement / misleading test | partially_demonstrated | Product conflict noticed; already-satisfied run spotted a missing call-count assertion; dedicated conflicting fixture remains unused |
| S09–S14 research closure, design, experiments and challenges | not_exercised by this model batch | Existing structural tests remain the evidence; no fresh four-phase feature proposal here |
| S15 recovery | partially_demonstrated | Root resume/audit recovered stopped runs; no fresh recovery model was launched |
| S16 source drift | not_exercised by this model batch | Frozen hashes verified unchanged; existing drift tests remain the evidence |
| S17 optional collaborators / minority finding | not_exercised by this model batch | Controlled runs disabled internal collaborators; existing structural tests are separate |
| S18 interruption durability | partially_demonstrated | Timed-out model sessions left valid audits and captured research; corruption/retry variants remain structural tests |
| S19 useful document | partially_demonstrated | Blocked/already-satisfied/final simple variant exported useful interim material; numeric conclusion confidence remains absent |

Remaining work is not contingent on receiving a real customer ask. The next
controlled feature, contradiction, recovery and challenge scenarios can still
produce implementation evidence. This batch does not support a claim that
Discovery cannot improve further without real-world use.


## Feature and recovery follow-up

See [feature-and-recovery.md](feature-and-recovery.md) for separate inputs, controls,
results and limitations. This extends the preceding batch; it does not overwrite
what was unexercised in that batch.

| Observable | Updated evidence | Limit |
| --- | --- | --- |
| S04/S08 contradiction | A fresh model found the superseded global-ID rule and preserved current tenant-scoped identity | One deliberately constructed fixture |
| S15 fresh recovery | A new session reconstructed the selected ledger, applied a simulated reply and preserved history; old conversation/outcome reads denied | Correct reconstruction did not prevent overblocking delegated design choices |
| S06 research lanes | Fully scoped storage feature completed research with source-backed current-behavior claims and documented alternatives | Does not prove semantic completeness of research |
| S11 proposal | Reached Phase 3 and exported an implementation direction without target changes | Error-classification flaw remains in the original interim proposal |
| S12 experiment | Formal receipt truthfully records a nested-sandbox denial before execution | Host probe is separate; full experimental proof was not obtained |
| S13 independent challenge | Fresh reviewer identified a masked constraint failure and a test that bypassed the proposed function | Review continuation in Phase 3, not a completed Phase 4 |
| S14 regression/retraverse | Still not exercised by this model campaign | No Phase 4 checkpoint existed; no seeded regression was run |
| S17 preference | Probe selected disabled investigators under a policy disabling native agents | Confounded; cannot establish behavior when choices are available |
| S19 confidence | Reports express limitations and qualitative confidence | Numeric conclusion confidence remains absent |

The follow-up narrows several evidence gaps but does not close all twenty scenarios.
Fresh drift, closure-lead, minority objection, later-phase UNKNOWN, and full
regression observations remain necessary. The source-guidance refinements are
motivated by observed behavior; they are not yet evidence of stable improvement.


## Phase 4 retry and repair

See [phase4-retry.md](phase4-retry.md). This is an informed repair followed by fresh
isolated review, not a cold repeat of the whole original investigation.

| Observable | New observation | Limit |
| --- | --- | --- |
| S12 isolated experiment | External handoff ran the real sandbox with restricted reads; eight-case then nineteen-case prototype receipts were recorded | Evaluator-controlled stopped-session handoff, not automatic dispatch |
| S13 challenge depth | All twelve categories reviewed; reviewer found an existing-schema NOCASE counterexample despite eight passing tests | One root issue appeared in seven category records; these are not independent confirmations |
| S14 regression/retraverse | Reviewer confirmed the issue, regressed 4→3, and requested new proof; revised proposal passed the normal gate back to Phase 4 | Root authored informed repair; subsequent independent review is separately recorded |
| S15 recovery | Fresh review reconstructed exact draft and retained rejected/historical work without treating it as current proof | Selected durable history is intentionally available; unrelated logs remain denied |
| S19 report/data structure | Revised narrative explains evidence limits and changed schema boundary; category duplication and receipt registration friction observed | Numeric conclusion confidence and proportional document size remain open |

No target feature was implemented. These observations add specific process evidence;
they do not establish general reliability or close every scenario.


The second fresh Phase 4 review found a distinct filename-interpretation defect;
after empirical reproduction and repair the run retraversed into Phase 4 again.
The third review was interrupted by a usage limit before completing any current-draft
category. Finalization was therefore still unobserved at that checkpoint.
S19 also produced a source rendering change: the same-snapshot Markdown comparison
shrunk by 60.8%, retained exact machine records, and labeled rejected requirements.
This does not demonstrate reduced model cost or supply a numeric confidence score.


## Completed selected-run continuation

The next fresh session (`phase4-review-4`) completed all twelve current-draft
categories, found no new material defect within the proposal's stated scope, and
finalized SPEC-004 through the ordinary gate. S11/S13/S14 now have model-run evidence
of a scoped feature proposal, semantic challenge, two 4→3 regressions with new proof,
and forward traversal to final export. This was an informed repair campaign,
not an independent cold end-to-end run.

S19 includes a final package whose evidence limits survived review and whose
Markdown labels rejected requirements and references full execution records. The
score 100 remains procedural assurance, not conclusion-confidence calibration.
S20 remains open: this continuation took 385.569 seconds and reported 1,818,844
cumulative input tokens (1,711,360 cached), plus 18,842 output tokens. The latest
review does not establish a model-cost benefit from the renderer change.

Final audit: 273 events, valid with no orphan artifacts. Target source and ticket
hashes were unchanged. Details and export location are in
[the completed continuation report](phase4-retry.md#completed-continuation-final-proposal-with-scoped-assurance).


## Canonical findings, confidence and cost refinement

See [refinement-iteration.md](refinement-iteration.md) for controls, negative
observations, code changes and raw evidence paths.

| Observable | New observation | Limit |
| --- | --- | --- |
| S01/S05/S20 simple answer | Same-input old baseline and two fresh candidates answered correctly; candidates recorded less redundant research and lower measured cost | Only one baseline and two candidates; no deterministic model budget enforcement |
| S07/S19 unavailable evidence | First run saved unresolved confidence but missed final delivery; fresh repeat delivered in 207 seconds with unknowns and no invented score | Similar example exists in skill guidance; not unseen-domain calibration |
| S13/S14 challenge/regression | One canonical defect linked six categories and triggered 4→3; exact external probe corroborated its static prediction | Other previously observed boundary defects were not rediscovered; category completion is not exhaustiveness |
| S15/S18 recovery | Compact recovery preserves gates; fresh selected checkpoint denied old report access; post-probe audit of 159 events valid | Seeded continuation intentionally includes selected prior research |
| S17 investigator isolation | Schema 6 write guard regression discovered and fixed; direct/import completed-check guards tested | No live multi-investigator semantic campaign in this iteration |
| S19 conclusion confidence | Structured ordinal assessments separate defect support from unresolved overall readiness; new receipt stales prior judgment | Attributed judgment, not calibrated probability or independent assessment review |

The focused boundary follow-up found both earlier filename/schema counterexamples
in 226 seconds, recorded two distinct findings and regressed while leaving the
full checklist incomplete. This changed task focus as well as guidance, so it is
not evidence of stable full-review recall. Its Phase 4 research-record rejection
also prompted clearer CLI recovery guidance; the underlying phase gate is intact.
