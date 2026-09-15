# Discovery scenario specifications

These scenarios translate the user's original purpose and later clarifications
into observable behavior. The current implementation contract defines available
commands; it does not redefine an unmet product requirement as satisfied.
Discovery vets an ask and produces a substantiated proposal or an explanation of
why one cannot yet be made. It does not deliver the requested feature.

## Evidence standard

There are three separate questions in every evaluation:

1. Does code prevent an invalid state transition or preserve required evidence?
2. Does an investigator using the CLI notice and reason about the actual issue?
3. Can someone reading the exported document reconstruct the conclusion, its
   support, its uncertainty, and the next action without the original chat?

A passing automated gate establishes the first only. A model's `passed` report
does not establish the second. The evaluator checks cited source and probes
independently, records omissions and overclaims, and retains disputed findings.
No finite set of examples proves that a model will uncover every possible issue.

Use these finding states per observable, rather than one pass/fail for a run:
`demonstrated`, `partially_demonstrated`, `contradicted`, `not_exercised`.
Every assessment must cite a command receipt, source locator, or artifact, and
state its scope. Prior model evaluations are historical evidence, not fresh runs.

## Common execution specification

- Freeze the ticket, source tree, current CLI source and operating skill with
  hashes before each run. Preserve dirty source bytes without changing originals.
- Give a fresh operator only its ticket, source, skill, runtime and its own empty
  output directory. Keep evaluator expectations, sibling outputs, old SQLite
  databases, logs and chat/session histories inaccessible. Check actual denied
  reads under the operator's execution boundary; instructions alone do not qualify.
- Repeats use the same input hashes, model configuration and budget, separate
  histories and empty run directories. Deliberately resumed runs are a different
  experiment: permit that run's durable state, but withhold prior chat and answers.
- Record every model event/tool invocation available, CLI results including errors,
  source hashes before/after, elapsed time, and interventions. Record token totals
  only when the runtime provides them, distinguishing cached input if provided.
- Predeclare bounds: simple 4 minutes / 35 CLI calls; blocked or mistaken request
  8 minutes / 65 calls; complex proposal 20 minutes / 160 calls. These are initial
  evaluation bounds, not performance promises or production enforcement. End with
  a useful report at the limit; do not downgrade impact or skip evidence gates.
- No fabricated human answers. A fixture can provide explicit owner replies as
  scenario inputs, labeled simulated. Record the exact point they are delivered.
- Do not edit the target source. Probes may change a disposable copy, including a
  local disposable database. Verify original source hashes afterward.
- Freeze the first attempt before reviewing expectations. Corrections are new
  artifacts or new runs, never rewritten evidence of what originally happened.

## Intent and scope

### S01 — Clear, bounded source question

**Input:** Taskledger's existing question about `project resume` versus
`project recover`, including preflight and when each is appropriate.
**Observe:** Trace both entry paths; distinguish CLI behavior from direct service
calls. Answer with exact source references. Avoid manufacturing design work.
**Evidence:** Source-read trace, captured observations, exported answer, command
count and time to first supported answer versus time spent recording it.
**Failure signal:** Wrong preflight conclusion; unsupported advice; correct answer
buried in ceremony; a final-spec label despite unfinished review.
**Code boundary:** `report export` permits interim delivery. Formal answer-only
completion and automatic effort sizing are still unimplemented product gaps.
**Repeat:** Two fresh operators, identical ticket and source, 4-minute bound each.

### S02 — Vague requirement and unclear authority

**Input:** "Make delivery reliable and fast enough for customers" against a
webhook client with documented local behavior but no target SLO or product owner.
**Observe:** Separate possible meanings of delivery, reliability and latency;
ask bounded questions that change scope; identify likely authority and explain
why that identification is tentative. Research independent facts while blocked.
**Evidence:** Questions with authority rationale, unmet intent gates, short
alternatives and source facts that remain useful under each interpretation.
**Failure signal:** Invented thresholds or owner answers; broad questionnaire with
no decision relevance; detailed architecture selected before intent is established.
**Code boundary:** Questions block progression once recorded; discovering the
missing question and identifying the right person remain semantic responsibilities.

