# Experimental Observation exporter retirement

Date: 2026-09-14

## Decision

The optional `scripts/observation_export.py` and its isolated test were deleted. They were the only Runtime code references to `ordivon-observation-core`; no systemd unit, installed command, product API, deployment path, or other Runtime component consumed the exporter.

The exporter targeted a custom cross-owner Observation Plane. That abstraction is not retained as a current Ordivon owner. Runtime continues to own exact Workspace/Job/Attempt/event/artifact facts through Runtime-native APIs and its Registry. Generic telemetry, metrics, logs, black-box probes, and dashboards are composed through the mature Operations observability stack (OpenTelemetry, Prometheus, Vector/Loki, Gatus, Grafana as applicable).

## Consequence

Runtime no longer has a source dependency on `ordivon-observation-core` or `/root/projects/ordivon-computing` for Observation export. Historical research/evidence about the experiment remains in Git and in the archived Computing corpus.

Reintroduce a cross-owner export contract only after a concrete consumer demonstrates a requirement that owner-native APIs plus mature observability/provenance substrates cannot satisfy.
