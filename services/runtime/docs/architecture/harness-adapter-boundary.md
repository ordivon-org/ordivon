# Harness / Adapter Boundary

> **Status**: Canonical runtime boundary rules
> **Date**: 2026-04-26
> **Phase**: Docs-D2 — core baseline documentation
> **Supersedes**: Pre-H-1 narrative in [hermes-model-layer-integration.md](hermes-model-layer-integration.md) (that doc will be rewritten in Docs-D3)

## Purpose

This document defines the boundary between the Ordivon system and external model runtimes. It answers:

1. **What is the harness?** — The external runtime that executes model inference.
2. **What is the bridge?** — The controlled HTTP service that wraps the external model API.
3. **What is the brain runtime?** — The Ordivon-side adapter that talks to the harness.
4. **Why can't the harness pollute core?** — The anti-contamination rules.

---

## One-Sentence Rule

> The harness provides intelligence. The system owns governance, state, execution, and knowledge. The harness must never know it is inside Ordivon.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        ORDIVON SYSTEM                         │
│                                                               │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐ │
│  │ Orchestrator │───▶│ Intelligence  │───▶│  Brain Runtime   │ │
│  │  (workflow)  │    │  (judgment)   │    │  (HermesRuntime)  │ │
│  └─────────────┘    └──────────────┘    └────────┬─────────┘ │
│                                                   │           │
│                                          RuntimeResolver     │
│                                          (adapter selection)  │
│                                                   │           │
│  ┌──────────────────────────────────────────────────┼─────┐  │
│  │              HARNESS ADAPTER                      │     │  │
│  │  ┌───────────────────────────────────────────────▼───┐ │  │
│  │  │              HermesClient                          │ │  │
│  │  │  Translates Ordivon task → Hermes Bridge protocol  │ │  │
│  │  └───────────────────────┬───────────────────────────┘ │  │
│  └──────────────────────────┼─────────────────────────────┘  │
└─────────────────────────────┼────────────────────────────────┘
                               │ HTTP (127.0.0.1:9120)
┌──────────────────────────────┼────────────────────────────────┐
│                    HERMES BRIDGE                               │
│  ┌───────────────────────────▼───────────────────────────┐    │
│  │  services/hermes_bridge/app.py                         │    │
│  │  Safety invariants: ALLOW_TOOLS=False                  │    │
│  │                     ALLOW_FILE_WRITE=False              │    │
│  │                     ALLOW_SHELL=False                   │    │
│  └───────────────────────┬───────────────────────────────┘    │
│                           │ OpenAI SDK                         │
│  ┌───────────────────────▼───────────────────────────────┐    │
│  │              External Model API                         │    │
│  │  (OpenAI / Anthropic / Google / DeepSeek / ...)        │    │
│  └───────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
```

---

## The Harness (External Runtime)

The harness is the external process or API that executes model inference. It is **outside** the Ordivon system boundary.

### Current harness

**Hermes Bridge** (`services/hermes_bridge/`) — wraps the OpenAI SDK to provide a controlled model inference endpoint.

### Harness invariants

The harness must:

| Invariant | Implementation |
|-----------|---------------|
| Execute model inference | Hermes Bridge calls OpenAI/Anthropic/Google SDK |
| Accept task contracts | `POST /pfios/v1/tasks` with TaskRequest schema |
| Return structured responses | TaskResponse with ToolCall list, usage info |
| Enforce safety invariants | `ALLOW_TOOLS=False`, `ALLOW_FILE_WRITE=False`, `ALLOW_SHELL=False` |
| Be health-checkable | `GET /pfios/v1/health` |

The harness must **never**:

| Prohibition | Why |
|------------|-----|
| Know about Ordivon governance | Governance is system concern, not runtime concern |
| Know about Ordivon state objects | State truth belongs to Ordivon, not the harness |
| Write to Ordivon databases | Truth source bypass |
| Define what "success" means for a workflow | Workflow success is defined by the orchestrator + governance |
| Return Ordivon-specific objects | Response must be a generic TaskResponse, not an `IntelligenceRun` |
| Make policy decisions | Policy is governance concern |

### Future harnesses

The system may support multiple harnesses:
- Direct OpenAI API (no bridge, for development)
- Direct Anthropic API
- DeepSeek API
- MCP (Model Context Protocol) servers
- Local model runtimes (llama.cpp, vLLM)
- Multi-provider routers

Each harness must implement the same contract:
```
TaskRequest → [Harness-specific protocol] → External Model → [Harness-specific protocol] → TaskResponse
```

---

## The Brain Runtime (Ordivon-Side Adapter)

The brain runtime is the Ordivon-side code that:
1. Receives a task from the intelligence layer
2. Selects the appropriate harness via RuntimeResolver
3. Translates the task into harness-specific protocol
4. Translates the harness response back into Ordivon objects

### Current brain runtime

**HermesRuntime** — the current implementation. Handles:
- Task → Hermes Bridge protocol translation
- Response parsing
- Error handling and fallback

### Brain runtime must never

| Prohibition | Why |
|------------|-----|
| Assume it is the only runtime | RuntimeResolver must support multiple runtimes |
| Define governance rules | Governance is above the intelligence layer |
| Write directly to state | State writes go through the orchestrator flow |
| Know domain specifics | Brain runtime handles generic tasks, not finance-specific ones |
| Leak harness errors upward | Harness errors become `RuntimeError` with context, not raw HTTP errors |

---

## The RuntimeResolver

The RuntimeResolver is the abstraction that selects which brain runtime to use.

### Contract

```python
class RuntimeResolver:
    def resolve(self, task: Task) -> IntelligenceRuntime:
        """Return the appropriate runtime for this task."""
