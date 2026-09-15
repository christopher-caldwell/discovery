# CLI reference

This guide describes the public command surface. Use command help for the exact options
accepted by an operation:

```sh
uv run discovery --run /absolute/path/to/run <family> <action> --help
```

## Global options

`--run` points to the directory that owns `discovery.sqlite`, artifacts, scratch state,
and exports. State commands require it; `guide`, `--version`, and help do not.

`--json` returns a stable machine envelope. It can appear before or after the command.

Mutations also require:

```text
--request-id UUID
--actor-id UUID
--actor-name NAME
--actor-kind human|model|system
```

`--session-id` is optional attribution. A generated value is used when it is absent.
Leased investigators also use `--agent-run` and `--lease`.

Global options appear before the command family. Options belonging to the command appear
after its action.

## Command families

| Family | Purpose |
| --- | --- |
| `guide` | Read the bundled agent guide or a detailed reference without a run |
| `run init`, `run upgrade` | Create a run or upgrade an active older schema |
| `status`, `resume` | Read current phase, state, drift, gates, and next actions |
| `report export` | Export a useful interim report without finalizing |
| `question` | Create, classify, answer, assume, withdraw, and target questions |
| `assumption` | Create, discharge, invalidate, and link explicit assumptions |
| `research-need` | Define and answer the unknowns the investigation must resolve |
| `lane` | Plan, activate, order, close, reopen, and check focused research lanes |
| `surface` | Add or disposition places that must be inspected |
| `research` | Record activity, capture observations, or record a natural finding |
| `lead` | Preserve and disposition new research avenues |
| `method` | Add and disposition research methods |
| `artifact` | Capture immutable source or result material |
| `evidence` | Register or retract observations with provenance |
| `claim` | Create, challenge, evaluate, reject, and inspect claims |
| `argument` | Link reasoning to evidence, verify it, and resolve counterevidence |
| `source` | Inspect or refresh source baselines |
| `plan` | Read the exact research plan and submit its semantic review |
| `phase` | Check gates, advance one phase, or regress with a cause |
| `strategy` | Record, select, and reject implementation approaches |
| `decision` | Record and disposition technical decisions |
| `obligation` | Define and prove important design obligations |
| `requirement` | Connect accepted decisions to needs and acceptance criteria |
| `experiment` | Plan, execute, finish, abort, and replace disposable probes |
| `challenge` | Initialize and complete adversarial review checks |
| `defeater` | Record, confirm, link, resolve, or accept a contextual flaw |
| `spec` | Draft, revise, inspect, and export the technical specification |
| `assessment` | Record and read attributed conclusion confidence |
| `assurance` | Calculate procedural coverage, not correctness probability |
| `group`, `agent`, `finding` | Operate isolated partitioned or overlap investigators |
| `audit` | Verify the event chain, state, schema, and artifacts |

## Agent bootstrap

`discovery guide` emits the shared Markdown operating guide. `--json` instead
returns `{"ok":true,"result":{"markdown":"..."}}`. Use `guide --topic TOPIC` for
phase-specific detail; `guide --help` lists the accepted topics. It reads installed
resources without requiring `--run`, actor flags, an agent plugin, or network access.

`run init` defaults `--subagents` to `disabled`. Explicit `disabled`, `partitioned`,
and `overlap` remain accepted. Omitting the flag has the same logical input as
explicit `disabled`, including on an idempotent retry. Existing runs keep their
recorded mode. The agent supplies the request file and mutation identity; the user
can provide their request in chat.

## Natural research operations

Three commands cover the common evidence path without hiding semantic decisions.

`research capture` records a saved result, research activity, and one or more evidence
observations in one transaction. It creates no claim.

`research finding` adds one proposed claim and its supporting argument. The argument
still needs explicit verification, and the claim still needs evaluation.

`claim challenge` records a critical claim's falsification report, activity,
observations, evidence, and supporting, refuting, or qualifying argument. It completes
the claim's planned falsification method. It does not verify the argument, admit the
claim, close the lane, or advance the phase.

These operations are conveniences for coherent investigator actions. Lower level
commands remain available for unusual provenance or relationships.

## References

Commands return short run local references such as:

```text
Q-001     question
AS-001    assumption
RN-001    research need
L-001     lane
S-001     surface
M-001     method
RA-001    research activity
A-001     artifact
E-001     evidence
C-001     claim
ARG-001   argument
D-001     decision
PO-001    proof obligation
EXP-001   experiment
CH-001    adversarial check
DEF-001   defeater
SPEC-001  specification revision
```

Entity arguments accept the short reference or stored UUID. A short reference is local
to one run.

## Replay and request identity

A mutation is identified by its request UUID, actor, command, and canonical logical
input. Repeating that exact mutation returns the stored result with `"replayed": true`
and creates no new event.

Changing the logical input while keeping the request UUID returns
`IDEMPOTENCY_CONFLICT`. Generate a new UUID for the new action.

List flags are sorted and duplicate values are removed before identity is calculated.
File based commands include the content hash in their logical input. Preserve the input
file until the result is known.

## Output and exit status

`guide` uses plain Markdown unless `--json` is supplied. Other successful commands use:

```json
{"ok":true,"result":{}}
```

Mutation results also include the replay state. A domain or argument failure uses:

```json
{"ok":false,"error":{"code":"...","message":"...","details":{}}}
```

Exit status meanings:

| Status | Meaning |
| --- | --- |
| `0` | The command completed. A gate query can still report that advancement is blocked. |
| `2` | Argument, state, gate, or integrity error |
| `3` | SQLite or filesystem error |
| `4` | Unexpected internal error |

`phase check` returning status zero means the query succeeded. Read `can_advance` to
know whether the phase gate passed.

## SQLite contention

Connections wait up to five seconds for SQLite contention. A remaining conflict returns
`SQLITE_BUSY`. Retry the exact mutation with the same request UUID. Stop and inspect the
run if the same conflict repeats without progress.

## Upgrades

New runs use schema 7. Active schema 3, 4, 5, or 6 runs require `run upgrade` before
mutation. Verify the audit first, then run the upgrade with normal mutation identity.

The upgrade preserves history and artifacts. It can make older plans or claims stale
when schema 7 requires information that was not present. Resolve those gaps through the
normal workflow. Do not edit SQLite directly.

Finalized schema 5 and 6 runs remain readable and exportable without an upgrade.

## Read commands

Read commands need only `--run` and optional `--json`. They include status, resume,
list operations, gate checks, plan and spec snapshots, report and spec exports,
assurance calculation, and audit verification.

Exports materialize already committed state. `spec export` requires a compiled
specification. `report export` is available before finalization and does not imply that
gates passed.
