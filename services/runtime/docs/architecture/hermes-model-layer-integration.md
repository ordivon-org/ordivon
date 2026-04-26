# Hermes Bridge Integration

> **Status**: Current architecture document — replaces pre-H-1 design narrative
> **Date**: 2026-04-26
> **Phase**: Docs-D3 — Hermes Bridge / Harness Boundary Rewrite
> **Supersedes**: Previous version (2026-04-22) which described aspirational Hermes-runtime integration that does not exist

## Purpose

This document describes the **actual** Hermes Bridge integration as it exists in the repository. It is not a design proposal. It documents the H-1 validated path: One Real Model Under Ordivon Control.

---

## What This Is

The Hermes Bridge (`services/hermes_bridge/`) is an **Ordivon-owned adapter** that wraps the OpenAI-compatible SDK to provide a controlled model inference endpoint. It is the current harness — the external runtime that executes model inference.

The bridge is **not** the full Nous Research Hermes Agent CLI. It is a minimal HTTP service that:

1. Accepts a bounded task contract (`POST /pfios/v1/tasks`)
2. Calls an external model API via OpenAI-compatible SDK
3. Returns a structured response
4. Enforces hard safety invariants

---

## Validated Path (H-1: One Real Model Under Control)

```
Ordivon System
  │
  ├── orchestrator/workflows/analyze.py
  │     Declares ANALYSIS_WORKFLOW
  │
  ├── intelligence/engine.py
  │     Resolves provider: mock | hermes
  │
  ├── intelligence/runtime/hermes_client.py
  │     HermesClient: Ordivon-side adapter
  │     Translates task → bridge protocol
  │
  └── HTTP POST → 127.0.0.1:9120/pfios/v1/tasks
                    │
┌───────────────────┼──────────────────────────────────┐
│    HERMES BRIDGE (services/hermes_bridge/)            │
│                                                       │
│  app.py: FastAPI server                               │
│    ├── Auth: Bearer token (BRIDGE_API_TOKEN)          │
│    ├── Task route: POST /pfios/v1/tasks               │
│    │     └── Only accepts task_type="analysis.generate"│
│    └── Health: GET /pfios/v1/health                   │
│                                                       │
│  hermes_runner.py:                                    │
│    ├── Builds OpenAI-compatible request               │
│    ├── Calls external model API                       │
│    ├── Parses structured JSON response                │
│    └── Returns TaskResponse                           │
│                                                       │
│  Safety (hard constants):                             │
│    ├── ALLOW_TOOLS = False                            │
│    ├── ALLOW_FILE_WRITE = False                       │
│    └── ALLOW_SHELL = False                            │
│                                                       │
│  Default model: deepseek-v4-pro @ api.deepseek.com    │
└───────────────────┬──────────────────────────────────┘
                    │ OpenAI-compatible SDK
                    ▼
              External Model API
                    │
                    ▼
            Structured JSON response
                    │
                    ▼ (back through the bridge → HermesClient)
Ordivon System
  │
  ├── IntelligenceRun written (pending → completed)
  ├── AgentAction written (provider, model, session_id, tool_trace, usage)
  ├── AnalysisORM written
  ├── GovernanceDecision executed
  ├── Recommendation generated
  ├── AuditEvent written
  ├── ExecutionReceipt written
  └── API returns complete structure with governance metadata
```

This path was validated in H-1B through H-1D. All stages — IntelligenceRun, AgentAction, GovernanceDecision, AuditEvent, ExecutionReceipt — are written by Ordivon Core, not by the bridge.

---

## What This Is NOT

| This is NOT | The bridge does not | Reality |
|-------------|--------------------|---------|
| Full Hermes Agent harness | No Hermes CLI, no ACP, no MCP | Bridge is a standalone FastAPI app; does not import Hermes internals |
| Agentic tool execution | No tools, no shell, no file write | `ALLOW_TOOLS=False`, `ALLOW_SHELL=False`, `ALLOW_FILE_WRITE=False` — hard constants |
| Multi-task runtime | Only `analysis.generate` | Other task types return 400 |
| Delegation engine | No subagents | `enable_delegation` in execution_policy is accepted but defaults to False |
| Memory provider | No memory/session persistence | `enable_memory` defaults to False; bridge has no session store |
| Mixture-of-agents | No MOA aggregation | `enable_moa` defaults to False |
| Multiple providers | Currently DeepSeek only | Config changeable via env vars; no dynamic provider routing in bridge |
| Ordivon truth source | Does not write to Ordivon DB | Bridge has no PostgreSQL/DuckDB connection; no ORM access |
| Governance engine | Does not execute governance | Governance runs in Ordivon workflow after bridge returns |
| Receipt creator | Does not create receipts | Receipts are created by Ordivon Execution layer |
| Side-effect executor | Does not touch broker/filesystem | No broker, no notification, no report write from bridge |

