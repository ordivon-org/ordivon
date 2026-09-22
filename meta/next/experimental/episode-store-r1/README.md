# Experimental Episode PostgreSQL Store R1

Status: **task-local analytical consumer / not deployed owner truth**

This consumer exists only because Experimental Episode R1 survived two materially different pressure tests: historical Runtime R5C and Harness RSI evidence.

## Owner boundary

PostgreSQL stores a rebuildable analytical projection. It does not replace Runtime, Harness, Host, Git, Artifact, domain, or evaluation truth.

Workstation continues to own PostgreSQL deployment/backup substrate. This directory owns only the consumer schema, migrations, ingest semantics, and analytical-store acceptance.

There is no long-lived service in R1.

## Projection-version law

The primary identity is `(episode_id, projection_digest)`.

A later enrichment of the same Episode creates another projection version. It never silently overwrites an earlier projection and does not assert which projection is owner-current.

## R1 tables

- `episode_projections`
- `episode_owner_refs`
- `episode_evidence_bindings`
- `episode_dimensions`
- `episode_measures`
- `projection_ingests`

No raw owner payload, prompt, workspace snapshot, execution plan, event payload, artifact bytes, credential, or secret column exists.

## Migration law

Alembic is the sole schema authority. The ingest program never creates or migrates schema.

## Ingest law

An ingest is bound to exact corpus ID, profile ID, source file SHA-256, projection-set digest, Episode schema digest, and adapter digest.

The deterministic ingest ID makes replay idempotent. Replaying an accepted ingest returns the retained receipt instead of writing a second ingest or mutating owner truth.
