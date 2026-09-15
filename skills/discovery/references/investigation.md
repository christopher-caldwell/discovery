## Phase 2 investigation

Activate planned lanes and record research against lane surfaces. Link `research record`
to a method with `--method M-001`. When the saved result itself is the evidence artifact,
prefer `research capture` for observations or `research finding` when the same action
also proposes one claim and a supporting argument. These operations do not verify an
argument, admit a claim, or close work. A completed method still requires actual work.

Artifact capture is available in Phases 2–4; use `research record --report FILE`
for Phase 1 observations. Inspect each command result before dependent batch work;
a deterministic phase error requires changing the workflow, not repeating it.

Capture saved source bytes with `artifact capture --file FILE --origin-uri URI`; add `--source-backed` for files in the source baseline. Register explicit evidence observations and locators, then claims and supporting/refuting/qualifying arguments. Classify direct/primary, secondary, or empirical evidence truthfully. A copied ticket is still an assertion. Verification reports are model/human judgments about the exact linked argument, not automatic fact checks.

Use `argument verify` to record an attributed report. `claim evaluate` computes admissibility and returns violations; an `ok:true` evaluation may still report `proposed` or `contested`. Do not present it as verified success unless its status is `admissible`. Material profiles need primary evidence and contradiction search; critical profiles add explicit falsification. The claim's selected method controls appropriate proof: an authoritative record requires primary authority evidence, while a test or experiment requires empirical evidence. Inspection and analysis do not manufacture a runtime observation. Unavailable required verification keeps the claim proposed. There is no confidence override or majority-vote resolution.

Register new leads with their source activity. Investigated leads require a separate same-lane activity. Other terminal dispositions require reasons and the corresponding duplicate/question link. A new lead invalidates closure even if later judged irrelevant. Material human-input leads need blocking questions. Use `question create --technical` for Phase 2 answer uncertainty; new uncertainty about request meaning requires regression to Phase 1.

Finish primary research, then `lane closure-begin`. Perform every generated method;
the run policy scales the set from evidence-gap review for contextual work through
contradiction search for material work and full terminology/relationship expansion for
critical work. If a new lead appears, investigate it and begin a fresh iteration.
Reevaluate material claims after the sweep, then close the lane. A material `UNKNOWN`
still needs a linked blocking question.

A critical claim provisions a primary falsification method when it is created. Use
`claim challenge` for the ordinary path: supply the claim, lane surface, report,
observations, evidence classification, result role, reasoning, and limitations. The
operation completes the falsification method and links the records atomically, but it
leaves argument verification, claim evaluation, lane closure, and phase advancement
explicit. If an older run lacks the method, `lane closure-begin` provisions it before
starting the closure sweep.

Use `research-need answer` after all covering lanes close. Phase 2 advances to Phase 3 only when needs are answered, lanes exhausted, claims supported, questions resolved, and source/audit checks pass.

`source refresh --reason ...` records a new baseline. Source-backed artifacts whose
captured bytes still match the same locator are explicitly revalidated against it.
Changed or missing source retracts affected evidence and reopens dependent claims,
lanes, answers, and designs. External snapshots and unrelated work remain current.

Active schema 3/4/5/6 runs require the explicit transactional `run upgrade` command using ordinary mutation identity flags. Upgrade preserves history and the run's frozen policy, but a Phase 1 plan review may become stale after added fields. Never reset a run to solve a version mismatch.
