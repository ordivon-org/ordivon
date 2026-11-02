# Dagster Asset-Centric Orchestration Kernel

Status: **REGISTERED / PROTOTYPE-READY**
Registered: 2026-09-14

## One-sentence model

**Dagster replaces step-first thinking with asset-first thinking: define the data products that should exist, their dependency/partition structure and quality/freshness conditions, then let orchestration decide which materializations/backfills are required to bring the asset graph into the desired state.**

## Mechanism 1: model the durable thing, not just the computation

Traditional workflow language often starts with:

```text
run step A
then B
then C
```

Asset-centric orchestration starts with:

```text
Asset C depends on B
Asset B depends on A
```

Then asks:

> Which assets/partitions are missing, stale or invalid, and what computation will restore them?

This is valuable when the outputs outlive individual runs and are continuously maintained data products.

## Mechanism 2: materialization history is asset state evidence

A materialization record says that Dagster observed/produced an asset update at a particular time/run/partition with metadata.

It enables questions like:

- when was this partition last produced;
- which code/run produced it;
- what upstream lineage existed;
- which checks passed/failed;
- which downstream assets became stale.

But the materialization event is not the physical dataset itself.

General rule:

`control-plane state about data != data-plane content`.

## Mechanism 3: partitions encode natural recomputation units

A partition should correspond to a slice that can be independently reasoned about and, ideally, recomputed.

Useful examples:

- date/time period;
- tenant/customer;
- experiment/project;
- region;
- arriving object identity.

Partitions make status/freshness/backfill queries precise.

Avoid hyper-partitioning simply for bookkeeping: partition count/cardinality has operational/UI/storage consequences.

## Mechanism 4: backfill is first-class historical correction

Data logic evolves. Historical products may need recomputation.

The durable pattern is:

```text
new transformation/model logic
       ↓
select affected historical partitions
       ↓
backfill
       ↓
track success/failure by partition
```

This is distinct from generic workflow retry: retry repeats a failed operation; backfill intentionally recomputes historical slices because desired data state changed or was absent.

## Mechanism 5: freshness is relative to dependency state, not only clock time

A cron alone says:

> run at 02:00.

Asset automation can say:

> materialize when parents are updated and this asset is missing/stale.

This is a more natural expression when the goal is maintaining derived data products rather than firing arbitrary jobs.

## Mechanism 6: checks belong with assets but do not own domain truth

Asset checks are useful for local contracts:

```text
schema
nullability
row-count bounds
freshness
basic invariants
```

They can prevent bad data from propagating downstream.

But one green data-quality check cannot establish scientific validity, model fairness, business correctness or regulatory compliance. Those remain domain-specific V&V predicates.

## Mechanism 7: storage is replaceable behind the asset identity

Dagster's IOManager/resource patterns separate logical assets from where/how bytes/tables are materialized.

This supports dev/test/prod substitution.

The lesson to retain is:

**logical data-product identity and physical storage implementation are separable when the storage contract permits it.**

Do not abstract away storage semantics that materially affect correctness (transactions, constraints, access control, schema evolution).

## Mechanism 8: external compute should remain external

Dagster Pipes is especially important because it avoids the "orchestrator must execute everything" trap.

The orchestrator can provide context, start/observe external compute and collect structured metadata while Spark/Databricks/Kubernetes/subprocess/other languages do the work.

This supports Ordivon's general composition principle:

`control plane coordinates; mature provider owns execution mechanics`.

## Mechanism 9: Asset graph is not a universal graph ontology

Dagster's graph means data lineage/dependency.

Do not use asset nodes to represent:

- human approvals;
- Agent conversations;
- legal obligations;
- generic tasks;
- business process states;
- arbitrary tool calls.

Use Temporal/Plane/n8n/Codex/domain systems for their own natural semantics.

## Mechanism 10: data orchestration and scientific workflow are adjacent, not identical

Snakemake is excellent when outputs are project-scoped files/artifacts and the desired property is reproducible computational build order.

Dagster becomes stronger when outputs are continuously operated data products requiring persistent catalog/lineage/partition/backfill/freshness behavior.

Selection rule:

```text
project/research computational DAG
    -> Snakemake first

continuously maintained data-product graph
    -> Dagster candidate
```

Do not migrate merely for UI polish.

## Mechanism 11: data orchestration and durable workflow are different authorities

Temporal asks:

> Where is this durable process and what event/state transition comes next?

Dagster asks:

> Which asset partitions are in the desired materialized state?

