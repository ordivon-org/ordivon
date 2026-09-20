# Provider: Dagster

Status: **PROTOTYPE-READY / ON-DEMAND DATA-ASSET ORCHESTRATOR / NOT LOCALLY INSTALLED**
Role: asset-centric orchestration platform for recurring data products, partitions, backfills, lineage, quality checks and external data-compute integration.

## One-sentence understanding

**Dagster models durable data products as dependency-aware Assets and orchestrates their materializations, partitions, backfills, checks and automation while keeping physical storage/compute behind replaceable resources, I/O managers and external integrations.**

## Current upstream observation — 2026-09-14

- repository: `dagster-io/dagster`;
- approximately 16.1k GitHub stars observed during this study;
- Apache-2.0 license;
- current release stream observed at core `1.13.21` / libraries `0.29.21`;
- project positioning remains explicitly asset-centric: development, production and observation of data assets with integrated lineage and observability.

## Current local observation

No `dagster` executable, importable Dagster Python package, uv tool or obvious local Dagster project was observed during the 2026-09-14 census.

Do not install Dagster merely to fill a generic orchestration slot. Activate it when a real recurring data-asset network exposes partition/backfill/lineage/freshness/quality requirements that existing Snakemake/SQL/n8n/Temporal composition handles poorly.

## Core primitive: Asset

A Dagster Asset represents a logical data product/object whose value is expected to exist in some storage/external system.

Examples:

```text
raw/orders
clean/orders
customer_features
monthly_revenue
trained_model
published_dataset
```

An Asset definition knows its upstream dependencies. This is the central distinction from step-first orchestration.

The durable semantic object is not "task 17 ran" but:

> **asset X, possibly partition Y, was materialized/observed under definition/version Z with metadata/check results.**

## Materialization

A materialization is the event that computation for an Asset produced/updated its physical value.

Conceptually:

```text
Asset definition
      ↓ execute
external/physical data written
      ↓
AssetMaterialization event + metadata
```

Dagster's materialization record is orchestration metadata/evidence. It is not the authoritative row/object content itself unless the application's storage design explicitly makes it so.

Keep:

```text
Dagster
= knows definitions, dependencies, partition/materialization/check history

warehouse/object store/database
= owns actual data
```

## Asset graph / lineage

Assets form a dependency graph:

```text
raw_orders
   ↓
clean_orders
   ↓
customer_daily
   ↓
monthly_revenue
```

This graph expresses **data-product lineage**, not arbitrary workflow/control-flow semantics.

Use it when upstream data changes determine which downstream products are stale/missing and should be recomputed.

Do not use Asset edges for approvals, customer-support workflows, browser actions or generic Agent control flow.

## Partitions

A partition splits one logical Asset into independently tracked slices, commonly by:

- day/time window;
- customer/tenant;
- region;
- experiment/project;
- dynamic arriving keys.

Example:

```text
asset = daily_orders
partitions = 2026-09-01, 2026-09-02, ...
```

Partitions are valuable because freshness/completeness/recomputation can be reasoned about at the natural data slice rather than as an undifferentiated whole-table task.

Partitioning should follow a meaningful independent recomputation/storage boundary. Do not create partitions solely for UI granularity.

## Backfills

A backfill materializes a selected historical set/range of missing or stale partitions.

Typical reasons:

- initial historical load;
- corrected transformation logic;
- upstream data correction;
- changed model/features;
- missing partitions after failure.

This is a distinct data-platform primitive:

```text
change data logic today
     ↓
identify affected historical partitions
     ↓
recompute them deliberately
```

Dagster supports one-run or many-run backfill strategies depending on asset/IO semantics.

## Asset checks

Asset Checks attach explicit predicates to data products, e.g.:

- schema matches expectation;
- required IDs are non-null;
- row counts/metadata fall within bounds;
- freshness deadline is met;
- domain-specific invariant passes.

Checks can warn or block downstream materialization.

A passing Asset Check means only that the specific declared predicate passed. It does not establish scientific/statistical/business validity of the data product.

Prefer deterministic checks for deterministic data contracts; keep specialized statistical/domain validation with the owning method/domain.

## Automation conditions / schedules / sensors

Dagster can launch asset/check runs through several mechanisms.

### Schedule

Time-driven trigger.

### Sensor

Programmatic evaluation of external/runtime state that emits run requests.

### Declarative Automation / AutomationCondition

Asset-centric rule such as:

```text
materialize if missing
materialize when upstream updated
materialize after cron tick once parents are ready
```

This is stronger than a raw cron when the true requirement is data freshness relative to dependencies.

Do not let Dagster sensors become a universal event bus or business workflow engine.

## Resources

Resources provide runtime dependencies/configuration such as database clients, APIs or service handles.

They let the same asset definition use different implementations/configuration across dev/test/prod.

A Resource is an execution dependency adapter, not data authority by itself.

## I/O Managers

I/O Managers control how asset/op outputs are stored and loaded for downstream computations.

Conceptually:

