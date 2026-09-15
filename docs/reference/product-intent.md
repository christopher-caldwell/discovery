# Product intent

Discovery sits before implementation.

Give it a questionable engineering request and the real project. It should return a
technical specification that an engineer can reasonably trust and build from.

The request does not need to be accurate or complete. Discovery expects vague language,
missing decisions, contradictions, weak research, and confident claims that the source
does not support. The request is evidence of what somebody asked for. It is not proof
that their description of the system is true.

## The division of responsibility

A capable model performs the investigation. It interprets the request, reads the
project, asks focused questions, weighs evidence, compares approaches, runs useful
probes, and challenges its own recommendation.

Deterministic code keeps the work durable and difficult to fake. It records provenance,
open questions, assumptions, source freshness, required research, contrary evidence,
decisions, experiments, and review findings. It prevents illegal phase movement and
rejects conclusions that lack their required evidence case.

The code does not decide semantic truth. A passed gate means the required case was
recorded and remains current. It does not mean the conclusion cannot be wrong.

## Product boundary

Discovery has four phases: intent, investigation, solution design, and adversarial
refinement. Forward movement is sequential. Regression preserves history and requires
the affected path to be traversed again.

Questions, assumptions, observations, claims, arguments, decisions, requirements, and
defeaters remain distinct when that distinction affects trust or invalidation.

Research effort grows with consequence and uncertainty. A contextual fact does not
perform the same research cycle as a critical conclusion. Important counterevidence
cannot be outvoted.

SQLite, immutable artifacts, idempotent transactions, audit history, and the evidence
graph are foundations. They should stay mostly out of the investigator's way. Natural
CLI operations can bundle record keeping, but they never bundle semantic approval.

Experiments use disposable copies and disposable local data. They may use synthetic or
sanitized fixtures. They never receive production credentials or authorization to
mutate live data. Read only provider research happens outside the experiment process
and enters the run as evidence. Optional macOS containment is available when useful,
but Discovery is not a universal security sandbox.

Optional investigator modes preserve isolated reports and credible minority findings.
Agreement is a convergence signal, not proof.

Discovery never implements the target feature. Temporary prototypes can answer a
question, but they remain disposable and never merge into the source project.

## The product is the specification

The primary output is readable engineering prose. It explains what was requested, what
the investigation found, which premises were corrected, what should be built, why that
approach fits, how to verify it, and what remains uncertain.

Exact graph state, hashes, receipts, and procedural coverage belong in supporting
machine artifacts. They should not crowd out the answer.

The model should spend most of its effort understanding the request and system. It
should not spend most of its effort operating an audit database.
