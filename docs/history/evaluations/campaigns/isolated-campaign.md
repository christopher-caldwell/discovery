# Isolated request-vetting campaign

The [scenario specifications](scenario-specs.md) define 20 observable behaviors
from the user's requests. The [coverage ledger](coverage-ledger.md) separates
executable state guarantees, historical investigations and missing observations.
This campaign starts with repeat investigations rather than treating a single
successful answer as reliability evidence.

## Controls

Each operator receives the exact ticket, a sanitized frozen source copy, Discovery
0.2.0/schema 5 and the current source skill. Each gets an empty run directory and
a new ephemeral model session. The macOS process boundary denies old run contents,
evaluator keys, sibling directories and original Codex history. Probes exercise
direct reads, listings, child-process reads and symlink reads, including a real
prior SQLite file and evaluator key. Source and ticket writes are denied.

The harness copies only the configured model defaults into a fresh configuration:
`gpt-5.6-terra`, reasoning `xhigh` in this environment. This is not necessarily the
same model configuration used by historical inherited-context operators. Therefore
this batch cannot isolate the causal effect of the skill changes from model and
environment differences. Within-batch repeats retain the same configuration.

App, plugin and MCP configuration is not inherited. Local metadata queries remain
permitted; file contents and directory listings are allowlisted. Outbound HTTPS
and DNS remain available for model access and public research, with localhost and
app IPC denied. This is local evidence isolation, not a claim of complete remote
account confinement. Run-local authentication is removed when execution ends.

Source exclusions, exact prompt/ticket/skill/package hashes, boundary policies,
pre/post integrity, raw model events, elapsed time and runtime-provided usage are
retained under `.discovery/scenario-campaign/runs/<case>-<replica>/control/`.
The exact ticket is distinct from runner instructions and is the Discovery input.
Omitted `.git` metadata means source identity is the copied content, not an asserted
original commit. Preparation/startup failures are harness evidence, not Discovery
investigations. A failed TLS smoke was followed by a successful verified-TLS smoke
using exported public system trust certificates; verification was not disabled.

## Predeclared first batch

| Case | Scenarios | Per-run bound | Repeats | Main observation |
| --- | --- | --- | --- | --- |
| Taskledger resume/recover | S01, S20 | 240 seconds / 35 CLI calls | 2 | Accurate bounded explanation and recording overhead |
| Taskledger launch-wave preview | S03, S04, S06 | 480 seconds / 65 CLI calls | 2 | False eligibility premise and governing selection ownership |
| ParcelPulse retry objective | S07, S19 | 480 seconds / 65 CLI calls | 2 | Local tests cannot substantiate a production delivery guarantee |

The runtime enforces elapsed-time termination. The prompt asks the operator to
track the command bound and reserve 45 seconds for reporting; the command bound
is not yet automatically enforced. A timeout or unfinished report remains part
of the result. The unavailable-evidence fixture is an easy positive control:
its README and contract explicitly describe the operational boundary. Recognizing
it does not prove detection of subtly missing or misleading evidence.

## Structural evidence gathered separately

83 existing tests passed in 41.95 seconds, with zero skipped cases. The retained
JUnit report is `.discovery/scenario-campaign/evaluator/structural-tests.xml`.
They exercise phase sequencing/regression, blocking questions and material UNKNOWN,
claim support/counterevidence, closure invalidation, draft/challenge freshness,
isolated probes, replay/interruption, source refresh, investigator scope, report
export and audit integrity. The suite uses synthetic attributed reviews; it does
not show that model-authored reviews are substantively correct.

Two separate harness tests exercise private-file isolation and copy exclusions.
These establish the test boundary, not Discovery's research quality.

## Known unmet requirements

Numeric conclusion confidence is absent. Existing assurance measures procedural
coverage and cannot substitute for the requested confidence in the conclusion.
An answer-only investigation also lacks a formal completion path: an interim
report can be useful without satisfying a final technical-specification gate.
These remain product gaps regardless of the results below.

## First observations, before any corrective changes

