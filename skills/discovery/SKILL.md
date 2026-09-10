---
name: discovery
description: Operate the local Discovery CLI to clarify a request, persist research plans and search provenance, inspect phase gates, or resume a Discovery run. Use when the user asks for Discovery or a durable pre-implementation discovery workflow; ordinary web research does not require it.
metadata:
  version: "0.2.0"
---

# Discovery

Use `discovery` for durable workflow state. The model interprets meaning; the CLI owns validation, transactions, phase revisions, evidence bookkeeping, and audit events. Treat incoming ticket statements as assertions until supported. Record questions, assumptions, observations, and conclusions distinctly.

## Start or resume

First run `discovery --version`. This skill targets release 0.2.0 and schema 5. If the executable is absent or incompatible, report the mismatch; do not improvise SQL or silently install a different tool.

For an existing run, begin with:

```sh
discovery --json --run /absolute/path/to/run resume
```

Use its current phase, gate violations, and legal next actions. Its
`research_activities` and `research_reports` preserve earlier observations and
captured report paths; inspect those before repeating research. Read its immutable request artifact when needed. SQLite state is authoritative; do not reconstruct current state from prior chat or replay the event log yourself. If multiple run directories are plausible, inspect their statuses and ask which to continue when intent remains ambiguous.

For a new run, establish the request file, source directory, and subagent preference. Ask about subagents if the user has not specified a preference. Use `disabled`, `partitioned`, or `overlap` as requested. Ask whether overlap is desired when the user enables agents without choosing a mode. The CLI manages investigator state; the assistant launches actual workers after dispatch.

Use `<source>/.discovery/runs/<generated-uuid>` unless the user selects another location. Ensure `.discovery/` is ignored before initialization; preserve existing ignore rules. Creating authorized Discovery state requires no additional generic branch confirmation: Discovery does not modify source files or create implementation worktrees. Do not initialize a run merely to test installation.

```sh
discovery --json --run /absolute/path/to/run \
  --request-id REQUEST_UUID --actor-id ACTOR_UUID \
  --actor-name 'Discovery investigator' --actor-kind model --session-id SESSION_UUID \
  run init --title 'Request title' --input /absolute/path/to/request.txt \
  --source /absolute/path/to/source --subagents disabled
```

Generate actual UUIDs. Use a model actor for your own submissions; never attribute your inference to a human. Use `question resolve` to record a genuine answer with its authority/source clear in the answer text. Missing human-authority answers remain questions.

## Intent and proportionate research

Distinguish a source explanation from a proposed change before planning research.
For change requests, inspect the relevant governing product/technical contract as
well as code and operating guidance; preserve discrepancies as questions rather
than treating the ticket as authority. Before elaborating a blocked proposal, read
[request-vetting.md](references/request-vetting.md) for source selection, ownership
checks and stopping boundaries. Keep small questions scoped; do not reduce impact
or claim unfinished evidence review is complete to save effort.

For an explanation-only request, capture the source-supported answer and its
limits with `research record` on the relevant Phase 1 surfaces, then export the
interim report once useful. Do not create an implementation plan or finish every
planning surface merely to obtain an answer export. Unmet gates remain visible;
this route does not mean formal research closure or a finalized specification.

## Command discipline

Global options precede the command; `--json` also works at the end. Every mutation needs a request UUID and actor identity. Retain the exact request and inputs until the outcome is known. Retry a lost response or `SQLITE_BUSY` with the same UUID and logical input. A new action needs a new UUID. Stop retrying if the same contention repeats without progress; preserve the request for later. Do not retry an `IDEMPOTENCY_CONFLICT` as though it were transient.

Read commands need only `--run` and `--json`. Inspect command help for required arguments:

```sh
discovery --run /absolute/path/to/run lane create --help
```

Supported command families (inspect help for each operation):

- `status`, `resume`, `report export`, `audit verify`, `run upgrade`
- `artifact capture/list`, `source refresh/list`
- `lead create/list/disposition`, `method create/list/disposition`
- `evidence create/list/retract`, `claim create/list/check/evaluate/reject`
- `argument create/list/verify/resolve-counter`
- `question create/list/resolve`
- `research-need create/list/answer`
- `lane create/list/depends-on/activate/reopen/closure-begin/close/check`
- `surface list/disposition`, `research record/list`
- `plan snapshot/review`
- `phase check/advance/regress`

