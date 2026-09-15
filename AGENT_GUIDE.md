# Discovery agent guide

Use `discovery` for durable workflow state. The investigator judges meaning and
evidence relevance; the CLI owns transactions, history, freshness, procedural gates,
and legal transitions. Treat a ticket as assertions until supported. Never edit the
SQLite database or captured artifacts directly.

## One guide, any agent

This is the shared operating guide for Cursor, Codex, Claude Code, or another agent
that can read Markdown, run local commands, and read/write local files. It requires
no provider API, agent-specific rules file, plugin, slash command, or skill registry.
Use this guide when the user requests a Discovery investigation or continuation.
When asked to develop or document the Discovery tool itself, work on that request
normally; do not start an investigation or treat the no-implementation boundary as
a ban on maintaining this repository.

You operate Discovery on the user's behalf. Take the supplied request through the
four phases to an exported technical specification. Do not stop after setup, a plan,
or a passed intermediate gate. Discovery ends before implementing the target feature.
For explanation-only work or a genuine blocker, export an honest interim report.

If a skill loader has already resolved an installed executable or uv command prefix,
retain it for every command in this guide. Command examples use `discovery` as shorthand.

The CLI and this guide must come from the same build. Run `discovery --version` and
`discovery guide`. This source targets release 0.2.0 and schema 7. The installed
`guide` command is authoritative for that installation, including when an attached
or cached skill is older. Guide and help commands do not need a run directory.
If `guide` is unknown, use the current checkout as below or report the older runtime;
do not silently operate a new guide against an incompatible executable.

If `discovery` is absent and the user supplied a Discovery checkout, use
`uv run --project /absolute/path/to/discovery discovery` as the command prefix
throughout, including for `guide`, help, and every run command. This prepares the
checkout environment without installing anything in a particular agent application.
If neither executable nor checkout is available, state the missing prerequisite and
ask for the checkout or an installed CLI. Do not guess a package registry/repository
address. See the README for installation. Do not rewrite global agent configuration.

Detailed references are available from the installed CLI even if the user supplied
only this Markdown file. Read the topic needed for the current phase:

```sh
discovery guide --topic request-vetting
discovery guide --topic investigation
discovery guide --topic design-review
discovery guide --topic evidence-review
discovery guide --topic confidence
discovery guide --topic investigators
```

Relative reference links below are a convenience when the full skill folder is
present. If a linked file is absent, use its basename without `.md` as `--topic`.
Do not require the user to install those files separately. Use the host's ordinary
shell, file, browser/search, and conversation tools; no particular tool API name is
required. Missing web access means unavailable evidence, not invented research.

## Start or recover

1. Establish the source path from the user or the current project. Ask only if it is
   genuinely ambiguous. Inspect the supplied request and existing context before
   asking for information already available.
2. If the user supplied a run path, recover it. For a request to continue without a
   path, inspect `<source>/.discovery/runs/` for `discovery.sqlite` and read candidate
   runs. Select only a clearly matching run; ask when several remain plausible.
   Do not initialize a replacement to bypass a blocked, interrupted, or older run.
3. For new work, use a supplied request file unchanged. If the request is in chat,
   preserve its wording in `<source>/.discovery/requests/<uuid>.md` yourself. Include
   relevant user corrections with attribution; keep your interpretation separate.
   Do not make the user write a ticket or fill out a CLI setup form.
4. Keep generated reports, probe inputs, and run data under `.discovery/`. In Git
   repositories, check that `.discovery/` is ignored before baseline capture; if
   necessary append `/.discovery/` to the repository's local Git exclude file without
   overwriting existing entries (locate it with `git rev-parse --git-path info/exclude`).
   Do not modify tracked project configuration for agent setup. Non-Git directories
   are also supported. Respect any user-supplied run location.
5. Choose a unique run directory such as `<source>/.discovery/runs/<uuid>`. Generate
   actor, session, and request UUIDs yourself with Python `uuid.uuid4()` or the host's
   UUID generator. Use one actor for your actual investigator identity and one session
   per chat session. Record the run path in the chat so another agent can continue.
6. Use the default single investigator (`disabled`) unless the user requested
   `partitioned` or `overlap`. Do not ask about modes as a setup question. Those modes
   require the host to launch separate sessions; Discovery never launches models.
   If an explicitly requested mode is unavailable, explain that limitation and ask
   whether a single investigator is acceptable before initializing a different mode.

```sh
discovery --json --run /absolute/source/.discovery/runs/RUN_UUID \
  --request-id REQUEST_UUID --actor-id ACTOR_UUID \
  --actor-name 'Discovery investigator' --actor-kind model --session-id SESSION_UUID \
  run init --title 'Request title' --input /absolute/request.md \
  --source /absolute/source

discovery --json --run /absolute/source/.discovery/runs/RUN_UUID resume --compact
```

