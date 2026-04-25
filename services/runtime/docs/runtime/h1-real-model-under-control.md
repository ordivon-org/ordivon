# H-1: One Real Model Under Ordivon Control

Status: **CLOSED**  
Date: 2026-04-26  
Tags: `h1`, `real-model`, `bridge`, `deepseek`, `governance-gate`, `contract`

## Overview

H-1 proves that an external real model (DeepSeek) can run **inside** the Ordivon
governance framework — producing real analysis that flows through the full
governance/audit/receipt chain.

This is **not** a full Hermes Agent harness integration. It is the existence
proof: "One Real Model Under Ordivon Control."

---

## H-1B: One Real Model Under Ordivon Control ✅

### What was built

- `services/hermes_bridge/` — a controlled FastAPI adapter that exposes a
  minimal contract (`GET /pfios/v1/health`, `POST /pfios/v1/tasks`).
- The bridge wraps the OpenAI-compatible SDK, calling DeepSeek API with a
  strict system prompt that enforces JSON-only responses with no tool usage.
- Ordivon connects via `HermesRuntime` → `HermesClient` → bridge, activated
  by `PFIOS_REASONING_PROVIDER=hermes`.

### Verification (H-1B smoke pass)

```
Ordivon
  → HermesRuntime
  → services/hermes_bridge
  → OpenAI-compatible SDK
  → DeepSeek API (deepseek-v4-pro)
  → structured JSON
  → AnalysisResult
  → PersistAnalysis (AnalysisORM ✓)
  → GovernanceGate
  → Recommendation (RecommendationORM ✓)
  → Audit (AuditEventORM ✓)
  → ExecutionReceipt (ExecutionRequestORM / ExecutionReceiptORM ✓)
  → IntelligenceRun (IntelligenceRunORM ✓)
  → AgentAction (AgentActionORM ✓)
```

| Assertion | Result |
|-----------|--------|
| summary is NOT "Mock analysis" | ✅ |
| AnalysisORM written | ✅ |
| RecommendationORM written | ✅ |
| AuditEventORM written | ✅ |
| ExecutionRequestORM / ExecutionReceiptORM written | ✅ |
| IntelligenceRunORM written | ✅ |
| AgentActionORM written | ✅ |
| provider/model = deepseek / deepseek-v4-pro | ✅ |
| tool_trace = [] | ✅ |
| Governance by Ordivon RiskEngine | ✅ |
| llm_cache_enabled = false | ✅ |
| Bridge has no --yolo | ✅ |
| Bridge has no tool execution | ✅ |
| Bridge has no file write | ✅ |
| Bridge has no shell execution | ✅ |

---

## H-1C: Bridge Contract Hardening ✅

### What was built

- `tests/unit/services/test_hermes_bridge_contract.py` — 15 contract tests
  covering the bridge's HTTP surface without any real API calls.

### Test coverage

| # | Test | Coverage |
|---|------|----------|
| 1 | `test_health_returns_provider_and_model` | Health endpoint structure |
| 2 | `test_health_tools_explicitly_disabled` | tools_enabled=False invariant |
| 3 | `test_tasks_analysis_generate_success` | Successful task with mocked model |
| 4 | `test_tasks_unsupported_task_type` | 400 on unknown task_type |
| 5 | `test_tasks_empty_task_type` | 400 on empty task_type |
| 6 | `test_tasks_non_analysis_task_type` | 400 on execution.run (proves not general agent) |
| 7 | `test_health_rejects_missing_auth` | 401 without Authorization header |
| 8 | `test_tasks_rejects_missing_auth` | 401 on POST without auth |
| 9 | `test_health_rejects_wrong_bearer_token` | 401 with wrong token |
| 10 | `test_tasks_rejects_wrong_bearer_token` | 401 on POST with wrong token |
| 11 | `test_health_accepts_valid_bearer_token` | 200 with correct token |
| 12 | `test_tasks_failed_model_output_is_not_completed` | Failed output not masked as completed |
| 13 | `test_tasks_failed_output_has_no_summary` | Failed output carries no fake data |
| 14 | `test_config_safety_flags_all_false` | ALLOW_TOOLS/FILE_WRITE/SHELL = False |
| 15 | `test_bridge_has_no_llm_cache_config` | Bridge config excludes LLM cache |

