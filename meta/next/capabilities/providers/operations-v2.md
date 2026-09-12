# Provider: Operations v2

- Source: `/root/projects/ordivon-operations-v2`
- Observed revision: `047ca7f2a943`
- Role: task-local execution/integration substrate provider
- Migration mode: metadata only; implementation stays external

## Capabilities

- durable workflow via Temporal;
- integration-edge automation via n8n;
- host desired-state/configuration via Ansible/Nix/DSC-facing composition;
- external/cloud desired-state via OpenTofu where applicable;
- telemetry composition via OpenTelemetry/Prometheus/Vector/Loki/Grafana;
- generic PostgreSQL/backup operational substrate;
- service lifecycle via mature OS/container facilities.

## Boundary

Operations provides mechanics and observable substrate facts. It does not establish Research, Finance, Network, Artifact, Security or other domain semantic success.

## Activation

Load into an active working set only when the current task needs durable orchestration, integration edge automation, host/infrastructure realization, or shared observability.
