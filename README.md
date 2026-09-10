# Discovery

A deterministic Python CLI for turning request assertions into a durable, reviewable research plan. SQLite owns workflow state; models and humans supply attributed semantic judgments.

**All four phases can now traverse through finalization.** Discovery supports intent clarification, evidence and claim investigation, leased partitioned/overlap investigators, strategies and proofs, isolated experiments, adversarial defeaters, and structured specification exports. The project is still iterating at **0.2.0**; the storage format is **schema 5**. See [the completion workflow](docs/completion-workflow.md) for the new commands and current boundaries.

## Install and validate

Requires Python 3.11+, SQLite 3.37+ with JSON support, Git available on PATH, and a local POSIX filesystem. No runtime Python dependencies. Development uses uv, pytest, and Ruff.

```sh
uv sync
uv run discovery --help
uv run pytest -q
uv run ruff check src tests
uv run ruff format --check src tests
uv build
```

The wheel includes the executable schema. A run must not be stored on a network filesystem. Copy a live WAL database only with an appropriate SQLite backup/checkpoint procedure; copying the main database file alone is insufficient.

For system-wide editable CLI installation, the direct skill, and the personal Codex plugin, follow [the installation guide](docs/AI_ORCHESTRATED_TOOL_INSTALLATION.md).

## Start a run

Global options precede the command. `--json` also works after the command. Every mutation requires a caller-retained request UUID and explicit actor identity. A session UUID is generated per invocation unless provided. Reuse the **same request UUID and logical input** after a lost response; use a new UUID for a new operation.

```sh
uv run discovery --json --run .discovery/runs/example \
  --request-id 10000000-0000-4000-8000-000000000001 \
  --actor-id 20000000-0000-4000-8000-000000000001 \
  --actor-name 'Discovery investigator' --actor-kind model \
  run init --title 'Investigate webhook ordering' \
  --input /absolute/path/to/ticket.txt --source /absolute/path/to/source \
  --subagents disabled

uv run discovery --json --run .discovery/runs/example status
uv run discovery --json --run .discovery/runs/example resume
```

The run directory is explicit; its name need not equal the generated run UUID. Each directory owns exactly one database and artifact tree. Initialization never replaces an existing run. Request contents are captured as **request assertions**, not verified evidence.

`--subagents` is an explicit invocation choice. Only `disabled` is implemented in this milestone; `partitioned` and `overlap` return `FEATURE_NOT_IMPLEMENTED`. There is no interactive prompt, model API call, automatic messaging, or automatic agent dispatch.

## Command surface

| Command | Purpose |
| --- | --- |
| `run init/upgrade` | Initialize a run or explicitly upgrade schema 3/4 while preserving its audit history |
| `status`, `resume` | Read current state, observed drift, gate violations, and next actions |
| `question create/list/resolve` | Record questions, authority hypotheses, and attributed answers |
| `research-need create/list/answer` | Record needs traced to the request artifact |
| `lane create/list/depends-on/activate/reopen/closure-begin/close/check` | Link needs to scoped questions with impact, methods, surfaces, and acyclic dependencies |
| `surface list/disposition` | Dispose current Phase 1 baseline surfaces with an explicit reason |
| `research record` | Record search strategy, result summary, origin URI, and immutable result artifact |
| `lead create/list/disposition` | Register leads and terminal investigated/irrelevant/duplicate/inaccessible/human-input outcomes |
| `method create/list/disposition` | Record required research methods and completion provenance |
| `artifact capture/list`, `source refresh/list` | Capture snapshots and replace drifted source baselines explicitly |
| `evidence create/list/retract` | Register and retract observations with artifact provenance |
| `claim create/list/check/evaluate/reject` | Evaluate consequence-based evidence profiles |
| `argument create/list/verify/resolve-counter` | Record reasoning, semantic verification, and evidenced counterargument resolutions |
| `plan snapshot/review` | Export exact review context and register an attributed semantic review of its hash |
| `phase check/advance/regress` | Evaluate gates, move one step, or create revisions for an earlier traversal |
| `strategy`, `decision`, `obligation`, `requirement` | Build traceable design and verify proof obligations |
| `experiment plan/exec/finish/abort/replace` | Execute and recover isolated, audited experiments |
| `challenge`, `defeater` | Complete exact-draft adversarial checks and resolve attacks |
| `group`, `agent`, `finding` | Leased isolated investigators and durable reconciliation |
| `spec draft/revise/export`, `assurance calculate` | Compile structured specifications and coverage indicators |
| `audit verify` | Verify event chain, schema/state checksum, foreign keys, SQLite integrity, and artifacts |

