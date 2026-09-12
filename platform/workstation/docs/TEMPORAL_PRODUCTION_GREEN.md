# Temporal production green cluster

Operations owns the production self-hosted Temporal service lifecycle and PostgreSQL persistence. Workstation owns only the exact upstream binary materialization.

## Green-cluster rule

The existing Agent Automation dogfood cluster on `127.0.0.1:7233` is not modified by this rollout. Production acceptance is first performed on `127.0.0.1:17233` with separate PostgreSQL persistence. Existing Workflow histories are never fabricated or bulk-imported into the green cluster.

## Persistence

- server: Temporal 1.31.2;
- SQL plugin: `postgres12`;
- core DB: `temporal`, schema 1.19;
- visibility DB: `temporal_visibility`, schema 1.14;
- PostgreSQL substrate: Operations-managed local PostgreSQL/pgBackRest;
- schema authority: the exact Temporal 1.31.2 `temporal-sql-tool` plus exact upstream schema directory.

## Ports

All endpoints are loopback-only during green acceptance:

- frontend gRPC `17233`;
- frontend HTTP `17243`;
- history `17234`;
- matching `17235`;
- internal worker `17239`;
- metrics `29092`;
- pprof `17936`.

No public ingress, TLS termination, or multi-node membership is claimed by this slice.

## Cutover gate

Do not point Agent Birth, Artifact, or Host migration workflows at the green cluster until all of the following are independently true: schema versions exact, service stable, cluster health passes, namespace exists, real Workflow execution passes, PostgreSQL backup/recovery is proven, and the old cluster's active workflows have an explicit drain/bootstrap disposition.