`simple-1` found and captured the correct answer, but the 240-second harness limit
terminated it before `outcome.md` or an export was written. Its durable report
distinguishes dispatcher preflight for resume from service preflight for recover,
response shape, retained-session baseline, and unresolved operations. It had two
CLI errors: it supplied a lane reference where a surface reference was expected,
then attempted Phase 1 research on a lane surface reserved for Phase 2. It also
created one comma-delimited surface name instead of separate repeated flags.
These are operator mistakes made harder to recover from by insufficient command
guidance. A root read-only audit after termination verified 10 events and no
orphans; resume retained the research. Root inspection is not operator completion.

`unavailable-1` delivered an interim report and separate outcome. It distinguishes
inability to approve the objective from evidence that production fails. It locates
the local transport-success semantics, labels staging readiness as an unverified
ticket assertion, records the absence of measurements/SLA inputs, and leaves a
blocking authority/SLO question open. It ran the two local fixture tests and did
not present them as a production SLO measurement. The run remains Phase 1; this
does not exercise model operation of the Phase 2 material-UNKNOWN closure route.
A root audit verified 10 events and no orphans.

Both first blocked operators attempted `--authority-confidence high`. Current help
does not describe the required numeric scale, and the conversion error reports
an invalid value without supplying it. One searched the installed runtime to
discover the accepted representation. The planned correction is explicit 0–1
help/error guidance, not acceptance of an ambiguous confidence label.

The frozen environment also blocked the host Git shim's Command Line Tools
library. Operators still read the source and Discovery used content baselines.
This is harness friction, not evidence of broken target Git behavior. It must be
reported separately and repaired for subsequent campaigns, while paired runs
retain the same boundary for comparability.

`simple-2` also hit the 240-second limit before outcome/export. Its last completed
actions were planning-surface dispositions, surface/research listings, phase check
and plan snapshot. Two unchanged isolated attempts therefore expose a repeatable
delivery problem under this initial bound, not merely one erroneous lane call.
The answer itself still requires independent source review; a timeout does not
mean its recorded factual conclusions were wrong.

## Refinement under evaluation

After all six initial runs had frozen their inputs, the CLI help/error text was
changed to describe numeric authority confidence, repeated lane method/surface
flags and planning-versus-lane surface references. Invalid confidence remains
invalid; no gates were relaxed or names silently split. The Phase 1 scope error
now explains how to locate an applicable planning surface.

The skill now explicitly permits an explanation-only investigation to record the
supported answer on relevant planning surfaces and export promptly, without
building a needless implementation plan or finishing every planning surface.
The exported report remains interim with visible unmet gates; formal answer-only
completion has not been added. `simple-refined-1` is a new isolated investigation
of the same ticket/source/budget with those changes, not a continuation or replay.

51 targeted CLI/planning/gate tests passed after the refinement, and manual CLI
validation confirmed that `--authority-confidence high` now reports the accepted
numeric range. These checks validate the implementation change, not whether it
improves independent investigator behavior.

The first refined Taskledger explanation still timed out without exporting. It
avoided a plan but completed all seven surfaces and queried resume/gates/export
help at the deadline. That change therefore did not demonstrate timely delivery.
The next narrow revision makes reporting availability explicit in `status`,
`resume` and `phase check`: phase completion is not a prerequisite to interim
export. The export help describes the same boundary. `simple-delivery-guidance-1`
tests this additional change; it is a distinct variant, not the second replica
of `simple-refined-1`. A blocked-run test checks that reporting stays available
while the blocking question and advancement restrictions remain intact.

## Paired findings

Both launch-wave investigations found the governing ownership/parallel-safety
rules and contradicted the ticket's inference. Unlike the historical miss, both
read relevant product-specification sections. They offered conditional choices
instead of silently implementing a classifier. The second retained a substantial
conditional metadata design; it remains debatable whether that much design is
useful before Product chooses scope. It wrote outcome and interim export but
hit the 480-second limit before the model session completed. The outcome exists;
the session did not finish, and token usage was not emitted.

Both unavailable-evidence investigations separated local transport acceptance from
remote delivery and declined to substantiate rollout approval. Neither proved the
objective impossible. Both stayed in Phase 1 with a blocking question; only the
second created a critical need/lane. This is agreement on the bounded conclusion
with differing structured representations. Both used the easy fixture's explicit
contract exclusion, so harder missing-evidence cases remain necessary. Their
numeric authority judgments also differed without a calibration basis.

