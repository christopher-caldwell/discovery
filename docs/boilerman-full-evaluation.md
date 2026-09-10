# Full Boilerman evaluation — September 10, 2026

Discovery completed all four phases against a frozen copy of real Boilerman code.
The final specification is SPEC-002. Its audit verifies 141 events with no failures
or orphan artifacts. Structural coverage is 92/100, a procedural indicator rather
than a correctness probability; performance evidence is explicitly unavailable.

## Scope and phase results

1. **Intent:** exercised a blocking scope question, then resolved it from the
   explicitly narrow evaluation request. Preserve the existing zero-argument
   console renderer, helper signatures, and ID/Row conventions. The earlier real
   investigation's broader owner questions remain unanswered in its separate run.
2. **Investigation:** inspected real source, tests, dependencies and history;
   admitted evidence and evaluated claims. The CLI correctly rejected request
   text as primary evidence. A mistaken lead-origin reference was corrected by
   regressing from Phase 3 to Phase 2, recording the correct follow-up, closing
   research again and reevaluating claims. Historical records were retained.
3. **Design and proof:** compared alternatives and produced a three-file repair:
   correct the entry import, use the supplied EJS function-name variable, consume
   complete helper signatures, and adjust the default sample's signature to
   preserve its output. Executed the real renderer and all five generated actions
   in a disposable copy. An incomplete repair was rejected by negative controls.
4. **Challenge:** an independent lighter-model reviewer inspected the exact
   receipt, probe, patch and results across all twelve categories. After resolving
   an observed runtime defect, review found no material issue within the stated
   scope. The gate passed and the specification and handoff were finalized/exported.

## What iteration improved

The first sandbox attempt failed to find Node through its minimal PATH. The
second passed assertions and 41 helper tests, but nested Vitest stderr reported
EPERM and a timeout while terminating a fork worker. This exposed a Discovery
sandbox defect that the successful wrapper exit code concealed.

Discovery now permits signalling child processes, while continuing to deny
signals to an unrelated process. Two actual subprocess tests verify both sides.
New execution receipts capture the exact sandbox profile. Skill guidance now
requires inspecting nested test output and resolving external executable paths.

The third experiment passed with empty outer and nested stderr: the default
renderer, five actual EJS outputs parsed by gofmt, unchanged helper bytes and all
41 helper tests. The negative control also checks delete's error-result count:
its malformed two-error signature parses, so syntax validation alone would miss
that defect. The repair patch passes git apply --check against the frozen source.

A post-finalization status check also exposed misleading missing-review warnings:
the final export receives a new specification revision, while reviews correctly
remain attached to the reviewed draft. Closed runs now report their inactive
gate without treating that final revision as unfinished work. A full-traversal
regression test verifies both status and phase-check output.

Discovery validation after the fixes: **97 tests passed**, Ruff lint and formatting,
package build, and skill/plugin validators passed. Base version remains 0.2.0.

## Evidence and limits

Local evidence lives under `.discovery/boilerman-full/`:

- `reports/confirmed-results.json`, `proof-map.md`, and `repair.patch`.
- `reports/independent-review-final.md` records each category's scope and limits.
- `reports/final-audit.json` and `final-export.json` record final integrity/export.
- `run/exports/fb479250-55a5-451e-9b9a-bd500004f48c/` contains the final specification,
  evidence manifest and machine-readable handoff.

Frozen source commit: `4fd3b2ffea64ba073326f407de8c540832ffaedc`.
Successful experiment: `0498fb6b-8a94-44e8-b824-3f71e5a93988`, receipt A-037.
Failed/inconclusive attempts remain preserved. Original Boilerman files were not
changed; its preexisting edit in `src/gen/index.ts` remains intact.

This proves the narrow rendering repair on the pinned local toolchain. It does
not prove a clean dependency installation, full Go/SQL type compilation, runtime
UUID behavior, concurrency, crash recovery, performance or general sandbox
security. Those limits are recorded rather than treated as passing tests.
