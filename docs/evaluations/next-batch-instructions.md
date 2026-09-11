# Instructions for the next Discovery evaluation batch

Use this document as the evaluator's handoff. Prepare and run the batch, inspect
what happened, and fix concrete problems in Discovery. Do not give this document
or the evaluator's expectations to the model operating Discovery.

## Purpose and boundaries

Discovery receives a potentially vague, contradictory or incorrect request. It
establishes intent, researches focused questions, proposes an implementation when
justified, and challenges that proposal. Its output is an evidence backed document
with attributed confidence, explicit uncertainty and actionable questions. An
honest explanation that the available evidence cannot answer the request is a
valid outcome.

The target repository is research material. Do not implement the requested
feature, repair its source, or turn this into a target bug fixing exercise.
Disposable probes and databases are permitted. Changes to Discovery's own CLI,
skill, tests and evaluation harness are part of this task when observations justify
them. Keep the base release at 0.2.0 unless a separate requirement makes a release
change necessary.

Evaluate three things separately: code enforced invariants, investigator reasoning,
and whether a reader can reconstruct the answer from the exported document.
Passing gates or tests does not establish semantic correctness or exhaustive review.

## Starting point

Repository: `/Users/christophercaldwell/Code/projects/discovery`.

Read these files before preparing cases:

- [Latest iteration and its limitations](refinement-iteration.md)
- [Scenario coverage](coverage-ledger.md)
- [Timing instrumentation](timing-instrumentation.md)
- [Scenario catalog](scenario-specs.md)
- [Current operating skill](../../skills/discovery/SKILL.md)

The scenario catalog contains historical gaps. Current source and the latest
iteration take precedence when checking implemented commands. At this handoff,
release 0.2.0 uses schema 6, supports canonical findings across review categories,
and records conclusion assessments separately from procedural assurance.

The last integrated suite passed 152 tests. The subsequent timing instrumentation
passed 13 focused harness and restricted experiment tests. These are historical
results, not checks performed by the new evaluator.

From the repository, inspect the current checkout and verify the harness:

```sh
git status --short
git log -3 --oneline
uv run discovery --version
uv run pytest -q scripts/evaluation/test_isolated_run.py scripts/evaluation/test_restricted_experiment.py
uv run ruff check scripts/evaluation
```

Preserve unrelated changes. Record the current commit and any dirty source bytes.
Do not reset the checkout or upgrade historical finalized ledgers.

## Prepare fresh cases

Use new examples rather than the familiar SQLite receipt store, retry SLA, or
Taskledger launch preview tickets. Search `~/Code` for suitable working projects.
Choose a coherent, small source slice for bounded cases, retaining the governing
contracts and dependencies needed to interpret it. A larger feature case should
retain enough architecture to support a serious proposal. Document sanitization
and omissions without changing the original repository.

Delegate disposable fixture construction to an available lower strength model.
Give each worker a narrow assignment: create the source snapshot or small fixture,
its ticket, a private evaluator key with exact source references, and an inventory.
Workers must not edit Discovery or run the investigation. The evaluator verifies
the fixture before freezing it. Internal Discovery investigators stay disabled in
this batch so their behavior is not another changing variable.

Keep the ticket natural. Do not plant headings such as “intentional false premise”
or announce the expected blocker in an operator README. Existing ordinary product
contracts should remain visible; hiding relevant evidence is not a valid test of
whether the model finds it.

Prepare these cases and private expectations:

| Case | Initial ask and fixture | What the evaluator examines | Runs and bound per run |
| --- | --- | --- | --- |
| Simple existing behavior | A precise question about behavior already present, with a nearby test and a meaningful scope limitation | Correct answer, actual assertions, no redundant feature plan, early delivery | 2 fresh runs; 240 seconds, 35 CLI calls |
| Plausible incorrect premise | A ticket proposes a change on the basis of one believable but incorrect statement about current behavior | Whether the model locates contrary evidence, corrects the premise and checks whether intent still requires a change | 2 fresh runs; 480 seconds, 65 calls |
| Conflicting sources and authority | Code, an older design document and a current requirement disagree; the accountable decision maker is not established | Preservation of current versus desired behavior, source authority, focused questions and useful research while blocked | 1 run; 480 seconds, 65 calls |
| Evidence becomes insufficient during research | Intent is clear enough to investigate, but a material implementation choice depends on an unavailable external contract, compatibility fact or operational observation | Whether Phase 2 or 3 preserves the unknown and stops unsupported design; evidence needed to resume | 1 run; 900 seconds, 110 calls |
| Complex feature in a working repository | A realistic feature spanning several components, with enough product intent to research alternatives and propose a design | Relevant lanes, operational constraints, traceability, meaningful probes, adversarial depth, confidence and a usable technical document | 1 run; 1,200 seconds, 160 calls |

