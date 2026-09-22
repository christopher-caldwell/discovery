# Product realignment review synthesis

Two isolated reviewers audited the same uncommitted implementation without reading
each other's report. Both independently found the assumption-impact loophole and the
ambiguous assumed-question resolution path. Both were fixed with impact-preserving
link/create/gate checks and an explicit confirm/contradict resolution contract whose
contradiction path invalidates dependent claims, lanes, and accepted decisions.

Reviewer B additionally found that bundled evidence capture failed to stale a running
closure. The capture path now matches lower-level evidence invalidation and rejects
same-call completion of a closure method. Both reviewers identified misleading legacy
verification defaults: schema-7 migration now marks historical verification
unavailable with an explicit repair rationale, old unscoped assumptions fail the gate,
and later-phase verification repair is allowed while conservatively staling dependents.

Reviewer A's experiment wording objection was accepted. Receipts no longer claim
general source preservation; they name the included snapshot check, exclusions, and
its inability to detect restored mutations. Reviewer B's portability objection was
also accepted: receipts attest platform/adapter and trusted-local rejects platforms
other than macOS/Linux. README and installation-version contradictions were corrected.

The reviewers' method-to-evidence provenance concern remains a declared limitation,
not a hidden pass condition. The release structurally requires primary evidence for
authoritative records and empirical evidence for tests/experiments, but it does not
prove semantic applicability or bind every label to an external execution system.
Linux trusted-local behavior is unit-controlled but was not run on a Linux host in
this workspace. No fresh blind live-project campaign was performed.
