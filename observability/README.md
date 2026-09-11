# Observability composition

R1 deliberately contains no Ordivon collector implementation.

Selected composition:

```text
node_exporter -> Prometheus
journald -> Vector -> Loki
OTel SDK/Collector -> standard telemetry path when introduced
Gatus -> black-box endpoint contracts
Grafana -> visualization
```

Rules:

1. every collector is an upstream component;
2. monitoring configuration is version-controlled desired state;
3. labels/attributes identify Ordivon owner/e2e/job/attempt only when the source can support that identity truthfully;
4. an availability probe must state exactly what path it proves;
5. no black-box probe is promoted into an owner semantic-success verdict;
6. alerting should be actionable and SLO-oriented rather than one alert per low-level check.
