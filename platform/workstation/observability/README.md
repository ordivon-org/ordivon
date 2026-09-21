# Observability composition

Operations v2 deliberately contains no Ordivon collector implementation.

Selected composition:

```text
node_exporter -> Prometheus
journald -> Vector -> Loki
OTel SDK/Collector -> standard telemetry path when introduced
Gatus -> black-box endpoint contracts
Grafana -> visualization when explicitly admitted
```

Current live shared slices:

- metrics: node_exporter `127.0.0.1:29100` -> Prometheus `127.0.0.1:29091`;
- logs: journald -> Vector -> Loki HTTP `127.0.0.1:3100` / gRPC `127.0.0.1:9096`.
- traces: OTLP `127.0.0.1:4317/4318` -> Vector -> Tempo OTLP/HTTP `127.0.0.1:14318` -> query API `127.0.0.1:3200`; desired state does not itself prove live trace acceptance.
- black-box SLO: Gatus `127.0.0.1:8080`, with desired state now owned under `observability/gatus/`; direct A/B endpoint probes bind the existing loopback CONNECT carriers without becoming Network or domain truth.

Rules:

1. every collector is an upstream component;
2. monitoring configuration is version-controlled desired state;
3. labels/attributes identify Ordivon owner/e2e/job/attempt only when the source can support that identity truthfully;
4. an availability probe must state exactly what path it proves;
5. no black-box probe, metric or log line is promoted into an owner semantic-success or root-cause verdict;
6. alerting should be actionable and SLO-oriented rather than one alert per low-level check;
7. downstream components with readiness windows must converge before dependent native health checks are admitted; health checks are not disabled to hide ordering bugs.