All 15 tests pass without a real API key (mock `run_analysis`).  
Full unit suite: 275 tests pass.

---

## Current Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Ordivon (PFIOS)                             │
│                                                                      │
│  /api/v1/analyze-and-suggest                                         │
│       │                                                              │
│       ▼                                                              │
│  orchestrator/workflows/analyze.py                                   │
│       │                                                              │
│       ▼                                                              │
│  HermesRuntime (adapters/runtimes/hermes/runtime.py)                 │
│       │                                                              │
│       ▼                                                              │
│  HermesClient (intelligence/runtime/hermes_client.py)                │
│       │  HTTP (PFIOS_HERMES_BASE_URL)                                │
└───────┼──────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────────────┐
│  services/hermes_bridge (Port 9120)                                  │
│                                                                      │
│  GET  /pfios/v1/health                                               │
│  POST /pfios/v1/tasks  (only analysis.generate)                      │
│       │                                                              │
│       ▼                                                              │
│  hermes_runner.run_analysis()                                        │
│       │  OpenAI SDK (openai>=1.0.0)                                  │
│       ▼                                                              │
│  DeepSeek API (api.deepseek.com)                                     │
│       │                                                              │
│       ▼                                                              │
│  TaskResponse { status, output, provider, model, tool_trace: [] }    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Running the Bridge

```bash
# Start the bridge on localhost:9120
uv run uvicorn services.hermes_bridge.app:app --host 127.0.0.1 --port 9120
```

---

## Ordivon Environment Variables

```bash
PFIOS_REASONING_PROVIDER=hermes
PFIOS_HERMES_BASE_URL=http://127.0.0.1:9120/pfios/v1
PFIOS_HERMES_API_TOKEN=<local token>
PFIOS_LLM_CACHE_ENABLED=false
```

---

## Testing

```bash
# Bridge contract tests (no API key needed)
uv run pytest -q tests/unit/services/test_hermes_bridge_contract.py -vv

# Full unit suite
uv run pytest -q tests/unit -p no:cacheprovider
```

---

## Safety Boundaries (Hard Invariants)

The bridge is an **analysis adapter**, not an agent harness. These are
compile-time constants, not runtime configuration:

| Boundary | Value | Rationale |
|----------|-------|-----------|
| `ALLOW_TOOLS` | `False` | No tool execution under any condition |
| `ALLOW_FILE_WRITE` | `False` | No filesystem writes |
| `ALLOW_SHELL` | `False` | No shell access |
| `--yolo` | disabled | Never auto-approve dangerous operations |
| browser | disabled | No web automation |
| MCP | disabled | No model context protocol |
| LLM cache | `false` | Cache is Ordivon concern (R-3B), not bridge |
| DB writes | none | Bridge does not touch Ordivon database |
| Governance | none | Bridge does not perform governance decisions |
| Receipts | none | Bridge does not create execution receipts |
| Output | structured JSON only | `{summary, thesis, risks, suggested_actions}` |

---

## What H-1 Does NOT Include (Explicitly Out of Scope)

- ❌ Full NousResearch/hermes-agent harness runtime integration
- ❌ Hermes CLI / ACP / MCP / tools / memory / terminal execution
- ❌ Multi-step agent workflows
- ❌ Tool-augmented reasoning
- ❌ File operations of any kind
- ❌ Browser automation
- ❌ Shell command execution
- ❌ Model context protocol servers
- ❌ LLM caching (R-3B, separate workstream)
- ❌ P4 finance control loop vertical slice
- ❌ P5 observability / telemetry expansion
- ❌ Docker deployment of the bridge

**H-1 is a single proof: one real model running under Ordivon governance,
with contract-hardened boundaries.**

---

## Commits

| Commit | Description |
|--------|-------------|
| `5866387` | feat: add controlled real-model hermes bridge (H-1B) |
| `a57f2d1` | test: harden hermes bridge contract (H-1C) |
| (this commit) | docs: close h1 real model bridge baseline (H-1D) |

## Tags

```
h1-real-model-bridge-baseline
```
