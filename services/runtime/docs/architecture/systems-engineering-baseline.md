# Systems Engineering Baseline

> **Status**: Canonical engineering rules document
> **Date**: 2026-04-26
> **Phase**: Docs-D2 — core baseline documentation
> **Depends on**: [ordivon-system-definition.md](ordivon-system-definition.md), [core-pack-adapter-baseline.md](core-pack-adapter-baseline.md)

## Purpose

This document defines the **engineering rules** that govern how the system is built, changed, and tested. It translates the identity invariants from the system definition into concrete engineering constraints.

It does not describe what the system is. It describes **how the system must be built**.

---

## Rule 1: Every Module Has a Clear Owner

### The rule

Every module must declare which layer owns it and whether it is Core, Pack, or Adapter.

### Why

Without explicit ownership, modules drift. A module that starts as a pack helper gradually absorbs core-like responsibilities because "it's already there."

### Compliance check

Every new module must answer:
1. Which layer owns it? (Experience / Capability / Orchestration / Governance / Intelligence / Execution / State / Knowledge / Infrastructure)
2. Is it Core, Pack, or Adapter?
3. What is it explicitly NOT allowed to do?

### Violation example

A finance-specific validation function that lives in `governance/` and imports `packs/finance/` is acceptable. A finance-specific validation function that lives in `governance/` and is treated as a universal governance primitive is a violation.

---

## Rule 2: Core Must Not Import Pack

### The rule

Code classified as Core must never import from Pack.

### Why

Import direction encodes ownership. If Core imports Pack, then Pack semantics bleed into system order. This makes the platform fragile: removing a pack would break the system.

### Compliance check

For every file in `orchestrator/`, `governance/`, `execution/` (primitive portions), `state/`, and `knowledge/` (primitive portions):
- Does this file import anything from `packs/` or from a domain-specific module?
- If yes: is this a genuine core primitive, or should it be reclassified?

### Allowed exceptions

- Configuration-driven pack loading (e.g., pack registry that discovers pack modules at runtime via string names)
- Abstract interfaces defined in core, implemented in pack (pack imports core, not the reverse)

---

## Rule 3: Adapter Implementation Must Not Define System Semantics

### The rule

Adapter code (Hermes Bridge, storage backends, tool connectors) may implement contracts. It may not define what the system means.

### Why

When adapter details leak into system semantics, the system becomes locked to the current adapter. Changing providers would require redefining the system.

### Example

| Acceptable | Unacceptable |
|-----------|--------------|
| `HermesClient` implements `IntelligenceRuntime.run(task)` | `IntelligenceRuntime.run()` assumes Hermes-specific session IDs |
| DuckDB adapter implements `TruthRepository` | DuckDB-specific SQL leaks into ORM models |
| Finance pack defines `RiskEngine.validate_intake()` | Finance pack overrides `GovernanceDecision` semantics |

---

## Rule 4: Every Seam Must Be Testable in Isolation

### The rule

Every seam (internal or external) must be testable without standing up the entire system.

### Why

If a seam can only be tested by running the full integration stack, it is not a real seam. It is a coupled dependency masquerading as a boundary.

### Compliance check

For every module boundary:
- Can the caller side be tested with a mock of the callee?
- Can the callee side be tested with a mock of the caller?
- If no to either: the seam is not isolated.

### Test patterns

| Seam type | Test pattern |
|-----------|-------------|
| Internal seam (function reference) | Unit test with mock |
| External seam (HTTP) | Contract test + integration test |
| Database seam | Repository test with test database |
| Runtime seam | Mock provider in unit test; real bridge in integration test |

---

## Rule 5: State Mutations Must Be Traceable

### The rule

Every state mutation (create, update, delete) on a truth-bearing object must produce a trace record.

### Why

Without traceability, the system cannot answer "how did we get here?" This makes audits impossible and debugging guesswork.

### Required trace records

