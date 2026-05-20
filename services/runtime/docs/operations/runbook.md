# Ordivon Infrastructure Runbook

**Who this is for:** Anyone who needs to debug, restart, or recover Ordivon's
infrastructure services. Written for 3am incidents — every command should be
copy-pasteable.

**Last updated:** 2026-05-17
**Authority:** supporting evidence only; canonical architecture and plan
direction are defined by the post-reset source documents in `docs/ai/`,
`docs/architecture/`, `docs/product/`, and `docs/audits/certification/`.
**Services:** PostgreSQL, NATS JetStream, Temporal, OpenFGA, MinIO/S3, OPA (CLI)

---

## Quick Reference

```bash
# Is everything running?
python3 scripts/health_check.py

# Which containers are up?
docker ps --format '{{.Names}}  {{.Status}}'

# Restart everything
docker restart ordivon-pg ordivon-nats ordivon-temporal ordivon-temporal-db ordivon-openfga ordivon-minio

# View logs for a service
docker logs --tail 50 ordivon-<name>

# Full infrastructure restart (if containers were deleted)
docker compose -f docker-compose.infrastructure-mirror.yml up -d
docker run -d --name ordivon-openfga -p 8081:8080 \
  -e OPENFGA_DATASTORE_ENGINE=memory -e OPENFGA_AUTHN_METHOD=none \
  docker.m.daocloud.io/openfga/openfga:v1.5 run
```

---

## Service: PostgreSQL (`ordivon-pg`)

**Purpose:** Primary database — document registry, debts, evidence records, all governance data.

**Port:** 5432
**Image:** `docker.m.daocloud.io/pgvector/pgvector:pg16`
**Credentials:** `ordivon` / `ordivon`

### Health Check

```bash
docker exec ordivon-pg pg_isready -U ordivon
# Expected: /var/run/postgresql:5432 - accepting connections
```

### Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `connection refused` | Container stopped | `docker start ordivon-pg` |
| `FATAL: database does not exist` | Data volume lost | Re-run migration: `python3 scripts/migrate_governance_to_pg.py` |
| Queries slow | Table bloat or missing indexes | `docker exec ordivon-pg psql -U ordivon -c "SELECT tablename, n_live_tup FROM pg_stat_user_tables;"` |
| App can't connect but pg_isready OK | Wrong `ORDIVON_DB_URL` in `.env` | Check `.env` has `ORDIVON_DB_URL=postgresql://ordivon:ordivon@localhost:5432/ordivon` |

### Backup & Restore

```bash
# Manual backup (also runs daily at 09:00 via cron)
python3 scripts/backup_db.py --s3

# List backups in S3
python3 scripts/backup_db.py --list

# Restore from S3 backup
python3 scripts/backup_db.py --restore backups/ordivon_backup_YYYYMMDD_HHMMSS.sql.gz
# Then: gunzip <file> | docker exec -i ordivon-pg psql -U ordivon
```

### Fallback

When PG is down, the app auto-falls back to SQLite (`data/ordivon.sqlite`).
All reads work. Writes go to SQLite and may need re-sync to PG later.

---

## Service: NATS JetStream (`ordivon-nats`)

**Purpose:** Event streaming — governance events (object.registered, evidence.attached,
debt.opened, etc.) are published and consumed through JetStream.

**Ports:** 4222 (client), 8222 (HTTP monitoring)
**Image:** `docker.m.daocloud.io/library/nats:2.10-alpine`

### Health Check

```bash
curl -s http://localhost:8222/healthz
# Expected: {"status":"ok"}

# Stream info
curl -s http://localhost:8222/streamz | python3 -m json.tool | head -20
```

### Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `connection refused` | Container stopped | `docker start ordivon-nats` |
| Events published but not consumed | Consumer group stuck | Check stream: `curl -s http://localhost:8222/streamz` |
| Stream full | 100K message limit reached | Increase `max_msgs` in stream config or purge old messages |

### Fallback

When NATS is down, events dispatch in-process via `events.py`.
Events are NOT persisted — they fire once and are lost if no handler is registered.

---

## Service: Temporal (`ordivon-temporal` + `ordivon-temporal-db`)

**Purpose:** Durable workflow execution — reconciliation pipelines, AOS submission flows.

**Ports:** 7233 (gRPC), 5433 (temporal-db Postgres)
**Image:** `docker.m.daocloud.io/temporalio/auto-setup:1.27`

### Health Check

```bash
# TCP check (Temporal uses gRPC, not HTTP)
python3 -c "import socket; s=socket.create_connection(('localhost',7233),timeout=3); s.close(); print('OK')"

# Or via Python client
python3 -c "
import asyncio
from temporalio.client import Client
asyncio.run(Client.connect('localhost:7233'))
print('connected')
"
```

### Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `connection refused` | Container restarting | `docker logs ordivon-temporal --tail 20` |
| `config/dynamicconfig/development.yaml: no such file` | Missing config file | Set `SKIP_DYNAMIC_CONFIG=true` env var on container |
| temporal-db unhealthy | Postgres not ready | `docker restart ordivon-temporal-db`, wait 10s, restart temporal |

