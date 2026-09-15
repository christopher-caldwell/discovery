# Investigator modes

Discovery can use one investigator or preserve work from several isolated model
sessions. Multiple investigators are optional. They help with speed or omission
detection, but agreement never becomes proof.

Choose the mode once when initializing the run.

## Disabled

`disabled` uses one primary investigator. This is the default choice for ordinary work
when no separate investigation is needed.

## Partitioned

`partitioned` assigns different research lanes to different investigators. Use it when
the lanes can progress independently and parallel work will save time.

Each investigator receives immutable scoped context, a distinct actor identity, and a
lease. Its findings remain private until reconciliation. The primary investigator
reviews imported work before it becomes canonical evidence or a claim.

## Overlap

`overlap` assigns the same question to two or more investigators without sharing their
answers first. Use it when omission detection is worth the added model cost.

Investigators can report:

- `support`, when their evidence supports the proposition
- `refute`, when they found credible contrary evidence
- `unique`, when they found a distinct issue or avenue
- `not_seen`, when they did not observe the issue

`not_seen` is not disagreement. If one investigator finds a credible contradiction,
the others failing to notice it does not cancel it. The primary investigation must
resolve the evidence.

## What consensus means

Agreement is a convergence signal. It can increase confidence that obvious avenues
were not missed, but several models can make the same mistake. Claim admission still
depends on evidence, argument verification, and the normal gates.

The requested number of investigators remains visible. Failed or expired participation
cannot silently reduce the denominator. Supersede a failed group explicitly and create
a replacement when the investigation still needs it.

## Operational boundary

Discovery stores assignments, leases, scoped context, findings, and reconciliation.
It does not call a model provider or launch workers. The surrounding agent environment
starts the sessions and supplies each lease.

Lease isolation protects the workflow from accidental cross submission through the
CLI. It is not authentication against a filesystem owner who can impersonate another
actor or edit files outside the CLI.

## When to use each mode

Use `disabled` for most runs.

Use `partitioned` when independent lanes are large enough to justify parallel work.

Use `overlap` when the consequence of a missed issue justifies independent duplication.
Do not choose it automatically merely because several workers are available.

The detailed command sequence is in
[Design, experiments, and finalization](completion-workflow.md#leased-investigators).
