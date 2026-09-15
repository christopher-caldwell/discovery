# Product realignment validation

This matrix separates code-enforced safeguards, controlled observations, and semantic
investigator evidence. Passing a test establishes only its assertions.

| Situation | Implemented behavior | Evidence | Status / limitation |
| --- | --- | --- | --- |
| Genuine blocking ambiguity | `question assume` rejects blocking questions; interim export leads with the blocker and useful recorded context. | `test_blocking_question_cannot_be_assumed_and_interim_remains_available` | Mechanically tested. Semantic stopping judgment remains the investigator's responsibility. |
| Delegated engineering choice | The operating skill routes technical choices into research/recommendation and reserves product intent for authority. | `skills/discovery/SKILL.md`, `references/request-vetting.md` | Guidance reviewed; no fresh blind live ticket in this pass. |
| Non-blocking uncertainty | Scoped assumptions record justification and invalidation conditions, survive recovery/export, cannot understate dependent impact, and stale dependents when an answer explicitly contradicts them. | `test_assumption_authority_and_custom_surface_survive_recovery_and_regression`, `test_invalidating_assumption_reopens_linked_claim`, `test_question_reclassification_resolution_and_withdrawal_are_explicit` | Mechanically tested. Code cannot decide whether prose is truly non-blocking. |
| New discovery surface | Investigator-added surfaces join the plan/gate/export and are recreated pending on Phase-1 regression without replacing baseline surfaces. | `test_assumption_authority_and_custom_surface_survive_recovery_and_regression` | Mechanically tested. |
| Uncertain respondent | Ranked candidates retain kind, confidence, rationale, attribution, optional evidence, and explicit unknown identity. | Same focused test and interim renderer | Mechanically tested; code cannot authenticate organizational authority. |
| Different critical claim kinds | Critical authoritative claims use primary authority evidence plus falsification; test/experiment claims require empirical evidence; a runtime experiment cannot establish product intent; unavailable required proof blocks. | `test_claim_verification_matches_assertion_and_unavailable_proof_blocks`, `test_runtime_experiment_cannot_establish_product_intent`, revised Phase-2 tests | Obvious method/category errors are mechanical; nuanced relevance remains semantic. |
| Higher-level research operation | `research capture` stores one result/activity plus explicit evidence in one audited transaction and exact replay, without claims or advancement; new evidence stales an in-progress closure and cannot complete that closure's method in the same call. | `test_research_capture_bundles_persistence_without_semantic_approval`, `test_research_capture_invalidates_an_in_progress_closure` | Mechanically tested. It deliberately supports one evidence kind/locator per call. |
| Investigator-facing finding | `research finding` stores the result, observations, proposed claim, and supporting argument in one idempotent transaction without verifying, admitting, closing, or advancing. | `test_research_finding_bundles_bookkeeping_without_semantic_approval` | Mechanically tested. Semantic judgment remains explicit. |
| Proportional closure | Contextual lanes check evidence gaps, material lanes add contradiction search, and critical lanes add terminology and relationship expansion. | `test_closure_rigor_is_proportional_to_consequence` and normal lane closure tests | Mechanically tested; investigators still judge whether additional work is warranted. |
| Targeted refresh | Exact bytes at the same source locator are revalidated against the new baseline; changed or missing files retract affected evidence. | `test_source_refresh_revalidates_unchanged_source_evidence`, existing invalidation tests | Mechanically tested at file granularity. Broader locators conservatively invalidate. |
| Disposable experiment | Portable local execution is the default and records that it is not confinement. Explicit original-source paths are rejected, source drift is checked, and optional macOS restricted mode never falls back. | `test_local_receipt_is_portable_and_restricted_mode_never_falls_back`, `test_local_cli_records_actual_result_and_preserves_original`, `test_local_experiment_rejects_explicit_original_source_path`, existing restricted tests | Local and restricted paths executed on macOS. Local mode is trusted execution, not a security product. |
| Adversarial review usability | One substantive report can disposition several current review checks in one transaction while each finding and defeater remains canonical. | `test_one_adversarial_report_can_cover_multiple_checks`, existing defeater/regression tests | Mechanically tested; report substance remains investigator-owned. |
| Disabled/partitioned/overlap | Existing preferences, isolated reports, denominators, failures, refutations, and unique findings are retained. | Existing `test_agents.py`, completion overlap tests, two fresh isolated implementation reviews in `docs/reviews/` | Mechanics tested; the fresh reviews demonstrate isolated semantic overlap but are not statistical independence. |
| Defeated proposal | Existing explicit regression invalidates traversal/spec revisions and requires every intervening gate again; assumptions are accepted regression causes. | Existing completion/defeater tests plus custom-surface regression test | Mechanically tested; no new blind end-to-end seeded defect campaign was run. |
| Fresh-session recovery | Compact resume now includes questions, respondents, assumptions/dependencies, surfaces, findings, current phase, gates, and legal actions without execution payloads. | Existing compact-context test and focused assumption/surface recovery test | Mechanically tested. |
| Exported result | Interim report leads with current outcome/next action. Final specs lead with authored engineering prose, requirements, assumptions, validation, and risks; raw graph state remains in the handoff and manifest. | Reporting/spec readability tests and `docs/examples/product-realignment-example-spec.md` | Readability mechanically tested; the example is controlled, not a deployed or blind live result. |

## Declared validation set

- Full invariant suite: 160 repository tests passed on macOS.
- Focused restored-behavior suite: 14 tests passed in
  `tests/test_product_realignment.py`.
- Static/style validation: Ruff and `git diff --check` passed.
- Basic execution: actual default local CLI receipt plus optional macOS Seatbelt tests.
- Portable local execution: exercised through the ordinary CLI on macOS; no OS gate
  defines the feature. A separate Linux host was not available for this run.
- Semantic overlap: two isolated reviewers receive the same bounded audit question and
  write separate reports before root synthesis. Their agreement is a convergence
  signal; any concrete minority objection is investigated rather than outvoted.

## Result boundaries

- **Implemented:** schema-7 lifecycle, gates, commands, recovery, reports, experiment
  modes, migration, and operator guidance described above.
- **Mechanically tested:** the declared 160-test run and 14-test focused run.
- **Observed with investigators:** two fresh isolated code audits found convergent
  assumption defects and one independent closure defect; the root disposition is in
  `docs/reviews/product-realignment-review-synthesis.md`.
- **Specification usefulness:** the example specification demonstrates conditional
  conclusions and traceability in a controlled fixture only.
- **Not demonstrated:** a fresh blind live Discovery ticket, execution on a separate
  Linux host, authenticated authority, or semantic proof that a selected verification
  method is appropriate.
