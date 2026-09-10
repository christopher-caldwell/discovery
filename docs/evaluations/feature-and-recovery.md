# Feature, contradiction and recovery follow-up

This follows the [nine-run isolated campaign](isolated-campaign.md). It addresses
scenarios that the first batch did not exercise with model operators. These are
disposable, deliberately constructed product requests; source implementations
remain unchanged. Fixtures and evaluator keys were authored by gpt-5.6-terra at
low reasoning effort. Operators use the same configured default as the first
batch, gpt-5.6-terra with xhigh reasoning.

## Predeclared cases

| Case | Input and observation | Bound |
| --- | --- | --- |
| `conflicting-1` | Working receipt store, old global-ID design, current tenant-scoped contract, misleading test name, and a replay ticket with the wrong identity premise. Look for explicit contradiction and decision questions. | 480 seconds / 65 CLI calls |
| `conflicting-recovery-1` | Fresh model session receives only the selected durable run, its source/ticket and a simulated product reply. Old chat, outcome, loose reports and event transcript are denied. Look for faithful reconstruction and careful treatment of incomplete answers. | 480 seconds / 65 CLI calls |
| `scoped-storage-1` | Independent, fully scoped optional SQLite store request against the same working fixture. Composite identity, first-payload preservation, reopen, concurrent connections, rollback and error behavior require evidence and a technical proposal. No external archive or production SLA is in scope. | 1200 seconds / 160 CLI calls |
| `preference-1` | A new Discovery request without a supplied investigator preference. Observe whether the skill asks before selecting a mode. | 120 seconds |

The scoped feature ticket supplies desired product choices. It is not evidence
that current code implements them. Source investigations, alternative strategies,
disposable probes and concrete adversarial attacks must substantiate the proposal.
Finalization is not required when a real blocker or failed proof remains.

The recovery case deliberately permits its own prior SQLite state and captured
artifacts: that is the behavior under test. It is not a cold repeat. Its new
process cannot read the prior operator's conversation, outcome or raw log. It must
not infer that a product reply answers technical questions the reply leaves open.
The reply is labeled simulated, not attributed to an actual human stakeholder.

The preference case has a harness limitation: model-native delegation is disabled
in the isolated runtime, though the Discovery CLI supports investigator modes.
Record whether this affects the response; do not treat it as an unrestricted
end-to-end test of launching research collaborators.

## Evidence locations

Inputs and separate evaluator keys are under
`.discovery/scenario-campaign/evaluator/`; the fixture is
`.discovery/scenario-campaign/fixtures/conflicting/`. Each operator's boundary,
hashes, events and usage are under its fresh run/session `control/` directory.
Recovery preserves the selected run at its original path, validates that the
source and immutable ticket match the ledger, and records before/after audits.
No database path rewriting or reconstructed event history is used.

## Completed observations

The conflicting request finished in 366.292 seconds, with three durable questions
and an interim report. It found that the old global receipt-ID premise conflicts
with both current code and the explicitly superseding contract. The recovery
session finished in 212.021 seconds. Its boundary denied the old conversation,
outcome and raw event transcript, while allowing the selected ledger and captured
artifacts. Before/after audit checks were valid; the source and ticket hashes were
unchanged. It recovered the original disagreement and questions, recorded the
simulated reply as such, and resolved the identity question without rewriting the
historical ticket.

That is useful recovery evidence, but the resulting workflow also overblocked:
the reply delegates archive-interface and durability details to the implementation
design. The report acknowledges that the product scope permits design, yet calls
those remaining technical choices blockers and remains in Phase 1. Some genuine
questions about what recovery invokes remain; the observation does not justify
silently resolving every question. The request-vetting guidance now distinguishes
human/product decisions from delegated technical design choices, and asks the
operator to track the latter as research needs. This is a guidance correction,
not a new deterministic guarantee that the CLI can classify a question's meaning.

The preference probe selected disabled investigators, explaining that the execution
policy did not permit subagents. Because the harness disabled native delegation,
this observation is confounded. It does not establish whether the skill asks for
preference when the available choices are genuinely open. The run hit its 120-second
limit; no final usage record was emitted.

Completed usage: conflicting input 995,430, of which 926,464 was cached, with 17,875
output tokens; recovery input 489,993, of which 387,840 was cached, with 10,763 output
tokens. These are cumulative session counters, not counts of newly generated tokens.

## Feature experiment boundary

The feature operator traversed intent and research into Phase 3. Its formal
experiment returned exit 71 before running any assertion: macOS denied applying
the nested sandbox inside the isolated evaluation process. The operator correctly
recorded the experiment as blocked and distinguished that environment failure from
proof for or against SQLite behavior. This restricts what this campaign can show
about full traversal; it is not evidence that the proposed feature is impossible.
No boundary was weakened to manufacture a completed run.

An independent evaluator concern, recorded before inspecting the selected strategy,
is that catching every IntegrityError and checking for an existing pair can suppress
an unrelated constraint failure. The operator selected that approach. A local
counterexample is retained separately in `evaluator/storage-error-probe.json`;
it is evaluator evidence, not evidence gathered by the original operator. The
proposal's own challenge phase has not yet tested it.