The unchanged simple pair both recorded the correct source explanation but failed
to deliver an export within four minutes. The skill-only refinement also missed
that limit. This contradicts a claim that the current simple-question flow is
already efficient, while supporting that evidence survives interruption.

## Already-satisfied case

`already-satisfied-1` used the refined skill on a second ticket in the small
ParcelPulse fixture. It completed in 192.2 seconds, proposed no product change,
ran the local tests, and exported after recording four relevant surfaces. It left
three planning surfaces pending and explicitly described the report as interim.

It also identified a nuance beyond the evaluator key: the test verifies attempts
and payload but does not directly assert `len(vendor.calls) == 1`. The source's
immediate return supplies the exact-one-local-call support. Its optional suggestion
to strengthen that assertion did not become an implementation task. This is useful
evidence of reading assertions rather than trusting a test name, but not proof of
that behavior on arbitrary misleading tests. The fixture is much smaller than
Taskledger; it is not a controlled speed comparison.

## What the evidence does and does not establish

There is direct evidence for rejecting the planted false premise, locating the
product boundary, delivering a useful blocked answer, recognizing already-existing
behavior, and preserving work when an operator is stopped. There is also direct
evidence of excessive planning work and failure to deliver the larger simple
answer under the declared bound. The cases do not establish a confidence scoring
model, universal research completeness, or substantive four-phase review of a new
complex feature. Those scenarios remain explicitly unexercised by this batch.

The runtime's input-token totals are cumulative and include cached input. Retain
cached, uncached and output separately; never describe a cached total as newly
generated tokens. Timeout runs did not emit final usage, so their usage is
unavailable rather than zero. Raw model tool events are retained, but CLI counts
from model self-report are not independently instrumented exact totals in this
harness. The metrics file distinguishes shell calls from observed JSON envelopes.

## Harness follow-up

After all campaign processes had loaded their frozen boundary, the reusable
harness was formatted and corrected to permit the installed Command Line Tools
runtime. A test now executes Git through the boundary while private sentinel reads
remain denied. Preparation cleanup was also scoped to a newly created run so
accidentally reusing an existing run path cannot remove that run's authentication
file. Three harness tests pass. The original campaign harness is retained as
`evaluator/isolated-run-used.py`; these fixes do not retroactively change its runs.

## Final measured outcomes

| Run | Seconds | Session cutoff | Outcome + export | Input / cached input / output tokens |
| --- | ---: | --- | --- | --- |
| already-satisfied-1 | 192.2 | no | yes | 433,097 / 391,680 / 8,703 |
| complex-1 | 458.4 | no | yes | 3,889,790 / 3,714,816 / 22,041 |
| complex-2 | 480.0 | yes | yes | unavailable |
| simple-1 | 240.0 | yes | no | unavailable |
| simple-2 | 240.0 | yes | no | unavailable |
| simple-delivery-guidance-1 | 240.0 | yes | yes | unavailable |
| simple-refined-1 | 240.0 | yes | no | unavailable |
| unavailable-1 | 360.2 | no | yes | 1,076,421 / 1,000,704 / 18,053 |
| unavailable-2 | 356.2 | no | yes | 1,129,316 / 1,049,344 / 17,214 |

All nine run audits verified, all frozen input hashes matched after execution,
and all run-local authentication copies were removed. The original Taskledger
69-file manifest also matched. Exported reports remain interim: none of these
runs was presented as a finalized technical specification.

`simple-delivery-guidance-1` wrote its outcome and report before the cutoff,
unlike the preceding three Taskledger explanation attempts. It still reached
240 seconds before its model session ended. That is evidence of earlier artifact
delivery in one trial, not proof of consistent speed or complete session success.
Its source-supported core answer is correct; it also notes potential documentary
response-shape drift without asserting that the target must be changed.

Post-change validation: 58 CLI/report/completion/regression tests passed, three
harness tests passed, lint/format checks passed, the distribution built, and skill
and plugin validation passed. Release 0.2.0 and schema 5 remain unchanged.

Next evidence needed: a formally scoped answer-only completion route and cheaper
recording/output; genuinely ambiguous intent; subtler conflicting/missing evidence;
a fresh-session recovery operator; and a working-repository feature proposal
challenged through all four phases. A conflicting-evidence fixture and controlled
owner reply are prepared separately, but were not run in this batch.
