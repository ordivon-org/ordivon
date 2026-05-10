# GOS-N1A: Auto-Maintained Path Map — Design

> **This is a design document, not an implementation receipt.**
> No code has been written. Schema exists. Scripts are planned.

**Authority**: `proposal`
**Status**: `proposed`
**Phase**: `GOS-Hardening → N1`
**Owner**: `ordivon-core-maintainer`
**Freshness**: 2026-05-10
**Parent**: `docs/product/ordivon-gos-hardening-roadmap.md` (GOS-N1)

---

## 1. Problem

Current architecture diagrams (`ordivon-architecture-overview.txt`, `ordivon-architecture.html`) contain hand-written counts, layer lists, and component inventories. When repo reality changes (new files, new checkers, new debts), the diagrams drift.

```
Current state:
  File reality:  540 files, 445 registered
  Diagrams:      hand-maintained, counts embedded in ASCII/SVG

Drift risk:
  Every new file not reflected in diagrams
  Every new checker not reflected in diagrams
  Every removed document not reflected in diagrams
```

Root cause: **duplicated representation without enforced consistency** (AP-1: Hardcoded Count Drift, L-CI-SELFCAL-001).

---

## 2. Design Principle

```text
Single source of truth → deterministic classification → generated view → CI verify → drift → BLOCKED
```

Not "better diagrams." The diagrams must be **compiled from repo reality**, not drawn.

---

## 3. Sources of Truth

```
1. git ls-files                        → actual files on disk
2. document-registry.jsonl             → document metadata (owner, authority, doc_type, lifecycle)
3. document-types.json                 → valid doc_types
4. governed-exclusions.json            → intentionally excluded files
5. path-map-rules.json                 → classification rules (routes + fallbacks)
6. checkers/*/CHECKER.md               → checker inventory
7. .github/workflows/*.yml             → CI job inventory
8. lesson-ledger.jsonl                 → lesson inventory
9. dependency-audit-debts.jsonl        → debt inventory
10. candidate-rule-drafts.jsonl        → CandidateRule inventory
```

No additional source. The path map derives from these, not from hand-written observations.

---

## 4. Classification Algorithm

```
For each git-tracked file F:
    1. is_excluded?    → node.kind = "excluded" + reason
    2. in_registry?    → node.metadata = registry entry
    3. match_route?    → node.route = matched route ID
    4. no_route?       → fallback:
        protected?     → finding: BLOCKED
        non-protected? → finding: warning, exclusion recommended
    5. attach_related  → link to checker / CI / debt / lesson if applicable
    6. emit node
```

Deterministic only. AI may propose but may not classify authoritatively.

---

## 5. Outputs

```
Generated (never hand-edited):
  docs/governance/generated/path-map.json    ← machine-readable
  docs/governance/generated/_path-map.md     ← human-readable
  docs/governance/generated/path-map.dot     ← graph (future)
  docs/governance/generated/path-map.svg     ← diagram (future)
```

Architecture diagrams reference these, not hand-counted numbers.

---

## 6. Scripts

```
scripts/update-path-map.py     ← reads sources, generates outputs
scripts/verify-path-map.py     ← CI mode: regenerates and compares
```

CI job:
```yaml
verify-path-map:
  run: uv run python scripts/verify-path-map.py
```

---

## 7. Atomic Governance

Adding a new file requires one of these in the same commit:

```
A. Governed path:
   - document-registry.jsonl entry
   - valid doc_type from document-types.json
   - owner + authority
   - path-map route match (explicit or via path-map-rules.json)
   - generated path map updated

B. Excluded path:
   - governed-exclusions.json entry
   - reason + owner + review_date
   - generated path map updated

C. Generated file:
   - placed in docs/**/generated/ or named _*.md/_*.json
   - source_refs documented
   - verify script covers it
```

Otherwise: `atomic-governance: BLOCKED`.

---

## 8. Implementation Order (4 steps)

### Step 1: Document path map only

```
Scope: docs/**/*.md + document-registry.jsonl
Output: _document-path-map.md + document-path-map.json
Minimum viable auto-classification
```

### Step 2: Add checker + CI inventory

```
Add: checkers + .github/workflows
Output: checker → CI job → governed area mapping
```

### Step 3: Add knowledge assets

```
Add: lessons + debts + CandidateRules
Output: finding → debt → lesson → CandidateRule chain
```

### Step 4: Generate SVG / architecture view

```
path-map.json → path-map.dot → path-map.svg
Replace hand-drawn architecture diagram counts
```

---

## 9. Related Work

| System | Pattern | Ordivon Difference |
|--------|---------|--------------------|
| Docusaurus | auto sidebar from filesystem | adds owner + authority + risk |
| MkDocs | auto nav from markdown | adds governance metadata layers |
| Nx | auto project graph from imports | adds document→checker→CI→debt chains |
| GitHub CODEOWNERS | auto owner from path pattern | adds evidence + receipt + debt routing |

---

## 10. Status

```
Schema:               PROPOSED (path-map-rules.json created)
Design:               PROPOSED (this document)
Implementation:       NOT STARTED
Scripts:              PLANNED (update-path-map.py, verify-path-map.py)
CI integration:       PLANNED
Diagrams updated:     PLANNED
```

---

```text
READY means selected checks passed; it does not authorize execution.
```
