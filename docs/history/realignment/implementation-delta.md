# Product realignment delta

This record compares the user-approved design package with the behavior at
`3669d780a7e3a3ec470064ea7d8051bb7caad660`. It is the implementation checklist
for the realignment, not a replacement product contract.

The subsequent investigator-first correction is governed by
[product intent](../../reference/product-intent.md). It retained the completed restoration below
and made five deliberate simplifications: impact-proportional closure, automatic plan
review binding, a higher-level `research finding` action, exact-byte source
revalidation, and portable local experiments as the default. The macOS restricted
adapter remains optional rather than defining the ordinary workflow. Human-readable
specifications no longer embed the normalized state graph.

## Confirmed gaps

| Intended behavior | Current observed behavior and evidence | Correction | Acceptance check |
| --- | --- | --- | --- |
| A non-blocking question may proceed under an explicit, scoped assumption whose lifecycle and dependent conclusions remain traceable. | The schema has dormant question and assumption states, and the Phase 1 gate understands them, but the CLI exposes only `question create/list/resolve`; the current skill explicitly says assumption/withdrawal commands do not exist (`src/discovery/cli.py`, `src/discovery/application/planning.py`, `skills/discovery/SKILL.md`). | Expose question assumption, withdrawal/reclassification, and assumption create/discharge/invalidate commands. Record scope, dependencies, invalidation criteria, resolution, attribution, and history. Reopen or stale dependent work on contradiction. | Focused CLI tests show blocking questions cannot be assumed, critical assumptions fail, safe assumptions permit Phase 1 progression, recovery/export retain them, and invalidation reopens dependent work. |
| Human questions carry tentative authority categories plus ranked candidate people/groups with reasons, attribution, source support, and uncertainty. | `question_respondent` exists in schema and state snapshots but no command can create a respondent (`ddl.sql`, `cli.py`, `planning.py`). | Add an attributed candidate command that accepts a role/group/person or an explicitly unknown identity, rank, rationale, confidence, and optional supporting artifact. | Tests preserve multiple ranked candidates and an unknown identity without inferring authority from file authorship. |
| Phase 1 discovery surfaces are a minimum and investigators may add justified surfaces. | Initialization creates the baseline surfaces and the CLI exposes only list/disposition. The implementation contract calls custom surfaces a future extension. | Add `surface create` in Phase 1, with a request-tied reason. Include it in plan hashing, gates, recovery, research recording, and exports without changing baseline surfaces. | A new surface remains pending until honestly dispositioned, stales plan review, survives recovery/export, and leaves all baseline surfaces intact. |
| Verification requirements fit the claim kind and consequence. | Evidence profiles are selected only from impact. Every critical claim therefore requires empirical evidence and the same falsification/empirical methods (`domain/policy.py`, `domain/investigation.py`). | Add a small claim verification-method selection: `inspection`, `analysis`, `authoritative_record`, `test`, or `experiment`, with applicability and rationale. Keep impact floors, provenance, semantic verification, contradiction search, and unavailable-required-proof blocking. | Critical intended-behavior claims can require authoritative records without irrelevant experiments; runtime claims can require tests/experiments; a required but unavailable method prevents admission. |
| Ordinary evidence gathering persists related activity, artifact, evidence, and observations without reconstructing identifiers while keeping semantic judgments distinct. | `research record`, `artifact capture`, and `evidence create` are separate operations. The only combined operation completes surfaces/methods; it does not register evidence (`cli.py`, `planning.py`, `investigation.py`). | Add one higher-level Phase 2 research-capture operation that atomically stores the report, activity, and one or more explicitly classified observations as evidence. It must not create/admit claims, verify arguments, close lanes, or advance phases. | Tests show fewer mutations for the bundle, exact retry behavior, and unchanged claim/lane gates. |
| Useful experiments work on ordinary macOS and Linux while accurately distinguishing enforced restriction from explicit trusted-local execution. | `experiment exec` is macOS Seatbelt-only and fails elsewhere; copied state is correctly not described as a sandbox (`adapters/process/sandbox.py`, `implementation-contract.md`). | Retain Seatbelt as hardened macOS mode. Add an explicit, scoped trusted-local disposable-copy mode for Linux/macOS, record the mode and limitations in the receipt, never downgrade a requested restricted mode, and preserve original-source checks. | Platform-controlled tests prove mode selection, no restricted fallback, explicit trusted-local audit data, original-source preservation, and visible failures. Linux execution is reported as live only when actually run on Linux. |
| Recovery and exports expose current blockers, assumptions, contrary evidence, and actionable next work without making the ledger the deliverable. | Compact recovery and interim exports exist, but the skill remains command/data-model heavy and the rendered final specification foregrounds generated structure (`skills/discovery/SKILL.md`, `application/queries.py`, `application/specification.py`). | Shorten the primary skill around operator actions, move command detail to focused references, add operational examples, and improve the report/spec lead sections and traceability labels. | Readability tests and a declared example run show the recommendation/blocked outcome, support, uncertainty, next action, and evidence package can be understood without chat. |

## Suspicions to verify before changing behavior

- Investigator modes, canonical minority findings, and failed participation already
  have substantial schema, guard, and test coverage. Preserve them unless focused
  review identifies a concrete violation.
- Regression and retraversal already invalidate phase revisions and specification
  freshness. Extend assumption invalidation through these mechanisms instead of
  creating a parallel workflow.
- Existing experiment copying, receipts, timeouts, output limits, and Seatbelt rules
  are useful and should remain; only portability and truthful mode description need
  targeted work.

## Documentation errors

- The current contract describes schema 5 as the active persistence baseline while
  later paragraphs correctly identify schema 6. The realigned contract must identify
  one current schema and explicit compatibility path.
- The original command contract lists assumption, respondent, and custom-surface
  commands as product behavior, while the current skill labels them extensions.
  The implementation, current contract, help, and skill must agree after this pass.

## Deliberate improvements, not restored omissions

- A task-oriented research capture is a usability improvement over the original
  low-level command inventory. It bundles transport and persistence only; it does
  not merge semantic judgments.
- Trusted-local execution is an explicit portability option, not a security sandbox
  and not equivalent to Seatbelt. It is acceptable only for reviewed commands in a
  disposable copy with auditable scope and limitations.