Replace placeholders with real paths and UUIDs; read returned record references
instead of guessing `S-001`, `L-001`, or other IDs. Global options precede the command
family; `--json` may appear anywhere. All stateful operations require `--run`.
Every mutation needs a new request UUID and the actor flags above. Read commands need
only the run path. Never attribute model inference or a convenient answer to a human.

Keep the exact argv, request UUID, actor identity, and input files until each mutation
has a known result. Retry an uncertain response or transient `SQLITE_BUSY` with the
same logical input and UUID. An idempotency conflict is not transient. Never generate
a fresh request UUID merely to retry. Keep shell arguments properly quoted; prefer
argv arrays from a process API for arbitrary request text and paths with spaces.

Recovery starts with `resume --compact`. It retains phase, blockers, assumptions,
contrary findings, research reports, gate failures, and legal next actions. Follow
artifact paths to saved research before repeating it. Read focused lists or full
`resume` only when needed. SQLite is authoritative; do not rebuild state from chat or
replay the event log. A new agent uses a new actor/session identity and the same run,
without impersonating an earlier investigator. Leased workers use their assigned
identity and lease instead. Audit a run before upgrading an active schema 3–6 run
with `run upgrade`; never reset it. Finalized schema 5/6 runs remain readable.

## Continue until delivery or a real blocker

After each meaningful action, inspect its JSON result. `ok:true` means the command
ran, not that the conclusion was admitted or a gate passed. Check claim status and
`phase check`'s `can_advance`. Resolve the named gaps through actual research, then
use `phase advance` for one step. Re-read `resume --compact` after transitions,
regressions, interruptions, or conflicting state. Do not repeatedly poll a gate whose
inputs have not changed, fabricate reports to satisfy it, or reduce claim impact to
avoid proof requirements.

Continue authorized local work without asking the user to approve each command,
research lane, gate transition, or internal bookkeeping choice. Keep chat updates
focused on findings and decisions. Use ordinary chat questions for missing product
intent, authority, access, or a material scope choice. Ask a focused question, record
it, and continue independent useful work. Honor the host's actual permission rules;
this guide supplies no authorization to contact people or mutate external systems.

When no useful authorized work remains, export `report export`, give the user its
path and the exact unresolved question or missing prerequisite, and retain the run
for resumption. A blocker is a supported outcome, not permission to invent an answer.
A long task may need another session; leave the run path and next action, and describe
that as unfinished work. Do not promise unattended/background execution unless the
host actually supports it and the user requested it.

## Work in operator actions

Think in outcomes: clarify intent, preserve uncertainty, record what a search
established, evaluate a claim, compare designs, test a hypothesis, and challenge the
draft. Inspect `--help` only when an action's arguments are unclear.

Prefer `research capture` when one saved result supports observations. Prefer
`research finding` when the same natural action also proposes a claim and its supporting
argument. Both preserve explicit evidence classification and provenance. Neither
verifies an argument, admits a claim, closes a lane, or advances a phase. Use lower-level
operations for unusual provenance. Persist evidence while gathering it; a registered
search is not proof that a source is correct or exhaustive.

Creating a critical claim automatically provisions its falsification obligation. Use
`claim challenge` to record one substantive attempt to disprove it: the operation
bundles report capture, observations, evidence, argument linkage, and method completion.
Choose `supports`, `refutes`, or `qualifies` according to what the attempt found. Then
verify the argument and evaluate the claim explicitly; the bundled operation never
does either semantic step and never closes or advances work.

## Phase 1: intent and bounded plan

Read [request-vetting.md](skills/discovery/references/request-vetting.md). Separate requested,
observed, intended, inferred, and proposed behavior. A missing product rule,
permission, or business definition may block. A delegated technical choice normally
becomes research and a recommendation; do not ask the human to design the solution.

Questions block by default. `question assume` applies only to a non-blocking question
and records the assumption, why it is safe, its scope, and what invalidates it.
Blocking and critical uncertainty cannot be assumed away. `question withdraw` and
`question reclassify` correct mistakes without deletion. A real answer uses
`question resolve`; for an assumed question, declare `--confirms-assumption` or
`--contradicts-assumption`. A contradiction invalidates dependent conclusions.

Use `question respondent-add` for ranked authority hypotheses. Record an authority
category first, then evidence-backed role/group/person candidates. Use
`--identity-unknown` when the individual is unknown. Do not infer authority merely
from file authorship and do not invent people.

The seven initialized discovery surfaces are a minimum. Add a useful request-tied
surface with `surface create --name ... --reason ...`. Once added, research it or
record an honest `unavailable`, `inaccessible`, or `not_applicable` disposition. It
remains an obligation across recovery and Phase-1 regression. There is no generic
skip. Needs trace to the request; lanes require a scoped question, rationale, impact,
methods, and surfaces.

Review the `plan snapshot` context and submit a substantive `plan review`; the command
binds the report to the current snapshot automatically. Use `--plan-hash` only when an
external workflow needs to assert a previously read hash. Edits stale the review. Stop
Phase 1 when intent is adequate and the reviewed plan covers the
consequential unknowns, or export an interim report when only unavailable authority
can resolve a blocker. Continue independent useful research while blocked, but do
not conduct assumption-dependent design or mark later phases complete.

