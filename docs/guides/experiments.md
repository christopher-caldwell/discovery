# Experiments and disposable state

Discovery can test an implementation idea instead of reasoning about it from a
distance. The experiment exists to answer a specific question. It does not implement
the target feature and it never merges its changes into the real project.

## The practical isolation boundary

An experiment runs against a disposable copy of the captured source baseline. It may
create files, alter copied configuration, start local processes, and use a disposable
local database. Common dependency links are materialized inside the copy so writes do
not follow them back into the original project.

The original source tree is checked after execution. The receipt states exactly what
that comparison covered and what it could not detect.

A copied directory is not a security boundary. In ordinary `local` mode, an arbitrary
process can still attempt filesystem, network, process, credential, or service access.
Discovery uses a scrubbed environment and rejects command arguments that contain the
original source path, but it does not describe those checks as universal confinement.

## The live data rule

Experiment subprocesses must not mutate live data or live services.

Allowed inputs include:

- the disposable source copy
- a disposable local Postgres, SQLite, Redis, or similar service
- synthetic fixtures
- sanitized snapshots that contain no production credentials
- temporary files created for the experiment

Do not pass production credentials. Do not point an experiment at a production API,
queue, bucket, database, control plane, or mutation capable provider.

The investigator may query a deliberately read only provider outside the subprocess.
Capture that result as research evidence with its source, time, scope, and limitations.
The provider must enforce read only access. A promise in the prompt is not an access
control.

If the only useful test requires a live mutation, mark the experiment blocked. Record
the disposable fixture, service, or permission boundary needed to run it safely.

## Execution modes

`local` is the portable default on macOS and Linux. It runs a reviewed command in the
disposable copy with a scrubbed environment. It provides working state separation, not
operating system containment.

`restricted` requests the macOS Seatbelt adapter. It denies networking and limits
writes to the disposable copy. If Seatbelt is unavailable, execution fails. Discovery
never falls back to `local` after the caller requested `restricted`.

`trusted-local` remains a compatibility spelling for `local`.

Windows execution is not supported by the current contract.

## Plan before execution

Create an experiment only when its result can change a claim, decision, or proof
obligation. Record:

- the hypothesis
- the exact procedure
- the decision being tested
- the result that would support or weaken the hypothesis
- known limitations

```sh
uv run discovery --json --run /absolute/path/to/run \
  <mutation identity> \
  experiment plan \
  --decision D-001 \
  --name 'Concurrent publication probe' \
  --hypothesis 'Exactly one writer can publish the final path' \
  --procedure 'Race two writers against a disposable destination'
```

`<mutation identity>` stands for the global request UUID and actor arguments described
in [Getting started](getting-started.md).

## Execute once

Pass the command as a JSON array. Discovery does not invoke a shell implicitly.

```sh
uv run discovery --json --run /absolute/path/to/run \
  <mutation identity> \
  experiment exec EXP-001 \
  --command '["/usr/bin/python3","probe.py"]' \
  --timeout 60 \
  --execution-mode local
```

For a multiline Python probe, use the helper documented in
[Design, experiments, and finalization](completion-workflow.md). It creates a command
file without shell quoting problems.

Execution reserves the attempt before starting the process. A retry with the same
request UUID recovers the same receipt; it does not run the command twice. A missing
receipt means the attempt was interrupted. Inspect it, stop any surviving process,
abort the attempt, and create an explicit replacement.

## Interpret the receipt

The receipt records the command, scrubbed environment, mode, adapter, platform,
restrictions, limitations, output, exit code, timeout, source identity, and source
comparison.

Read it before calling `experiment finish`. A zero exit code means the process exited
normally. It does not prove the hypothesis. A failed experiment remains part of the
record and can still provide useful evidence.

Choose `passed`, `failed`, `inconclusive`, or `blocked` according to what the result
actually established. Link the experiment to a proof obligation only when the receipt
supports that exact obligation.

## Safety checklist

Before execution, confirm all of the following:

- The command uses only disposable or synthetic state.
- No production credential is present in an argument, file, or configuration.
- No live mutation capable endpoint is reachable by design.
- The hypothesis and failure signal are specific.
- The original project path is not an argument.
- Generated output can remain inside the disposable copy.
- The selected execution mode is described honestly.

If any item is false or unknown, do not execute the command.
