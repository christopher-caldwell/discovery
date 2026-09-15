# Evaluation timing observations

New isolated runs preserve `control/events.jsonl` unchanged and write a separate
`control/timing.jsonl` as the process runs. Each complete event line gets a
one-based index, byte offset/length, parent-observed UTC timestamp and monotonic
elapsed time. A partial last line is retained and indexed at shutdown, with an
invalid-event marker when it cannot be parsed. Timing never changes Discovery's
ledger, phase gates or model prompt.

The parent polls at a nominal 250 ms interval. Events emitted together or buffered
by the child may share an observation time; this is not a measurement of when the
model internally began or finished reasoning. Each record includes the previous
poll time so inspection can account for observation granularity.

The observer records the first new, nonempty file in each delivery category:

- `outcome.md` and `answer.md` in the session workspace.
- Interim `exports/reports/*/report.md` files.
- `exports/*/technical-spec.md` specification exports.

Export lookup covers the selected resumed run and ordinary workspace `run`,
`.discovery/runs/*`, and `source/.discovery/runs/*` locations. Other custom run
locations are not discovered automatically. Pre-existing nonempty files are
excluded so a resumed run does not appear to deliver its old report immediately.
A candidate may be incomplete, inaccurate or useless: the evaluator must inspect
its content before calling this time-to-useful-answer. No automatic semantic
quality judgment or investigation/bookkeeping classification is made.

`result.json` includes the timing summary and `summarize_runs.py` exposes it.
Historical runs without this instrumentation return null timing; their event times
are not reconstructed from file modification timestamps. Missing usage at timeout
also remains unavailable rather than zero.

Verification uses a real local child process, without a model call, to test early
output, normal completion, a deadline cutoff, raw event preservation and credential
cleanup. Recorder checks also cover partial lines, pre-existing reports, empty
files and both export formats. The existing isolation and restricted-runner tests
remain part of the focused check.
