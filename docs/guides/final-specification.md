# The final technical specification

The technical specification is the reason Discovery exists. A complete ledger with a
weak specification is a failed outcome. The engineer receiving the document should be
able to understand what to build without reading the original chat or opening the
SQLite database.

## Lead with the answer

Start with the recommendation and its scope. State what should change, what should stay
the same, and any condition that could alter the decision.

Do not begin with audit hashes, phase history, assurance scores, or a tour of Discovery
records. Those details remain available in supporting artifacts.

The renderer owns the document's single top level title. Begin the authored narrative
with the executive conclusion. If the narrative contains its own leading H1, the
renderer removes it as redundant.

## What the specification should contain

Use the structure that best fits the project. Most specifications need these subjects:

### Executive conclusion

Give the recommended implementation in concrete terms. Include the most important
reason and any unresolved condition.

### Request and interpreted intent

Summarize what was asked and what Discovery determined the requester actually needs.
Call out any corrected premise.

### Current system behavior

Describe the relevant behavior of the existing project. Cite the evidence that matters,
especially when the ticket described the system incorrectly.

### Recommended implementation

Name the affected components, control flow, data behavior, API changes, compatibility
choices, and failure behavior. Use the project's actual abstractions and terminology.

### Alternatives and decisions

Include alternatives that would be reasonable to an engineer reading the spec. Explain
why the selected option fits better. Do not pad this section with ceremonial options.

### Assumptions and unresolved conditions

Put active assumptions near the decisions they affect. State what would invalidate
them. Keep unresolved blockers visible and name the authority or evidence needed.

### Acceptance criteria and validation

Write criteria that distinguish a correct implementation from a plausible one. Cover
the normal path, meaningful edge cases, failure behavior, compatibility, and the tests
or observations that should verify the result.

### Adversarial findings and risk

Describe substantive attacks on the proposal, what they found, and how confirmed flaws
were resolved. Preserve remaining limits without burying the recommendation in generic
caution.

### Conclusion confidence

Use supported, refuted, conditional, or unresolved. Describe support as limited,
moderate, or strong and explain why. Do not translate procedural coverage into a
probability.

### Traceability

Reference the important claims, decisions, requirements, evidence, and experiment
receipts in a compact form. Leave exhaustive rows and payloads to the JSON artifacts.

## Write requirements an engineer can implement

A requirement should say what behavior must hold, the decision it implements, the need
it answers, how acceptance will be judged, and how it will be verified.

Weak:

> Handle collisions safely.

Useful:

> Derive the destination from the source root relative path and replace only the final
> extension. Two source files in different directories must not map to the same output
> unless their relative paths are otherwise identical.

The useful version gives an engineer a rule and gives a test author something to
assert.

## Keep facts, assumptions, and proposals distinct

Use direct language for established facts. Use conditional language only where a
condition exists. Do not let a recommendation read like current behavior, and do not
let an active assumption read like a confirmed product decision.

Evidence references should support the sentence they accompany. A source file can
support a statement about current code. A product record can support intended behavior.
An experiment receipt supports only what happened under its recorded conditions.

## The export bundle

`technical-spec.md` is the primary engineering document.

`discovery-summary.md` gives the result, active conditions, and remaining review limits
in a shorter form.

`handoff.json` contains exact decisions, requirements, proof obligations, graph
relationships, confidence records, and procedural assurance.

`evidence-manifest.json` contains evidence, artifact provenance, arguments, assumption
links, and experiment artifact references.

The Markdown files should not embed giant JSON blocks. Links and run relative artifact
paths keep the readable result connected to the detailed record.

## Final review

Before finalization, read `technical-spec.md` as if you were the implementing engineer:

- Is the recommendation obvious in the first section?
- Are corrected ticket premises explicit?
- Does every important behavior have a concrete rule?
- Are assumptions and blockers impossible to mistake for facts?
- Can the acceptance criteria catch the failures found during investigation?
- Did adversarial review change the document where it found a real issue?
- Can evidence references be resolved from the export and run directory?
- Is internal workflow detail kept out of the main reading path?

If the document fails this review, revise it before finalization. Passing structural
gates does not rescue unclear engineering prose.
