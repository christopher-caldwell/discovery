# Canonical findings across adversarial checks

Release 0.2.0 uses schema 6 for new writes. One defeater can cover several checks
in the same current specification revision and Phase 4 traversal:

```sh
discovery --run RUN --request-id UUID --actor-id UUID --actor-name Investigator \
  --actor-kind model --session-id UUID \
  defeater link-check DEF-001 --check CH-002 \
  --reason 'The same reproduced failure also applies to this check'
```

Create the finding once with `defeater create`, then link it to additional pending
checks before resolving it. Each link records its reason, actor, and creation
time. `challenge complete --disposition completed_findings` accepts either the
original owner link or an additional link. The finding keeps one status,
resolution, evidence set, and gate consequence; linking does not resolve it or
complete any check. A confirmed finding still requires regression before repair.

New links require a nonterminal defeater and a pending check in the same current
specification and traversal. Historical revisions cannot acquire links. Repeating
an existing link in the current scope is a successful no-op, even if the finding
or check has since become terminal; its original reason and attribution remain
unchanged. Reusing a request UUID follows the normal exact-input replay rules.

The original `defeater.adversarial_check_id` remains its historical owner.
`defeater_check` stores all memberships, including the owner. Snapshots and report
JSON preserve the full relationship records. Markdown reports list check IDs per
canonical finding. Specification handoffs, evidence manifests, and adversarial
records also include the memberships. Audit hashes cover the relation and its
attribution; final-review freshness includes the links. The structured design
hash is unchanged because linking does not change the proposed design.

## Existing runs

Inspect an old run with `audit verify`, then use the usual actor/request flags for
`run upgrade` when continuing an active schema 3, 4, or 5 run. The schema 6 upgrade
is transactional and replayable. It backfills original owner links with the
original actor and timestamp and preserves canonical defeater rows, earlier
events, and the run's frozen policy. The upgrade also adds the conclusion
assessment storage used by the assessment commands.

Schema 5 remains readable and auditable without upgrading. Its existing compiled
specification and interim reports can still be exported. Finalized schema 5 runs
remain immutable and do not need an upgrade. Active legacy runs require upgrade
before new mutations; a pre-upgrade Phase 4 review may require repeating because
its reviewed relationship representation has changed.