```

### Resolution rules

| Input | Resolution |
|-------|-----------|
| `PFIOS_REASONING_PROVIDER=mock` | MockReasoningProvider (no harness call) |
| `PFIOS_REASONING_PROVIDER=hermes` | HermesRuntime → Hermes Bridge |
| `PFIOS_REASONING_PROVIDER=openai` | OpenAIRuntime → Direct OpenAI API |

The resolver is configuration-driven. Adding a new provider does not require changing intelligence layer code.

---

## Anti-Contamination Rules

### Harness must not pollute Core

| Violation | Example | Fix |
|-----------|---------|-----|
| Harness error codes in governance | GovernanceDecision references "Hermes timeout" | Map to generic `RuntimeError` with `provider` metadata |
| Harness session IDs in state | IntelligenceRun.session_id is Hermes-specific format | Use generic `session_id`; store harness-specific metadata separately |
| Harness-specific models in core | `if model == "google/gemini-3.1-pro-preview":` in orchestrator | Model selection is adapter concern, not orchestrator concern |
| Harness API tokens in core | OpenAI API key in `governance/` code | Tokens stay in adapter configuration only |

### Adapter must not colonize Pack

| Violation | Example | Fix |
|-----------|---------|-----|
| Pack assumes Hermes | Finance pack workflow hardcodes `HermesRuntime` | Use `RuntimeResolver` abstraction |
| Pack references bridge endpoints | `POST http://127.0.0.1:9120/pfios/v1/tasks` in finance workflow | Never; this goes through intelligence layer |
| Pack-specific task contracts leak to harness | Hermes task schema contains `symbol=BTC/USDT` | Task contracts are generic; domain specifics are payload fields |

### MCP servers must not become system identity

MCP (Model Context Protocol) servers are tool providers. They are adapters, not system components.

| Rule | Why |
|------|-----|
| MCP servers implement `ToolProvider` contract | They are tools, not system layers |
| MCP server failure must not crash the system | Tool unavailability → graceful degradation |
| MCP server output is evidence, not truth | Evidence enters governance; it does not override state |

---

## Safety Invariants (Hard Constants)

These are enforced by the Hermes Bridge and must be enforced by any future harness:

| Invariant | Value | Enforced by |
|-----------|-------|-------------|
| `ALLOW_TOOLS` | `False` | Hermes Bridge `app.py` — hard constant |
| `ALLOW_FILE_WRITE` | `False` | Hermes Bridge `app.py` — hard constant |
| `ALLOW_SHELL` | `False` | Hermes Bridge `app.py` — hard constant |

These are **not configuration**. They are hard constants. Changing them requires an explicit ADR and a code change, not an env var flip.

The bridge exists to enforce these invariants. If a future harness bypasses the bridge (e.g., direct OpenAI API), it must implement equivalent invariants.

---

## Error Handling Across the Boundary

### Harness errors → Ordivon errors

| Harness error | Ordivon error | System behavior |
|--------------|---------------|-----------------|
| Bridge unreachable | `RuntimeUnavailableError` | Fallback to mock; log; health endpoint updated |
| Bridge timeout | `RuntimeTimeoutError` | Retry with backoff; if exhausted, fallback to mock |
| Model API error (4xx) | `RuntimeConfigError` | Log; do NOT retry; return error to caller |
| Model API error (5xx) | `RuntimeProviderError` | Retry with backoff; if exhausted, fallback |
| Invalid response format | `RuntimeResponseError` | Log; do NOT retry; return error to caller |
| Safety invariant violation | `RuntimeSafetyError` | HARD STOP; log critical; alert operator |

### Ordivon must survive harness failure

The system must never crash because a harness is unavailable. Every harness call path must have:
1. Timeout (default: 30s)
2. Retry policy (default: 1 retry with 0.2s backoff)
3. Fallback (default: MockReasoningProvider)
4. Health signal (updates `/api/v1/health`)

---

## Future: Multi-Harness Architecture

When the system supports multiple simultaneous harnesses:

```
                         ┌──────────────┐
                         │ RuntimeResolver│
                         └──────┬───────┘
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
        │HermesRuntime │ │OpenAIRuntime│ │LocalRuntime │
        └───────┬──────┘ └──────┬──────┘ └──────┬──────┘
                │               │               │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
        │ Hermes Bridge│ │ Direct API  │ │ llama.cpp   │
        └──────────────┘ └─────────────┘ └─────────────┘
```

Each harness implements the same `IntelligenceRuntime` contract. The orchestrator does not know which harness is active.

---

## Relationship to Other Documents

- [ordivon-system-definition.md](ordivon-system-definition.md) — what the system is
- [core-pack-adapter-boundary.md](core-pack-adapter-boundary.md) — adapter anti-contamination rules
- [systems-engineering-baseline.md](systems-engineering-baseline.md) — Rule 3: Adapter must not define system semantics
- [hermes-model-layer-integration.md](hermes-model-layer-integration.md) — pre-H-1 design doc (Docs-D3 rewrite target)
- [pfios-infra-integration skill](/pfios-infra-integration) — operational startup and configuration
