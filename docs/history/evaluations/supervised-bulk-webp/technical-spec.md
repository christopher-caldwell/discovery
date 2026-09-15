# Recursive conversion and safe reruns

# Preserve nested output paths and make reruns non-destructive

## Executive conclusion

Do not add a second recursion mechanism. The package already discovers nested files.
Change destination planning so every source file maps to the same relative path beneath
the output root with only its final extension changed to `.webp`. Encode to a unique
temporary file, then publish it with an exclusive no-replace operation; if the final path
already exists, discard the temporary file and report a skip. Return a structured result
and let the CLI render that same result.

Also correct the reversed long CLI option names. This was not the ticket's central claim,
but it is an evidence-backed compatibility defect directly relevant to the request that
library and CLI behavior remain consistent.

## Request and corrected premise

The request said nested images are ignored. That premise is false: `getAllFilePaths`
recursively descends into directories, and a disposable probe returned files from two
nested directories. The actual failure is later. `changeOutputPath` removes every parent
directory and maps only the basename into the output root. For example:

```text
source/alpha/photo.jpg -> output/photo.webp
source/beta/photo.png  -> output/photo.webp
```

The target behavior is:

```text
source/alpha/photo.jpg -> output/alpha/photo.webp
source/beta/photo.png  -> output/beta/photo.webp
```

“Safe rerun” was clarified in the controlled scenario to mean: never overwrite an
existing mapped output; skip it, report it, and do no freshness comparison. Deleting an
output is the explicit way to force reconversion. This answer was a predeclared simulated
owner response, not a real maintainer decision, so ratification remains a release condition.

## Current system behavior

- `bulkWebPConvert` resolves source and output roots from the current working directory.
- `getAllFilePaths` recursively returns every non-directory path. Apart from a string
  check for `.DS_Store` and the optional library filter, files are passed to the encoder.
- `changeOutputPath` strips the source directory and changes the final extension.
- No code creates a nested output parent, checks whether the destination exists, or
  prevents the output directory from being inside the source tree.
- The library resolves to the string `done`; it does not expose converted/skipped results.
- CLI short aliases `-ps` and `-po` match the README, but long names are reversed in
  `src/cli.ts` and in actual help output.
- The repository has no automated test script or checked-in test suite.

## Recommended implementation

### 1. Separate discovery from destination planning

Keep recursive discovery, but make the mapper accept `sourceRoot`, `sourceFile`, and
`outputRoot`.

1. Resolve all three paths with Node's `path` module.
2. Compute `relativePath = path.relative(sourceRoot, sourceFile)`.
3. Reject a relative path that is empty, absolute, or begins with `..` after normalization.
4. Replace only the final extension of `relativePath` with `.webp`.
5. Resolve that path beneath `outputRoot` and assert it remains beneath that root.

Do not parse paths with hard-coded `/` separators. Keep path mapping as a pure helper so
POSIX and Windows-shaped cases can be unit tested.

### 2. Validate roots before traversal

Resolve source and output roots once. Reject output equal to source or lexically inside
source. This prevents a rerun from discovering prior outputs and prevents the current run
from traversing directories it creates. Keep symlink behavior explicitly unchanged in
this pass; do not claim a realpath security boundary.

### 3. Convert to temporary state and publish without replacement

For each discovered and filter-approved source:

- compute the mapped destination and create its parent with recursive `mkdir` semantics;
- an initial existence check may avoid unnecessary work, but it is only an optimization;
- when absent, call `cwebp` with a unique temporary path in the same destination directory;
- publish by hard-linking the completed temporary file to the final path. Creation of the
  final link must be exclusive: `EEXIST` means another actor won, so remove the temporary
  file and append an `output_exists` skip;
- on successful publication, unlink the temporary name and append a converted record;
- on encoder or publication failure, best-effort remove the temporary file and propagate
  the error. Never fall back to rename or another operation that may replace the final.

This prevents two cooperating package processes from overwriting one another and prevents
an encoder failure from publishing a partial final output. Preserve current overall failure
behavior for encoder rejection. Completed successes remain on disk and are discoverable on
the next run through the existing-output rule. Do not add a manifest or freshness database.
If hard-link publication is unsupported on a target filesystem, fail clearly rather than
silently weakening the no-overwrite contract; verify supported deployment filesystems.

### 4. Return one shared result contract

Replace the opaque `done` result with a typed summary such as:

```ts
interface BulkConvertResult {
  converted: Array<{ sourcePath: string; outputPath: string }>
  skipped: Array<{
    sourcePath: string
    outputPath: string
    reason: 'output_exists'
  }>
}
```

Use stable paths relative to the supplied roots in the result rather than leaking host
absolute paths. The CLI should print converted and skipped counts and list individual
entries only in verbose mode. The progress total should still count eligible planned
inputs, and skipped entries must advance progress.

### 5. Correct CLI names and document compatibility

Declare the source option as `-ps,--pathToSource` and the output option as
`-po,--pathToOutput`. Keep both short aliases unchanged. Because existing users could
have adapted to the reversed long-name bug, call this out in the changelog/release notes;
there is no way to make the same two spellings simultaneously mean both mappings.

