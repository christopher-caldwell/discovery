# Discovery documentation

Use Discovery from an agent chat. The human entry point is the
[README](../README.md); the agent's operating contract is
[AGENT_GUIDE.md](../AGENT_GUIDE.md). The CLI records the work and checks its gates.

## Start here

To install, open this checkout in your agent and say “Install this skill for me.”
The [installation procedure](guides/agent-installation.md) is carried out by the agent.

1. [Getting started](guides/getting-started.md) covers the chat workflow, one CLI
   installation, and continuation in another agent.
2. [Agent integration](reference/agent-integration.md) explains the generic core,
   thin Cursor/Claude/Codex entry files, and optional skill packaging.
3. [How a Discovery run works](guides/workflow.md) explains the four phases.
4. [The final technical specification](guides/final-specification.md) describes
   the artifact the investigation should deliver.

The remaining command guides support agents, troubleshooting, and direct CLI use.
Users do not need to perform those commands manually to start an investigation.

## Concept guides

- [Questions and assumptions](guides/questions-and-assumptions.md) explains what blocks, what
  can be assumed, and how owner answers change existing work.
- [Evidence, claims, and burden of proof](guides/evidence-and-claims.md) explains provenance,
  claim kinds, impact, counterevidence, and falsification.
- [Experiments and disposable state](guides/experiments.md) defines the practical isolation
  boundary and the live data rule.
- [Resume, regression, and recovery](guides/resume-and-recovery.md) covers long investigations,
  source changes, interrupted experiments, and earlier phase corrections.
- [Investigator modes](guides/investigator-modes.md) explains disabled, partitioned, and
  overlap work without treating consensus as proof.

## Operator reference

- [CLI reference](reference/cli.md) lists command families, mutation identity, output,
  replay, and upgrade behavior.
- [Phase 2 workflow](guides/phase2-workflow.md) is a compact command sequence for evidence work.
- [Design, experiments, and finalization](guides/completion-workflow.md) is the detailed Phase 3
  and Phase 4 command guide.
- [Canonical defeaters](reference/canonical-defeaters.md) explains how one defect can cover several
  review categories without duplicate records.
- [Optional Codex skill installation](reference/codex-installation.md) covers the
  existing skill/plugin distribution path; it is not required for ordinary use.

## Maintainer reference

- [Product intent](reference/product-intent.md) defines what belongs in Discovery and what does not.
- [Implementation contract](reference/implementation-contract.md) records current runtime behavior.
- [Decision log](reference/decisions.md) explains why the implementation changed.

The runtime schema in `src/discovery/adapters/sqlite/ddl.sql` is authoritative for
storage. The implementation contract is authoritative for current product behavior.
The decision log explains intentional changes but does not override either source.

## Historical material

The [history index](history/README.md) collects the original design handoff, evaluation
campaigns, validation logs, and product realignment reviews. These files show what a
particular run or review observed at a particular point in development. They are not
current operating instructions.

The runtime schema in `src/discovery/adapters/sqlite/ddl.sql` remains authoritative for
storage. The current implementation contract and product intent take precedence over
historical design files where behavior has changed.