---

## Ownership Boundary

| Component | Owned by | Location |
|-----------|----------|----------|
| Bridge (FastAPI app) | Ordivon Adapter | `services/hermes_bridge/app.py` |
| Bridge config | Ordivon Adapter | `services/hermes_bridge/config.py` |
| Bridge schemas | Ordivon Adapter | `services/hermes_bridge/schemas.py` |
| Bridge runner (SDK call) | Ordivon Adapter | `services/hermes_bridge/hermes_runner.py` |
| HermesClient (Ordivon side) | Ordivon Adapter | `intelligence/runtime/hermes_client.py` |
| RuntimeResolver (provider selection) | Ordivon Intelligence | `intelligence/engine.py` (resolves `reasoning_provider`) |
| IntelligenceRun ORM | Ordivon Core | `domains/intelligence_runs/orm.py` |
| AgentAction ORM | Ordivon Core | `domains/ai_actions/orm.py` |
| AnalysisORM | Ordivon Core | `domains/analysis/orm.py` |
| GovernanceDecision | Ordivon Core | `governance/` |
| AuditEvent | Ordivon Core | `governance/audit/` |
| ExecutionReceipt | Ordivon Core | `execution/` |

---

## Adapter Responsibilities

The Hermes Bridge (as an adapter) is responsible for:

| Responsibility | Implementation |
|---------------|---------------|
| Accept task contracts | `POST /pfios/v1/tasks` with `TaskRequest` schema |
| Validate task type | Only `analysis.generate` accepted; others → 400 |
| Authenticate callers | Bearer token from `BRIDGE_API_TOKEN` env |
| Call external model API | OpenAI-compatible SDK → DeepSeek API (configurable) |
| Parse structured response | Extract `summary`, `thesis`, `risks`, `suggested_actions` |
| Return structured response | `TaskResponse` with status, output, provider, model, usage |
| Report health | `GET /pfios/v1/health` returns provider/model/status |
| Enforce safety invariants | Hard constants: no tools, no file write, no shell |

The bridge is NOT responsible for:

| Non-responsibility | Why |
|--------------------|-----|
| Writing IntelligenceRun | Core concern; written by orchestrator workflow |
| Writing AgentAction | Core concern; written by HermesClient after bridge returns |
| Writing AnalysisORM | Core concern |
| Executing governance | Core concern; governance runs after intelligence completes |
| Creating receipts | Core concern; execution layer creates receipts |
| Persisting sessions | Bridge is stateless; no session store |
| Managing memory | Bridge has no memory provider; `enable_memory=False` |
| Tool execution | `ALLOW_TOOLS=False` — hard constant |

---

## Core Responsibilities

Ordivon Core (not the bridge) is responsible for:

| Responsibility | Code path |
|---------------|-----------|
| Workflow orchestration | `orchestrator/workflows/analyze.py` |
| Provider resolution | `intelligence/engine.py` → `RuntimeResolver` |
| IntelligenceRun persistence | `domains/intelligence_runs/orm.py` |
| AgentAction persistence | `domains/ai_actions/orm.py` |
| Analysis persistence | `domains/analysis/orm.py` |
| Governance execution | `governance/` — runs AFTER intelligence returns |
| Audit event writing | `governance/audit/` |
| Execution receipt creation | `execution/` — creates plan-only or live receipts |
| State truth management | PostgreSQL via SQLAlchemy ORM |

---

## Safety Constraints

These are hard constants in `services/hermes_bridge/config.py`. They are NOT configuration. Changing them requires an explicit ADR and code change.