### 6. Bound file eligibility

Do not introduce a new extension allowlist in this change. The current package attempts
to convert every discovered non-directory except `.DS_Store`, and available evidence does
not establish the intended supported-format contract. Preserve that behavior, add a
follow-up issue, and ensure new tests use valid fixture names while mocking the encoder.

## Alternatives considered

- A manifest with content hashes could support freshness-aware reruns, but the clarified
  request explicitly excludes freshness and the extra persistent state is unjustified.
- Keeping a flat output and suffixing collisions does not preserve source structure and
  makes output names dependent on traversal order or a new naming policy.
- Logging skips while continuing to return `done` is smaller, but it leaves library callers
  unable to observe the behavior consistently or test it without intercepting output.

## Acceptance criteria

1. Nested source paths are reproduced beneath the output root with only the final
   extension changed to `.webp`.
2. Equal basenames in different source directories map to distinct destinations.
3. Destination parents are created before encoder invocation.
4. An existing destination is normally not passed to the encoder and appears once in
   `skipped` with reason `output_exists`; a concurrent late `EEXIST` produces the same result.
5. Converted entries are returned only after successful encoder completion.
6. Output equal to or inside source is rejected before traversal.
7. Library results and CLI counts are derived from the same result object.
8. `-ps`/`--pathToSource` and `-po`/`--pathToOutput` bind to the documented values.
9. Current quality, parallelism, logging, and filter semantics remain unchanged.
10. Two concurrent publication attempts create exactly one final output without replacement.
11. Encoder/publication failures leave no partial final output and clean temporary files on
    a best-effort basis.
12. The target repository remains unmodified by discovery and validation activity.

## Validation strategy

Add an automated test runner and focused tests for:

- pure relative mapping on nested paths, multi-dot filenames, and equal basenames;
- path containment and source/output overlap rejection;
- recursive parent creation;
- preexisting destination skip with a spy proving `cwebp` was not called;
- two concurrent temp publications proving one success, one `EEXIST` skip, and no overwrite;
- encoder and publication failures proving no partial final output and temporary cleanup;
- successful converted records and encoder rejection behavior;
- filter interaction and progress increments for skipped files;
- CLI help and parsing for short and corrected long options;
- platform-shaped path cases through Node's path APIs.

Then run lint, type-check, build, and one disposable integration test with real image
fixtures. The supervised probe already established the present recursion/collision behavior,
but it did not validate proposed code because Discovery correctly did not edit the target.
The built-in disposable executor initially blocked on ordinary `node_modules/.bin` symlinks.
After a narrow copy correction materialized link targets inside disposable state, the
replacement experiment ran successfully and recorded the original target tree unchanged.

## Adversarial concerns to retain

- Exclusive hard-link publication depends on filesystem support and same-filesystem temp
  placement. Unsupported filesystems must produce an explicit error, never an overwrite
  fallback.
- Lexical containment is not protection against symlink escapes. This change is path
  correctness, not a filesystem security boundary.
- Changing the library return type and correcting long CLI flags are observable contract
  changes. Release notes and a version decision are required.
- Unsupported-file and symlink policies remain unresolved follow-up product questions; do
  not quietly convert them into new guarantees.

## Evidence and confidence

Strong support exists for the narrow current-behavior findings: direct source, checked-in
documentation, installed dependency documentation, and a disposable actual-helper probe
agree. The implementation recommendation has moderate support because no proposed code was
built and the rerun semantics are based on a simulated owner fixture. Real maintainer
ratification plus passing implementation tests would raise confidence.

Primary traceability: C-001/E-001 (recursive discovery), C-002/E-002 (flattened collision),
C-003/E-003 (controlled skip intent), C-004/E-004 (CLI long names), C-005/E-005 (missing
guards), and C-006/E-006 (dependency output-path capability).

## Next action

Have the package maintainer ratify the skip/result contract and compatibility treatment.
Then implement the four accepted decisions in `src/helpers.ts`, `src/index.ts`, and
`src/cli.ts`, add the test harness and cases above, and release with an explicit note about
the library result and corrected long flags.


## Conclusion confidence

Model or human attributed judgment: ordinal support ratings 1=limited, 2=moderate, 3=strong, null=unassessed. Not a probability, calibrated confidence, or procedural score. Validation checks structure and references, not semantic truth. Finalization does not establish independent review of this assessment.

Assessment status: **current**. No aggregate score is assigned.

### The frozen implementation already discovers nested files but flattens equal-stem nested sources to a colliding destination.

Disposition: supported; support: strong (ordinal rating 3).

Scope: bulk-webp-converter at Git revision cbd8cd01ed15e1accb86a48d27cc2f5567c45544 on the current macOS host

Rationale: Direct source inspection and two disposable actual-helper probes agree, and contradiction search found no alternate mapper.

Supporting evidence: E-001, E-002

Contrary evidence: None recorded

Limitations: Encoder write ordering and cross-platform path behavior were not needed for or covered by this narrow finding

