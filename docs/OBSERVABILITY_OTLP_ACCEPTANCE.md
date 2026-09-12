# Operations observability / OTLP acceptance

Date: 2026-09-12

## Standing

**OTLP LOGS + METRICS ACCEPTED. TRACE STORAGE DEFERRED.**

The Operations observability slice now uses mature external components without an additional OpenTelemetry Collector daemon:

- OTLP ingress: Vector 0.57.0 on loopback `4317` (gRPC) and `4318` (HTTP);
- logs: Vector native OTLP log decoding -> Loki 3.6.6;
- metrics: preserved OTLP metric envelope -> Vector OpenTelemetry HTTP sink -> Prometheus 3.14.0 native OTLP receiver;
- host/system metrics: existing node_exporter scrape path remains unchanged;
- traces: explicitly consumed by a deferred blackhole and **not** represented as persisted/observable traces because no trace backend has been admitted.

No `otelcol`, `otelcol-contrib`, Grafana Alloy, Tempo, or custom telemetry gateway is introduced by this acceptance.

## Log reliability repair

The pre-existing `journald -> Vector -> Loki` standing was false-green: `vector.service` had reached `start-limit-hit` because packaged `ExecStartPre=/usr/bin/vector validate` performed a live Loki sink healthcheck while Loki was still inside its readiness window.

Operations now installs a systemd drop-in that:

- statically validates config with `vector validate --no-environment`;
- runs Vector with `--require-healthy false`;
- orders Vector after/wants Loki without turning Loki readiness into a process-admission dependency;
- retains the disk buffer with `when_full: block`.

A real journald marker was observed through Vector in Loki after the repair.

## Backlog / outage proof

Fault injection stopped Loki while Vector remained active, emitted a unique journald marker, then restored Loki. The marker was later read from Loki while the Vector PID remained unchanged.

Accepted outage window evidence:

- buffered marker: `ordivon-buffer-zero-drop-1789189921549646118`;
- Vector drop/400/429 count: `0`;
- Loki ingestion-rate / too-far-behind / 400 / 429 rejection count: `0`.

The earlier failure mode was reproduced before repair: Loki's prior default 4 MB/s ingestion limit caused 429 responses, and an older buffered batch was rejected as `entry too far behind`, producing a real Vector drop count of 726 events.

The accepted Loki limits therefore use:

- global ingestion rate: 10 MB/s;
- burst: 20 MB;
- unordered writes enabled;
- old-sample rejection remains enabled with a 168h absolute bound;
- stream time sharding enabled, with recent logs excluded from time sharding for 40m.

This preserves validation while allowing bounded durable backlog replay; it does not simply disable age checks.

## OTLP HTTP proof

Vector HTTP ingress requires protobuf OTLP on this installed build. `application/json` was intentionally rejected by the live source as an invalid content type, so acceptance used standard `application/x-protobuf` requests.

A real OTLP log Export request returned HTTP 200 and was read from Loki with the decoded fields intact, including:

- `message = ordivon-otel-log-1789190282181459844`;
- resource `service.name = ordivon-operations-otel-smoke`;
- scope `ordivon.operations.otel.smoke`;
- marker attribute, severity, and observed timestamp.

A real OTLP metric was received through the same Vector ingress and forwarded as preserved OTLP to Prometheus' native receiver at `/api/v1/otlp/v1/metrics`.

Prometheus stored and returned:

- metric: `ordivon_otel_live_gauge_ratio`;
- value: `42.5`;
- `job = ordivon-operations-otel-smoke`;
- `standing = acceptance`.

The `_ratio` suffix is Prometheus' OTLP translation for the submitted unit `1`; Operations does not hand-write this translation.

## OTLP gRPC proof

A real OpenTelemetry `LogsService.Export` RPC was sent to `127.0.0.1:4317` and returned successfully. Loki subsequently returned the unique marker:

`ordivon-otel-grpc-1789190576252996025`

The acceptance window reported `vectorErrors=0` and `lokiRejects=0`.

## Trace boundary

Vector's OpenTelemetry source necessarily exposes a trace signal alongside logs and metrics. This deployment does **not** claim trace observability: `otel.traces` is routed to an explicitly named deferred blackhole until a real owner/use-case justifies a trace backend such as Tempo. Clients must not treat the shared Operations OTLP endpoint as an accepted trace-storage endpoint.

The correct future change is to bind a mature trace backend when trace queries materially affect an E2E decision; it is not to create an Ordivon trace database or gateway now.