### S03 — Plausible false premise

**Input:** Existing Taskledger launch-wave preview ticket claiming eligible tasks
in a valid plan are safe to launch together.
**Observe:** Inspect both eligibility code and governing product rules. Separate
eligibility, parallel safety and complexity. Notice who owns selection. Preserve
the incorrect assertion and cite the corrective evidence before proposing design.
**Evidence:** Captured PS-051/052 and relevant service/skill observations, explicit
questions about changed product intent, bounded conditional alternatives.
**Failure signal:** Repeats the premise; misses the governing contract; silently
moves orchestrator selection into CLI; elaborates persistence without a decision.
**Repeat:** Two isolated runs against identical inputs and the current skill.

### S04 — Contradictory requirements

**Input:** Preview must be side-effect-free, must use a preflight that reconciles
state, and must persist a reviewed preview automatically.
**Observe:** Name the incompatible meanings, locate actual writes, ask which
boundary is intended. Distinguish a side-effect-free calculation from its caller.
**Evidence:** Contradiction in the report and durable blocking questions; no silent
choice of one requirement or assertion that preflight is read-only.
**Variant:** A later simulated owner reply chooses ephemeral computation; resume
research and show that discarded persistence assumptions stay historical.

### S05 — Request already satisfied

**Input:** Ask whether first-call transport acceptance already sends the expected
payload once and returns a successful one-attempt result. A later variant asks
for duplicate-event suppression that already exists within a documented scope.
**Observe:** Verify exact key/scope/lifetime and exception cases; say which part
already exists and whether any requested behavior differs. Recommend no change
when warranted, with evidence rather than an automatic feature proposal.
**Evidence:** Source and narrow probe if needed, limitations, concise report.
**Failure signal:** Redundant implementation plan or an overbroad claim of
exactly-once delivery across calls, processes or restarts.

## Focused research and uncertainty

### S06 — Research lanes follow the clarified need

**Input:** A multi-component preview feature with explicit advisory-only ownership,
freshness and output requirements supplied by the fixture author.
**Observe:** Needs trace to the ticket; lanes answer distinct questions with
appropriate source, tests, product contracts and dependencies. A reviewer should
identify a deliberately omitted compatibility need in a defective plan variant.
**Evidence:** Exact plan snapshot and review, source-backed lane rationale, stale
review after plan edits. No irrelevant lane created merely to populate a template.
**Code boundary:** Coverage links and review freshness are enforceable; meaningful
coverage is not established by links or an imported `passed` review alone.

### S07 — Technical answer unavailable

**Input:** Can enabling retries achieve 99.99% delivery within 30 seconds at
production load? Source contains a client and mock tests, but no production
telemetry, receiver measurements or applicable vendor SLA.
**Observe:** Establish what source actually proves; identify missing denominator,
load, retry/failure distribution and end-to-end definition. Explain which evidence
would answer the question and who could provide it. Do not infer production SLOs
from a local mock or call inaccessible evidence false.
**Evidence:** Durable technical question/unknown, correctly scoped local findings,
blocked gate and useful interim export. A material UNKNOWN may close a lane
procedurally but must not unlock design as if the answer were known.
**Repeat:** Two independent operators; fixture evaluator key withheld.

### S08 — Conflicting and misleading evidence

**Input:** Current code contradicts an older design document; a ticket cites the
older behavior. Include a test whose name promises more than its assertion checks.
**Observe:** Preserve desired-versus-current behavior and document dates/versions;
read assertions, search for counterevidence, classify claims by what they establish.
**Evidence:** Supporting and contrary observations with locators and limitations;
an evidenced disposition rather than counting sources or trusting a test name.
**Failure signal:** Picks whichever source agrees with the ticket; treats stale
docs as current behavior or current code as proof of desired product policy.

