# Operations E2E v2 — R2 Acceptance

Date: 2026-09-11

## Standing

**SUPPORTED FOR SHARED LOG TRANSPORT SLICE** — journald -> Vector -> Loki.

This standing proves generic local log transport and queryability only. It does not confer owner semantic truth on log contents.

## Implemented

```text
systemd-journald
      |
      v
Vector 0.57.0
      |
      v
Loki 3.6.6
```

Operational bindings:

- Loki HTTP: `127.0.0.1:3100`
- Loki gRPC: `127.0.0.1:9096`
- Vector reads the current boot's new journald events and uses its native Loki sink.
- Loki stores local single-node TSDB/filesystem data under `/var/lib/loki`.
- both services are systemd-owned and enabled.
- no public listener or Grafana UI was introduced.

## Failure discovered and repaired

The first apply exposed an orchestration defect rather than a Vector/Loki defect. Loki became ready, then a deferred Ansible restart handler restarted it after Vector had begun startup. Vector's native sink health check observed Loki's temporary `503 Service Unavailable`, failed closed, and systemd eventually reached `start-limit-hit`.

The repair flushes Loki configuration/restart handlers before downstream startup and explicitly waits for Loki `/ready == 200` before Vector may start. No health check was disabled.

## End-to-end proof

A new journal event with canary:

```text
ORDIVON_OPS_V2_R2_CANARY_1789111840
```

was emitted after the pipeline was live. Loki's query API returned the canary in a stream carrying:

```text
ordivon_owner="operations-v2"
source="journald"
```

This proves the tested path:

```text
new journald event -> Vector native journald source -> Vector native Loki sink -> Loki ingest -> Loki query API
```

## Idempotence

A subsequent Ansible apply returned:

```text
ok=8 changed=0 failed=0
```

Vector live validation also passed source/component configuration and Loki sink health check.

## Boundaries

- logs are evidence/facts, not automatic root-cause proof;
- Operations v2 does not infer owner semantic success from a log event;
- Network v2 Prometheus and existing Gatus ownership remain separate;
- Grafana stays inactive until its auth/binding/provisioning contract is explicit.
