# Synthetic outbox worker cold-evaluation oracle

Keep this file outside `tests/fixtures/outbox_worker/` when giving the source
directory to an investigator.

Expected checks:

- `python3 -m unittest -v` runs 3 tests: 1 passes and 2 are intentional
  expected failures.
- The normal path creates one synthetic effect and marks the outbox row and
  job complete.
- The crash path commits a synthetic effect before its outbox completion mark;
  a retry therefore creates a duplicate effect.
- The crash path leaves the event retryable with its attempt count incremented,
  violating the test's full atomic rollback expectation; the ticket does not
  explicitly require attempts to roll back. An investigator should distinguish
  that extra test assumption from the ticket's no-duplicate-effect requirement.
  The duplicate comes from a non-atomic effect/acknowledgement pair.
- The unresolved policy is whether ambiguous handler outcomes are retried or
  quarantined; the fixture intentionally does not choose.

No network, real user data, or third-party dependency should be introduced.