These seven initial sessions total at most 67 minutes of configured operator time,
excluding setup, evaluation, probes and any justified repeats. Time limits are
harness enforced; CLI call limits are prompt guidance, not exact enforced quotas.

A later evidence gap might reasonably be detected in Phase 1. Preserve that
observation instead of steering the operator into a later phase. If necessary,
add a separately labeled checkpoint continuation to exercise the later state;
do not represent it as a cold investigation. A complex case that stops at a real
blocker is also evidence, not a reason to fabricate an answer or bypass a gate.

Write any simulated owner replies before running the case. Mark them simulated
and specify when they become available. Never invent a human answer after seeing
which response would make the run finish.

## Keep the operator blind

Create a new batch directory under `.discovery/`, with separate `fixtures`,
`tickets`, `prompts`, `evaluator` and `sessions` directories. Keep evaluator keys
outside source trees. Session directories must not already exist.

Use `scripts/evaluation/isolated_run.py`. It freezes the CLI and skill, creates a
fresh model session, checks actual read denials, and prevents target source writes.
Prompt instructions alone are not sufficient isolation. Do not replace a denied
probe with a weaker check just to start the model.

The harness inherits configured model defaults. Record the actual model and
reasoning configuration from each manifest. Keep input hashes, model configuration
and budgets identical within a repeat pair. Do not alter account settings silently.

An operator receives only its natural ticket, permitted source, current skill,
ordinary execution instructions, and its own state. It must not receive the
private expectations, prior outcomes, sibling SQLite databases, logs or this plan.
The evaluator must not act as the supposedly independent operator.

## Operator prompt and invocation

Create a separate prompt file for each case. Replace the budget placeholders;
otherwise keep the instructions the same across replicas:

> Use the Discovery skill to investigate ticket.md against source/ in this
> workspace. Vet the request before proposing changes. Investigators are disabled.
> Research and record evidence through the CLI, distinguish observed facts from
> assumptions, and preserve unanswered questions without inventing owner replies.
> Do not modify target source or implement the requested feature. Choose a
> proportionate workflow and produce an appropriate Discovery export and outcome.md
> explaining the answer or proposal, evidence, confidence, limitations and actual
> stopping state. Record structured conclusion confidence where appropriate;
> unassessed is valid when support is unavailable. Do not force a blocked request
> through later phases to obtain a score or report. Use the ordinary sequential
> forward phases and explicit regression rules. You have BUDGET_SECONDS seconds
> and a soft ceiling of CLI_CALL_LIMIT CLI calls. Deliver a useful interim result
> as soon as possible and reserve at least 45 seconds for final delivery. New
> formal experiments requiring execution outside this model boundary must be
> prepared as exact external runner requests, not executed through a workaround.

Use absolute paths for the variables below. This is a template, not a command to
run before the fixture and prompt exist:

```sh
uv run python scripts/evaluation/isolated_run.py \
  --source "$CASE_SOURCE" \
  --ticket "$CASE_TICKET" \
  --prompt "$CASE_PROMPT" \
  --run-dir "$NEW_SESSION_DIR" \
  --timeout "$BUDGET_SECONDS"
```

For an intentionally resumed run, also supply `--resume-run` with the selected
ledger and `--deny-probe` with an existing prior report that must remain unreadable.
Use a new session directory and clearly distinguish selected durable history from
forbidden chat or evaluator knowledge. Read the current harness's recovery checks
before constructing a checkpoint.

Explain each case to the user before launch and provide meaningful updates at
least once a minute while working. Explain what the operator thought, what the
source actually showed, what remains uncertain and which change follows. Do not
narrate every command or call a completed process a successful investigation.

## External probes and interruptions

