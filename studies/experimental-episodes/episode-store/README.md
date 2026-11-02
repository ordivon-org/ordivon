# Experimental Episode PostgreSQL Store R1

Canonical source owner: `studies/experimental-episodes/episode-store/`. This is a Study analytical projection consumer, not a Next-stage service. The relocation changes no Python distribution name, Alembic schema, source semantics, or PostgreSQL authority. Earlier source coordinates are historical evidence rather than supported imports or installed paths.

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

## Runtime R5C projection capability (R2.1)

The portable deterministic projection now resides in the **existing** Study Python
package, not in a task-local `meta` or `next` owner. It is distinct from the
PostgreSQL ingest authority:

- **I:** a typed Runtime R5C owner-native record and the installed Composition
  experimental-episode JSON Schema; optionally a JSONL stream of such records.
- **O:** a validated Episode binding, or a JSONL stream and a deterministic
  cardinality/distribution/digest summary.
- **S:** no persistent projection state; PostgreSQL storage belongs to `ingest.py`.
- **pre/post:** structural source constraints and digest validation are enforced;
  accepted inputs produce deterministic bindings, and duplicate identities
  are explicitly reported instead of silently promoted.
- **inv/eff:** no owner semantic truth, Runtime execution authority, secrets, or
  external publication is created. `runtime_backfill.py` reads source data and
  writes only the caller-designated projection/summary files.
- **c/epsilon/prov/unfold:** the native locked Composition/JSON Schema dependency
  is the implementation basis; invalid source, digest mismatch and collision
  form explicit counterexamples. Source evidence is the exact Git revision and
  immutable historical corpus receipt. Flow is
  `runtime_projection → runtime_backfill → ingest`, with ingest optional and
  separately authorized.

Use the native package CLI, rather than a legacy `meta/next` script path:

```bash
cd studies/experimental-episodes/episode-store
uv sync --locked
uv run --locked ordivon-episode-project project-r5c input.jsonl episodes.jsonl summary.json
uv run --locked ordivon-episode-project validate episode.json
mise run verify
```

The separately retained `queries/runtime_r5c_source.sql` is the PostgreSQL
source-query carrier. Historical frozen manifests may still cite their original
Git coordinates; those are provenance, not current file/import destinations.
