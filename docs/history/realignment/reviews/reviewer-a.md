# Product realignment audit — reviewer A

## Scope and method

Independent review of the current uncommitted product-realignment changes, with emphasis on assumption boundaries, claim-appropriate evidence, expandable/recoverable surfaces, experiment safety language, schema compatibility, and convenience-command side effects. I did not read sibling review reports and did not modify product source.

Validation observed:

- `pytest -q tests/test_product_realignment.py tests/test_upgrade.py`: 17 passed.
- `pytest -q`: 151 passed.
- `git diff --check`: passed.
- `uv run ruff check .`: failed on `tests/test_product_realignment.py:164` (`E501`, 105-character line). This line appeared while the review was in progress, so the worktree was changing concurrently.

## Findings

### A-1 — High — A low-impact assumption can be the sole trace for a critical decision

**Evidence:** `src/discovery/application/design.py:62-78` accepts a decision when either admissible claims or active assumptions are supplied, but it does not compare assumption impact with decision impact. The decision's impact is written independently at `src/discovery/application/design.py:79-87`. The Phase 3 gate in `src/discovery/domain/completion.py:137-158` accepts any linked active or discharged assumption as decision trace, again without an impact floor. Meanwhile, only assumptions explicitly labeled critical are rejected (`src/discovery/domain/gates.py:40-42`).

**Impact:** An operator can label an uncertainty `contextual`, then use it as the only basis for a `critical` decision. This bypasses the stated rule that critical uncertainty must block and weakens the impact-preservation invariant already enforced for lanes and claims. Proof obligations test the chosen design but do not establish that the assumed product premise was safe to assume.

**Focused fix:** Enforce `assumption.impact >= decision.impact` at link/create time and in `design_violations`. Since active critical assumptions are forbidden, require at least one admissible critical claim for critical decisions rather than allowing assumption-only trace. Add a negative test for a critical decision backed solely by a contextual/material assumption.

### A-2 — High — Resolving an assumed question can bless contradictory downstream conclusions

**Evidence:** `question.resolve` changes every active assumption for that question to `discharged` without recording whether the answer confirms or contradicts it (`src/discovery/application/planning.py:68-83`). It reopens only lanes that used the question as a lane/lead answer (`src/discovery/application/planning.py:85-92`), not claims and decisions linked through `assumption_claim` or `assumption_decision`. Explicit invalidation does stale those dependents (`src/discovery/application/planning.py:196-217`), but the Phase 3 gate treats a discharged assumption as valid support (`src/discovery/domain/completion.py:143-155`), and `claim_violations` never evaluates assumption links (`src/discovery/domain/investigation.py:1-115`). The operator skill merely instructs the user to invalidate first when an answer contradicts the assumption (`skills/discovery/SKILL.md:63-68`).

**Impact:** A user can answer an assumed question with the opposite fact using the natural `question resolve` command; the system records the premise as discharged and can leave linked admissible claims and accepted decisions usable. Correctness depends on remembering an undocumented-in-CLI two-command ordering at precisely the recovery boundary this feature is meant to make safe.

**Focused fix:** Make resolution of an assumed question require an explicit relation such as `--confirms-assumption` or `--contradicts-assumption`. Confirmation may discharge; contradiction should invoke the same dependent invalidation/reopen path as `assumption invalidate`. At minimum, refuse ambiguous resolution while an active linked assumption has downstream dependencies. Test both branches with linked claims and accepted decisions.

### A-3 — Medium — Verification method is a label, not evidence that the selected method was applicable or performed

**Evidence:** Admission reads the selected method and rationale but never compares `claim_kind` with that method (`src/discovery/domain/investigation.py:54-85`). For `test` and `experiment`, it only checks that some supporting evidence row is classified `empirical`; for `authoritative_record`, it only checks `primary`. `research capture` can classify any supplied text report as primary/secondary/empirical (`src/discovery/application/investigation.py:319-364`) without a test/experiment receipt or authoritative-source relationship. An attributed passed argument is enough to turn that classification into support (`src/discovery/domain/investigation.py:47-52`). The validation matrix acknowledges “Method relevance remains semantic” (`docs/product-realignment-validation.md:12`).

**Impact:** Structurally, a runtime claim marked `experiment` can be admitted from a hand-authored text artifact labeled empirical, and an arbitrary document labeled primary can satisfy `authoritative_record`. The new UI therefore looks stronger than the enforced provenance and can overstate “claim-appropriate verification.”

**Focused fix:** Add explicit method-result provenance: test/experiment verification should reference a compatible execution/result artifact or activity; authoritative records should reference source-backed primary evidence (or an explicit authority attestation). If applicability is intentionally semantic, rename/report it as a proposed verification method and keep admission dependent on a separately verified method-performance record. Add negative tests for mismatched claim kind/method and synthetic empirical labels.

