# Vet the request before designing the answer

Start by distinguishing an explanation of existing behavior from a proposed change.
Record that scope and the important premises in the request-surface research report.
For a small source question, trace the relevant caller and implementation and inspect
nearby tests/contracts; widen the search when a contradiction or missing dependency
justifies it. Do not manufacture implementation strategies for explanation-only work.
An interim report remains interim when formal claim review or closure is unfinished.

## Check the governing contract

For a proposed change, locate the current product specification, technical contract,
API documentation or decision records governing the affected behavior. Read the
relevant ownership and lifecycle rules alongside implementation and operating skills.
A skill describing how to operate a system is not a substitute for its product
contract. If no governing document is available, record the search and limitation.

Separate what the ticket asserts, what the written contract requires, what the code
currently does, and what the proposal would change. Documents can be stale; code
behavior is not automatically intended behavior. Preserve disagreements rather than
silently choosing whichever source enables progress. Cite exact sections and source
locations, and identify the role that could authorize a changed contract.

A proposed preview, recommendation or automatic action needs an explicit owner:
who supplies the judgment, who approves it, and who acts on it? When a product
contract reserves a choice to an orchestrator or human, a proposed CLI projection
must not silently take ownership of that choice.

## Stop speculative design at the right boundary

When an unanswered product or authority decision would change the API or persistence
model, record the blocking question and the minimal alternatives needed to answer it. For example,
show the difference between ephemeral advice and a durable reviewed artifact;
do not select storage tables before that distinction is resolved. Continue independent
research that helps frame the question, but defer detail likely to be invalidated.

Separate those human decisions from technical choices the request delegates to the
proposal. An unspecified storage interface or transaction boundary is not automatically
a Phase 1 blocker: research alternatives and propose a justified choice when the
product scope permits it. Keep unavailable operational evidence explicit. On a reply,
reassess each question: preserve unanswered product requirements, but record delegated
design work as research needs rather than demanding that the owner supply the design.
For a compound question, state which parts were answered and where the remaining
parts are tracked; do not resolve the whole question with an invented answer.

A Phase 1 report can substantiate why a premise is disputed without admitting a
Phase 2 claim. Keep supported observations, inferences, alternatives and unknowns
separate. Multiple research activities referencing the same report do not create
independent corroboration. A semantic plan review should explicitly check whether
relevant governing sources and contrary premises were investigated or remain gaps.

## Preserve the reasoning for the next session

Write focused research reports with the inspected procedure/source locations,
observation, qualifications, and unanswered decision. Use concise activity summaries
that point to those reports. On resume, inspect `research_activities` and follow
`research_reports` artifact paths before repeating work or treating prose as a
verified claim. Formal evidence capture and claim verification remain separate.