```text
asset function returns logical value
      ↓
IO Manager
      ↓
S3 / warehouse / local filesystem / other store
```

They reduce storage boilerplate and can vary by environment.

Do not hide critical domain storage semantics behind an opaque IO Manager if callers need explicit transactional/schema/security behavior. Use the abstraction only where the storage contract remains clear and testable.

## Dagster Pipes

Dagster Pipes is an important boundary mechanism: Dagster can orchestrate computation that runs outside the Dagster process/environment, pass context into the external process, and stream structured logs/metadata/events back.

This allows:

```text
Dagster asset orchestration
      ↓
Pipes client
      ↓
external compute
Databricks / Kubernetes / Docker / subprocess / other language
      ↓
structured execution metadata back to Dagster
```

Dagster therefore does not need to own every compute runtime.

For Ordivon, a future Dagster asset could invoke Runtime, Snakemake, dbt, Spark, a cloud job or another domain engine rather than reimplementing them.

## Authority boundary

Dagster naturally owns:

- Asset definitions/catalog identity;
- declared asset dependency graph;
- partition definitions/status;
- Dagster run/materialization/check history;
- backfill/automation state;
- asset-specific orchestration metadata.

Dagster does **not** automatically own:

- underlying warehouse/file/object bytes;
- scientific/business correctness;
- Temporal-style general business workflow truth;
- Runtime physical effect truth;
- n8n SaaS/integration truth;
- source-system records;
- financial/accounting truth.

Keep asset/materialization metadata as a projection/control plane over natural data authorities.

## Boundary with Snakemake

### Snakemake

Best when the problem is a reproducible **file/artifact-oriented scientific/computational DAG**:

```text
input files
  ↓ rules
output files
```

Strengths include scientific workflows, content/file dependencies, HPC execution and project-scoped reproducibility.

### Dagster

Best when the problem is a continuously operated **data-product/asset graph**:

```text
data asset definitions
  ↓ partitions/materializations
lineage/freshness/checks/backfills
```

Use Snakemake for current Research computational pipelines unless real recurring data-asset lifecycle requirements appear. Do not migrate an accepted scientific DAG into Dagster merely for a richer UI/catalog.

## Boundary with n8n

n8n owns API/SaaS/webhook/integration automation.

Dagster owns data-asset lifecycle orchestration.

Example:

```text
SaaS webhook/API glue
    -> n8n

hourly warehouse tables, feature sets, ML datasets
    -> Dagster
```

n8n can trigger Dagster; Dagster can call APIs. Do not merge their state models.

## Boundary with Temporal

Temporal owns general durable application/workflow state across long waits, messages, retries and arbitrary business processes.

Dagster owns data-asset graph/materialization/partition/backfill semantics.

A useful distinction:

```text
"Has this customer approval process reached stage 4?"
    -> Temporal

"Which daily partitions of customer_features are stale/missing?"
    -> Dagster
```

Do not encode a durable business state machine as fake data assets.

## Boundary with data storage / dbt / compute engines

Dagster should orchestrate mature data engines rather than absorb them.

Typical composition:

```text
Dagster
├─ dbt models
├─ SQL warehouse jobs
├─ Spark/Databricks
├─ Python analytics
├─ ML training
└─ external jobs through Pipes
```

Dagster is the asset control/observation plane; compute/storage remain provider-native.

## Adoption threshold

Use Dagster when several of these become recurrent:

- data products live continuously rather than as one-off research outputs;
- dozens/hundreds of assets need persistent lineage/catalog visibility;
- date/tenant/project partitions must be tracked independently;
- historical backfills are routine;
- freshness/missing/upstream-changed semantics should trigger recomputation;
- asset-specific quality checks should gate downstream updates;
- data teams need operational materialization history and ownership metadata;
- compute spans multiple tools while one data-asset control plane is useful.

Stay with Snakemake/SQL/Python/n8n/Temporal when these conditions are absent.

## Operational boundary

Dagster OSS requires an orchestration control plane (webserver, daemon/scheduler/sensor processes, instance storage, code locations/executors depending on deployment). Larger deployments may add Kubernetes/Cloud infrastructure.

This is real operational cost. Do not introduce it for a handful of periodic scripts.

## Prototype recipe

A minimal Dagster-like architectural prototype needs only:

1. define `Asset{key, deps, partitions, compute_fn}`;
2. persist materialization events by `asset_key + partition_key`;
3. compute which asset partitions are missing/stale relative to upstream materializations;
4. topologically schedule the required recomputations;
5. support one time-partitioned asset;
6. launch a historical backfill range;
7. attach one deterministic Asset Check;
8. trigger one recomputation when upstream materializes;
9. keep actual asset data in an external file/database/store;
10. display/query lineage + partition/materialization state.

This reproduces the architectural kernel without reimplementing Dagster's production engine/catalog/UI/integration ecosystem.

## Prototype readiness gate

**PASS.** Asset, materialization, partition/backfill, check, automation and external storage/compute boundaries are explicit enough to implement a minimal asset orchestrator or adopt Dagster directly when the workload warrants it.
