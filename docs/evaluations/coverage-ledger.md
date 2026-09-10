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
