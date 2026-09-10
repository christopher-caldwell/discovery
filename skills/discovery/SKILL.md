---
name: discovery
description: Operate the local Discovery CLI to clarify a request, persist research plans and search provenance, inspect phase gates, or resume a Discovery run. Use when the user asks for Discovery or a durable pre-implementation discovery workflow; ordinary web research does not require it.
metadata:
  version: "0.2.0"
---

# Discovery

Use `discovery` for durable workflow state. The model interprets meaning; the CLI owns validation, transactions, phase revisions, evidence bookkeeping, and audit events. Treat incoming ticket statements as assertions until supported. Record questions, assumptions, observations, and conclusions distinctly.

## Start or resume

First run `discovery --version`. This skill targets release 0.2.0 and schema 4. If the executable is absent or incompatible, report the mismatch; do not improvise SQL or silently install a different tool.

For an existing run, begin with:

```sh
discovery --json --run /absolute/path/to/run resume
```

Use its current phase, gate violations, and legal next actions. Read its immutable request artifact when needed. SQLite state is authoritative; do not reconstruct current state from prior chat or replay the event log yourself. If multiple run directories are plausible, inspect their statuses and ask which to continue when intent remains ambiguous.

For a new run, establish the request file, source directory, and subagent preference. Ask about subagents if the user has not specified a preference. This release supports only `disabled`; explain that partitioned/overlap execution is unavailable if requested. Do not launch unmanaged reviewers to imitate supported agent execution.

Use `<source>/.discovery/runs/<generated-uuid>` unless the user selects another location. Ensure `.discovery/` is ignored before initialization; preserve existing ignore rules. Creating authorized Discovery state requires no additional generic branch confirmation: Discovery does not modify source files or create implementation worktrees. Do not initialize a run merely to test installation.

```sh
discovery --json --run /absolute/path/to/run \
  --request-id REQUEST_UUID --actor-id ACTOR_UUID \
  --actor-name 'Discovery investigator' --actor-kind model --session-id SESSION_UUID \
  run init --title 'Request title' --input /absolute/path/to/request.txt \
  --source /absolute/path/to/source --subagents disabled
```

Generate actual UUIDs. Use a model actor for your own submissions; never attribute your inference to a human. Use `question resolve` to record a genuine answer with its authority/source clear in the answer text. Missing human-authority answers remain questions.

## Command discipline

Global options precede the command; `--json` also works at the end. Every mutation needs a request UUID and actor identity. Retain the exact request and inputs until the outcome is known. Retry a lost response or `SQLITE_BUSY` with the same UUID and logical input. A new action needs a new UUID. Stop retrying if the same contention repeats without progress; preserve the request for later. Do not retry an `IDEMPOTENCY_CONFLICT` as though it were transient.

Read commands need only `--run` and `--json`. Inspect command help for required arguments:

```sh
discovery --run /absolute/path/to/run lane create --help
```

Supported command families (inspect help for each operation):

- `status`, `resume`, `audit verify`, `run upgrade`
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

Blocking is the default for questions. This release has no assumption/withdraw commands. Needs trace to the request artifact. Lanes must pose specific questions, link needs, and declare scope, impact, methods, and surfaces. Do not reduce impact to pass a gate.

Record actual searches with `research record`, including the query/procedure, result summary, origin URI, and immutable report file. A `searched` surface requires this activity. Other terminal dispositions require truthful reasons; unavailable/inaccessible/not_applicable are not convenient substitutes for unfinished work.

For semantic coverage review, inspect `plan snapshot`'s exact `context`, write a substantive report, and submit `plan review --plan-hash HASH --outcome passed|findings|inconclusive --report FILE`. Submit `passed` only when your semantic assessment supports it. Plan edits stale the review. A submitted review is attributed reasoning, not independent consensus or verified factual truth.

Use `phase check` to see all blockers. Its success exit code does not mean `can_advance` is true. `phase advance` moves exactly one step. When meaning needs correction, explicitly regress with a durable cause such as `--cause need:RN-001`; explain the defect in `--reason`. Preserve historical knowledge.

## Phase 2 investigation

Activate planned lanes and record research against lane surfaces. Link `research record` to a method with `--method M-001`. A completed method requires an actual linked research activity.

Capture saved source bytes with `artifact capture --file FILE --origin-uri URI`; add `--source-backed` for files in the source baseline. Register explicit evidence observations and locators, then claims and supporting/refuting/qualifying arguments. Classify direct/primary, secondary, or empirical evidence truthfully. A copied ticket is still an assertion. Verification reports are model/human judgments about the exact linked argument, not automatic fact checks.

Use `argument verify` to record an attributed report. `claim evaluate` computes admissibility and returns violations; an `ok:true` evaluation may still report `proposed` or `contested`. Do not present it as verified success unless its status is `admissible`. Material profiles need primary evidence and contradiction search; critical profiles also require empirical evidence and completed falsification/empirical methods. There is no confidence override or majority-vote resolution.

Register new leads with their source activity. Investigated leads require a separate same-lane activity. Other terminal dispositions require reasons and the corresponding duplicate/question link. A new lead invalidates closure even if later judged irrelevant. Material human-input leads need blocking questions. Use `question create --technical` for Phase 2 answer uncertainty; new uncertainty about request meaning requires regression to Phase 1.

Finish primary research, then `lane closure-begin`. Perform and record every generated closure method. If a new lead appears, investigate it and start a new closure iteration; old iteration records remain historical. Reevaluate material claims after the sweep, then `lane close --answer ... --limitations ...`. A known material answer needs an admissible claim at the lane's impact. A material `UNKNOWN` needs `--question Q-001` linked to a blocking question and can close procedurally while still blocking advancement. Answering that question reopens its dependent lanes so the answer is incorporated.

Use `research-need answer` after all covering lanes close. Phase 2 advances to Phase 3 only when needs are answered, lanes exhausted, claims supported, questions resolved, and source/audit checks pass.

`source refresh --reason ...` records a new baseline. It retracts evidence captured from the replaced baseline and reopens affected/dependent lanes, claims, and need answers. External snapshots are retained. Recapture source evidence and record new arguments as needed; refresh does not silently bless old evidence. This version invalidates by source baseline, not individual changed lines.

Schema 3 runs require the explicit transactional `run upgrade` command using ordinary mutation identity flags. Upgrade preserves history and the run's frozen policy, but a Phase 1 plan review may become stale after the added fields. Never reset a run to solve a version mismatch.

## Current boundaries

Phases 1 and 2 can complete and enter Phase 3. Phase 3–4 completion, leased/overlap agents, experiments, final rendering, and Taskledger handoff remain deferred. On `PHASE_NOT_IMPLEMENTED`, explain the boundary and preserve the run. Do not synthesize a finalized-spec claim from an incomplete run or edit state to bypass a gate.

Source drift blocks advancement. Audit corruption requires investigation, not automatic database repair. Use `audit verify` for integrity checks. Never write `discovery.sqlite` directly, alter captured artifacts, erase history, or run production mutations. Independent source edits, external messages, deployments, and installation changes require authorization appropriate to the user's actual task; a Discovery request alone does not authorize them.