For a blocked investigation or an explanation that does not call for an implementation,
use `report export` to produce a non-final Markdown report and structured snapshot.
It preserves questions, observations, claim statuses, source drift and unmet gates;
it does not advance phases, assign conclusion confidence or finalize a specification.
Do not invent design work to obtain an export. The report remains explicitly interim
when formal evidence review is unfinished.

Blocking is the default for questions. This release has no assumption/withdraw commands. Needs trace to the request artifact. Lanes must pose specific questions, link needs, and declare scope, impact, methods, and surfaces. Do not reduce impact to pass a gate.

`question create --authority-confidence` takes a number from 0 to 1 describing
the proposed respondent's authority, not confidence in the answer. Repeat lane
`--surface` and `--method` flags for separate names. Research commands take a
surface reference (`S-001`), not a lane reference: Phase 1 uses current planning
surfaces with `research_lane_id: null`; lane surfaces are for Phase 2.

Record actual searches with `research record`, including the query/procedure, result summary, origin URI, and immutable report file. When the recorded search completes the work, add `--complete-surface "reason"`
to mark its surface searched in the same transaction. In Phase 2,
`--method M-001 --complete-method "reason"` also completes that linked method.
These flags require the actual recorded work and retain ordinary scope/closure
validation; omit them when more research is needed. A `searched` surface requires this activity. Other terminal dispositions require truthful reasons; unavailable/inaccessible/not_applicable are not convenient substitutes for unfinished work.

For semantic coverage review, inspect `plan snapshot`'s exact `context`, write a substantive report, and submit `plan review --plan-hash HASH --outcome passed|findings|inconclusive --report FILE`. Submit `passed` only when your semantic assessment supports it. Plan edits stale the review. A submitted review is attributed reasoning, not independent consensus or verified factual truth.

Use `phase check` to see all blockers. Its success exit code does not mean `can_advance` is true. `phase advance` moves exactly one step. When meaning needs correction, explicitly regress with a durable cause such as `--cause need:RN-001`; explain the defect in `--reason`. Preserve historical knowledge.

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

Schema 3/4 runs require the explicit transactional `run upgrade` command using ordinary mutation identity flags. Upgrade preserves history and the run's frozen policy, but a Phase 1 plan review may become stale after the added fields. Never reset a run to solve a version mismatch.

## Design, experiments, and adversarial refinement

Phase 3 selects one strategy, records accepted decisions traced to admissible claims, and creates impact-preserving proof obligations. Use `strategy create/select/reject`, `decision create/accept/reject`, `obligation create/attach-evidence/attach-experiment/satisfy/fail/block/not-applicable`, and `requirement create`. Requirements link an answered need, a decision, acceptance criteria, and a verification plan. Do not disguise unresolved decisions or proofs as contextual to pass gates.

`experiment plan` records a hypothesis and procedure. `experiment exec --command '["/usr/bin/python3","-c","print(123)"]'` copies the source baseline and executes in a macOS Seatbelt sandbox. Writes are limited to the copy and networking is denied. This is not a VM or protection against credential reads; the process can read filesystem content. Unsupported platforms fail closed. Do not execute untrusted arbitrary programs on the assumption that the copy alone isolates them. Additional output files stay in scratch and must be captured explicitly when needed as durable evidence.

Inspect captured exit code, `output_limited`, stdout/stderr, hashes, and limitations, then record `experiment finish --outcome ... --conclusion ... --limitations ...`. A zero exit does not prove the hypothesis. Before accepting empirical proof, read [evidence-review.md](references/evidence-review.md) and map each material conclusion to its actual assertion, receipt observation, and limitation. Execution has separately audited reservation and receipt-registration transactions. Retry the same request to recover a recorded receipt, never to rerun. Output capture stops the process group when either stream exceeds 2,000,000 bytes; an output-limited result cannot pass. On `EXPERIMENT_INTERRUPTED`, inspect the existing scratch attempt and stop any surviving child process (a killed controller cannot clean it up), then abort it explicitly and create a replacement. Do not hide failed attempts or delete their records.

