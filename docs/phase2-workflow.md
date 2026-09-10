# Phase 2 operator workflow

All mutations below use global `--run`, `--json`, `--request-id`, `--actor-id`, `--actor-name`, and `--actor-kind` before the command. Read commands require only the run path. Use actual generated UUIDs and preserve request identities for retries. Inspect command help for the complete required arguments.

1. Enter Phase 2 through the real Phase 1 gate. Use `lane activate L-001`.
2. Inspect `surface list` and `method list`. Record concrete research with `research record S-008 --method M-001 --query ... --summary ... --origin-uri ... --report FILE`. Mark searched surfaces and completed methods only after linked activities exist.
3. Capture source or external snapshots with `artifact capture --file FILE --origin-uri URI`. Add `--source-backed` when FILE belongs to the captured source tree. Use `evidence create --lane L-001 --artifact A-... --kind primary|secondary|empirical --locator ... --observation ...` to distinguish source bytes from observations.
4. Add a scoped claim with `claim create --lane L-001 --kind vendor_capability --impact material --text ...`. Add an argument with `argument create --claim C-001 --role supports --evidence E-001 --reasoning ... --limitations ...`. Submit its semantic verification report with `argument verify ARG-001 --outcome passed --report FILE` only after actually assessing the argument.
5. Register new leads using `lead create --lane L-001 --activity RA-... --text ... --impact material`. Every lead must receive a terminal disposition. Investigation requires a separate research activity; duplicate and human-input dispositions require corresponding references. There is no skip.
6. When primary investigation and the lead queue are complete, run `lane closure-begin L-001`. Record and complete each returned closure method. A new lead or evidence invalidates the cycle; finish investigating and start a fresh one. Do not reuse historical closure methods.
7. Run `claim evaluate C-001`. Its result may be proposed or contested even though the command succeeded. Address all violations. Counterarguments remain open until explicitly resolved with distinct evidence, irrespective of supporting argument count.
8. Check `lane check L-001`, then close with `lane close L-001 --answer ... --limitations ...`. Known material answers need an admissible claim; material UNKNOWN requires a linked blocking question via `--question Q-...`. Use `question create --technical` for answer uncertainty in Phase 2. Ambiguity about intended meaning requires Phase 1 regression instead.
9. Answer covered needs with `research-need answer RN-001 --answer ...`. A material UNKNOWN need requires a covering lane linked to an open blocking question; explanatory text beginning with UNKNOWN follows the same rule. Inspect `phase check` and `resume`; advance when all gates pass. The resulting Phase 3 entry is a checkpoint, not a completed technical specification.

If source changes, `source refresh --reason ...` records a replacement baseline and invalidates source-backed evidence from the old baseline. Recapture/reverify affected research. External snapshots and unrelated lanes remain; dependency reopening is automatic. If a human answers a question attached to a closed UNKNOWN lane, that lane reopens to incorporate the answer.

## Synthetic validation

`tests/fixtures/phase2/` contains a small webhook consumer with a deliberate late-retry defect, an inaccurate ticket assertion, fabricated vendor guidance, a reproduction, and a human-policy UNKNOWN. A lighter subagent created the environment. Every document is explicitly fabricated; it is not evidence about a real vendor.

Run its standalone demonstration separately from Discovery's tests:

```sh
uv run pytest tests/fixtures/phase2/test_webhooks.py -q
```

Expected result: one reproduction test passes and one inaccurate-ticket assertion is an intentional strict xfail. Discovery's own test suite excludes that fixture from automatic collection and exercises actual CLI state transitions against synthetic evidence in `tests/test_phase2.py`.