Unknowns: None recorded

Would change with: A different current implementation path or evidence that the probed helpers are not used by bulkWebPConvert

### Relative mapping plus temporary encoding and exclusive no-replace publication is the appropriate implementation for the controlled request.

Disposition: conditional; support: moderate (ordinal rating 2).

Scope: Controlled scenario with skip-and-report semantics and no freshness comparison

Rationale: The design follows the clarified contract, fits the current dependency boundary, survived a material adversarial regression, and its exclusive publication primitive passed a focused disposable probe.

Supporting evidence: E-003, E-005, E-006, E-008

Contrary evidence: None recorded

Limitations: No proposed target code was implemented, Hard-link publication was tested only on the current macOS filesystem, The owner answer is a simulated fixture rather than a real maintainer decision

Unknowns: Maintainer acceptance of the structured result and compatibility break, Hard-link support on all intended deployment filesystems

Would change with: Real maintainer ratification, Passing implementation tests on supported environments, Evidence that required filesystems do not support the proposed publication primitive

Recorded open questions: 0; confirmed defeaters: 0.

## Assumptions and conditional conclusions

No active assumptions.

## Structured technical requirements

### Current accepted decisions

- REQ-001: Map each discovered source to a source-root-relative .webp destination beneath the output root. (D-001, RN-001; accepted)
  Acceptance: Nested paths are preserved and equal basenames in different directories produce distinct output paths.
  Verification: Unit-test pure mapping and a disposable integration case with two nested equal-stem sources.
- REQ-003: Align CLI long source/output names with their documented semantics while preserving short aliases. (D-003, RN-002; accepted)
  Acceptance: Help and parser tests show -ps/--pathToSource for source and -po/--pathToOutput for output.
  Verification: Snapshot help and parse both short and long invocations into identical BulkConvertArgs.
- REQ-004: Reject output equal to or inside source, create destination parents, preserve current file eligibility, and add automated regression tests. (D-004, RN-003; accepted)
  Acceptance: Overlap fails before traversal, nested parents exist before cwebp, and lint/type/build/test scripts pass.
  Verification: Add unit tests for overlap and mkdir ordering, mock the encoder, then run the repository quality commands and a disposable real-image smoke test.
- REQ-005: Publish completed temporary outputs without replacing an existing final destination, including under concurrent package runs. (D-005, RN-002; accepted)
  Acceptance: Two concurrent publications yield one final output, one output_exists skip, no replacement, and no partial final on encoder failure.
  Verification: Race two same-directory publications; inject encoder and publication failures; assert final integrity and best-effort temp cleanup.

### Historical rejected decisions — not current acceptance work

- REQ-002: Skip and report every source whose mapped output already exists, with no freshness comparison. (D-002, RN-002; rejected)
  Acceptance: The encoder is not invoked for existing outputs and the structured result contains one output_exists skipped record per source.
  Verification: Mock cwebp, precreate the mapped output, run conversion, and assert call count and returned result.


## Validation performed

- EXP-001 — Nested destination collision reproduction: blocked. Result: not yet interpreted. Receipt: no execution receipt.
  Limitations: Disposable copy validation rejected ordinary node_modules/.bin symlinks before command execution; no receipt was produced and no fallback was used.
- EXP-002 — Nested destination collision reproduction after symlink-copy correction: passed. Result: The actual frozen helpers discovered both nested fixture files and mapped them to one unique destination, reproducing the corrected problem statement.. Receipt: A-046, sha256 485f3c6a5da1d28910188fc41b7b23e3d572858c9803b342b994c25db7e5579e, run-relative `artifacts/sha256/485f3c6a5da1d28910188fc41b7b23e3d572858c9803b342b994c25db7e5579e`.
  Limitations: This reproduces current mapping behavior only; it does not validate proposed implementation code or encoder concurrency.
- EXP-003 — Exclusive no-replace publication probe: passed. Result: Two concurrent same-directory hard-link publications produced exactly one success, one EEXIST, and one intact winner on the current macOS filesystem.. Receipt: A-055, sha256 68c2976ac0bc5e94fbf3c23fcdb822ea496d26bd42739b61a920d8f8e70da53a, run-relative `artifacts/sha256/68c2976ac0bc5e94fbf3c23fcdb822ea496d26bd42739b61a920d8f8e70da53a`.
  Limitations: Validates the host filesystem and Node runtime only; supported deployment filesystems still require verification, and encoder temp cleanup was not exercised.

## Adversarial findings and remaining risks

- DEF-001 (defeated, material): Check-then-encode does not guarantee no overwrite under concurrent runs and publishes partial final files during encoder failure.

## Traceability and audit material

The readable specification intentionally omits raw ledger state and execution payloads. Exact requirements, decisions, graph relationships, experiment commands, review checks, and procedural assurance were retained in the original run's `handoff.json`. Artifact hashes and run-relative locations were retained in its `evidence-manifest.json`. Those generated files were not kept in the repository. Procedural coverage is supporting audit information, not a probability that this proposal is correct.
