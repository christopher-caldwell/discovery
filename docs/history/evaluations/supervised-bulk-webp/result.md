# Supervised run result

## Verdict

Pass, with actionable product friction.

Discovery independently corrected the frozen ticket's false recursion premise, identified
basename-only output flattening and collisions as the actual defect, surfaced the ambiguous
rerun contract, used the predeclared simulated owner response, and produced an implementable
specification. It also found an unseeded adjacent issue: the CLI's long source/output option
names are reversed.

The first design did not survive adversarial review. A check-then-direct-write race violated
the unconditional no-overwrite contract. Discovery recorded one canonical material defeater,
regressed to Phase 3, replaced the decision with temporary encoding plus exclusive no-replace
publication, ran a focused publication probe, defeated the finding with distinct evidence,
and repeated Phase 4.

## Frozen-rubric comparison

- Wrong recursion premise corrected: yes.
- Actual flattening/collision defect identified: yes.
- Safe-rerun ambiguity surfaced rather than assumed: yes.
- Source-grounded current behavior: yes.
- Library and CLI design supplied: yes.
- Disposable validation used: yes; two successful recorded experiments after one preserved
  blocked attempt.
- Adversarial review changed the design: yes.
- Engineer-usable next step: yes.
- Target repository modified: no; Git worktree remained clean and receipts retained the
  original source tree hash.
- Fresh-session recovery: yes; compact resume returned finalized conclusions, confidence,
  and no missing actions without chat history.

## Product friction exposed

1. Critical lanes require a falsification method, but proportional closure did not create
   that method automatically. Adding it later invalidated closure and forced a second full
   closure cycle. The tool should provision every method required by its own claim policy or
   expose the missing action directly in resume/gate guidance.
2. The disposable copier initially rejected ordinary `node_modules/.bin` symlinks, making a
   harmless local experiment impossible. The supervised pass implemented the narrow fix:
   materialize link targets in the disposable copy, retain the no-symlink postcondition, and
   verify that writes through the copied path do not affect the original.
3. The exported specification contains two H1 titles because the renderer adds the run title
   above a narrative that already begins with a title.
4. The outcome is strong, but ordinary operation still required 169 audit events and several
   ID-oriented recovery steps after predictable validation errors. High-level operations
   helped, especially grouped Phase-4 review, but the main remaining simplification work is
   gate-directed remediation and fewer mechanical calls—not weaker evidence rules.

## Validation

- Discovery tests: 161 passed.
- Ruff check: passed.
- Ruff format check: passed.
- Git diff whitespace check: passed.
- Discovery audit: valid, 169 events, no audit failures.
- Target Git status: clean.

This was supervised, not blind or independent. No subagents participated. Controlled
scenario input and model-authored reports establish workflow behavior, not independent-model
agreement or real product-owner authority.