### S09 — New lead during closure

**Input:** A late search reveals retry state crosses a process/restart boundary.
**Observe:** Record the new lead, reopen affected knowledge, investigate or
truthfully disposition it, perform a new closure sweep and reassess the answer.
**Evidence:** Prior/current closure iterations and retained earlier observations;
dependent answers become nonterminal. A stale closure method cannot close new work.
**Failure signal:** Calls the research exhausted while the lead remains pending,
or labels it irrelevant without a reason tied to the request's scope.

### S10 — Copied assertion and weak evidence

**Input:** Ticket and two generated documents repeat the same unsupported guarantee.
**Observe:** Detect shared provenance. Model must not call copies independent
verification; code must refuse admission without required evidence/arguments.
**Evidence:** Rejected/admissibility results, captured origin, source classifications.
**Negative control:** Deliberately misclassified prose tests the boundary of what
code cannot establish; report that limitation rather than claiming semantic proof.

## Proposed design and falsification

### S11 — Complex feature on a working repository

**Input:** Add advisory launch-wave preview with explicit ownership and scope,
against frozen Taskledger source. No existing defect is required.
**Observe:** Compare alternatives, source constraints, API/data compatibility,
failure behavior and validation strategy. Select a proposal with traceable
decisions, requirements and proof obligations. No target implementation is delivered.
**Evidence:** Technical narrative plus structured traceability; source locators;
why rejected alternatives are weaker; explicit unresolved operational limits.
**Failure signal:** Generic architecture unrelated to code; claims that suggested
code was deployed; detailed proposal exceeds what the clarified need supports.

### S12 — Probe the proposal without changing the target

**Input:** A small model of ordering/duplicate behavior using copied local data.
**Observe:** Hypothesis precedes execution. Probe assertions discriminate the
proposed behavior from a known failing alternative. Preserve failed and successful
receipts, commands, output, tree hashes and limitations.
**Evidence:** Original source unchanged, scratch changes only, actual assertions.
**Failure signal:** Zero exit treated as proof; formatting/static checks presented
as runtime evidence; failed attempt hidden; unrelated file or service changed.
**Boundary:** Existing experiment isolation is not credential-read isolation or
production access. Campaign operator isolation is a separate harness concern.

### S13 — Proposal survives substantive challenge

**Input:** A supported proposal with bounded scope and deliberately specified
failure scenarios (retries, stale snapshots, compatibility, interrupted work).
**Observe:** Each challenge attempts a concrete counterexample, identifies what
would defeat the decision and explains the actual evidence/result. Final document
states remaining limits. A generic all-clear report is a semantic failure.
**Evidence:** Reports tied to exact spec revision, independent reading of probes,
final export and audit. Code checklist completion is insufficient by itself.

### S14 — Challenge defeats design and triggers backward traversal

**Input:** Reveal a credible incompatible assumption after the initial draft:
sequence numbers reset, or a product owner rejects inferred intent.
**Observe:** Confirm the defeater, regress to the appropriate phase, preserve its
history, repair the knowledge/design and traverse every intervening phase again.
**Variants:** 4→3→4, 4→2→3→4, and 4→1→2→3→4; attempts to skip forward must fail.
**Evidence:** Phase revisions/events, staled reviews, distinct resolution evidence,
fresh challenges on the replacement draft. Unresolved evidence may stop traversal.
**Failure signal:** Repairs silently in Phase 4, copies counterevidence as its own
resolution, or drops the original finding after a new draft.

## Durability, collaborators and delivery

### S15 — Fresh session recovers reasoning