| Mutation | Required trace |
|----------|---------------|
| Create entity | TraceLink with causality edge to creating event |
| Update entity status | TraceLink with before/after state |
| Governance decision | AuditEvent |
| Execution action | ExecutionReceipt |
| Recommendation | WorkflowRun lineage |

---

## Rule 6: External Side Effects Require Governance

### The rule

Any side effect that touches an external system (broker, notification, file write, API call) must pass through governance before execution.

### Why

Without governance gating, the system cannot control what external systems are affected or when.

### Current side-effect families

| Family | Governance gate | Execution adapter |
|--------|----------------|-------------------|
| Report write | GovernanceDecision required | Wiki writer adapter |
| Notification send | GovernanceDecision required | Notification adapter |
| Broker order | Not yet implemented (H-7+) | Future broker adapter |
| File write | ALLOW_FILE_WRITE flag (Hermes Bridge) | Bridge enforces |

---

## Rule 7: Tests Must Assert Invariants, Not Just Behavior

### The rule

Tests must verify that system invariants hold, not just that "the code does what we expect."

### Why

Behavioral tests pass when the code works. Invariant tests pass when the system cannot be broken. The difference is critical.

### Invariant test examples

| Invariant | Test |
|-----------|------|
| Intelligence is not sovereignty | Test that mock provider cannot write to state truth table |
| Governance gates execution | Test that execution adapter is not called when governance says "deny" |
| Core does not import pack | Static analysis or import-time assertion |
| Receipt is immutable | Test that receipt update endpoint returns 405 |

---

## Rule 8: Deletion Is a Design Tool

### The rule

If you can delete a module and nothing meaningful breaks, the module is dead weight.

### Deletion test

For any module candidate:
1. Delete the module (conceptually or in a branch)
2. Run the full test suite
3. If all tests pass: the module is unused — remove it
4. If core invariants still hold: the module was redundant — merge it

### When to apply

- Before refactoring a module
- When auditing capability inventory
- When a module's tests consistently mock everything (sign of low leverage)

---

## Rule 9: Configuration Must Be Feature-Flagged

### The rule

New infrastructure, runtime behavior, or integration paths must be gated behind configuration flags that default to OFF.

### Why

Feature flags allow:
- Zero-impact deployment
- Gradual rollout
- Easy rollback
- Testing both paths independently

### Flag pattern

```python
# settings.py
class Settings(BaseSettings):
    new_feature_enabled: bool = False  # Default OFF
    new_feature_config: str = ""       # Empty = disabled

# runtime
if settings.new_feature_enabled:
    # new path
else:
    # original path (preserved exactly)
```

### Test requirements

Every feature flag must have tests proving:
- Flag OFF → original behavior unchanged
- Flag ON → new behavior active
- Flag ON + dependency unavailable → graceful fallback (never crash)

---

## Rule 10: The System Must Survive Adapter Failure

### The rule

No adapter failure may crash the system. Every adapter call must have a fallback, timeout, or circuit breaker.

### Why

Adapters connect to external systems. External systems fail. The system must remain operational even when an adapter is unavailable.

### Required failure handling

| Adapter type | Failure behavior |
|-------------|-----------------|
| Model runtime (Hermes Bridge) | Fallback to mock provider; log error; return degraded response |
| Storage backend (DuckDB/PostgreSQL) | Connection retry with backoff; health endpoint reports unhealthy |
| Redis cache | Silently skip cache; fall through to provider |
| External API | Timeout + retry policy; log failure; return error to caller |

---

## Relationship to Other Documents

- [ordivon-system-definition.md](ordivon-system-definition.md) — what the system is
- [core-pack-adapter-baseline.md](core-pack-adapter-baseline.md) — platformization classification
- [aegisos-design-doctrine.md](aegisos-design-doctrine.md) — philosophy-to-engineering mapping
- [LANGUAGE.md](LANGUAGE.md) — vocabulary for expressing these rules

---

## Compliance

Every code review, architecture audit, and refactoring proposal must reference these rules. If a rule is violated, the violation must be explicit and justified, not accidental.
