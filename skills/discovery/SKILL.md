---
name: discovery
description: Operate the local Discovery CLI to clarify a request, persist research plans and search provenance, inspect phase gates, or resume a Discovery run. Use when the user asks for Discovery or a durable pre-implementation discovery workflow; ordinary web research does not require it.
metadata:
  version: "0.2.0"
---

# Discovery

Use `discovery` for durable workflow state. The model interprets meaning; the CLI owns validation, transactions, phase revisions, evidence bookkeeping, and audit events. Treat incoming ticket statements as assertions until supported. Record questions, assumptions, observations, and conclusions distinctly.

## Start or resume

First run `discovery --version`. This skill targets release 0.2.0 and schema 6. Schema 5 runs remain readable; upgrade an active older run explicitly before mutation. If the executable is absent or incompatible, report the mismatch; do not improvise SQL or silently install a different tool.

For an existing run, begin with:

```sh
discovery --json --run /absolute/path/to/run resume --compact
```

Use its current phase, gate violations, and legal next actions. Compact recovery omits embedded execution payloads and export bundles; use ordinary `resume`, `experiment list`, or referenced receipt artifacts when those details are needed. It does not delete or reclassify history. Its
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

When the user supplies a time or token budget, check the remaining budget after
initial inspection and before expanding research. As soon as a useful answer or
blocking boundary is recorded, export a report and deliver its conclusion and
location; refine it within the remaining budget. Do not defer all delivery until
optional surface dispositions, repeated state reads, or additional formatting are
finished. A budget cutoff means incomplete work, never a passed gate.

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

## Conclusion confidence

For a conclusion-confidence assessment, read [confidence.md](references/confidence.md).
`assessment record --file FILE` stores an attributed assessment and `assessment list`
shows whether its evidence context is current. Interim and final exports distinguish
these support ratings from procedural assurance. Do not invent a percentage or force
an unresolved request through more phases merely to produce a score.

## Phase 2 investigation

For Phase 2 evidence gathering and lane closure, read [investigation.md](references/investigation.md) before recording or closing research.

## Design, experiments, and adversarial refinement

For Phase 3 design/proof or Phase 4 challenge work, read [design-review.md](references/design-review.md) before creating proposals, executing probes, or reviewing a draft.

## Leased investigators

When collaborators are enabled or an investigator lease is supplied, read [investigators.md](references/investigators.md) before dispatching or submitting work.

## Boundaries and recovery

All four phases support traversal through finalization. Explicit assumption/withdrawal conveniences, additional OS experiment adapters, and direct Taskledger ingestion remain extensions. The release number remains unchanged during development; check schema compatibility separately.

Source drift blocks advancement. Regress to Phase 2 (or Phase 1) before refresh and revalidation. Audit corruption requires investigation, not automatic repair. Never write the database directly, alter captured artifacts, erase history, bypass phase gates, or run production mutations. A finalized run rejects new mutations; preserve it as an immutable research package.