### Note

Temporal UI (`temporalio/ui:2.34`) could not be pulled (DaoCloud mirror 403).
Server runs without UI. Use Python client or `tctl` CLI for management.

### Fallback

When Temporal is down, workflows execute locally via
`_run_reconciliation_locally()`. No durability, no retry — but the same
logic runs.

---

## Service: OpenFGA (`ordivon-openfga`)

**Purpose:** Relationship-based authorization — "Can user X do Y on object Z?"

**Ports:** 8081 (API), 3000 (Playground UI)
**Image:** `docker.m.daocloud.io/openfga/openfga:v1.5`
**Store ID:** `01KRH456APTF4GAQ4KYHHVMYBX`

### Health Check

```bash
curl -s http://localhost:8081/healthz
# Expected: {"status":"SERVING"}
```

### Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `connection refused` | Container stopped | `docker start ordivon-openfga` |
| `code: latest_authorization_model_not_found` | No model uploaded | Upload model via API or OpenFGA Playground (port 3000) |
| Check always returns `allowed: false` | No model OR no matching tuples | Verify model exists and tuples are written |

### Fallback

When OpenFGA is down, all authorization checks return `False` (DENY).
This is fail-safe: nobody gets unauthorized access, but authorized users
are also blocked until OpenFGA is back.

---

## Service: MinIO / S3 (`ordivon-minio`)

**Purpose:** Evidence object storage — blobs, backups, screenshots, command outputs.

**Ports:** 9000 (S3 API), 9001 (Console UI)
**Image:** `docker.m.daocloud.io/minio/minio:latest`
**Credentials:** `ordivon` / `ordivon123`

### Health Check

```bash
curl -s http://localhost:9000/minio/health/live
# Expected: 200 OK (HTML response)
```

### Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `connection refused` | Container stopped | `docker start ordivon-minio` |
| Upload fails | Bucket doesn't exist | Client auto-creates on `upload_evidence()` |
| Data lost | Volume not mounted | Check `/tmp/minio-data` exists and is mounted |

### Fallback

When S3 is down, evidence files stay on local disk (`docs/governance/evidence/`).
The S3 client returns `available() == False` and callers should fall back to
local file I/O.

---

## Service: OPA (CLI, not a Docker service)

**Purpose:** Policy evaluation — "Is this state transition valid under current rules?"

**Binary:** `/usr/local/bin/opa` (v1.3.0)
**Policies:** `policies/opa/rules/authority_transitions.rego`

### Health Check

```bash
opa version
# Expected: Version: 1.3.0

opa check policies/opa/rules/authority_transitions.rego
# Expected: no output = valid
```

### Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `opa: command not found` | CLI not installed | Install from https://github.com/open-policy-agent/opa/releases |
| `rego_parse_error` | Policy syntax error | Check `.rego` file for Rego v1 syntax issues |
| `var _ is unsafe` | Rego v1 requires `some` instead of `_` | Replace `valid_transitions[_]` with `some i; valid_transitions[i]` |

### Fallback

When OPA CLI is not available, `check_transition_opa()` falls back to
Python `VALID_*_TRANSITIONS` dicts. These are exhaustively tested for
consistency with the Rego policies.

---

## Monitoring & Alerts

```bash
# Automated health check (runs every 6h via cron job 0999735f82c6)
python3 scripts/health_check.py --alert

# All services healthy?
python3 scripts/health_check.py | python3 -c "import sys,json; d=json.load(sys.stdin); print('ALL OK' if d['all_healthy'] else f'FAILED: {d[\"failed\"]}')"
```

## Recovery Scenarios

### Scenario 1: Everything is down (server reboot)

```bash
# Start core infrastructure
docker compose -f docker-compose.infrastructure-mirror.yml up -d

# Start OpenFGA (separate because it's not in that compose file)
docker run -d --name ordivon-openfga -p 8081:8080 \
  -e OPENFGA_DATASTORE_ENGINE=memory -e OPENFGA_AUTHN_METHOD=none \
  docker.m.daocloud.io/openfga/openfga:v1.5 run

# Wait for services, then verify
sleep 30
python3 scripts/health_check.py
```

### Scenario 2: Database corrupted

```bash
# Find latest S3 backup
python3 scripts/backup_db.py --list

# Restore
python3 scripts/backup_db.py --restore backups/ordivon_backup_YYYYMMDD_HHMMSS.sql.gz

# Verify
python3 scripts/migrate_governance_to_pg.py --dry-run
```

### Scenario 3: App can't connect to PG but PG is running

```bash
# Check env
cat .env | grep ORDIVON_DB_URL

# Should be: ORDIVON_DB_URL=postgresql://ordivon:ordivon@localhost:5432/ordivon
# If missing, app falls back to SQLite — just means data is in SQLite not PG
```