### A-4 — Medium — Trusted-local receipts overstate “original source preserved”

**Evidence:** Trusted-local runs with no OS containment (`src/discovery/adapters/process/sandbox.py:99-107,171-190`). After execution, `original_source_preserved` compares only revision and a tree hash (`src/discovery/application/experiments.py:243-248`). That tree hash intentionally skips configured directories, the run directory, and `.DS_Store` (`src/discovery/adapters/git/repository.py:17-25`); Git HEAD also does not detect working-tree edits that are restored before the post-run scan (`src/discovery/adapters/git/repository.py:27-36`). `experiment.finish --outcome passed` trusts this Boolean (`src/discovery/application/experiments.py:103-117`).

**Impact:** A trusted command may mutate excluded source content such as `.git` or `.discovery`, modify external paths, or alter and restore tracked files, while the receipt states `original_source_preserved: true`. The receipt correctly says there is no security boundary, but the preservation field and pass gate are broader than the check.

**Focused fix:** Rename the field to the exact assertion, e.g. `included_source_snapshot_unchanged_after_execution`, record the excluded paths beside it, and avoid using it as proof of general preservation. Keep the trusted-local limitations prominent in exported experiment results. If stronger preservation is required, use platform containment or a read-only source mount rather than a post-hoc hash.

### A-5 — Medium — Schema-7 defaults create asymmetric and under-documented legacy behavior

**Evidence:** The migration backfills existing assumptions with empty scope and invalidation condition (`src/discovery/adapters/sqlite/realignment_migration.sql:1-2`), while the gate checks only status/impact and permits noncritical active assumptions with those empty fields (`src/discovery/domain/gates.py:28-42`). Existing claims are backfilled as `inspection`, `available`, with an empty rationale (`src/discovery/adapters/sqlite/realignment_migration.sql:11-17`), but claim admission requires a nonempty rationale (`src/discovery/domain/investigation.py:54-65`). The contract mentions that Phase 1 plan review may stale after upgrade but does not state that legacy active assumptions can remain incompletely scoped or that legacy claims lose admissibility until reclassified (`docs/implementation-contract.md:17-22`).

**Impact:** Upgrade preserves bytes but not a coherent operational meaning: legacy assumptions gain the new privilege without the new required context, while legacy claims gain a default that immediately violates the new gate. Phase 2/3/4 runs can require regression or repair steps not surfaced by the migration contract.

**Focused fix:** Treat migrated active assumptions with blank scope/condition as `ASSUMPTION_SCOPE_REQUIRED`; do not let them pass a gate. Backfill legacy claim verification as explicitly `unavailable`/`migration_required` (or add a legacy-unspecified state), and document the exact repair/regression path for each active phase. Extend upgrade tests with nonempty historical assumptions and admissible claims in Phases 1–4, not only schema shape/audit preservation.

### A-6 — Low — The top-level README contradicts the implemented release

**Evidence:** `README.md:99` still calls schema 5 DDL authoritative, `README.md:103-105` describes only schema 3/4/5 upgrade/read behavior, and `README.md:111` says experiments are macOS-only and assumption/withdrawal commands are future work. The same README announces schema 7 and these features at `README.md:5,56-57,107`.

**Impact:** Operators can follow mutually exclusive compatibility and safety guidance from the primary entry point, especially around whether trusted-local Linux execution exists and whether assumption commands are supported.

**Focused fix:** Update the authority, upgrade, and next-slice sections together; add a documentation consistency assertion for current schema/version and supported command names.

## Focus-area conclusions

- **Expandable surfaces/recovery:** I found no blocking defect in the custom-surface path. Added surfaces are part of the plan hash/gate and are recreated pending on Phase-1 regression. Coverage is narrow (one regression/recovery scenario), but the implementation is internally consistent.
- **Convenience commands:** `research capture` does not create/admit claims, verify arguments, close lanes, or advance phases. Its `--complete-surface` and `--complete-method` flags do advance gate-relevant dispositions through `complete_record` (`src/discovery/application/investigation.py:13-27,365-369`), but those effects are explicit flags rather than silent defaults. Documentation should continue to distinguish “no phase transition” from “can satisfy prerequisites.”
- **Migration mechanics:** Transactional upgrade and audit-chain tests pass. The concern is semantic compatibility of migrated rows, not DDL atomicity.

## Priority recommendation

Fix A-1 and A-2 before treating assumption support as production-safe. They permit consequential work to survive an assumption boundary that should block or reopen it. Then tighten or relabel the verification and trusted-local claims (A-3/A-4), and make legacy repair behavior explicit (A-5). The current test suite is green for functional paths but does not cover these negative invariants.
