# Reviewing experiment evidence and adversarial work

Read this when accepting empirical proof or completing adversarial checks. The
CLI validates references and procedural gates; it cannot determine whether a
report's prose is true. A confidence score or clean process exit cannot supply
missing observations. Inspect nested tool results as well as the outer process: a wrapper may exit successfully while a test runner reports worker-cleanup errors or other failures in an embedded stderr field.

## Empirical review

For each material conclusion, identify the immutable receipt/script, relevant
case, actual assertion, observed result, and scope limitation. A short table in
the verification report is sufficient. Follow the code to confirm that the
assertion checks the claimed state before a reset or another test changes it.
Resolve non-system runtime executables to verified absolute file paths before preparing the command. The sandbox uses a minimal PATH; host-shell success does not prove the executable will be found there. Keep scratch paths under the sandbox cwd.

Printed expected values, tautological assertions and expected-failure test suite
exit codes are not proof of repaired behavior.

Check that cases begin from appropriate independent state. For concurrency,
verify separate workers/connections exercise the real proposed function and that
the setup establishes the contention being claimed. For crash claims, distinguish
cooperative rollback from abrupt process exit and from power loss. Test shared
processing code at explicit boundaries instead of an independently rewritten
approximation. These checks apply when those behaviors are claimed, not to every
experiment regardless of purpose.

Separate original behavior, proposed behavior, requirements and test assumptions.
A test may enforce an assumption absent from the request. Capture that ambiguity;
do not silently promote it into a user requirement. Read the actual failing
assertion and exception before assigning meaning to failure.

If a previous passing interpretation was wrong, retain its receipt and record the
new finding. Reopen/fail the obligation; use explicit regression when required.
Later evidence can repair the proof, but the final narrative should identify which
receipt supports its current claims. Do not rewrite historical reports to make
them appear correct in retrospect.

## Adversarial review

Each configured category needs a specific attack or inspection, the target claim
or decision, observed result, evidence references, and remaining limitations.
Use separate reports or clearly labeled category sections. A generic paragraph
saying the probe passed does not show that security, performance and recovery
were each examined. Static review can support a scoped conclusion; do not label
it a runtime test. Record unavailable evidence honestly and leave material
unresolved findings blocking. A lower coverage score is preferable to an
unsupported completion claim.

For consequential proofs, an independent reviewer should inspect the exact
script, assertions and final draft without being told to confirm the author's
conclusion. Account for the reviewer's actual scope; independence does not turn
its report into primary evidence or guarantee correctness.
