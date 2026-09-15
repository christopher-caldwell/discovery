# Product Realignment Audit — Reviewer B

## Scope and method

Independent review of the current uncommitted product-realignment implementation, with emphasis on assumption safety, claim/evidence fit, extensible discovery surfaces and recovery, truthful experiment safety, schema compatibility, and whether convenience commands silently validate or advance work. I did not read any sibling review report.

I inspected the implementation, migration, operator documentation, and focused tests, and ran:

```text
pytest -q tests/test_product_realignment.py tests/test_upgrade.py tests/test_phase2.py
34 passed in 19.02s
```

The passing focused suite is useful regression evidence, but it does not cover the unsafe state sequences below.

## Findings

### B-01 — High — Assumption impact is caller-selected and is not constrained by the consequence of its dependent claim or decision

**Evidence.** `question.assume` and `assumption.create` reject only the literal value `critical`; they do not derive or constrain impact from the question or future dependency (`src/discovery/application/planning.py:94-120`, `src/discovery/application/planning.py:166-182`). `assumption.link-claim` and `assumption.link-decision` insert a dependency without comparing impact or scope (`src/discovery/application/planning.py:220-235`). Likewise, `decision.create` accepts any active assumption as the sole trace for a decision of any impact (`src/discovery/application/design.py:62-78`), while the phase gate blocks only assumptions whose own stored impact is `critical` (`src/discovery/domain/gates.py:40-42`).

**Impact.** An operator can label an uncertainty `contextual`, then use it as the only trace for a critical decision. This bypasses the stated rule that critical uncertainty cannot be assumed away. The audit trail records the loophole, but the gate still treats it as legal progression.

**Focused fix.** Enforce `assumption.impact >= dependent claim/decision impact` at both link creation and gate evaluation. If the intended rule is stricter, prohibit assumptions as sole support for critical decisions. For question-backed assumptions, record the question's consequence/impact independently and require the assumption not to understate it. Add tests for contextual-to-critical and material-to-critical links through both `decision create --assumption` and the later link commands.

### B-02 — High — Resolving an assumed question can silently preserve conclusions that depended on a contradicted assumption

**Evidence.** `question.resolve` unconditionally changes every active assumption for that question to `discharged` with the fixed note “Replaced by a recorded answer” (`src/discovery/application/planning.py:68-83`). It does not ask whether the answer confirms or contradicts the assumption and does not traverse `assumption_claim` or `assumption_decision`. Its Phase-2 reopening query covers only lanes directly linked through `answer_question_id` or leads (`src/discovery/application/planning.py:85-92`). Claim admission does not inspect assumption dependencies at all (`src/discovery/domain/investigation.py:48-115`). The design gate currently treats discharged assumptions as valid dependency trace (`src/discovery/domain/completion.py:143-155`). The focused test exercises only the benign sequence and asserts automatic discharge (`tests/test_product_realignment.py:136-169`).

**Impact.** A genuine answer that contradicts an assumption can be recorded with the natural `question resolve` command while assumption-dependent claims remain admissible and decisions remain accepted. Safety depends on the operator remembering the skill text's two-command ordering (“invalidate first”), which is exactly the kind of semantic convenience loophole the ledger is meant to prevent.

**Focused fix.** Make resolution explicit: require a `--relationship confirms|contradicts|supersedes` (or require the assumption to be dispositioned first). A contradictory answer must run the same transitive invalidation/reopen logic as `assumption.invalidate` in the same transaction. Gate claim and decision dependencies by an explicit resolved status, not merely `active`/`discharged`, and add a contradiction-path test proving claims, lanes, accepted decisions, drafts, and later gates become stale.

### B-03 — High — `research capture` adds evidence without invalidating an in-progress closure sweep

**Evidence.** Ordinary `evidence.create` calls `reopen(...)` after inserting evidence (`src/discovery/application/claims.py:24-67`). The bundled path inserts one or more evidence rows and then may immediately complete the selected surface or method, but never calls `reopen` (`src/discovery/application/investigation.py:313-373`). It accepts a current closure method whenever the lane closure is `running` (`src/discovery/application/investigation.py:304-311`). The product contract says new evidence invalidates closure, while the focused test only checks capture on a simply active lane (`tests/test_product_realignment.py:182-213`).

**Impact.** During a closure iteration, one `research capture ... --method <closure-method> --complete-method ...` can introduce new evidence and mark that same sweep step complete. The lane may then close without beginning the fresh closure cycle required for newly introduced evidence. The convenience command therefore has weaker invalidation semantics than its lower-level equivalent and can silently advance closure readiness.

**Focused fix.** Give bundled evidence insertion exactly the same invalidation path as `evidence.create`. Because reopening makes the current closure iteration stale, either reject `--complete-method` for closure methods when the same command adds evidence, or reopen first and require a new `lane closure-begin`. Add parity tests comparing the bundled and decomposed command sequences from a lane with `closure_status=running`.

### B-04 — High — Schema-7 upgrade creates mandatory verification failures that later-phase runs cannot repair in place