Write substantive technical narrative and use `spec draft --narrative FILE`. Structured changes stale the draft. Phase 3 advances only after traceability and proof gates pass.

For multiline probes, prepare a JSON argv file without shell quoting:

```sh
python3 /path/to/discovery/skill/scripts/prepare_experiment.py --script /absolute/probe.py --output /absolute/command.json
discovery ... experiment exec EXP-001 --command-file /absolute/command.json
```

Resolve the helper relative to this skill. It embeds the exact script bytes, preserves the sandbox working directory, and refuses to overwrite a copied project file with the same basename. It only prepares argv; the CLI executes it. A source script already in the baseline can instead use a JSON argv file such as `["/usr/bin/python3", "probe.py"]`. Retain the command file unchanged for retries; edited bytes with the same request are a conflict. The interpreter must exist in the sandbox host environment.

In Phase 4, use `challenge initialize` to create the configured checks against the exact draft. Try to break the design; submit actual reports with `challenge complete`. Read [evidence-review.md](references/evidence-review.md) for category-specific attacks, observations, and evidence limits; generic pass statements are insufficient. Findings need linked `defeater create` records targeting a claim or decision with evidence. `defeater confirm` requires explicit regression before repair; `defeater defeat` needs distinct active resolution evidence and a report. Only contextual risks can be accepted. Revision with `spec revise` requires a fresh set of checks; prior defeaters are not erased.

`assurance calculate` reports procedural coverage, not correctness probabilities. Scores never override gates. Phase 4 `phase advance` atomically compiles final artifacts, records scores, and finalizes the run. `spec export` materializes `technical-spec.md`, `discovery-summary.md`, `evidence-manifest.json`, and `handoff.json`. It does not submit work to Taskledger. Describe remaining limitations honestly even when all structural gates pass.

## Leased investigators

For Phase 2 use `group dispatch --lane L-001 --count N`; Phase 4 omits `--lane` and targets the current draft. Partitioned groups contain one investigator, overlap groups 2–8. Each replica must receive an actor UUID distinct from the orchestrator and other replicas, an independent session, and a fresh random lease of at least 32 characters. Do not put the raw lease into authored reports or shared prompts; give it only to its worker.

Start with global `--lease TOKEN` before `agent start AR-001`. The CLI stores only its hash. Give each worker `--agent-run AR-001 --lease TOKEN resume` and its immutable context. Do not share sibling findings or your preferred conclusion. Workers submit `agent finding` with `support`, `refute`, `not_seen`, or `unique`, source/report provenance, and impact; Phase 4 accepts challenges or `not_seen`. Use `agent heartbeat` during long read-only work and `agent complete --outcome ... --report FILE` at the end. Expired leases require `agent reclaim` with a new token; stale tokens cannot write.

Workers submit isolated findings rather than canonical mutations. Scope is enforced through these CLI interfaces, not authenticated against someone deliberately inventing another actor or reading the shared filesystem directly. Keep workers on their provided context and source scope.

Only after every requested replica completes may the orchestrator run `finding reconcile` and `group reconcile`. Substantive findings become leads or defeaters; `not_seen` is not a negative vote. Imported reports are secondary evidence requiring direct corroboration and semantic verification. A credible material refutation contests the claim regardless of supporting counts. If a replica fails, supersede the group with a reason and dispatch a new group; do not reduce the denominator to claim consensus.

## Boundaries and recovery

All four phases support traversal through finalization. Explicit assumption/withdrawal conveniences, additional OS experiment adapters, and direct Taskledger ingestion remain extensions. The release number remains unchanged during development; check schema compatibility separately.

Source drift blocks advancement. Regress to Phase 2 (or Phase 1) before refresh and revalidation. Audit corruption requires investigation, not automatic repair. Never write the database directly, alter captured artifacts, erase history, bypass phase gates, or run production mutations. A finalized run rejects new mutations; preserve it as an immutable research package.
