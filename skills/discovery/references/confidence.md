# Attributed conclusion confidence

`assessment record --file assessment.json` records an attributed judgment against
the current investigation state. `assessment list` shows current/stale status and
history. Interim reports and technical exports include the latest assessment.
These commands do not advance phases or supply proof for implementation decisions.
Existing gates do not require an assessment; absence remains `not_assessed`.

Record separate propositions when the requested outcome is unresolved but a narrower
finding is supported. For example, production reliability may be unknown while
source evidence strongly establishes that the repository only contains mock tests.
Do not turn evidence absence into evidence that the production objective is false.

```json
{
  "conclusions": [
    {
      "conclusion": "Retries meet the requested production delivery objective",
      "scope": "Provided repository; no production telemetry supplied",
      "disposition": "unresolved",
      "support_level": "unassessed",
      "supporting_evidence": [],
      "contrary_evidence": [],
      "limitations": ["Mock tests do not establish production latency or reliability"],
      "unknowns": ["Representative load, latency and failure distributions"],
      "rationale": "Available observations cannot substantiate this objective",
      "would_change_with": ["Production measurements covering the agreed delivery definition"]
    }
  ]
}
```

The JSON accepts exactly these fields. `conclusion`, `scope`, and `rationale` are
nonempty text. Evidence, limitations, unknowns, and change conditions are arrays.
Limitations and `would_change_with` cannot be empty.

Disposition is `supported`, `refuted`, `conditional`, or `unresolved`. Supported
and conditional propositions require supporting active `E-NNN` references;
refuted propositions require contrary references. Conditional and unresolved
propositions require unknowns. Unresolved propositions use `unassessed` and may
have no evidence references, including while blocked in Phase 1. A Phase 1
research artifact alone cannot satisfy the evidence-reference requirement for a
supported assessment; leave it unassessed rather than inventing evidence.

Support levels encode an **ordinal attributed judgment**, not a probability:

- `limited` (1): some relevant evidence, with substantial limits on inference.
- `moderate` (2): relevant support with material conditions or validation limits.
- `strong` (3): direct support for the stated narrow scope, with counterevidence
  considered and remaining limitations stated.
- `unassessed` (null): no justified support rating for the proposition.

The CLI supplies `support_rating` in output. Do not provide it in input. There is
no aggregate score. Code validates shape, active references and freshness; the
investigator judges relevance, sufficiency and semantic truth. A finalized run
**does not establish independent review of the confidence assessment itself**.

A later substantive change makes the assessment stale, including new or retracted
evidence, changed questions, findings, source drift, regression or a changed
technical narrative. Assessment writes, unreferenced artifact captures and report
exports do not themselves stale it. Old assessments remain visible and attributed.
A stale assessment must not be presented as current confidence. Record a fresh
assessment after considering the changed evidence; do not merely copy its rating.

Schema 5 runs remain readable with no assessment. Upgrade an active run explicitly
before writing schema 6 records; historical finalized runs are not backfilled.
