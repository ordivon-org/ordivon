# HAP-2 — Stage Notes

> **Status:** OPEN | **Date:** 2026-05-02 | **Authority:** current_truth

## 1. Purpose

HAP-2 dogfoods HAP-1 objects with ADP-1 agentic failure patterns through
local, non-executing scenario fixtures. 14 scenarios, 30 boundary guard
tests, all BLOCKED receipts prove boundary enforcement.

## 2. Strategic Position

```
OGAP → external adapter governance (CLOSED)
HAP-1 → harness object model (CLOSED)
EGB-1 → external benchmark reference (CLOSED)
ADP-1 → agentic pattern mapping (CLOSED)
HAP-2 → ADP-1 pattern fixture dogfood (OPEN)
```

## 3. Phase Inventory

| Deliverable | Content |
|------------|---------|
| 14 scenario fixture directories | `examples/hap/adp-scenarios/*/` |
| 2 test files (30 tests) | Boundary guards + fixture validation |
| Runtime doc | `docs/runtime/hap-fixture-dogfood-hap-2.md` |
| Stage notes | This document |

## 4. Key Numbers

- 14 ADP-1 patterns covered (of 14 high-priority)
- 56 fixture files (4 per scenario)
- 11 BLOCKED scenarios — boundary enforcement dominates
- 2 DEGRADED (evidence quality, CandidateRule advisory)
- 1 READY_WITHOUT_AUTHORIZATION (disclaims execution)
- 30 tests (22 boundary guards + 8 fixture validation)
- All CandidateRule suggestions remain NON-BINDING
- 0 can_access_secrets references
- 0 compliance/certification/endorsement claims

## 5. Next Phase

**GOV-X** (Capability-Scaled Governance) or **ADP-2** (Pattern Detection Implementation).

*Created: 2026-05-02 | HAP-2 foundation*
