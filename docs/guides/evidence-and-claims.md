# Evidence, claims, and burden of proof

Discovery keeps the inspected thing, the observation, and the conclusion separate.
That distinction makes a result traceable and lets later source changes invalidate only
the work that depended on them.

## The evidence chain

```text
artifact
   |
   v
evidence observation
   |
   v
argument
   |
   v
claim
   |
   v
decision
   |
   v
requirement
```

An artifact is captured material: a source file, document, command receipt, or saved
research report. Evidence records a specific observation and locator within that
material. An argument explains why one or more observations bear on a claim. A claim is
the proposition Discovery may rely on.

Capturing a ticket again does not turn its assertions into evidence.

## Evidence kinds

Primary evidence comes directly from the authority or system that can establish the
proposition. Examples include relevant source code, an applicable contract, or a
current product decision from the responsible owner.

Empirical evidence records an observation from a test, runtime probe, or experiment.
It establishes what happened under the recorded conditions. It does not automatically
establish a general rule.

Secondary evidence summarizes, interprets, or reports another source. It can guide
research and support contextual conclusions, but consequential claims usually need a
stronger source.

The investigator classifies evidence. The CLI checks provenance and required classes;
it cannot decide whether the observation was interpreted well.

## Claim kind determines the right proof

Current behavior is usually established through source inspection, analysis, tests, or
an experiment. A runtime observation can be necessary when static code does not settle
the behavior.

Intended behavior requires an authoritative product record or clarification. A passing
test cannot prove what the product owner wants.

Vendor capability is commonly established through current first party documentation,
an applicable contract or version, and an empirical check when actual behavior matters.

A constraint takes its proof from its origin. That may be architecture, schema,
deployment, platform, contract, or a product decision.

Discovery rejects obvious method mismatches. The investigator still explains why the
chosen method is appropriate and records what it cannot establish.

## Impact controls depth

Claims have contextual, material, or critical impact.

Contextual claims need provenance. Material claims add primary or empirical support,
semantic verification, and contradiction search. Critical claims add a deliberate
attempt to disprove the proposition.

This does not mean every critical claim needs a runtime experiment. The challenge must
fit the claim. A critical product intent claim can be challenged by searching the
authoritative record for exceptions or conflicting decisions. A critical runtime claim
may need a focused test or experiment.

Creating a critical claim automatically provisions its falsification method. Use
`claim challenge` to record the report, observations, evidence, reasoning, and whether
the result supports, refutes, or qualifies that exact claim. The command handles record
wiring but does not verify the argument or admit the claim.

## Counterevidence

Any credible refuting or qualifying argument remains open until it receives an
evidenced disposition. Ten supporting arguments do not cancel one unresolved
contradiction.

Resolution needs distinct evidence. Copying the same artifact or rephrasing the
counterargument does not resolve it. The proper outcome can be a narrower claim, a
rejected claim, or an explicit unknown.

## Unknown is a valid conclusion

If the available evidence cannot establish an important proposition, keep the claim
proposed or contested. State what evidence is missing. A material unknown that blocks
implementation stays linked to an open blocking question.

Procedural exhaustion means the required investigation was performed and known leads
were handled. It does not claim that every fact in existence was found.

## Natural operator actions

Use `research capture` when one saved result produces one or more observations. Use
`research finding` when the same action also proposes a claim and supporting argument.
Use `claim challenge` for a critical claim's falsification attempt.

These operations are transactional and safe to replay with the same request UUID. None
of them performs semantic approval. Argument verification, claim evaluation, lane
closure, and phase advancement remain explicit.