A data pipeline can sometimes be implemented in either system, but the natural semantic center should choose the tool.

Use Temporal for long-lived business/process state; use Dagster for asset/partition state.

## Mechanism 12: data orchestration and integration automation are different

n8n excels at:

```text
webhook -> SaaS API -> transform -> notification
```

Dagster excels at:

```text
source dataset -> cleaned dataset -> feature set -> report/model
```

They can trigger each other without sharing an ontology.

## Mechanism 13: lineage/catalog is useful because assets are durable names

When many data tools are involved, the asset key becomes a stable logical name around which Dagster can assemble:

- owners;
- dependencies;
- materializations;
- checks;
- partitions;
- metadata;
- code location.

This is more valuable as the number of long-lived data products and teams grows.

For a few one-off datasets, Git/README/Research manifests may remain simpler.

## Mechanism 14: declarative automation is desired-state reconciliation

Automation conditions such as `missing`, `newly_updated`, code-version changes and cron-related rules express predicates over current asset/partition state.

The orchestrator periodically evaluates them and requests materialization when desired state is not satisfied.

This resembles reconciliation controllers more than fixed imperative schedules.

Use only for properties Dagster can actually observe reliably.

## Current Ordivon assessment

Current local reality:

- Dagster is not installed;
- no Dagster project is present;
- Research already has accepted Snakemake-based scientific workflows;
- n8n handles integration edges;
- Temporal is the selected general durable-workflow provider;
- Data & Analytics currently has no proven recurring enterprise-scale data-asset network.

Therefore Dagster exposes a genuinely distinct mature primitive, but **no current workload proves the operational cost is justified**.

## Adoption triggers for Ordivon

Re-evaluate/install Dagster when a real project has several of:

- many persistent datasets/tables/models/reports treated as named data products;
- recurring materializations over months/years;
- time/tenant/project partitions;
- routine historical recomputation/backfills;
- cross-tool lineage needs;
- freshness/missing/upstream-updated automation;
- shared data-quality checks blocking downstream products;
- multi-user operational catalog ownership.

Until then use simpler existing providers.

## What Ordivon should retain

1. Treat long-lived data products as Assets when asset lifecycle is the real problem.
2. Separate Asset identity/materialization metadata from physical data authority.
3. Partition by meaningful independent recomputation units.
4. Treat backfill as historical desired-state correction, distinct from retry.
5. Express data freshness relative to upstream state where useful.
6. Keep asset checks narrow and deterministic when possible.
7. Separate logical asset identity from replaceable storage/compute providers.
8. Keep external compute outside the orchestrator through thin protocols such as Pipes.
9. Use Dagster only for data-asset semantics, not universal task/workflow state.
10. Prefer Snakemake for current scientific DAGs unless persistent asset lifecycle requirements emerge.

## What Ordivon should not copy

- custom data-asset catalog;
- private materialization-event database;
- custom partition/backfill engine;
- asset lineage UI;
- private IOManager/resource framework;
- another scheduler/sensor daemon;
- Dagster's asset ontology as a global Ordivon ontology;
- duplicated generic retry/workflow semantics already owned by Temporal;
- Dagster installation without a real persistent data-asset workload.

## Minimal prototype

```text
Asset definitions + deps
        ↓
Partition registry
        ↓
Materialization event store
        ↓
reconcile missing/stale partitions
        ↓
topological execution
        ↓
external storage/compute
        ↓
materialization + check metadata
```

Test with:

```text
raw_daily[date]
   ↓
clean_daily[date]
   ↓
monthly_summary[month]
```

Materialize several days, change clean logic, backfill a historical date range, fail one Asset Check, then verify only affected/downstream partitions are treated as needing attention.

## Project-study acceptance

### One-sentence test

PASS: Dagster is an asset-centric data orchestrator that maintains lineage/materialization/partition/backfill/check state around durable data products rather than treating workflow steps as the primary semantic objects.

### Prototype test

PASS: Asset+dependency definitions, partition/materialization state, stale/missing reconciliation, backfill and checks are sufficient to reproduce the architectural kernel.

## Verdict

**PASS — DISTINCT DATA-ASSET ORCHESTRATION PRIMITIVE, BUT KEEP DAGSTER ON-DEMAND. USE SNAKEMAKE FOR CURRENT SCIENTIFIC DAGS; ADOPT DAGSTER WHEN PERSISTENT DATA-ASSET LIFECYCLE BECOMES A REAL WORKLOAD.**