| Constant | Value | Enforced by |
|----------|-------|-------------|
| `ALLOW_TOOLS` | `False` | Hard constant; bridge does not pass tool definitions to model |
| `ALLOW_FILE_WRITE` | `False` | Hard constant; bridge has no filesystem access for model |
| `ALLOW_SHELL` | `False` | Hard constant; bridge does not execute shell commands |

The bridge exists to enforce these invariants. If a future harness bypasses the bridge, it must implement equivalent invariants.

---

## Environment Configuration

### Bridge side (`services/hermes_bridge/`)

| Env var | Default | Purpose |
|---------|---------|---------|
| `PFIOS_BRIDGE_HOST` | `127.0.0.1` | Listen address |
| `PFIOS_BRIDGE_PORT` | `9120` | Listen port |
| `PFIOS_BRIDGE_API_TOKEN` | `""` | Auth token (empty = auth disabled) |
| `PFIOS_BRIDGE_PROVIDER` | `deepseek` | Model provider |
| `PFIOS_BRIDGE_MODEL` | `deepseek-v4-pro` | Model name |
| `PFIOS_BRIDGE_BASE_URL` | `https://api.deepseek.com` | API base URL |
| `PFIOS_BRIDGE_API_KEY` | `$DEEPSEEK_API_KEY` | API key |

### Ordivon side (settings.py)

| Env var | Default | Purpose |
|---------|---------|---------|
| `PFIOS_REASONING_PROVIDER` | `mock` | Switch to `hermes` to use bridge |
| `PFIOS_HERMES_BASE_URL` | `http://127.0.0.1:9120/pfios/v1` | Bridge endpoint |
| `PFIOS_HERMES_API_TOKEN` | `""` | Must match `PFIOS_BRIDGE_API_TOKEN` |
| `PFIOS_HERMES_DEFAULT_PROVIDER` | `gemini` | Provider reported to bridge |
| `PFIOS_HERMES_DEFAULT_MODEL` | `google/gemini-3.1-pro-preview` | Model reported to bridge |
| `PFIOS_HERMES_TIMEOUT_SECONDS` | `30.0` | Bridge call timeout |
| `PFIOS_HERMES_MAX_RETRIES` | `1` | Retry count on failure |
| `PFIOS_HERMES_RETRY_BACKOFF_SECONDS` | `0.2` | Backoff between retries |

---

## Future Harness Integration Requirements

If a new model runtime (OpenAI direct, Anthropic, local llama.cpp, etc.) is added as a harness:

1. Must implement the same contract: `POST /pfios/v1/tasks` → `TaskResponse`
2. Must enforce equivalent safety invariants (no tools/shell/file write without explicit ADR)
3. Must be registered in `RuntimeResolver` as a configuration-driven option
4. Must not require changes to orchestrator, governance, or execution layers
5. Must be feature-flagged (default OFF)
6. Must pass H-1C bridge contract tests

---

## H-1 Validation Commands

### Start bridge
```bash
uv run uvicorn services.hermes_bridge.app:app --host 127.0.0.1 --port 9120
```

### Health check
```bash
curl http://127.0.0.1:9120/pfios/v1/health
# → {"status":"ok","bridge":"pfios-hermes-bridge","provider":"deepseek","model":"deepseek-v4-pro","tools_enabled":false}
```

### Contract tests
```bash
uv run pytest -q tests/unit/services/test_hermes_bridge_contract.py -vv
```

### Full H-1 validation (with mock provider)
```bash
PFIOS_DB_URL=postgresql://pfios:pfios@127.0.0.1:5432/pfios \
uv run pytest -q tests/unit tests/integration -p no:cacheprovider
```

---

## Relationship to Other Documents

- [ordivon-system-definition.md](ordivon-system-definition.md) — what the system is
- [harness-adapter-boundary.md](harness-adapter-boundary.md) — runtime boundary rules
- [core-pack-adapter-boundary.md](core-pack-adapter-boundary.md) — adapter anti-contamination rules
- [systems-engineering-baseline.md](systems-engineering-baseline.md) — engineering rules
- [h1-real-model-under-control.md](../runtime/h1-real-model-under-control.md) — H-1 closure record
- [hermes-runtime-bridge.md](../runbooks/hermes-runtime-bridge.md) — operational runbook
