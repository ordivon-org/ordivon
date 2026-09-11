# Operations E2E v2 — R1 Acceptance

Date: 2026-09-11

## Standing

**SUPPORTED FOR FIRST VERTICAL SLICE** — shared generic node metrics only.

This standing does not claim that the complete Operations E2E migration is finished.

## Implemented

- greenfield repository created without importing legacy Operations implementation code;
- external-first responsibility map established;
- Ansible installed and adopted as host desired-state mechanism;
- OpenTofu, Vector, Loki, Grafana, osquery and OPA installed but kept unbound/inactive where configuration is not yet explicit;
- node_exporter and a dedicated stock Prometheus instance configured through Ansible;
- all Operations v2 metric listeners are loopback-only;
- Network v2 Prometheus and Gatus remained active and separate.

## Live verification

Observed after apply:

```text
prometheus.service                 active enabled  127.0.0.1:29091
prometheus-node-exporter.service   active enabled  127.0.0.1:29100
network-v2-prometheus.service      active enabled  127.0.0.1:29090
ordivon-gatus.service              active enabled  127.0.0.1:8080
```

Operations Prometheus target API returned:

```text
operations-v2-node        http://127.0.0.1:29100/metrics   up
operations-v2-prometheus  http://127.0.0.1:29091/metrics   up
```

Instant query `up` returned value `1` for both Operations v2 targets.

## Runtime evidence lesson

Package installation produced `EXECUTABLE_RUNTIME_DRIFT` because the package manager changed executable-path topology while the Runtime Attempt was active. Package-manager output indicated completed external effects, so the operation was **not retried blindly**. Physical package state and versions were re-read before proceeding. This preserves the distinction between Runtime execution certainty and external-effect semantics.

## Not yet accepted

- log pipeline cutover;
- Grafana production UI;
- OTel collector path;
- alert routing/SLO burn alerts;
- osquery inventory replacement;
- OPA policy authority;
- OpenTofu production infrastructure authority;
- deletion of legacy Doctor/incident/backup wrappers.
