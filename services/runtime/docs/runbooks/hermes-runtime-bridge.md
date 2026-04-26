# Hermes Bridge Runbook

> **Status**: Operational runbook
> **Date**: 2026-04-26
> **Phase**: Docs-D3 — Hermes Bridge / Harness Boundary Rewrite
> **Supersedes**: Previous version which referenced external `hermes-runtime` project and Windows paths

## Purpose

This runbook covers starting, verifying, and troubleshooting the Ordivon-owned Hermes Bridge (`services/hermes_bridge/`).

The bridge is a standalone FastAPI server built into the PFIOS repository. It does NOT require an external `hermes-runtime` project.

---

## Architecture

```
Ordivon (PFIOS)
  └── HermesClient (intelligence/runtime/hermes_client.py)
        │
        └── HTTP POST → 127.0.0.1:9120/pfios/v1/tasks
                          │
              ┌───────────┴────────────┐
              │   Hermes Bridge         │
              │   services/hermes_bridge/│
              │   app.py (FastAPI)       │
              │   hermes_runner.py       │
              │   config.py              │
              │   schemas.py             │
              └───────────┬────────────┘
                          │ OpenAI-compatible SDK
                          ▼
                    External Model API
```

The bridge wraps the OpenAI-compatible SDK. By default it calls DeepSeek (`deepseek-v4-pro`).

---

## Start Bridge

```bash
cd /root/projects/financial-ai-os
uv run uvicorn services.hermes_bridge.app:app --host 127.0.0.1 --port 9120
```

### With custom model

```bash
PFIOS_BRIDGE_PROVIDER=openai \
PFIOS_BRIDGE_MODEL=gpt-4o \
PFIOS_BRIDGE_BASE_URL=https://api.openai.com/v1 \
PFIOS_BRIDGE_API_KEY=$OPENAI_API_KEY \
uv run uvicorn services.hermes_bridge.app:app --host 127.0.0.1 --port 9120
```

### With auth token

```bash
PFIOS_BRIDGE_API_TOKEN=your-local-token \
uv run uvicorn services.hermes_bridge.app:app --host 127.0.0.1 --port 9120
```

Without `PFIOS_BRIDGE_API_TOKEN`, auth is disabled (accepts all requests).

---

## Required Environment Variables

### Bridge side

| Variable | Default | Required | Notes |
|----------|---------|----------|-------|
| `PFIOS_BRIDGE_API_KEY` | `$DEEPSEEK_API_KEY` | Yes | API key for model provider |
| `PFIOS_BRIDGE_PROVIDER` | `deepseek` | No | Model provider name |
| `PFIOS_BRIDGE_MODEL` | `deepseek-v4-pro` | No | Model name |
| `PFIOS_BRIDGE_BASE_URL` | `https://api.deepseek.com` | No | API base URL |
| `PFIOS_BRIDGE_API_TOKEN` | `""` | No | Auth token (empty = no auth) |

### Ordivon side (to call the bridge)

| Variable | Default | Purpose |
|----------|---------|---------|
| `PFIOS_REASONING_PROVIDER` | `mock` | Set to `hermes` to use bridge |
| `PFIOS_HERMES_BASE_URL` | `http://127.0.0.1:9120/pfios/v1` | Bridge endpoint |
| `PFIOS_HERMES_API_TOKEN` | `""` | Must match `PFIOS_BRIDGE_API_TOKEN` if auth enabled |

---

## Health Check

```bash
# Bridge health
curl http://127.0.0.1:9120/pfios/v1/health

# Expected response:
# {"status":"ok","bridge":"pfios-hermes-bridge","bridge_version":"0.1.0",
#  "hermes_binary":"/root/.local/bin/hermes","provider":"deepseek",
#  "model":"deepseek-v4-pro","tools_enabled":false}
```

Key health signals:
- `status: "ok"` — bridge is running
- `tools_enabled: false` — safety invariant confirmed
- `provider` / `model` — confirm which model the bridge is configured to call

### Ordivon health (checks bridge reachability)

```bash
curl http://127.0.0.1:8000/api/v1/health

# Look for:
# "reasoning_provider": "hermes"  (or "mock")
```

---

## Task Check (analysis.generate)

```bash
curl -X POST http://127.0.0.1:9120/pfios/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "analysis.generate",
    "task_id": "health-check-001",
    "input": {
      "query": "Analyze BTC momentum",
      "symbol": "BTC/USDT",
      "timeframe": "1d"
    },
    "context_refs": {"provider": "deepseek", "model": "deepseek-v4-pro"},
    "constraints": {"must_return_fields": ["summary", "thesis", "risks", "suggested_actions"]},
    "execution_policy": {"enable_delegation": false, "enable_memory": false, "enable_moa": false}
  }'
```

Expected response:
```json
{
  "status": "completed",
  "task_id": "health-check-001",
  "task_type": "analysis.generate",
  "output": {
    "summary": "...",
    "thesis": "...",
    "risks": ["..."],
    "suggested_actions": ["..."]
  },
  "provider": "deepseek",
  "model": "deepseek-v4-pro",
  "session_id": "...",
  "usage": {"prompt_tokens": ..., "completion_tokens": ...}
}
```

---

## End-to-End Test (Ordivon → Bridge → Model)

With bridge running:

