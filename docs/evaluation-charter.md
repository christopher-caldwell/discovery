# Discovery evaluation charter

The product takes a potentially ambiguous or partly incorrect requirement and
vets it against a repository. Its outcome is a thorough, evidence-backed document
with an explained confidence assessment. A valid outcome can be that the available
evidence cannot answer the question. It must not implement or fix the target
request. Evaluation-driven changes to Discovery itself are in scope.

## Evaluate the process from outside

Keep the evaluator's expected issues separate from the operator's ticket. Preserve
what the operator actually inspected, inferred, asked, and failed to notice. Judge
workflow friction, data representation, provenance, uncertainty handling, document
quality and resource use, rather than treating gate completion as success.

| Scenario | What to observe |
| --- | --- |
| Plausible false premise | Does source evidence expose it before it becomes a design constraint? |
| Contradictory requirement | Does the process preserve the contradiction and identify the decision needed? |
| Missing owner decision | Does it ask a specific blocking question without inventing authority? |
| Insufficient or inaccessible evidence | Does it stop with a useful account of unknowns and needed evidence? |
| Simple answer available locally | Does it reach a supported answer without disproportionate research or ceremony? |
| Complex feature proposal | Does it identify affected components, alternatives, compatibility constraints and validation needs without implementing them? |
| Request already satisfied | Does it recognize existing behavior instead of proposing needless changes? |

For each exercise retain the input, independent evaluation expectations, source
baseline, operator transcript, durable records and resulting document. Record
elapsed time, command count, retries and evaluator interventions. Record token
usage only if available; do not infer it from transcript length. Establish budgets
before a run according to its complexity, and record overruns rather than silently
expanding scope. These are evaluation requirements, not claims of existing CLI
budget enforcement.

The resulting document should distinguish supported conclusions, disputed premises,
unresolved questions, missing evidence, and conditions that would change its
recommendation. Thoroughness means enough detail to substantiate the outcome,
not identical length or effort for every request.

## Confidence remains an evaluation gap

The existing `assurance calculate` score measures procedural coverage. It is not a
probability of correctness and must not be presented as the requested confidence
in the answer. Evaluate how a separate confidence assessment should explain
support, counterevidence, unknowns and scope. Test whether confident claims survive
independent review; do not add a numerical formula merely to satisfy the output
shape. Inability to answer the request can coexist with strong evidence that a
particular prerequisite or owner decision is missing.

## Interpretation of earlier runs

The Boilerman repair experiments exposed useful Discovery implementation defects,
but target repair success is not the product acceptance criterion. Future exercises
should stop at vetting and implementation recommendations, including a documented
inability to recommend implementation when warranted. Do not force unresolved
runs through all four phases to improve completion statistics.
