## Phase 2 investigation

Activate planned lanes and record research against lane surfaces. Link `research record` to a method with `--method M-001`. A completed method requires an actual linked research activity.

Artifact capture is available in Phases 2–4; use `research record --report FILE`
for Phase 1 observations. Inspect each command result before dependent batch work;
a deterministic phase error requires changing the workflow, not repeating it.

Capture saved source bytes with `artifact capture --file FILE --origin-uri URI`; add `--source-backed` for files in the source baseline. Register explicit evidence observations and locators, then claims and supporting/refuting/qualifying arguments. Classify direct/primary, secondary, or empirical evidence truthfully. A copied ticket is still an assertion. Verification reports are model/human judgments about the exact linked argument, not automatic fact checks.

Use `argument verify` to record an attributed report. `claim evaluate` computes admissibility and returns violations; an `ok:true` evaluation may still report `proposed` or `contested`. Do not present it as verified success unless its status is `admissible`. Material profiles need primary evidence and contradiction search; critical profiles also require empirical evidence and completed falsification/empirical methods. There is no confidence override or majority-vote resolution.

Register new leads with their source activity. Investigated leads require a separate same-lane activity. Other terminal dispositions require reasons and the corresponding duplicate/question link. A new lead invalidates closure even if later judged irrelevant. Material human-input leads need blocking questions. Use `question create --technical` for Phase 2 answer uncertainty; new uncertainty about request meaning requires regression to Phase 1.

Finish primary research, then `lane closure-begin`. Perform and record every generated closure method. If a new lead appears, investigate it and start a new closure iteration; old iteration records remain historical. Reevaluate material claims after the sweep, then `lane close --answer ... --limitations ...`. A known material answer needs an admissible claim at the lane's impact. A material `UNKNOWN` needs `--question Q-001` linked to a blocking question and can close procedurally while still blocking advancement. Answering that question reopens its dependent lanes so the answer is incorporated.

Use `research-need answer` after all covering lanes close. Phase 2 advances to Phase 3 only when needs are answered, lanes exhausted, claims supported, questions resolved, and source/audit checks pass.

`source refresh --reason ...` records a new baseline. It retracts evidence captured from the replaced baseline and reopens affected/dependent lanes, claims, and need answers. External snapshots are retained. Recapture source evidence and record new arguments as needed; refresh does not silently bless old evidence. This version invalidates by source baseline, not individual changed lines.

Active schema 3/4/5 runs require the explicit transactional `run upgrade` command using ordinary mutation identity flags. Upgrade preserves history and the run's frozen policy, but a Phase 1 plan review may become stale after the added fields. Never reset a run to solve a version mismatch.
