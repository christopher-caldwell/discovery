# Vendor webhook delivery guidance (fabricated fixture snapshot)

**Source kind:** primary vendor documentation (local fabricated transcription)

For this fixture, the vendor's delivery contract says:

1. A delivery is retried when acknowledgement is delayed or absent.
2. The same event can be delivered more than once; consumers should deduplicate
   using the provider delivery identifier.
3. Delivery order is not guaranteed across retries or concurrent deliveries.
4. Consumers that need resource ordering should compare the event revision or
   sequence supplied in the payload.

This document is intentionally stored locally so the scenario is deterministic
and requires no network or external service. It must not be cited as real
vendor research outside this fixture.
