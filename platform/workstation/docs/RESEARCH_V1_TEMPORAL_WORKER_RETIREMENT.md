# Research v1 Temporal worker retirement

Date: 2026-09-14

Status: **RETIRED / NO CURRENT CONSUMER / TEMPORAL SUBSTRATE RETAINED**

## Scope

This decision retires only the legacy systemd worker `ordivon-research-temporal-worker.service` and its automatic polling of the `ordivon-research-campaign` task queue. It does **not** retire Temporal itself, Research v2, Runtime, Snakemake, or the immutable historical release bytes under `/opt/ordivon/research-temporal/`.

## Evidence before retirement

A current consumer census found zero references to the worker service, task queue, launcher, or `/opt/ordivon/research-temporal` release path in current `ordivon-research-v2`, Runtime, Harness, Host v2, Operations, Next, Market Capital Next, Artifact, Media, or Game executable/source paths. Research v2 already declares itself the forward Research authority.

A read-only Temporal API query against namespace `default` and task queue `ordivon-research-campaign` found exactly two historical workflows and **zero open workflows**:

- `paper1-r4-snakemake-campaign-20260912` — `TERMINATED`;
- `paper1-r4-snakemake-campaign-20260912-r2` — `FAILED`.

The systemd journal showed the worker's last consequential activity on 2026-09-12; subsequent starts were ordinary service/boot restarts with no newly admitted workflow. The currently installed worker release is an orphaned materialization that no current source owner claims as a forward implementation.

## Retirement action

The service is stopped and disabled, its `/etc/systemd/system/ordivon-research-temporal-worker.service` unit is removed, and systemd is reloaded. Historical release bytes remain intact for provenance/reproduction.

## Current ownership rule

- Temporal service/runtime → mature Temporal substrate maintained operationally by Operations.
- Research workflow semantics and new Research workloads → `/root/projects/ordivon-research-v2`.
- Physical command execution/evidence → Ordivon Runtime.
- Historical Research v1 Temporal campaign implementation/release bytes → provenance only.

A future Research workload may use Temporal again if a real long-lived workflow needs it, but that use must be admitted from the current Research/Operations composition rather than by re-enabling this retired worker.
