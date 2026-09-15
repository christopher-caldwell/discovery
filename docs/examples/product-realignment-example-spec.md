# Example technical specification: preserve optional display names

Status: controlled, mechanically exercised example. This illustrates schema-7 output
expectations; it is not a live customer proposal and was not deployed.

## Recommendation

Keep stored identifiers and authorization behavior unchanged. When an optional display
name is absent, render the repository name in the operator-facing list only. Do not
persist the fallback and do not expose it through the API.

## Interpreted request and current behavior

The request is treated as a presentation improvement, not permission to change record
identity or visibility. Source inspection establishes that the list renderer reads the
optional label and that authorization filters run before rendering. The request does
not establish a new product rule for API consumers.

## Conditional premise

AS-001: the repository name is an acceptable fallback only for an empty UI label.
This is non-blocking because it does not change persistence, API behavior, or access.
It is invalidated by a product-owner decision selecting another fallback. D-001
depends on AS-001; invalidation returns that decision to proposed and requires a fresh
specification.

## Chosen approach

Add the fallback at the existing presentation boundary. Keep storage, identifiers,
authorization queries, API schemas, and background processing unchanged. A database
default was rejected because it would convert a display condition into durable state.
An API-layer fallback was rejected because it would broaden the behavior beyond the
interpreted request.

## Acceptance criteria

- A record with a display name renders that name unchanged.
- A record without one renders its repository name in the operator list.
- Serialized API responses and stored rows remain byte-for-byte unchanged.
- Authorization filtering still occurs before the label is rendered.
- Changing or invalidating AS-001 makes D-001 and this draft stale.

## Validation plan

Use inspection for the presentation boundary and focused tests for the two label cases,
unchanged serialization, and authorization ordering. No runtime experiment is relevant
to the product-intent premise; an authoritative owner record is the appropriate way to
replace AS-001. A test receipt establishes only the exercised renderer behavior, not
owner approval or production deployment.

## Challenges and remaining risk

Adversarial review should attack accidental persistence, API leakage, localization,
empty-versus-whitespace behavior, and authorization ordering. The remaining product
risk is the unresolved preferred fallback; it is visible as a non-blocking condition,
not presented as established fact.

## Evidence package

The portable run directory is required to resolve immutable artifacts, arguments,
receipts, source baselines, and audit history. The readable specification leads with
the recommendation; `handoff.json` retains exact structured traceability.