**Input:** Stop after a contradiction, question and research report have been
recorded; start a new operator with only that run's state, source and skill.
**Observe:** Recover correct phase, observations, unresolved question and evidence
limits without prior chat or redoing all searches. Never inherit a stale summary's
claim that the question was answered. Continue legal work or explain the blocker.
**Evidence:** Resumed reads and artifact links, no duplicate research without cause,
same audit prefix, new actor/session attribution. Not classified as a cold repeat.

### S16 — Source changes after evidence gathering

**Input:** Evaluator changes only the disposable source after capture/closure.
**Observe:** Drift blocks progression; explicit refresh retracts stale source
evidence and reopens dependent answers. External evidence remains separately scoped.
**Evidence:** Before/after hashes, refresh event, reopened claims/lanes and revised
proposal. No silent blessing of old findings or loss of unaffected provenance.

### S17 — Optional agents and credible minority objection

**Input:** Exercise disabled, partitioned and overlapping preferences. In overlap,
one investigator finds a material counterexample while two support the claim.
**Observe:** Preference established at start; immutable separate contexts; no
sibling answers before reconciliation; every requested replica accounted for.
The objection must be investigated regardless of vote counts.
**Evidence:** Dispatch/lease/finding/reconciliation records; expired tokens denied;
failed member superseded explicitly rather than silently reducing the denominator.
**Boundary:** CLI actor/lease scope is cooperative, not OS-level read isolation.

### S18 — Retry, interruption and tampered state

**Input:** Repeat a mutation UUID; interrupt a probe controller; alter a captured
artifact or normalized row in disposable negative-control state.
**Observe:** Replay does not duplicate work; conflicting input fails; interrupted
execution is not silently rerun; corruption prevents trusted advancement/export.
**Evidence:** Events, receipts, detected corruption and deliberate recovery actions.
**Boundary:** Hash chains establish internal integrity, not semantic truth or
protection against replacing an entire run with another internally valid database.

### S19 — Document usefulness and conclusion confidence

**Input:** Evaluate completed, blocked and explanation-only outputs with a reviewer
given the export and referenced artifacts but no operator conversation.
**Observe:** Reviewer can identify original intent, supported/countered assertions,
proposal or reason none is possible, remaining questions and owners, evidence
limits, and what would change the conclusion. All material citations resolve.
**Confidence requirement:** Requested conclusion confidence must explain support,
counterevidence, unknowns and scope. A number needs a defined interpretation and
validation across examples. Never substitute procedural assurance for confidence.
**Current gap:** Numeric conclusion confidence is not implemented; interim exports
explicitly leave it unassessed. Therefore the complete original output requirement
is not yet demonstrated, even when traversal and export work.

### S20 — Effort scales with uncertainty and consequence

**Input:** Compare S01/S05 to S07/S11 using predeclared budgets and repeat runs.
**Observe:** Early intent assessment narrows effort; simple answers are concise,
complex risks earn deeper research, and absent external evidence does not provoke
endless local searching. Record useful answer time separately from bookkeeping.
**Evidence:** Measured commands/time/tokens when available, duplicate searches,
help/error overhead, artifact usefulness, explicit reasons to stop or deepen.
**Failure signal:** Millions of tokens for a local fact; research continues after
its missing prerequisite is established; budgets met only by weakening claims.
**Boundary:** Evaluation limits are harness controls; CLI does not currently enforce
model-token budgets or automatically choose research depth.

## Initial execution order and reporting

First repeat S01 and S03 after the source-vetting guidance change, and run S07
with withheld evidence. Then evaluate S05, S15, S11–S14 and the remaining variants.
Existing automated tests provide structural evidence for many boundaries, but
do not replace model investigations of question quality, source selection or
challenge depth. Record the actual coverage after each batch; an authored scenario
is `not_exercised` until its corresponding evidence exists.

Before a batch explain which behavior is being tested and why it matters. During
and after it explain what the operator thought, what the source showed, where the
flow helped or failed, and which change follows from that observation. Keep raw
attempts alongside corrections. Report meaningful gaps even if every test passes.
