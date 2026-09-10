# Contradictory evidence: local reproduction

The sequence below is deterministic and runs entirely in `app.py`:

```text
invoice-7 seq=1  -> open
invoice-7 seq=2  -> paid
invoice-7 seq=1 retry -> open
```

The consumer returns `{"invoice-7": "open"}` because it applies the retry as a
new last write. This contradicts the ticket's expected `paid` result and shows
that arrival order is insufficient. The pytest reproduction is
`test_reproduction_late_retry_regresses_state`.