Run `uv run discovery --run PATH <command> --help` for required options. Entity arguments accept run-local references (`Q-001`, `RN-001`, `L-001`, `S-001`) or stored UUIDs. Regression causes use `kind:ref`, for example `need:RN-001` or `artifact:A-001`.

A typical Phase 1 sequence is:

1. Create questions. Blocking is the default. Record authority category, rationale, and confidence as a hypothesis; resolve with an attributed answer. Non-blocking questions must also be answered in this slice; explicit assumption commands are deferred.
2. Create research needs, then lanes linked with `--need RN-001`. Each lane requires a concrete question, rationale, scope, impact, at least one `--method`, and at least one `--surface`. Impact cannot be lower than any linked need. Add dependencies with `lane depends-on`.
3. Inspect `surface list`. For an actual search, first use `research record S-001 --query ... --summary ... --origin-uri ... --report /path/to/result.txt`, then disposition it as `searched`. Other supported dispositions are `unavailable`, `inaccessible`, and `not_applicable`, each with a reason. They represent real limitations and must not be used as a shortcut for available research.
4. Export `plan snapshot`. Have the model or human inspect its `context` and write a substantive review report. Submit `plan review --plan-hash HASH --outcome passed --report /path/to/review.txt`. The CLI verifies linkage and freshness; it does not decide whether the report's reasoning is correct.
5. Inspect `phase check` and fix violations. `phase advance` moves from 1 to 2 only if all required records and the current review exist. Subsequent plan edits stale the review. Continue with [the Phase 2 workflow](docs/phase2-workflow.md).
6. If request meaning needs correction, use `phase regress --to 1 --cause need:RN-001 --reason ...`. Questions and research remain. Revisit the new Phase 1 surfaces and review its new plan before advancing again.

Every mutation above also needs the global request and actor options shown in the initialization example. Do not modify the database or durable artifacts directly.

## Machine contract

Success: `{"ok":true,"result":...}`. Mutations additionally return `"replayed":true|false`; replays return the original result and create no event.

Failure: `{"ok":false,"error":{"code":"...","message":"...","details":{...}}}`. Machine stdout contains one JSON document, and unexpected internal diagnostics go to stderr. Exit status is 0 for success, 2 for argument/domain/integrity errors, 3 for SQLite/filesystem failures, and 4 for unexpected internal failures. Explicit `--help` uses normal argparse help text.

`phase check` is a successful query even when `can_advance` is false. `phase advance` with violations and `audit verify` with corruption return nonzero. SQLite contention waits up to five seconds and then returns `SQLITE_BUSY`; retry with the same request UUID. There is no hidden unbounded retry loop.

## Design authority

- [Current implementation contract](docs/implementation-contract.md) describes what this release supports and its boundaries.
- [Decision log](docs/decisions.md) records changes and clarifications to the handoff.
- [Runtime DDL](src/discovery/adapters/sqlite/ddl.sql) is authoritative for schema version 5.
- `discovery-design-package/` is the **unchanged historical handoff**. Within that package, DDL v2 supersedes v1; its CLI contract remains the target architecture for later slices. Its destructive SQL scripts are reference material and must never be run on a live run.
- The archived Independent Consensus Audit is reference material, not an active skill or normative instruction. Discovery retains the requested reviewer denominator and separates support, contradiction, and omission; consensus never establishes verification.

## Existing runs

Use `audit verify` to inspect a schema 3/4 run, then execute `run upgrade` with the normal request/actor flags. Upgrade is explicit, transactional, idempotent, and preserves historical events and the frozen policy. A current Phase 1 review may need repeating because the plan records gain fields. Do not reset a run to upgrade it.

## Next slice

Iterate on real projects, richer evidence profiles, source-refresh granularity, and additional OS sandbox adapters. Experiments currently execute only on macOS with Seatbelt; unsupported systems fail closed. Explicit assumption/withdrawal conveniences and direct Taskledger ingestion remain future extensions. `handoff.json` is produced without modifying an execution ledger. Synthetic fixtures remain available under `tests/fixtures/phase2/`.
