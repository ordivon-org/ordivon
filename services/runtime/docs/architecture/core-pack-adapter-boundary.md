# Core / Pack / Adapter Boundary

> **Status**: Canonical boundary rules
> **Date**: 2026-04-26
> **Phase**: Docs-D2 — core baseline documentation
> **Supersedes**: [core-pack-adapter-baseline.md](core-pack-adapter-baseline.md) (that doc remains as the classification baseline; this doc adds the contamination prevention rules)

## Purpose

This document defines **who owns what, who may not touch what, and what happens when boundaries are violated**.

It complements the Core/Pack/Adapter baseline by focusing on the enforcement side — the anti-contamination rules that prevent the platform body from being colonized by any single domain, provider, or runtime.

---

## The Three Ownership Zones

```
┌─────────────────────────────────────────────────────────┐
│                      CORE                                │
│  Owns: system order, governance, state, trace, audit    │
│  Must NOT: import pack, depend on provider, know domain │
│                                                         │
│  ┌──────────────────────┐  ┌─────────────────────────┐  │
│  │        PACK           │  │       ADAPTER            │  │
│  │  Owns: domain meaning │  │  Owns: integration       │  │
│  │  Must NOT: enter core │  │  Must NOT: define system │  │
│  │  May: import from     │  │  May: implement core     │  │
│  │        core           │  │        contracts         │  │
│  └──────────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Core: What It Owns

Core owns stable system order. These things are true regardless of domain.

| Category | Examples | Layer |
|----------|----------|-------|
| Workflow primitives | Task, Workflow, Step, Run, RetryPolicy, FallbackPolicy | Orchestration |
| Governance primitives | DecisionLanguage, Policy, RiskFlag, ApprovalRequirement, HumanReviewGate | Governance |
| Execution discipline | ActionRequest, ActionReceipt, IdempotencyKey, SideEffectClass | Execution |
| State primitives | EntityRef, StateRecord, LifecycleState, TraceLink, Outcome | State |
| Knowledge primitives | Lesson, FeedbackPacket, CandidateRule, Hint | Knowledge |
| Audit primitives | AuditEvent, EventType, TraceBundle, CausalityEdge | Knowledge + State |
| Runtime abstractions | AgentRuntime, TaskRuntime, Session, ContextBuilder | Intelligence |
| Experience semantics | TrustTier, MissingState, StatusSurface, TraceSurface | Experience |

### Core Anti-Contamination Rules

**Core must never:**

| Violation | Example | Consequence |
|-----------|---------|-------------|
| Import from Pack | `from packs.finance import Recommendation` in `governance/` | Pack colonizes system order; removing finance breaks governance |
| Know provider identity | `if provider == "hermes":` in `intelligence/` | System locks to one runtime; changing providers requires core changes |
| Contain domain nouns | `BTC`, `portfolio`, `position_size` in `state/` | Domain leaks into truth layer; adding a new domain would pollute state |
| Assume specific adapter | `DuckDB`-specific SQL in ORM models | Storage lock-in; changing backends breaks state layer |
| Depend on external API | Hardcoding `api.openai.com` endpoints | Runtime lock-in; system can't switch providers |

**Core may:**

- Define abstract interfaces (e.g., `IntelligenceRuntime.run(task) -> TaskResult`)
- Reference packs by configuration (e.g., string-based pack registry)
- Own registry/discovery mechanisms for packs and adapters
- Define state machine transitions that packs implement

---

## Pack: What It Owns

Packs own domain meaning. Finance is the first pack. Future packs (research, ops, compliance) follow the same rules.

### Current Finance Pack Ownership

| Category | Examples | Location |
|----------|----------|----------|
| Domain objects | Recommendation, Review, DecisionIntake, ExecutionRequest (finance-specific fields) | `packs/finance/` |
| Domain workflows | Finance-specific workflow steps, analysis profiles | `packs/finance/` |
| Domain policies | Trading limits, risk thresholds, symbol allowlists | `packs/finance/` |
| Domain validation | Finance-specific intake validation, risk parameter bounds | `packs/finance/` |
| Domain defaults | Default symbols, timeframes, analysis parameters | `packs/finance/` |
| Domain surfaces | Finance-facing UI components, analyze workspace | `packs/finance/` |

### Pack Anti-Contamination Rules

**Pack must never:**

| Violation | Example | Consequence |
|-----------|---------|-------------|
| Define system primitives | Finance pack defines its own `Policy` class that replaces core `Policy` | Two conflicting governance systems |
| Override core semantics | Finance pack changes what `GovernanceDecision.execute` means | Governance becomes domain-specific, not system-wide |
| Depend on other packs | Finance pack imports from a future `research` pack | Cross-pack coupling; packs become interdependent |
| Re-export core as pack | `from packs.finance import DecisionLanguage` | Confuses ownership; core primitives appear domain-specific |
| Own runtime identity | Finance pack assumes Hermes is the only model provider | Domain locks to one runtime |

**Pack may:**

- Import from core (this is the correct direction)
- Implement core interfaces (e.g., `RiskEngine` with finance rules)
- Extend core objects with domain-specific fields
- Own its own test suite, policies, and documentation

---

## Adapter: What It Owns

Adapters own replaceable integration. They implement contracts defined by core or pack.

### Current Adapter Zones

| Adapter | What it integrates | Contract it implements |
|---------|-------------------|----------------------|
| Hermes Bridge (`services/hermes_bridge/`) | External model API (OpenAI SDK) | `POST /pfios/v1/tasks` → TaskResponse |
| Hermes Client (`intelligence/runtime/hermes_client.py`) | Hermes Bridge → Ordivon task contracts | `IntelligenceRuntime.run(task)` |
| DuckDB adapter | DuckDB analytics engine | `TruthRepository` (analytics path) |
| PostgreSQL adapter | SQLAlchemy ORM (state truth) | `TruthRepository` (state path) |
| Redis client (`infra/cache/redis_client.py`) | Redis cache | `LLMCache` interface |
| Report renderer | Wiki/file writers | `ExecutionAdapter` (report_write family) |

### Adapter Anti-Contamination Rules

**Adapter must never:**

| Violation | Example | Consequence |
|-----------|---------|-------------|
| Define system semantics | Hermes Bridge defines what "analysis complete" means | Provider defines system meaning; system locks to one runtime |
| Mutate system state directly | Hermes Bridge writes to `IntelligenceRun` table | Truth source bypass; governance can't audit what happened |
| Own decision logic | Redis cache decides whether to skip governance | Adapter overrides system order |
| Leak implementation details | DuckDB-specific column types in ORM model definitions | Storage lock-in; ORM models become adapter-specific |
| Assume it is the only adapter | Hermes Client with no `RuntimeResolver` abstraction | Monopoly adapter; system can't have multiple runtimes |
| Pollute pack or core | Hermes-specific error codes in governance decisions | Runtime details leak upward into system semantics |

**Adapter may:**

- Implement core-defined contracts
- Have its own error handling, retry logic, and timeouts
- Be replaced by another adapter implementing the same contract
- Be feature-flagged (enabled/disabled via configuration)

---

## The Clean Import Rule

```
Core ← Pack     ✓  (Pack imports from Core — correct direction)
Core → Pack     ✗  (Core imports from Pack — COLONIZATION)
Core ← Adapter  ✓  (Adapter implements Core contract)
Core → Adapter  ✗  (Core depends on specific adapter — LOCK-IN)
Pack ← Adapter  ✓  (Adapter serves Pack needs)
Pack → Adapter  ✗  (Pack depends on specific adapter — LOCK-IN)
Pack ← Pack     ✗  (Cross-pack dependency — FRAGILITY)
```

### What "import" means

"Import" includes:
- Python `import` statements
- Direct references to concrete classes from another zone
- Assumptions about another zone's implementation details
- Configuration that hardcodes another zone's specifics

What it does NOT include:
- String-based configuration references (e.g., `"pack": "finance"`)
- Abstract interface references
- Registry lookups at runtime

---

## Boundary Violation Response

When a boundary violation is detected:

### During development (before merge)

1. Stop the implementation
2. Reclassify: is the code in the wrong zone, or is the architecture wrong?
3. Fix the violation before proceeding

### In existing code (legacy)

1. Document the violation in [boundary-map.md](boundary-map.md)
2. Add to migration tracking in [migration-map.md](migration-map.md)
3. Schedule remediation (not urgent unless it blocks a feature)
4. Do NOT silently accept it as "the way things are"

---

## Current Boundary Status

The repository is not yet physically organized as `core/`, `packs/`, and `adapters/`. Many modules still live in their original 9-layer structure. This is acceptable — the boundary is a conceptual classification first, a directory structure later.

### Known gray zones

| Zone | Current state | Resolution path |
|------|-------------|-----------------|
| Finance-specific logic in `governance/` | Mixed | Extract to `packs/finance/` governance rules; keep `DecisionLanguage` in core |
| Hermes references in `orchestrator/` | Mixed | Replace with `RuntimeResolver` abstraction; Hermes becomes one adapter |
| DuckDB-specific code in `state/` | Mixed | Ensure ORM models are backend-agnostic; adapter handles backend specifics |
| Finance nouns in `capabilities/` | Mixed | Finance capabilities become pack-owned; generic capabilities stay |

---

## Relationship to Other Documents

- [ordivon-system-definition.md](ordivon-system-definition.md) — what the system is (boundary rules enforce this)
- [core-pack-adapter-baseline.md](core-pack-adapter-baseline.md) — classification baseline (this doc adds enforcement)
- [systems-engineering-baseline.md](systems-engineering-baseline.md) — engineering rules (Rule 2: Core must not import Pack)
- [boundary-map.md](boundary-map.md) — current ownership map
- [migration-map.md](migration-map.md) — active migration tracking
