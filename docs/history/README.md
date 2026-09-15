# Historical records

This directory preserves design and evaluation evidence from earlier stages of
Discovery. It is useful when tracing why a decision was made or what a past campaign
observed. It does not define current product behavior.

Use the [product intent](../reference/product-intent.md),
[implementation contract](../reference/implementation-contract.md), and runtime schema
for current behavior.

## Original design

[`original-design/`](original-design/) contains the first design handoff, early schema
drafts, and the original CLI contract. Later implementation decisions may supersede it.

## Evaluations

[`evaluations/`](evaluations/) contains dated synthetic and real project evaluations.
The supervised bulk WebP run retains its final technical specification and evaluation
result while omitting its generated database, copied dependencies, and transient logs.

The `campaigns/` directory contains the larger schema 5 and schema 6 evaluation series.
Counts, paths, and commands in those reports describe their historical environment.

## Product realignment

[`realignment/`](realignment/) contains the implementation delta, validation matrix,
and independent review reports from the schema 7 product realignment. The current guides
and contract incorporate the accepted results.
