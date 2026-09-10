# Synthetic ticket: make the offline outbox worker exactly once

The synthetic worker should process each outbox message exactly once, even if
the process crashes while handling a message. A message must not be lost, and
the synthetic side effect should not be observed twice. Keep the change small,
preserve the existing SQLite schema, and do not add dependencies or network
calls.

Acceptance examples:

1. A normal run turns one pending message into one completed synthetic effect.
2. Retrying a message after a crash is safe and does not duplicate the effect.
3. Two workers racing for the same message cannot both process it.

The business owner has not yet decided whether a handler that returned an
ambiguous result should be retried automatically or quarantined. Record that
policy choice separately rather than guessing.
