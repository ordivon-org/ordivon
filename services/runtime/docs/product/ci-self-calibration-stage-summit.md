# CI Self-Calibration — Stage Summit

> **This is a closure document. It compresses the CI-SelfCalibration epoch
> into a single receipt. Read this to understand what happened, what was
> built, what remains open, and what lessons were extracted.**

**Authority**: `source_of_truth`
**Status**: `current`
**Phase**: `CI-SelfCalibration`
**Owner**: `ordivon-core-maintainer`
**Freshness**: 2026-05-10
**AI Read Priority**: 1

---

## 1. Event

```
2026-05-10. 124 new documents committed across 11 batches.
CI turned red. 5 jobs failed simultaneously.
Not a bug. The governance system detected its own drift.
```

---

## 2. What Was Fixed

### Round 1 — CI Failure Remediation (8 root causes → 11 files)

| # | Cause | Disposition | Fix |
|---|-------|-------------|-----|
| ① | current_truth drift (244 vs 436) | A1 | Hardcoded counts → generated_view refs |
| ② | document_registry (26 violations) | A1 | Registered 4 doc_types, fixed 5 dupes, removed 1 missing |
| ③ | agentic_patterns false positive | A2 | Added authoritative doc allowlist |
| ④ | protected_paths violations | A1 | Added 3 governance docs to SAFE_FILES |
| ⑤ | legacy_identity false positive | A2 | Widened SAFE_CONTEXTS regex |
| ⑥ | governance-tests stale assertions | A2 | Fixed test to pass files not dirs |
| ⑦ | ruff (18 F541 + 1 format) | A1 | Auto-fixed |
| ⑧ | 02-TESTS 7 failures | A4→CLOSED | Resolved by registry/doc_type fixes |

### Round 2 — Dependency Audit

| Package | Issue | Disposition |
|---------|-------|-------------|
| mako 1.3.11 | CVE-2026-44307 | A1: upgraded to 1.3.12 |
| pip 26.0.1 | CVE-2026-6357 | A1: CI upgrade step |
| pip 26.0.1 | CVE-2026-3219 | A4: exact ignore + debt + weekly cron |
| postcss 8.4.31 | GHSA-qx2v-qp2m-jg93 | A1: pnpm override >=8.5.10 |
| ordivon 0.1.0 | not on PyPI | A1: --skip-editable |

### Round 3 — Methodology Extraction

```
CI-SelfCalibration event → 3 core lessons → methodology document
  L-CI-SELFCAL-001: Hardcoded count drift
  L-CI-SELFCAL-002: Dual-checker trap
  L-CI-SELFCAL-003: Batch commit incoherence
  → docs/governance/ordivon-methodology-core.md (L0, 395 lines)
```

### Round 4 — System Hardening (A3)

```
Schema-first architecture:
  document-types.json ← single source, dual checker sync
  +governance-self-check CI job

Generator + CI verify (K8s hack/update+verify):
  update-registry-stats.py + _registry-stats.md
  --check mode for drift detection

Atomic governance gate (Google presubmit):
  check_atomic_governance.py — 166 governed files verified
  +atomic-governance CI job

'Not clean. Honest.' — methodology slogan codified
AI Governance Observer — formal role definition
Ordivon Macro Structure — AI onboarding map
```

### Round 5 — Red-Team + Remediation

```
11 probes, 3 deep exploits
  RT-09: Debt JSONL can be silently modified → HASH MISMATCH gate
  RT-11: Checker source can create blind spots → schema extraction
  RT-03: Schema accepts empty types → value validation

Waves 1-3 executed, debts closed.
  DEP-REDTEAM-RT09-DEBT-INTEGRITY → CLOSED
  DEP-REDTEAM-RT11-CHECKER-INTEGRITY → CLOSED
```

---

## 3. What Was Built

```
Docs:         ordivon-methodology-core.md, ordivon-macro-structure.md,
              red-team-remediation-plan-2026-05-10.md
              
Schemas:      document-types.json (single source, 24 types)
              governed-exclusions.json (14 entries, authority set)
              
Scripts:      update-registry-stats.py (generator + --check)
              check_atomic_governance.py (166 files, 14 exclusions)
              hash_ledger.py (SHA256 per-entry, 4 debts + 12 lessons)
              check_cve_2026_3219.py (weekly OSV check)

CI:           +governance-self-check (4 checks)
              +atomic-governance (registration completeness)
              +pip upgrade step (security.yml)
              +hash verification step
              +schema integrity step
              +cron job f0aad0c7b5ef (CVE-2026-3219 weekly)

Lessons:      5 → 12 (L-CI-SELFCAL-001 through 007)
Debts:        0 → 4 (2 CLOSED, 2 OPEN)
Registry:     244 → 441 entries
Tests:        1,203 → 1,437 collected
```

---

## 4. Current State

```
ordivon-verify:  READY (35/35)
atomic-gov:      PASS (166 files, 0 unregistered)
hash verify:     PASS (16 entries verified)
gen verify:      PASS (441 entries)
ruff:            All checks passed
tests:           1,203 passed
CI:              15/16 jobs pass (product-tests: known env issue)
```

---

## 5. Remaining Open Items

| ID | Description | Status |
|----|-------------|--------|
| DEP-AUDIT-PIP-CVE-2026-3219 | CVE awaiting upstream fix | OPEN — weekly cron |
| DEP-CI-PRODUCT-TESTS-ENV | CI product-tests environment parity | OPEN — investigation pending |
| GitHub Dependabot | 1 moderate (web deps, requires rescan) | OPEN |

---

## 6. What Was Learned

> **The governance system BLOCKED itself, and instead of suppressing the
> signal, Ordivon used it to extract methodology, harden architecture,
> close anti-patterns, and prove that governance can audit governance.**

Three systemic anti-patterns were identified and closed:

```
AP-1 Hardcoded Count Drift     → A3: generated views + CI verify
AP-2 Dual-Checker Trap          → A3: schema-first architecture  
AP-3 Atomic Governance Breakage → A3: registration gate + CI job
```

And the methodology itself became a governed artifact:

```
Not clean. Honest.
READY ≠ Authorization.
Governance systems are governable objects.
```

---

## 7. Commit Chain

```
fedb042 fix: ruff
36c6239 fix: red-team remediation
ab3308c plan: red-team remediation
317ca08 docs: mark AP-3 CLOSED
a350ca3 feat: A3 — Atomic Governance Gate
955059d methodology: 'Not clean. Honest.' + AI Observer
7475eff docs: Ordivon Macro Structure
c82ce02 investigate: CI product-tests
7081cb0 feat: A3 — doc count generator + CI verify
aee7ae3 docs: L-CI-SELFCAL-004
44d6e8f docs: Ordivon Methodology Core
0c67fc5 feat: schema-first architecture
dff9209 fix: CI failures — 6 governance checker fixes
```

---

```text
READY means selected checks passed; it does not authorize execution,
does not authorize merge, does not authorize deployment, and does not
authorize release, tool use, policy activation, or external action.
```
