# Questions and assumptions

Discovery treats uncertainty according to its consequence. Some questions must stop
the work. Others can proceed under a visible, limited assumption.

## Blocking questions

A question is blocking when a wrong answer could materially change the requested
behavior, scope, permissions, data handling, or acceptance criteria. Blocking is the
default.

Examples include:

- Which tenants may view the records?
- Does “safe rerun” mean skip existing output or replace it?
- Is backward compatibility required for the current public API?
- Which product rule governs retention?

A blocking question cannot be assumed away. Discovery can continue independent
research, but it cannot build an assumption dependent design and call it complete.

Each question records the likely authority category and why that authority fits. It can
also record ranked role, group, or person candidates. These are hypotheses, not facts.
Do not invent a person or infer product authority from the last Git author.

## Nonblocking questions

A question can be nonblocking when the uncertainty is limited, reversible, and does
not conceal a consequential product choice.

For example, a missing display label might temporarily default to the repository name
when that choice changes presentation only and can be replaced without data loss.

Reclassification is explicit. If later inspection shows that a question was too broad
or too consequential, change its classification with a reason. The history remains.

## What an assumption must say

An assumption records more than a convenient answer:

- the exact behavior being assumed
- why continuing is safe enough
- the scope where the assumption applies
- its impact
- the question it addresses, when applicable
- the condition that would invalidate it
- attribution

An assumption cannot support a claim or decision with greater impact than its own. A
critical uncertainty cannot be carried as an assumption.

## Answers, discharge, and invalidation

When a real answer arrives, record it with its authority and source. If the answer
confirms the assumption, discharge the assumption. If it contradicts the assumption,
invalidate it.

Invalidation does not edit history. It reopens the claims and lanes that depended on
the assumption, stales affected decisions and specification work, and leaves unrelated
research alone.

The run must then return to the earliest phase affected by the correction and traverse
the later gates again.

## What readers should see

Reports and specifications must distinguish three states:

- established: the current evidence supports the conclusion
- conditional: the conclusion depends on an active assumption
- unresolved: an important question still lacks an answer

Do not state an assumption dependent conclusion as an unconditional fact. Put the
condition near the recommendation it changes, not only in an appendix.

## Relevant commands

```text
question create
question reclassify
question respondent-add
question assume
question resolve
question withdraw
assumption create
assumption discharge
assumption invalidate
assumption link-claim
assumption link-decision
```

Use command help for exact arguments. All mutations require the normal request UUID and
actor identity.
