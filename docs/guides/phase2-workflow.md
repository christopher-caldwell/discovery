# Phase 2 operator workflow

This is the compact command sequence for Phase 2. Read
[Evidence, claims, and burden of proof](evidence-and-claims.md) first if the entity model
is unfamiliar.

All mutations use the global run path, request UUID, actor UUID, actor name, and actor
kind before the command. Read commands need only the run path and optional JSON output.

## 1. Enter and activate

Enter Phase 2 through the Phase 1 gate. List the planned lanes and activate the ones
whose dependencies are ready.

```text
lane list
lane activate L-001
```

## 2. Record research

Inspect `surface list` and `method list`. For a search or inspection that mainly records
what was done, use:

```text
research record S-008 --method M-001 --query ... --summary ... \
  --origin-uri ... --report FILE
```

Use `--complete-surface` or `--complete-method` only when the recorded work actually
completes that obligation.

Prefer `research capture` when the saved result supplies one or more evidence
observations. Prefer `research finding` when the same action also proposes a claim and
supporting argument. Use `artifact capture` plus `evidence create` when the provenance
needs a custom shape. Add `--source-backed` when a captured file belongs to the source
baseline.

## 3. Evaluate claims

A low level claim command records the proposition, kind, impact, verification method,
and rationale:

```text
claim create --lane L-001 \
  --kind vendor_capability \
  --impact material \
  --verification-method authoritative_record \
  --verification-rationale 'Current first party documentation governs this capability' \
  --text ...
```

Add an argument with `argument create`. Submit `argument verify` only after assessing
the reasoning, evidence, and limitations.

A critical claim automatically gains a falsification method. Use
`claim challenge C-001 --surface S-008 ...` to record the challenge report, evidence,
and argument linkage in one transaction. The operation does not verify or admit the
claim.

Run `claim evaluate C-001` after its evidence case is ready. Command success does not
mean admission. Read the returned status and violations. A proposed or contested claim
still needs work.

## 4. Follow leads and counterevidence

Register a new avenue with `lead create`. Every lead needs a terminal disposition.
Investigation requires a separate activity in the same lane. Duplicate and human input
dispositions need the corresponding reference. There is no generic skip.

Keep refuting and qualifying arguments open until distinct evidence resolves them.
Supporting argument count does not override counterevidence.

## 5. Close the research cycle

When primary research and the lead queue are complete, run:

```text
lane closure-begin L-001
```

Record and complete each returned closure method. New evidence or a new lead makes the
cycle stale. Finish the new work and begin another closure iteration. Historical
methods remain in the record and cannot complete a later iteration.

Run `claim evaluate` again after the closure sweep. Then use `lane check` before
`lane close`.

A known material answer needs an admissible claim at the lane's impact. A material
`UNKNOWN` answer needs a linked open blocking question. Use `question create --technical`
for answer uncertainty discovered in Phase 2. Return to Phase 1 when the uncertainty
changes intended meaning.

Answer each covered research need after all of its lanes close. Inspect `phase check`
and `resume`, then advance when the gate and the investigator's judgment both support
the move.

Continue with [Design, experiments, and finalization](completion-workflow.md).

## Source changes

Source drift blocks advancement. Regress when needed, then use `source refresh`.
Matching source backed artifacts are revalidated. Changed or missing source retracts
affected evidence and reopens its dependents. Unrelated lanes remain usable.

## Synthetic validation fixture

`tests/fixtures/phase2/` contains a fabricated webhook consumer, an inaccurate ticket,
vendor guidance, a reproduction, and an unresolved product policy. It is test material,
not evidence about a real vendor.

Run its standalone behavior check with:

```sh
uv run pytest tests/fixtures/phase2/test_webhooks.py -q
```

One reproduction test passes. One inaccurate ticket assertion is an intentional strict
xfail. Discovery's own Phase 2 tests exercise CLI transitions against the same synthetic
evidence.