```bash
cd /root/projects/financial-ai-os

# Start PostgreSQL + Redis (if not running)
docker compose up -d postgres redis

# Run analyze workflow against real model
PFIOS_DB_URL="postgresql://pfios:pfios@127.0.0.1:5432/pfios" \
PFIOS_REASONING_PROVIDER=hermes \
PFIOS_HERMES_BASE_URL=http://127.0.0.1:9120/pfios/v1 \
PFIOS_HERMES_DEFAULT_MODEL=deepseek-v4-pro \
PFIOS_HERMES_DEFAULT_PROVIDER=deepseek \
uv run python -c "
import os
os.environ['PFIOS_DB_URL'] = 'postgresql://pfios:pfios@127.0.0.1:5432/pfios'
os.environ['PFIOS_REASONING_PROVIDER'] = 'hermes'
os.environ['PFIOS_HERMES_BASE_URL'] = 'http://127.0.0.1:9120/pfios/v1'
os.environ['PFIOS_HERMES_DEFAULT_MODEL'] = 'deepseek-v4-pro'
os.environ['PFIOS_HERMES_DEFAULT_PROVIDER'] = 'deepseek'

from fastapi.testclient import TestClient
from apps.api.app.main import app

client = TestClient(app)
resp = client.post('/api/v1/analyze-and-suggest', json={
    'query': 'Analyze BTC momentum',
    'symbols': ['BTC/USDT']
})
print('Status:', resp.status_code)
result = resp.json()
print('Provider:', result.get('metadata', {}).get('provider'))
print('Agent action:', result.get('metadata', {}).get('agent_action_id'))
print('Analysis ID:', result.get('analysis_id'))
print('Governance:', result.get('decision'))
"
```

---

## Safety Flags

These are hard constants in `services/hermes_bridge/config.py`. They CANNOT be changed without an ADR.

| Flag | Value | Meaning |
|------|-------|---------|
| `ALLOW_TOOLS` | `False` | Model cannot call tools |
| `ALLOW_FILE_WRITE` | `False` | Model cannot write files |
| `ALLOW_SHELL` | `False` | Model cannot execute shell commands |

These are NOT environment variable overrides. They are Python constants. The bridge does not pass tool definitions to the model. The bridge has no filesystem or shell access.

---

## Common Failures

### Bridge won't start

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: No module named 'services.hermes_bridge'` | Not in project root | `cd /root/projects/financial-ai-os` first |
| `Address already in use` | Port 9120 occupied | `lsof -i :9120` then kill; or use different port |
| `openai.AuthenticationError` | Missing or wrong API key | Set `PFIOS_BRIDGE_API_KEY` or `DEEPSEEK_API_KEY` |

### Bridge starts but tasks fail

| Symptom | Cause | Fix |
|---------|-------|-----|
| `401 unauthorized` | Auth token mismatch | Set same token on bridge (`PFIOS_BRIDGE_API_TOKEN`) and Ordivon (`PFIOS_HERMES_API_TOKEN`) |
| `400 unsupported task_type` | Sending non-`analysis.generate` task | Only `analysis.generate` is supported |
| `openai.APIConnectionError` | Network issue | Check internet; verify `PFIOS_BRIDGE_BASE_URL` |
| `openai.RateLimitError` | Rate limited | Wait and retry; check API quota |

### Ordivon can't reach bridge

| Symptom | Cause | Fix |
|---------|-------|-----|
| `RuntimeUnavailableError` | Bridge not running | Start bridge first |
| `RuntimeTimeoutError` | Bridge slow to respond | Increase `PFIOS_HERMES_TIMEOUT_SECONDS`; check model latency |
| Ordivon falls back to mock | `PFIOS_REASONING_PROVIDER` not set to `hermes` | Set `PFIOS_REASONING_PROVIDER=hermes` |

### Contract test failures

```bash
uv run pytest -q tests/unit/services/test_hermes_bridge_contract.py -vv
```

| Failure | Likely cause |
|---------|-------------|
| Auth test fails | Mock target is wrong; patch `services.hermes_bridge.app.BRIDGE_API_TOKEN` not `config.BRIDGE_API_TOKEN` |
| Response model mismatch | Mock return value must be `TaskResponse` object, not raw dict |

---

## What NOT to Do

| Do NOT | Why |
|--------|-----|
| Start bridge and expect it to create IntelligenceRun records | Bridge does not write to Ordivon DB |
| Expect bridge to execute governance decisions | Governance runs in Ordivon after bridge returns |
| Expect bridge to create receipts | Receipts are created by Ordivon Execution layer |
| Enable tools/shell/file_write | These are hard constants; must be changed via ADR, never via env |
| Import bridge modules in Core code | Bridge is an adapter; Core must not import adapter |
| Expect multi-task support | Only `analysis.generate` is implemented |
| Use the old external `hermes-runtime` project | That project is not part of the current architecture |
| Reference Windows paths (`C:\...`) | The project now runs on Linux/WSL |

---

## H-1C Contract Tests

Bridge contract tests verify the bridge's HTTP contract without calling a real model:

```bash
uv run pytest -q tests/unit/services/test_hermes_bridge_contract.py -vv
```

Tests verify:
- `GET /pfios/v1/health` returns correct structure
- `POST /pfios/v1/tasks` with `analysis.generate` returns correct `TaskResponse`
- Auth rejection when token mismatch
- Unsupported task types return 400

All tests mock `run_analysis` — zero real API calls.

---

## References

- [hermes-model-layer-integration.md](../architecture/hermes-model-layer-integration.md) — architecture document
- [harness-adapter-boundary.md](../architecture/harness-adapter-boundary.md) — runtime boundary rules
- [h1-real-model-under-control.md](../runtime/h1-real-model-under-control.md) — H-1 closure record
- `services/hermes_bridge/` — bridge source code
- `tests/unit/services/test_hermes_bridge_contract.py` — contract tests
