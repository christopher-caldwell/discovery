---
name: discovery
description: Operate the local Discovery CLI to clarify a request, persist research plans and search provenance, inspect phase gates, or resume a Discovery run. Use when the user asks for Discovery or a durable pre-implementation discovery workflow; ordinary web research does not require it.
metadata:
  version: "0.2.0"
---

# Discovery

Use `discovery` for durable workflow state. The investigator judges meaning and
evidence relevance; the CLI owns transactions, history, freshness, procedural gates,
and legal transitions. Treat a ticket as assertions until supported. Never edit the
SQLite database or captured artifacts directly.

## Start or recover

Run `discovery --version`. This skill targets release 0.2.0 and schema 7. Schema 5
and 6 runs remain readable; upgrade an active older run explicitly before mutation.
If the executable is missing or incompatible, report that instead of improvising SQL.

Recover with `discovery --json --run /absolute/run resume --compact`. Compact recovery
retains phase, blockers, assumptions, contrary findings, research, gate failures, and
legal next actions while omitting large execution/export payloads. Read exact records
only when needed. SQLite is authoritative; do not rebuild state from chat or replay
the event log.

For a new run, establish the request file, source, and investigator preference. Ask
once only when the preference is missing. Honor `disabled`, `partitioned`, or
`overlap`; never silently choose a costlier mode. Ensure `.discovery/` is ignored.

```sh
discovery --json --run /absolute/source/.discovery/runs/RUN_UUID \
  --request-id REQUEST_UUID --actor-id ACTOR_UUID \
  --actor-name 'Discovery investigator' --actor-kind model --session-id SESSION_UUID \
  run init --title 'Request title' --input /absolute/request.txt \
  --source /absolute/source --subagents disabled
```

Use real UUIDs. Never attribute model inference or a convenient answer to a human.
Every mutation needs a new request UUID; retry a lost response with the same UUID and
identical logical input. An idempotency conflict is not transient.

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

## Phase 1 — intent and bounded plan

Read [request-vetting.md](references/request-vetting.md). Separate requested,
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

## Phase 2 — evidence and conclusions

Read [investigation.md](references/investigation.md). Use actual searches and source
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

## Phase 3 — design and validation

Read [design-review.md](references/design-review.md). Compare meaningful alternatives,
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

## Phase 4 — adversarial refinement

Attack actual assumptions, boundaries, failure modes, and proof strength. Mandatory
categories are a minimum with reasoned applicability, not duplicate approval text.
Use `challenge review` when one substantive report genuinely covers several related
checks. One defect may link to several categories but remains one finding. Confirming a
material flaw requires explicit regression to the earliest affected phase, followed
by normal traversal of every intervening gate. Old approvals never bless a revision.

Confidence is an attributed ordinal judgment, not probability or a gate. Read
[confidence.md](references/confidence.md) before `assessment record`. For actual
leased investigators, read [investigators.md](references/investigators.md); overlap
requires isolated outputs and preserves contradictions, minority findings, and failed
participation.

## Delivery and examples

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
