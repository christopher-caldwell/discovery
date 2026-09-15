# How a Discovery run works

Discovery separates investigation into four phases. The phases are not a checklist for
its own sake. Each one answers a different question, and each gate prevents a specific
kind of premature conclusion.

```text
Request and source
       |
       v
1. Intent and scope
       |
       v
2. Investigation and evidence
       |
       v
3. Solution design and validation
       |
       v
4. Adversarial refinement
       |
       v
Technical specification
```

Forward movement follows this order. Regression can return to an earlier phase. The
run keeps prior work and requires the affected later phases to be completed again.

## Phase 1: intent and scope

The first phase asks what the requester actually wants and what must be learned before
a design can be trusted.

Treat every ticket statement as an assertion. Check whether the repository already
does what the ticket asks for. Separate product decisions from engineering decisions.
Record ambiguity instead of silently choosing an interpretation.

Phase 1 begins with seven required research surfaces:

- the request
- source code
- tests
- documentation
- issue history
- external dependencies
- human authority

They are a floor, not a closed list. Add a surface when the project reveals another
meaningful source, such as deployment configuration, a schema history, an ownership
file, or a vendor contract.

Create research needs for consequential unknowns. Each lane should ask a focused
question, state why it matters, define its scope and impact, and name the methods and
surfaces it will use. Dependencies between lanes form a directed acyclic graph.

Before advancing, review the plan as a semantic question: if every lane were answered,
would the investigation cover what matters? The CLI binds that review to the exact plan
snapshot. A later plan edit makes the review stale.

Phase 1 can advance when intent is clear enough, blocking questions are resolved, every
surface has an honest disposition, and the current plan review passes.

## Phase 2: investigation and evidence

The second phase answers the focused research questions. It does not search every
possible source for every possible fact.

An ordinary research action records:

- what was inspected or queried
- the saved artifact or report
- the observation found there
- the source location
- limitations that affect interpretation

Claims are separate from observations. Arguments explain why specific evidence
supports, refutes, or qualifies a claim. A semantic verification records whether that
argument holds up. Admission remains a separate deterministic check.

New evidence can expose another lead. Record it and follow it when it matters. A
credible contradiction stays open until distinct evidence resolves or narrows it.
Supporting arguments do not outvote it.

Closure is proportional to consequence. Contextual work checks evidence gaps. Material
work also searches for contradiction. Critical work expands terminology and related
sources, and every critical claim receives a focused attempt to disprove it.

Phase 2 can advance when the required lanes are exhausted, research needs are answered,
important claims meet their evidence case, open leads are dispositioned, and no source
drift or blocking question remains.

Read [Evidence, claims, and burden of proof](evidence-and-claims.md) for the full model.

## Phase 3: solution design and validation

The third phase turns established knowledge into an implementation recommendation that
fits the actual project.

Compare meaningful strategies. Select one and record why. Technical decisions link
back to admissible claims or explicit assumptions. Requirements connect those decisions
to the research needs they answer, with acceptance criteria and a verification plan.

Proof obligations identify the parts of the proposal that need stronger support. A
useful experiment can satisfy one, but only when its actual result supports the exact
proposition. Exit code zero is not a conclusion.

Experiments run in disposable project state. They can use local databases and synthetic
or sanitized fixtures. They cannot use production credentials or mutate live data.
Read [Experiments and disposable state](experiments.md) before executing one.

Phase 3 ends with a draft technical specification. Structured changes make the draft
stale, because the prose must describe the current decisions and requirements.

## Phase 4: adversarial refinement

The last phase asks how the proposal could be wrong.

Review the actual design against requirements, correctness, data integrity,
concurrency, failure behavior, security, compatibility, performance, operations,
testability, maintainability, and evidence freshness. One substantive report can cover
several categories when the same investigation genuinely applies to each.

A real flaw becomes a defeater. Contextual risks can be accepted with a reason.
Confirmed material or critical flaws force regression. If the evidence was wrong, return
to Phase 2. If the evidence was sound but the design was flawed, return to Phase 3.

Revision does not erase the failed design or challenge. It creates a new current path,
and the revised specification receives a fresh adversarial review.

## Finalization

Finalization recompiles the specification against the current structure and review
state. It then freezes the run against further mutation. Export is safe to repeat and
does not change the run.

The human result is `technical-spec.md`. Audit state, exact graph relationships, and
artifact hashes remain available without taking over the document. See
[The final technical specification](final-specification.md).

## When to stop early

Sometimes Discovery cannot establish an important answer. That is a valid result.

Use `report export` to produce an interim report when authority, evidence, or a safe
test environment is unavailable. The report should state what is known, what blocks,
and what input would let the investigation continue. Do not invent certainty or force
later phases merely to produce a final score.
