# Temporal production green — acceptance

Date: 2026-09-12

## Standing

**PRODUCTION-GREEN SUBSTRATE ACCEPTED; CUTOVER NOT YET GRANTED.**

The green cluster proves the production self-hosted Temporal substrate on Operations-managed PostgreSQL without modifying the existing Agent Automation dogfood cluster on `127.0.0.1:7233`.

## Exact substrate

- Temporal Server: `1.31.2`;
- Temporal CLI: `1.8.3`;
- PostgreSQL plugin: `postgres12`;
- persistence database: `temporal`;
- visibility database: `temporal_visibility`;
- core schema: `1.19`;
- visibility schema: `1.14`;
- frontend gRPC: `127.0.0.1:17233`;
- Prometheus metrics: `127.0.0.1:29092`;
- systemd service: `temporal.service`.

## False-green repaired

The first green deployment failed because `/etc/temporal` was `root:root 0750`, while `temporal.service` runs as the unprivileged `temporal` user. The process could not traverse the directory to read `production.yaml`; systemd therefore accumulated restart attempts while the health probe remained unavailable.

The accepted permissions are:

- `/etc/temporal`: `root:temporal 0750`;
- `production.yaml`: `root:temporal 0640`;
- secret env: root-only `0600` and consumed by systemd;
- service state after convergence: `active/running`, `NRestarts=0` at acceptance observation.

This incident is retained as evidence that systemd admission alone is not a Temporal health gate.

## Workflow proof

A real Temporal Python SDK 1.32.0 worker was connected to the green cluster and executed workflow type `ordivon.operations.green-smoke`.

Accepted workflow:

- Workflow ID: `operations-green-smoke-9fcd4b92-c773-4c3a-9912-ce7713e73c4b`;
- Run ID: `01a093e7-0953-7df1-9ad5-9306f57d93e9`;
- result standing: `PASS`;
- Temporal status: `COMPLETED`;
- Event History: start, task scheduled, task started, task completed, execution completed;
- Visibility query returned the same Workflow as `Completed`.

The live PostgreSQL persistence and visibility stores both contained persisted execution rows after completion.

## Backup + restore proof

A new pgBackRest incremental backup was taken after the accepted Workflow:

- label: `20260912-041045F_20260912-123707I`;
- type: incremental;
- error: false.

That exact backup set was restored to a separate temporary PostgreSQL data directory and started on isolated port `55435`. The restored instance independently verified:

- `temporal.schema_version = 1.19`;
- `temporal_visibility.schema_version = 1.14`;
- the accepted Workflow ID is present in `executions_visibility`;
- restored workflow status value is `2` (`Completed` in the accepted Temporal visibility state);
- restore standing: `PASS`.

The restored PostgreSQL instance was then stopped and its temporary data/socket directories removed. Live PostgreSQL and live Temporal remained running throughout the restore test.

## Cutover remains separate

This acceptance does **not** authorize deleting or rewriting Event History from the existing `7233` dev cluster. Before application cutover:

1. inventory running/open workflows on `7233`;
2. classify each as drain, finish-in-place, cancel-with-owner-authority, or explicit bootstrap into a new Workflow;
3. repoint only new workflow admissions to the production cluster;
4. keep old cluster read-only/draining until no active owner workload depends on it;
5. archive the old `temporal.db` read-only before retirement.