**Evidence.** The migration gives every legacy claim `verification_method='inspection'`, `verification_availability='available'`, and an empty rationale (`src/discovery/adapters/sqlite/realignment_migration.sql:11-17`) without changing claim status or lane state. Current claim validation rejects an empty rationale (`src/discovery/domain/investigation.py:54-66`). The repair command `claim.verification` is handled by claim work, which is limited to Phase 2 (`src/discovery/application/claims.py:19-23`, `src/discovery/application/claims.py:124-145`). Thus an active schema-6 run already in Phase 3 or 4 upgrades successfully but can acquire failing upstream claim checks that cannot be repaired without an explicit regression. Existing upgrade tests verify structural integrity/replay, not post-upgrade gate continuity for populated later-phase claims (`tests/test_upgrade.py`).

**Impact.** “Additive” compatibility is operationally misleading: an active later-phase run can become stuck after the required upgrade, despite preserving an `admissible` claim status that no longer satisfies current validation. The default also asserts that legacy verification was inspection even though that fact was never recorded.

**Focused fix.** Define a truthful legacy state (`legacy_unspecified` or unavailable/pending verification) and an explicit migration transition. Either permit verification metadata repair in later phases while staling all dependent work, or have upgrade deterministically regress/stale affected runs with a documented result listing required actions. Add fixtures containing admissible claims and accepted decisions in schema 6 Phase 2/3/4, then assert the exact supported recovery path.

### B-05 — Medium — Verification “method” is not bound to evidence of that method having occurred

**Evidence.** Claim validation checks only a nonempty free-text rationale, availability, and broad evidence classification: `authoritative_record` requires any supporting `primary` evidence, while `test` and `experiment` require any supporting `empirical` evidence (`src/discovery/domain/investigation.py:54-85`). It does not link the claim's selected method to a matching research activity, completed method record, registered experiment receipt, or method-specific argument verification. The focused authoritative-record test demonstrates the broad classification check but not authoritative provenance (`tests/test_product_realignment.py:216-244`).

**Impact.** A report manually classified as empirical can satisfy a claim labeled `experiment` even if no experiment was registered, and any primary artifact can satisfy `authoritative_record`. Semantic judgment must remain model/human work, but the current data model makes the new method field closer to an unchecked label than an operational proof requirement.

**Focused fix.** Record the verification basis explicitly: link a claim (or its passed support argument) to a research activity/method or experiment receipt. Enforce structural compatibility while leaving relevance/truth to the reviewer. At minimum, require a completed matching method/activity for `test`/`analysis`/`inspection`, a registered passed experiment for `experiment`, and an artifact provenance declaration for `authoritative_record`.

### B-06 — Medium — Trusted-local portability is not platform-bounded or platform-attested

**Evidence.** The executor validates only that mode is one of two strings; the Darwin check exists solely inside restricted mode (`src/discovery/adapters/process/sandbox.py:42-68`). Trusted-local therefore attempts to run on any platform even though the contract supports macOS/Linux and explicitly leaves Windows outside the release. The receipt records mode and safety prose, but not the actual OS/platform (`src/discovery/adapters/process/sandbox.py:156-193`). The platform-controlled test proves Linux rejects restricted mode, but does not prove trusted-local accepts Linux or rejects Windows (`tests/test_product_realignment.py:297-317`).

**Impact.** A Windows attempt may fail through Unix-specific process APIs or, if adapted by the runtime, produce a receipt indistinguishable from macOS/Linux. The implementation cannot substantiate the contract's “Linux execution is reported as live only when actually run on Linux” condition from the receipt itself.

**Focused fix.** Before reservation/execution, explicitly allow trusted-local only on `Darwin` and `Linux`; return a stable unsupported-platform error elsewhere. Record `platform.system()`, release/architecture, and adapter identity in the immutable receipt. Add controlled Darwin/Linux/Windows selection tests and a real Linux CI smoke test before claiming Linux execution coverage.

### B-07 — Low — Installation documentation still states schema 6 is current

**Evidence.** `docs/AI_ORCHESTRATED_TOOL_INSTALLATION.md:68-71` says the current SQLite schema is version 6, then immediately says older runs upgrade to schema 7.

**Impact.** This creates avoidable ambiguity for installer/version checks and contradicts the CLI/implementation contract.

**Focused fix.** Change the first sentence to schema 7 and add a small documentation assertion if these version strings are intentionally machine-checked.

## Coverage and positive observations

- Restricted execution retains a hard Darwin/Seatbelt availability check and does not silently fall back (`src/discovery/adapters/process/sandbox.py:63-86`). Trusted-local receipts clearly say that no OS boundary is enforced and that preservation is checked after execution (`src/discovery/adapters/process/sandbox.py:171-193`).
- Custom surfaces are included in the plan snapshot through the full `research_surface` table, and Phase-1 regression recreates justified custom names as pending obligations (`src/discovery/adapters/sqlite/queries.py:7-31`, `src/discovery/application/phases.py:109-131`). The focused recovery/regression test covers the principal path.
- Report export remains a read projection with explicit procedural caveats; no reviewed code path made it advance a phase or admit a claim.
- Idempotent replay of `research capture` is covered, and the bundle does not itself create or evaluate claims. The material issue is closure invalidation parity, not atomicity or replay.

## Priority recommendation

Fix B-01 through B-04 before treating the realignment as gate-safe or migration-compatible. They are state-machine defects: each permits either understated uncertainty, stale dependent conclusions, stale closure, or an upgraded run whose recorded statuses disagree with current validation. B-05 and B-06 should follow before advertising claim-method enforcement and Linux/macOS portability as stronger than metadata-level guarantees.
