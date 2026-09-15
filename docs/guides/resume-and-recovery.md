# Resume, regression, and recovery

Discovery stores investigation state so a long run does not depend on one model session
or one chat transcript.

## Resume is the normal entry point

Start every returning session with:

```sh
uv run discovery --json --run /absolute/path/to/run resume --compact
```

The compact packet keeps the state needed to continue and omits large experiment
payloads and prior export bundles. It includes current conclusions, blockers,
assumptions, contrary findings, research obligations, proof obligations, source drift,
open defeaters, gate failures, and useful next actions.

Use ordinary `resume` for the larger projection. Use focused commands such as
`claim list`, `lane list`, `experiment list`, or `defeater list` when you need exact
records. Do not reconstruct current state by replaying audit events.

## Idempotent retries

Every mutation uses a caller supplied request UUID. If a response is lost or SQLite
returns a transient busy result, retry the exact logical command with the same UUID.
Discovery returns the original result without creating another event.

Use a new UUID for a new action. If the input differs under an existing UUID, Discovery
returns `IDEMPOTENCY_CONFLICT`. Do not treat that as a transient error.

## Source drift

Discovery compares the live project with its captured baseline during reads and gates.
Drift blocks advancement.

Regress to Phase 2, or Phase 1 when meaning also changed, then run `source refresh`.
Source backed artifacts whose captured bytes still match their locator are revalidated.
Changed or missing material retracts affected evidence and reopens dependent claims,
lanes, decisions, and specification work. Unrelated lanes remain usable.

The comparison is conservative when provenance cannot identify an exact file. Refresh
never silently blesses evidence it cannot check.

## Regression

Regression preserves history and creates a new traversal from the earliest affected
phase.

Return to Phase 1 when the request, scope, authority, or product intent was misunderstood.
Return to Phase 2 when evidence or a factual conclusion failed. Return to Phase 3 when
the evidence remains sound but the proposed implementation is flawed.

```sh
uv run discovery --json --run /absolute/path/to/run \
  <mutation identity> \
  phase regress \
  --to 3 \
  --cause defeater:DEF-001 \
  --reason 'Concurrent publication can overwrite a completed result'
```

The cause uses `kind:ref` syntax. Intervening phases must pass again. Earlier reviews do
not approve a revised plan or specification.

## Interrupted experiments

Experiment reservation and receipt registration are separate transactions. This keeps
database locks short while the process runs.

Retrying the exact request recovers an existing receipt without executing again. If an
attempt has no receipt, Discovery returns `EXPERIMENT_INTERRUPTED`. Inspect the scratch
directory and stop any surviving process. Then abort the old attempt, plan a new one,
and link it with `experiment replace`. Failed and interrupted attempts remain visible.

## Audit failure

Run:

```sh
uv run discovery --json --run /absolute/path/to/run audit verify
```

Audit verification checks the event chain, current state checksum, schema, foreign
keys, SQLite integrity, artifact bytes, and orphan artifacts. If it fails, stop mutation
work and investigate. Do not edit the database, rewrite artifacts, or reset the run to
make the check pass.

The audit is tamper evidence inside the run. It is not authentication against a
filesystem owner who can replace the entire run with another internally consistent
copy.

## Older schemas

Active runs from schemas 3 through 6 require an explicit `run upgrade` before mutation.
The upgrade is transactional and preserves events and artifacts. A current plan review
or later claim can become stale because the newer schema requires information that the
older record did not contain.

Finalized schema 5 and 6 runs remain readable and exportable without rewriting history.

## Useful output before completion

Use `report export` when the run is blocked or when a bounded investigation has a useful
answer but does not need a complete implementation design. The interim report states
what is known, what remains open, and which gates are unmet. It does not finalize the
run or pretend that unfinished work passed.