When an operator requests an external experiment, preserve its exact proposed
command and stop the operator first. Inspect the command, source provenance,
interpreter and intended assertions. Use `scripts/evaluation/run_experiment.py`
for its supported stopped-session handoff, after reading its request schema and
path requirements. It must still use Discovery's execution reservation, sandbox
and receipt registration, with restricted reads. Do not substitute a shell test
and imply it was a Discovery experiment.

If the handoff does not support the selected layout, record the limitation and
correct the harness with a focused test. Do not silently bypass it. Read the actual
receipt, including nested stderr, timeout and truncation flags, before recording
an outcome. A test that reproduces a defect is not a passing implementation proof.

Retain timeouts, setup errors, failed receipts and model errors. Record whether an
attempt failed before the model started. On permission or sandbox failure, request
an available approval when required; if the host disallows escalation, explain the
specific blocker. Never weaken isolation or claim an unexecuted phase completed.

## Inspect the evidence

For every session retain the manifest, frozen input hashes, raw events, timing
sidecar, stderr, result, exported documents, ledger, audit result and interventions.
Verify source integrity and authentication cleanup. Resumed sessions get automatic
audit snapshots; for cold runs locate the actual new ledger and explicitly run
`discovery --json --run /absolute/run/path audit verify`.

Use `summarize_runs.py` for observed counts and usage, but inspect the underlying
commands. One shell invocation can contain many CLI calls; observed JSON envelopes
are not an exact invocation count. Missing token usage is unavailable, not zero.

Assess the following with concrete references:

1. Intent: wrong premises, contradictions, relevant questions and proposed authority.
2. Research: source choice, reproducibility, counterevidence, missing facts and scope.
3. Structure: durable claims, provenance, canonical findings, valid transitions and recovery.
4. Proposal: justified alternatives and constraints, or a truthful reason no proposal is possible.
5. Challenge: actual attacks, missed cases, duplicated findings and unjustified exclusions.
6. Document: whether a reader without the chat can reconstruct the conclusion and next action.
7. Confidence: proposition scope, evidence, unknowns, stale assessments and separation from procedural assurance.
8. Effort: elapsed time, available token usage, repeated reads, command/help overhead and delivery timing.

For each observable use `demonstrated`, `partially_demonstrated`, `contradicted` or
`not_exercised`, with an evidence reference and limitation. Do not collapse the
whole batch into a pass rate.

Timing records show when the parent observed events and new nonempty delivery
files. Inspect the file before calling it useful. Files can be edited after first
observation, so their final contents do not prove what they contained at that first
time. Do not claim an exact reasoning versus bookkeeping split from buffered
events or infer missing historical timing.

## Fix and rerun

Finish both initial replicas of a paired case against the same frozen version
before changing behavior. Diagnose each concrete problem as a fixture issue,
evaluation harness issue, CLI invariant or usability issue, skill instruction
issue, or model reasoning failure. Explain that distinction in the report.

Fix justified Discovery problems during this task. Use focused tests for changed
invariants and process behavior, then repeat the affected scenario in a fresh
isolated session. Keep the original attempt untouched. Preserve identical inputs
and budgets when comparing versions; record any deliberate changes to task focus
or configuration as confounders. Do not add the fixture's expected answer to the
operator prompt or hardcode it into the skill.

Bound this handoff to the seven initial sessions and up to two corrective repeats
per affected scenario. This is a batch boundary, not a claim that Discovery cannot
improve further. If a blocker prevents a required session, preserve the failed
attempt and name the dependency rather than claiming coverage. Leave unresolved
findings explicit when the batch's repeat allowance is exhausted.

## Deliverables and completion

Write a new Markdown evaluation report in `docs/evaluations/` and append the
observations to the coverage ledger. Include inputs and controls, actual results,
source references, failed attempts, timing and cost limits, implementation changes,
validation and remaining uncertainty. Link the raw local evidence; do not commit
private fixtures, credentials, `.discovery/` databases or logs.

For source changes, run appropriate tests and lint, commit the intended changes,
and preserve unrelated work. If the operating skill changes, follow the existing
installation guide to synchronize its installed copies without changing the base
release merely to refresh a plugin cache. A user reload is not required to keep
using isolated sessions that freeze the current source skill.

Finish with a clear status: which cases ran, which could not run and why, what was
fixed, what the repeats showed, and whether any process remains active. Do not
leave a known authorized fix under an unexplained “future work” heading. The goal
is a defensible account of what we learned about Discovery, including where the
process still falls short.