The feature run finished in 936.087 seconds, before its 1200-second bound, with an
outcome and interim export. Its self-reported 159 CLI invocations includes help;
that count is not independently established by counting shell events. Session usage
was 4,281,147 input tokens (4,119,808 cached) and 46,387 output tokens. Its source,
ticket, skill and packaged runtime hashes stayed unchanged, credentials were removed,
and the ledger audit was valid. Phase 4 was never active, so the read-only checkpoint
watcher was stopped without creating a checkpoint. No regression scenario was seeded.

Static inspection also found that the host probe's forced NOT NULL failure bypasses
its own proposed `record` function: the test executes INSERT and rollback directly.
It establishes SQLite behavior, not that `record` classifies errors correctly.
The empirical-review guidance now explicitly asks that error injection traverse the
proposed operation, including pre-existing state that could mask the failure. This
adds a concrete review criterion; it does not make a passing probe sufficient proof.

A fresh, bounded `storage-review-1` session is specified separately: selected durable
ledger only, 300 seconds / 35 CLI calls, no evaluator counterexample, no original
conversation or loose outcome. It reviews proposal validity while respecting the
blocked experiment. This is an independent review continuation, not a cold repeat or
a formal Phase 4 traversal. Its completed result follows.


## Independent proposal review result

`storage-review-1` finished in 267.458 seconds with an outcome, interim export and
immutable review artifact A-039. It used the selected run state but could not read
the evaluator counterexample, old conversation or loose original outcome. Its frozen
runtime/skill and selected source/ticket hashes were unchanged, auth was removed, and
the final audit was valid with 96 events and no orphan artifacts. Usage was 800,765
input tokens (745,472 cached) and 7,425 output tokens.

It independently identified three concrete weaknesses:

1. An existing key does not establish that an IntegrityError was caused by that key.
   The review explains the NULL-payload example's invalid-input limitation and a
   controlled trigger-failure example with valid strings. These are static
   counterexamples in this session, not reported runtime reproductions.
2. The failure probe performs its own INSERT and rollback outside the proposed
   function. Begin/commit/cleanup/wrapping paths are omitted from the helper, so
   its observed success cannot support the broader design narrative.
3. The race assertion checks one True, one False and either payload, but loses the
   relationship between the successful caller and retained payload. A wrong-winner
   implementation could satisfy those assertions. The review also distinguishes
   normal reopen assertions from a duplicate call after reopening, which was absent.

The reviewer preserved supported current-behavior claims, created a failed proof
obligation for duplicate classification, reopened an overinterpreted compatibility
obligation as blocked, and retained the blocked empirical obligation. It did not
implement a store or retry the denied experiment. A conservative boundary prevented
finalization, but independent semantic review was needed to expose flaws in the
interim recommendation. This is evidence for the value of review, not proof that
any reviewer reliably finds all errors.

The review also separates investigator-authored accounts from source bytes: a report
with a vendor URL as its origin is still a report, not a captured vendor page. That
provenance distinction remains an evaluation concern; URI appearance does not confer
primary authority. The future design was not an admitted current-behavior claim.

## CLI change from this observation

At the time of review, `phase check` showed an undecided decision and missing
requirements/draft, but omitted its already failed/blocked proof obligations because
only accepted decisions' proofs were inspected. The run was blocked, but the diagnostic
list hid work the next investigator needed to see. `design_violations` now includes
existing proof and experiment failures for proposed material/critical decisions.
Rejected candidates remain excluded. This does not loosen a gate: those proposed
decisions already prevented advancement.

A regression test creates a proposed material decision, fails its obligation,
verifies that both the undecided decision and proof failure are visible, then rejects
the candidate and verifies its proof no longer blocks the chosen design. The 18
completion tests passed. A comparison of the same retained state under old/new gate
code adds exactly three unsatisfied proofs and one incomplete experiment, removing
nothing. This comparison is read-only; original operator results remain immutable.
Outside the isolated operator, the evaluator can see enclosing Git metadata, so its
absolute gate output also includes a source-context difference. Only the old/new
same-state difference is attributed to this change; source bytes were unchanged.

## Remaining limits

This follow-up adds five model sessions to the original nine: three new initial
investigations and two selected-ledger continuations. It supplies neither a completed
Phase 4 nor a regression/retraversal observation. Nested experiment support needs an
appropriate test environment; the current denial was retained without a workaround.
The new request/error-review guidance has not been cold-repeated after these final
edits. Numeric conclusion confidence, proportionality, source drift, late leads and
collaborator disagreement remain open areas. All twenty scenarios have initial
specifications; not all have fresh model-run evidence.

Final validation: all 108 project tests passed in 50.03 seconds; the five isolated
harness tests passed separately. Ruff checks and formatting passed for source, tests
and evaluation scripts, as did skill/plugin validation. Direct and cached skill
copies match the source. The CLI base version remains 0.2.0 and schema remains 5.
