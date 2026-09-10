# First real-project Discovery case: Boilerman

A bounded read-only scan of ~/Code/projects selected Boilerman because it has a
small real integration gap reproducible without live services. Other candidates
included schema_registry, server_proxy, dive_log and inngest_rust. This was not an
exhaustive audit of ~/Code. A lighter agent prepared the disposable reproduction.
No original project files were changed and no dependencies were installed.

## Reproduced findings

Source: `/Users/christophercaldwell/Code/projects/boilerman`, tracked commit
`4c6e629df4ab1d906c33723257db78f505d48d5b`. The current checkout has an unrelated
local edit commenting out an unused mock/helper block. Root inspected that diff;
it does not change the paths, locals or return helper under investigation.
The reproduction explicitly uses tracked HEAD, not the entire dirty worktree.

- **41 helper tests pass**, but the executable entry point fails to import
  `./actions/repo/single/render`; the tracked renderer is under `templates`.
- Calling the actual renderer fails because it supplies `fnName` while the EJS
  template reads `funcName`.
- A diagnostic harness supplies that missing alias without modifying source.
  Combining generator-helper output with the template then produces a doubled
  return/error signature. `gofmt` rejects the fragment. This is a diagnostic
  composition result, not a claim of full Go compilation or a wired public API.

These results give Discovery real evidence of a test coverage gap: helper
expectations can pass while executable and generated-output boundaries fail.

## Preserved ambiguity

The real request does not establish whether the supported interface should be a
payload-driven library renderer returning source, a CLI, or both. It also lacks
SQL/query definitions establishing numeric ID width and generated return-row
shapes. Existing tests expect int16 and Row types, but tests alone are not an
independent product or database contract. Both questions remain open.

Unlike the earlier synthetic evaluation, this run supplies no invented policy to
force completion. Its two material research needs and two scoped lanes distinguish
reproduced integration defects from unknown intent. The exact plan review passed
for coverage; Phase 1 advancement is blocked only by the two unanswered questions.

## Durable state and provenance

Disposable environment: `.discovery/real-boilerman/`.
The source snapshot has its own Git baseline. Its reproduction report includes
original HEAD/status, file hashes, commands, outputs and limits. Existing local
Node dependencies were used read-only through a temporary link removed before
baseline capture. This is not clean-install dependency validation.

Run: `.discovery/real-boilerman/run/`.
Audit verification passed: **20 events, zero integrity failures**. One orphan
artifact from an attempted Phase 1 evidence capture remains reported and retained;
the CLI correctly refused that Phase 2 command. Phase 1 research reports are
captured through research record instead. No Phase 2 claim admission is implied.
The reports and original request are recorded through legal Phase 1 operations.

Root inspection, exact plan snapshot/review, command transcript and state are in
`.discovery/real-boilerman/reports/`. The reproduction report is
`.discovery/real-boilerman/reproduction-report.md`.

To resume, run `discovery --json --run /absolute/path/to/.discovery/real-boilerman/run resume`,
inspect drift, and resolve the API/SQL questions from an actual owner answer or
authoritative project contract. Then continue investigation; no final technical
specification or repair to Boilerman is claimed here.
