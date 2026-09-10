# WEBHOOK-1842 — guarantee ordered, exactly-once webhook application

## Ticket assertion (deliberately inaccurate)

The webhook provider delivers invoice events in sequence order and retries do
not change the final state. Therefore the consumer may apply each request as it
arrives and the final state after `open(seq=1)`, `paid(seq=2)`, and a retry of
`open(seq=1)` is expected to be `paid`.

This assertion is the claim under audit. It is contradicted by the local
reproduction and by the vendor guidance snapshot.

## Acceptance assertion

`test_ticket_claim_events_are_monotonic_and_exactly_once` records the expected
ticket assertion. It is marked as an expected failure so the fixture test run
remains useful while preserving the inaccurate claim.