## Phase 2: evidence and conclusions

Read [investigation.md](skills/discovery/references/investigation.md). Use actual searches and source
locations. Reuse evidence with its original provenance instead of recapturing bytes.
Register contrary evidence and resolve or narrow it explicitly; supporting counts do
not outvote an evidenced objection.

For each claim select `inspection`, `analysis`, `authoritative_record`, `test`, or
`experiment`, explain why it fits what the claim asserts, and record unavailable
required proof honestly. Consequence still controls challenge depth, but critical
business intent does not require an irrelevant runtime experiment. Claims from tests
or experiments require empirical observations; authority claims require a primary
authoritative record. Product intent specifically requires authoritative support;
runtime experiments cannot establish what the product owner wants.

New leads reopen only affected lanes and dependents. Closure depth is proportional:
contextual lanes check evidence gaps; material lanes also search for contradiction;
critical lanes additionally expand terminology and relationships. Complete a fresh
closure cycle after a new eligible lead. Stop when required lanes are exhausted and
material conclusions are admitted, rejected, or explicitly unknown. A material
unknown that blocks implementation remains linked to a blocking question.

## Phase 3: design and validation

Read [design-review.md](skills/discovery/references/design-review.md). Compare meaningful alternatives,
select one strategy, record decisions, requirements, acceptance criteria, and proof
obligations. Link decisions to admissible claims or active assumptions; link the
assumption dependency explicitly so invalidation stales affected work. Draft the
engineer-facing answer only when the current evidence supports it.

Ordinary `experiment exec` runs a reviewed command in a disposable local copy with a
scrubbed environment and a recorded receipt. It is intentionally platform-neutral and
is not a security sandbox. It does not prevent filesystem, network, credential,
process, or service effects. Run only against disposable local databases and synthetic
or sanitized fixtures. Never pass production credentials, contact mutation-capable
live services, or execute a hypothesis that could mutate live data. Use deliberately
read-only providers outside the experiment subprocess for live research, capture their
results as evidence, and record a live-mutation-dependent hypothesis as blocked.
`--execution-mode restricted` optionally requests macOS Seatbelt containment and never
falls back. Exit zero does not prove a hypothesis; a reproduction is evidence of the
defect, not of its repair.

## Phase 4: adversarial refinement

Attack actual assumptions, boundaries, failure modes, and proof strength. Mandatory
categories are a minimum with reasoned applicability, not duplicate approval text.
Use `challenge review` when one substantive report genuinely covers several related
checks. One defect may link to several categories but remains one finding. Confirming a
material flaw requires explicit regression to the earliest affected phase, followed
by normal traversal of every intervening gate. Old approvals never bless a revision.

Confidence is an attributed ordinal judgment, not probability or a gate. Read
[confidence.md](skills/discovery/references/confidence.md) before `assessment record`. For actual
leased investigators, read [investigators.md](skills/discovery/references/investigators.md); overlap
requires isolated outputs and preserves contradictions, minority findings, and failed
participation.

## Delivery and examples

In Phase 4, initialize and complete the current draft's challenges, inspect
`phase check`, then `phase advance` to finalize when it passes. Run `spec export`
and use the returned paths to deliver `technical-spec.md`, `discovery-summary.md`,
`handoff.json`, and `evidence-manifest.json`. Link the specification first and state
remaining conditions. Do not claim finalization based only on a draft or export.

Use `report export` at any phase for a useful blocked/interim result. It does not
advance or finalize. Final delivery is the technical specification, not the ledger:
lead with the answer, scope, changed/unchanged behavior, evidence, alternatives,
acceptance criteria, validation, assumptions, challenges, risks, and next action.
The renderer owns its single H1; begin authored narrative at the executive conclusion
or use a leading H1 knowing it will be removed as redundant.
Keep the run directory because artifact references resolve through it.

- Blocking: “Which tenants may see these records?” stays with product/security;
  inspect existing authorization independently and export useful verified context.
- Safe assumption: a display-only label may default to the repository name; record
  its scope and the owner answer that would invalidate it.
- Delegated engineering: research which existing storage abstraction implements an
  agreed visibility rule and recommend one; do not ask the owner to choose a class.
- Contrary evidence: preserve the refuting/qualifying argument. Narrowing a claim
  requires a newly reviewed assertion, not silent substitution.
- Failed probe: retain the receipt and mark failed, blocked, or inconclusive according
  to what it observed; never hide it or rerun under a new story.
- Regression: a Phase-4 durability flaw returns to Phase 2 if evidence was wrong or
  Phase 3 if only design was wrong, then traverses every gate again.

Forward progression is always `1 → 2 → 3 → 4 → finalized`; `phase advance` moves one
step. History, retry protection, audit integrity, agent ownership, artifact retention,
and source-freshness checks remain mandatory. Discovery is not a security-platform
project; stronger containment is optional infrastructure, not an ordinary workflow
prerequisite.
