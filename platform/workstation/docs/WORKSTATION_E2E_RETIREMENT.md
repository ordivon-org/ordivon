# Workstation E2E retirement

Date: 2026-09-12

## Decision

There is no longer an independent Workstation implementation authority. Generic machine mechanisms are owned by mature upstream systems and their natural Ordivon owner. “Workstation readiness” is a projection of owner evidence for the concrete operation being attempted, not a daemon, global doctor, package registry, or configuration controller.

## Current owner map

- Windows desired state: WinGet Configuration + DSC v3; source under `workstation/windows/`.
- Linux user/tool desired state: Nix + Home Manager; source under `workstation/nix/`.
- Generic host desired state and service realization: Ansible + systemd under Operations.
- Generic host inventory: osquery; query contract under `inventory/queries/`.
- Generic workstation configuration consequences: `tests/test_workstation_consequences.py`.
- Telemetry: Netdata/Prometheus and Operations observability.
- Execution truth: Ordivon Runtime.
- Durable workflow: Temporal.
- Integration edge: n8n.
- Network semantics: Network E2E.
- Security policy/verification: Security E2E and OPA/Trivy/etc.
- Domain workload acceptance: the owning Research/Game/Artifact/Media/etc. E2E.

## Readiness model

A concrete E2E asks its actual owners for the evidence required by that operation. No central Workstation service aggregates unrelated observations into a universal green/red state. Generic host facts may be queried through osquery; stronger claims require the owner-specific real workload/consequence oracle.

## Retired repository

`/root/projects/ordivon-workstation-v2` is retained only as Git history and a retirement pointer. It has no runtime authority, desired-state source, executable scripts, tests, inventory queries, or project toolchain requirement after the retirement cut.

This retirement does not by itself retire `/root/workstation-lab`; that legacy repository still contains residual owner-transfer obligations (notably current Network realization and narrow Windows/Finance boundaries) and remains a compatibility oracle until those owners close them.
