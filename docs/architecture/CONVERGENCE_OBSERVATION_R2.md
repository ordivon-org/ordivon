# Convergence Observation R2

Date: 2026-09-23
Status: IMPLEMENTED IN ISOLATED WORKSPACE / CONTROL FEATURES REMAIN EVIDENCE-GATED

## Boundary

Convergence R2 separates four responsibilities:

1. provider adapters read GitHub authority;
2. normalizers emit provider-independent observations;
3. pure metric extractors derive measurements;
4. the pressure assessor diagnoses evidence without provider or mutation authority.

No observation module schedules work, cancels runs, reuses verification evidence, changes
Merge Queue configuration, or publishes Git state.

## LEGO mapping

- CQ-T10/T11/T12: `tools/repo/queue_telemetry.py`
  - GitHub provider snapshot
  - canonical QueueEpisode normalization
  - pure queue metrics
- CQ-T13: saved provider snapshot replay via `--input`
- CQ-T14: JSON Schema 2020-12 contracts under `docs/architecture/schemas/`
- CQ-T20/T21/T22: `tools/repo/ci_telemetry.py`
  - pull_request / merge_group / push run collection
  - job and step timing
  - termination reason separated from economic outcome
- CQ-G40: `tools/repo/convergence_pressure.py`
  - diagnosis-only gate projection

CQ-P31/P32 currently have one durable cross-cutting cost episode:
`docs/architecture/evidence/CONVERGENCE_OWNER_COST_F2EC_R1.json`.
That episode is evidence, not enough history to admit generalized long-tail optimization.

CQ-M80 now reuses the existing Experimental Episode analytical substrate instead of
creating a Queue-specific database:

- adapter: `meta/next/scripts/experimental_episode_convergence_r1.py`;
- queue profile: `convergence-queue-observation-v1`;
- CI profile: `convergence-ci-observation-v1`;
- shared contract: `profiles/experimental-episode/experimental-episode-binding-r1.schema.json`;
- PostgreSQL consumer: `studies/experimental-episode/postgres-projection-r1`.

The adapter emits stable Episode identities plus exact projection digests and binds only
bounded owner references, evidence-set digests, scalar dimensions and numeric measures.
It does not create a Queue schema, store raw provider payloads, or transfer GitHub authority
into PostgreSQL. An isolated PostgreSQL 18.6 acceptance run ingested 13 Queue Episodes and
20 CI Episodes into the existing schema, then replayed both ingests with zero new projection
rows. Evidence is frozen in
`docs/architecture/evidence/CONVERGENCE_OBSERVATION_DATASET_R1.json`.

## Economic classification

Provider conclusions are deliberately not treated as economic truth:

- `cancelled` does not mean wasted;
- `failure` does not mean productive failure;
- `success` does not prove the work was non-duplicated.

CI runs therefore default to `UNCLASSIFIED` economic outcome. A run is classified as
`AVOIDABLE_WASTE`, `DUPLICATED`, `INFRA_FAILURE`, `SAVED_WORK`, or another economic
state only through an explicit evidence annotation. This keeps CI observation distinct from
diagnosis.

## Pressure gates

The pressure assessor emits only:

- `INSUFFICIENT_EVIDENCE`
- `NOT_PROVEN`
- `PROVEN`
- `REGRESSED`

A `PROVEN` gate makes an experiment admissible for consideration; it does not grant
provider authority. GitHub remains the Merge Queue and Actions authority.

Current intended standing remains conservative:

- queue contention: not established by the R1/R2 queue episodes;
- sustained high queue depth: not established;
- CI waste: requires explicit economic classification;
- owner long tail: one cross-cutting episode exists, repeated comparable episodes required;
- predictor data: insufficient and no predictor is admitted.

## Commands

Live queue observation:

    python3 tools/repo/queue_telemetry.py --repo ordivon-org/ordivon

Live CI observation:

    python3 tools/repo/ci_telemetry.py --repo ordivon-org/ordivon

Deterministic replay:

    python3 tools/repo/queue_telemetry.py --input provider-queue.json
    python3 tools/repo/ci_telemetry.py --input provider-ci.json

Diagnosis from saved projections:

    python3 tools/repo/convergence_pressure.py --queue queue.json --ci ci.json

Hermetic contracts:

    uv run --with pytest==9.1.1 python -m pytest -q tools/repo/test_architecture_docs.py \
      -k 'queue_telemetry or ci_telemetry or pressure_gate or convergence_observation_schema'

The fixed R1 baseline remains historical acceptance evidence. Live values are rebuilt from
provider authority and are not copied into a mutable Ordivon queue database.

## Not admitted

The following remain blocked by evidence:

- custom queue scheduler;
- adaptive speculation controller;
- batching/bisection;
- verification-evidence reuse;
- cancellation controller;
- predictive cost scheduling.

CQ-M80 persistence is now implemented through the existing Experimental Episode consumer.
The next evidence step is accumulation of comparable owner-cost episodes and explicit CI
economic annotations; control experiments remain blocked until the corresponding pressure
gate becomes `PROVEN`.
