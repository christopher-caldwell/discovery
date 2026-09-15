## Design, experiments, and adversarial refinement

Phase 3 selects one strategy, records accepted decisions traced to admissible claims, and creates impact-preserving proof obligations. Use `strategy create/select/reject`, `decision create/accept/reject`, `obligation create/attach-evidence/attach-experiment/satisfy/fail/block/not-applicable`, and `requirement create`. Requirements link an answered need, a decision, acceptance criteria, and a verification plan. Do not disguise unresolved decisions or proofs as contextual to pass gates.

`experiment plan` records a hypothesis before execution. Ordinary `experiment exec`
copies the source baseline, runs a reviewed argv command there with a scrubbed
environment, captures its result, and compares the original source afterward. This is
portable disposable execution, not a security boundary; it cannot prevent external
effects. Do not use it for untrusted code or commands that may contact real services.
When stronger local containment is specifically useful, `--execution-mode restricted`
requests macOS Seatbelt, limits writes to the copy, denies networking, and never falls
back. The compatibility spelling `trusted-local` maps to ordinary `local` mode.

The disposable copy may contain local databases and synthetic or sanitized fixtures.
It must not contain production credentials or be used for any live mutation. When
current external information is necessary, call a deliberately read-only provider as
research outside the experiment subprocess and capture the result as evidence. If the
only meaningful test requires changing live data, mark the experiment blocked and
state what safe fixture or environment is missing.

Inspect execution mode, enforced restrictions, safety limitations, original-source comparison, exit code, `output_limited`, stdout/stderr, and hashes before `experiment finish`. A zero exit does not prove the hypothesis. Before accepting empirical proof, read [evidence-review.md](evidence-review.md) and map each material conclusion to its actual assertion, receipt observation, and limitation. Execution has separately audited reservation and receipt-registration transactions. Retry the same request to recover a recorded receipt, never to rerun. Output capture stops the process group when either stream exceeds 2,000,000 bytes; an output-limited result cannot pass. On `EXPERIMENT_INTERRUPTED`, inspect the existing scratch attempt and stop any surviving child process, then abort explicitly and create a replacement. Do not hide failed attempts or delete records.

Write substantive technical narrative and use `spec draft --narrative FILE`. Structured changes stale the draft. Phase 3 advances only after traceability and proof gates pass.

For probes already present in the source baseline, write a JSON argv file such as
`["/absolute/path/to/python3", "probe.py"]`, then use:

```sh
discovery ... experiment exec EXP-001 --command-file /absolute/command.json
```

For a new multiline probe, write the script and command file under `.discovery/`
(outside the captured artifact directory). A host Python process can prepare argv
without nested shell quoting:

```python
import json
from pathlib import Path

script = Path("/absolute/source/.discovery/probe.py").read_text(encoding="utf-8")
Path("/absolute/source/.discovery/command.json").write_text(
    json.dumps(["/absolute/path/to/python3", "-c", script]), encoding="utf-8"
)
```

The command runs in the disposable copy. Resolve the interpreter on the host first;
it must exist there. Probes must use paths relative to the copied working directory,
not the original source. Retain the command file unchanged for retries; edited bytes
with the same request are a conflict. A full source/skill checkout also provides
`scripts/prepare_experiment.py` for probes that require a script file and `__file__`;
that helper is optional and is not needed for the installed CLI workflow.

In Phase 4, use `challenge initialize` to create the configured checks against the exact draft. Try to break the design; submit actual reports with `challenge complete`. Read [evidence-review.md](evidence-review.md) for category-specific attacks, observations, and evidence limits; generic pass statements are insufficient. Findings need linked `defeater create` records targeting a claim or decision with evidence. When one defect affects several current review categories, create it once and use `defeater link-check DEF-001 --check CH-002 --reason "specific relevance"` for each additional check. Keep distinct defects separate. One canonical defect has one confirmation and resolution; category links are not independent confirmations. Links require the same exact draft and traversal. `defeater confirm` requires explicit regression before repair; `defeater defeat` needs distinct active resolution evidence and a report. Only contextual risks can be accepted. Revision with `spec revise` requires a fresh set of checks; prior defeaters are not erased.

`assurance calculate` reports procedural coverage, not correctness probabilities. Scores never override gates. Phase 4 `phase advance` atomically compiles final artifacts, records scores, and finalizes the run. `spec export` materializes `technical-spec.md`, `discovery-summary.md`, `evidence-manifest.json`, and `handoff.json`. It does not submit work to Taskledger. Describe remaining limitations honestly even when all structural gates pass.
