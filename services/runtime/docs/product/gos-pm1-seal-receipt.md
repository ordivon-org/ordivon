# GOS-PM-1: Auto-Maintained Path Map — Seal Receipt

> **This is a seal receipt, not a closure claim.** See methodology-core.md §8 for receipt standards.

**Authority**: `source_of_truth`
**Status**: `current`
**Phase**: `GOS-Hardening → PM-1`
**Owner**: `ordivon-core-maintainer`
**Freshness**: 2026-05-11

---

## Evidence

### Artifacts Delivered

| File | Type | Lines |
|------|------|-------|
| `docs/governance/schemas/path-map-rules.json` | Schema | 194 |
| `docs/governance/schemas/path-map-node.schema.json` | Schema | 38 |
| `docs/governance/schemas/path-map-edge.schema.json` | Schema | 22 |
| `scripts/update-path-map.py` | Generator | 273 |
| `scripts/verify-path-map.py` | Verifier | 117 |
| `scripts/explain-path-node.py` | Query | 122 |
| `checkers/path-map/CHECKER.md` | Checker | 72 |
| `checkers/path-map/run.py` | Checker runner | 63 |
| `docs/governance/generated/path-map.json` | Generated view | auto |
| `docs/governance/generated/_path-map.md` | Generated view | auto |
| `docs/governance/generated/path-map.dot` | Generated view | auto |

### Before / After

```
Before:
  No auto-maintained path map.
  Architecture diagrams contained hand-written counts.
  New files could exist without governance classification.

After:
  update-path-map.py classifies 2044 tracked files.
  801 governed · 75 generated views · 42 excluded · 0 blocked · 1126 debt-parked.
  verify-path-map.py detects manual drift (999→2035 demo confirmed).
  explain-path-node.py provides local governance context.
  CI job blocking — verify-path-map.
```

### Raw Command Output

```
$ python scripts/update-path-map.py
Stats: 2044 files → 801 governed, 75 generated, 42 excluded, 0 blocked, 1126 debt-parked

$ python scripts/verify-path-map.py
✓ Path map consistent with repo reality
  2044 files → 801 governed, 0 blocked

$ python scripts/explain-path-node.py docs/governance/ordivon-methodology-core.md
Path: docs/governance/ordivon-methodology-core.md
Kind: document · Route: governance-core · Status: governed
Owner: ordivon-core-maintainer · Authority: source_of_truth

$ ordivon-verify all → READY (39/39)
```

### Negative Demos

```
RT-1: Generated view as source_of_truth → 75 generated nodes, all marked must_not_be_source_of_truth=True ✓
RT-2: Protected path unclassified → 0 blocked, 0 debt-parked in docs/governance/ ✓
RT-3: Exclusion metadata → 43 exclusions, all with meaningful reasons ✓
RT-4: Manual drift → DRIFT DETECTED (999 vs 2035) ✓
RT-5: Local context query → explain-path-node returns route/owner/authority ✓
```

### New Schemas

| Schema | Entries |
|--------|---------|
| path-map-rules.json | 7 routes, 3 fallbacks |
| path-map-node.schema.json | 5 required fields, 10 kinds, 5 statuses |
| path-map-edge.schema.json | 12 edge types |
| governed-exclusions.json | 43 entries (was 36) |
| document-types.json | 24 types (was 23 — added checker + methodology) |

---

## Commit Chain

```
ab57e38 fix: new-ai-collaborator-guide.md — 38→39 checkers
a035f75 fix: 38→39 checkers in systems-reference.md
de2dde7 fix: update registry stats for path-map changes
703969f fix: regenerate path-map to match repo reality
cabcb39 fix: exclude generated path-map files from atomic governance
d98b41a fix: resolve path-map schema conflict
(pending) feat: GOS-PM-1 — explain + red-team + seal receipt
```

---

## Status (per controlled vocabulary)

```
Auto Path Map:              VERIFIED_AS_GENERATED_VIEW
Generated View Drift:       DETECTABLE (verify-path-map.py)
Protected Path Coverage:    0 blocked, 0 unclassified
Exclusion Governance:       43 entries, all with reasons
Governance Coverage:        READY_WITH_EXPLICIT_EXCLUSIONS
Full Closure:               NOT CLAIMED
External Governance:        NOT CLAIMED
```

---

```text
READY means selected checks passed; it does not authorize execution.
```
