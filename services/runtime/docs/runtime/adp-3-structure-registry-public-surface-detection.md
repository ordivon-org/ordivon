# ADP-3 Structure-Aware + Registry-Aware + PV-Aware Detection v0

> **v0 / local static detection / non-executing.** Detector PASS is not authorization.
> **Phase:** ADP-3 | **Risk:** AP-R0 | **Authority:** AI-0/AI-2

## 1. Purpose

ADP-3 extends ADP-2 line-based detection with three new awareness layers:
- **Structure-aware:** Parses HAP-3 TaskPlan/ReviewRecord JSON objects
- **Registry-aware:** Checks DG document-registry.jsonl for consistency violations
- **PV-aware:** Scans Ordivon Verify public-surface docs for overclaim

## 2. Detection Layers

| Layer | Input | Checks | Rules |
|-------|-------|--------|-------|
| ADP-2 (line-based) | Text lines | 12 rules | All existing ADP-2 rules |
| ADP-3 (structure) | JSON objects | HAP-3 TaskPlan/ReviewRecord | 6 rules |
| ADP-3 (registry) | document-registry.jsonl | DG consistency | 3 rules |
| ADP-3 (PV) | PV .md docs | Public-surface overclaim | 3 rules |

## 3. ADP-3 Rule Inventory

**Structure-aware (6 rules):**
| Rule | Pattern | Severity |
|------|---------|----------|
| ADP3-PLAN-EXEC | TaskPlan claims execution | blocking |
| ADP3-PLAN-C4 | C4 TaskPlan not BLOCKED | blocking |
| ADP3-PLAN-C5 | C5 TaskPlan not NO_GO | blocking |
| ADP3-PLAN-PPATH | Protected paths without boundary | degraded |
| ADP3-REVIEW-DETECTOR | Detector PASS as authorization | blocking |
| ADP3-REVIEW-COMMENT | COMMENT_ONLY as approval | blocking |
| ADP3-CR-BINDING | CandidateRule binding | blocking |

**Registry-aware (3 rules):**
| Rule | Pattern | Severity |
|------|---------|----------|
| ADP3-DG-SUPERSEDED | current + superseded_by | blocking |
| ADP3-DG-AI-STALE | High-priority AI doc archived | degraded |
| ADP3-DG-RECEIPT-AUTH | Receipt claims authorization | blocking |

**PV-aware (3 rules):**
| Rule | Pattern | Severity |
|------|---------|----------|
| ADP3-PV-RELEASE | Package/release overclaim | blocking |
| ADP3-PV-WEDGE | Wedge/core collapse | blocking |
| ADP3-PV-READY | READY as public approval | blocking |

## 4. Test Results

- ADP-3 new tests: 14/14 PASS
- ADP-2 existing tests: 26/26 PASS
- **Total: 40/40 PASS**

## 5. Detector Evolution

| Version | Capability | Rules | Tests |
|---------|-----------|-------|-------|
| ADP-2 | Line-based regex | 12 | 26 |
| ADP-3 | + Structure + Registry + PV | 12 + 12 = 24 | 40 |

## 6. Boundary Confirmation

| Boundary | Confirmed |
|----------|-----------|
| Detector is local static only | ✅ |
| Detector PASS is not authorization | ✅ |
| No public release claimed | ✅ |
| Ordivon Verify != full core | ✅ |
| No credentials accessed | ✅ |
| No external systems invoked | ✅ |

*Phase: ADP-3 | Local static detection only.*
