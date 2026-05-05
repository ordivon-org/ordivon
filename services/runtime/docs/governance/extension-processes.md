# Ordivon Extension Processes

Ordivon is a governance OS with a strict Core/Pack/Adapter ontology.
Every extension must follow a defined process, verified by automated gates.

**Authority**: source_of_truth
**Status**: current
**Phase**: DG-1 (Extension Process Deployment)

---

## 0. Universal Gates (apply to ALL extensions)

Before any extension — regardless of layer — these gates must pass:

### Gate U1: Document Registration

```
Every new file created → MUST be registered in document-registry.jsonl
  - doc_id (unique)
  - path
  - doc_type (valid from VALID_DOC_TYPES)
  - authority
  - last_verified (date)
  - stale_after_days

Validated by: document-registry checker (LL6, pr-fast)
```

### Gate U2: Architecture Boundary

```
New imports across Core/Pack/Adapter boundaries → MUST follow boundary rules:
  Core → Pack: NEVER (circular dependency)
  Core → Adapter: NEVER
  Pack → Core: ALLOWED (packs depend on core)
  Adapter → Core: ALLOWED
  Pack → Adapter: NEVER
  Adapter → Pack: NEVER

Validated by: architecture-boundaries checker (LL4A, pr-fast)
```

### Gate U3: Receipt Integrity

```
Every extension that changes >5 files → MUST produce a receipt at docs/runtime/
Receipt must NOT:
  - Claim "Ruff clean" without qualifying scope
  - Claim "all tests pass" without evidence
  - Claim "ready for production" without human review

Validated by: receipt-integrity checker (LL7B, pr-fast)
```

### Gate U4: Entropy Gate

```
Adding new files → must not exceed file ceiling (2500)
Adding new imports → must not exceed max depth (6)

Validated by: entropy-gate checker (LL4.5A, pr-fast)
```

### Gate U5: Freshness

```
Every registered document → must have last_verified within stale_after_days
Existing docs modified → must update last_verified

Validated by: document-freshness checker (LL6A, full)
```

---

## 1. Core Extension

### What Counts as Core

```
src/ordivon_verify/     ← checker registry + runner (THE core)
domains/                ← domain models (pure Python dataclasses)
shared/                 ← shared utilities (time, IDs, serialization)
```

Core is the governance engine. Core changes affect ALL packs and adapters.

### Process

#### Step 1: Design Document

```
If the change adds a new domain model or registry behavior:
  → Create docs/governance/<new-concept>-design.md
  → Register in document-registry.jsonl as authority=source_of_truth

If the change is a bug fix or refactor:
  → Skip to Step 2
```

#### Step 2: Domain Model Checklist

```
New domain model must be:
  □ Pure Python dataclass — no ORM, no DB, no side effects
  □ Immutable (frozen=True) or explicitly justified as mutable
  □ __post_init__ validates invariants
  □ No import from packs/, apps/, or external adapters
  □ 100% unit test coverage on __post_init__ validation paths
  □ Has a corresponding test file in tests/unit/<domain>/

Validated by: runtime-evidence checker (LL5, pr-fast)
             architecture-boundaries (LL4A)
```

#### Step 3: Test Requirement

```
Every new domain model:
  □ test_<model>_construction_valid()     — happy path
  □ test_<model>_construction_invalid()   — rejection paths
  □ test_<model>_immutability()           — frozen can't mutate
  □ test_<model>_invariants()             — all __post_init__ paths
```

#### Step 4: Registry Integration

```
If the new model is used by the checker registry:
  □ Update src/ordivon_verify/checker_registry.py
  □ All new public methods have docstrings
  □ Regression test added to tests/unit/product/

If the new model is a standalone domain:
  □ No registry changes needed
```

#### Step 5: Verification

```
Before merge:
  □ pr-fast: 12/12 PASS (includes architecture + document-registry)
  □ Full baseline: 26/26 HARD PASS + 7 escalation
  □ Read-only baseline: 26/26 HARD PASS (--read-only, no JSONL writes)
  □ New tests pass: tests/unit/<domain>/
  □ No new cross-boundary imports introduced
```

---

## 2. Pack Extension

### What Counts as a Pack

```
packs/coding/     ← coding discipline policy (active)
packs/finance/    ← finance governance (DEFERRED, Phase 8)
```

A Pack is a domain-specific governance module. Packs:
- Depend on Core (can import from domains/, shared/, src/ordivon_verify/)
- Cannot depend on other Packs
- Cannot depend on Adapters
- Define their own policies, checkers, and fixtures

### Process

#### Step 1: Pack Manifest

```
Create packs/<pack-name>/PACK.md:
  ---
  pack_id: <name>
  display_name: <Human Readable>
  status: draft | active | deferred | deprecated
  phase: Phase-X
  depends_on_core: true
  depends_on_packs: []
  protects_against: "<what governance risk does this pack mitigate>"
  authority: source_of_truth
  ---

Register PACK.md in document-registry.jsonl
```

#### Step 2: Domain Models

```
packs/<name>/models.py:
  □ Pure dataclasses (same rules as Core domain models)
  □ No ORM, no DB, no external API calls
  □ Import ONLY from: domains/, shared/, typing
  □ Unit tests in tests/unit/packs/<name>/
```

#### Step 3: Checker(s)

```
packs/<name>/checkers/<checker-name>/:
  □ CHECKER.md with YAML frontmatter
  □ run.py with def run() -> CheckerResult
  □ fixtures/ directory with test cases
  □ Declares: gate_id, layer, hardness, profiles

Checker must validate at least one of:
  □ Pack-specific invariants (e.g., "no live trading language")
  □ Pack-specific fixtures (e.g., "trading discipline test data valid")
  □ Pack-specific evidence (e.g., "paper dogfood ledger integrity")
```

#### Step 4: Policy (if applicable)

```
packs/<name>/policy.py:
  □ PolicyRecord subclass or standalone PolicyRecord
  □ Declares: scope, state (draft until activated), risk
  □ Has PolicyEvidenceRefs linking to checker findings
  □ Rollback plan defined BEFORE activation

Policy activation path:
  draft → proposed → approved → active_shadow → active_enforced

  Active states require:
    □ Owner is named (PolicyRecord.owner is not None)
    □ Owner signed off in policy-activation-ledger.jsonl
    □ Owner's ❌ is absolute (Rust RFC FCP pattern)

  Validated by: owner-activation checker (L4.3, full)
```

#### Step 5: CI Integration

```
For active packs:
  □ Dedicated CI job in .github/workflows/ci.yml
  □ Runs pack checkers + pack tests

For deferred packs (e.g., finance):
  □ Checkers still run (prevent evidence rot)
  □ Checkers run in full profile only (not pr-fast)
  □ No dedicated CI job — runs as part of full baseline
```

---

## 3. Adapter Extension

### What Counts as an Adapter

```
Adapters bridge Ordivon governance to external systems. Defined by:
  - OGAP (Ordivon Governance Adapter Protocol)
  - HAP (Harness Adapter Protocol)

Not yet implemented. Current state: protocol definition only.
```

### Process (when ready)

```
Step 1: Protocol Compliance
  □ Adapter implements the complete OGAP or HAP interface
  □ All required payload types are validated
  □ Adapter declares its integration level (1-5)

Step 2: Adapter Registry
  □ Register in adapters/ directory
  □ ADAPTER.md with frontmatter (adapter_id, protocol, version)
  □ Declares: external system, auth requirements, rate limits

Step 3: Boundary Isolation
  □ Adapter CANNOT import from packs/
  □ Adapter CAN import from domains/, shared/
  □ Adapter MUST NOT have side effects in Core data

Step 4: Security Audit
  □ Credential handling validated by protected-paths checker
  □ No secrets in adapter code
  □ External API calls wrapped in timeout + retry logic
```

---

## 4. Checker Extension

### The most mature extension process in Ordivon.

#### Step 1: Create Checker Package

```
checkers/<checker-name>/
├── CHECKER.md      ← YAML frontmatter + markdown body
├── run.py          ← def run() -> CheckerResult
└── fixtures/       ← test inputs (optional)
```

#### Step 2: CHECKER.md Frontmatter

```yaml
---
gate_id: <unique_id>           # lowercase_underscore
display_name: <Human Readable>
layer: <L# or L#A>             # governance layer
hardness: hard|escalation      # hard = blocks, escalation = advisory
purpose: <one-line description>
protects_against: "<what risk>"
profiles: ['pr-fast'] | ['full'] | ['pr-fast', 'full']
timeout: 30                    # seconds
tags: [tag1, tag2]
---
```

#### Step 3: run.py Contract

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class CheckerResult:
    status: str       # "pass" | "fail"
    exit_code: int    # 0 = pass, 1 = fail
    findings: list    # human-readable findings
    stats: dict       # structured metrics

def run() -> CheckerResult:
    # Pure logic — no side effects beyond reading files
    ...
```

#### Step 4: Auto-Discovery

```
Checker is automatically discovered by src/ordivon_verify/checker_registry.py.
No manual registration needed.

The registry scans checkers/*/CHECKER.md and:
  - Adds to bundled_manifest
  - Updates usage telemetry (.usage.json)
  - Includes in pr-fast or full baseline based on profiles

Validated by: gate-manifest checker (LL8, pr-fast)
```

#### Step 5: Hardness Decision

```
Choose hardness:
  hard:       "This checker catches things that MUST NOT happen"
              → pr-fast, blocks merge on failure
              → Example: document-registry, receipt-integrity

  escalation: "This checker catches things that SHOULD BE REVIEWED"
              → full only, advisory report
              → Example: lesson-extraction, policy-shadow, entropy-telemetry
```

#### Step 6: Checker Red-Teaming

```
Before declaring a checker "ready":
  □ Run against KNOWN-GOOD state: should produce 0 findings
  □ Run against KNOWN-BAD fixture: should detect the violation
  □ Run against FALSE-POSITIVE fixture: should NOT flag safe context
  □ Document false positive rate and false negative rate
```

#### Step 7: Maturity Promotion (NEW — Rust RFC + K8s KEP inspired)

```
Checker maturity stages:
  draft → shadow_tested → red_teamed → active

Promotion rules (enforced by checker-maturity gate, L4.2):
  □ draft → shadow_tested: requires shadow evaluation log entry
    with ALL red-team cases producing correct verdicts.
    Evidence source: shadow-evaluation-log.jsonl
    Reviewer MUST be different from author (no self-promotion).

  □ shadow_tested → red_teamed: requires red-team review receipt.
    Reviewer MUST be different from author.

  □ red_teamed → active: requires owner approval signoff +
    Policy Shadow Runner assessment.
    Both must come from someone other than the author.

  □ Every transition recorded in checker-maturity-ledger.jsonl
    with: checker_id, from_level, to_level, changed_by, evidence_refs.

Demotion (emergency rollback):
  □ active → draft: any level, owner can self-demote.
    Requires rollback receipt.

Validated by: checker-maturity checker (L4.2, pr-fast)
```

#### Step 8: Policy Owner Activation (NEW)

```
Policy activation to active_shadow or active_enforced requires:

  □ 1. PolicyRecord.owner is not None (named owner exists)
  □ 2. Owner has signed activation in policy-activation-ledger.jsonl
       with action="approve" or action="activate"
  □ 3. Signoff comes from the declared owner (not someone else)

  Rust RFC pattern applied: individual owner has ❌ veto power.
  No activation without the Owner's explicit ✅.

Validated by: owner-activation checker (L4.3, full)
```

---

## 5. Test Governance

### Test Layers

```
Layer 1: Unit Tests (tests/unit/)
  - One test file per domain module
  - Pure logic — no DB, no network, no file system
  - Coverage requirement: 100% on __post_init__ validation paths

Layer 2: Integration Tests (tests/integration/)
  - Cross-domain interaction tests
  - May use temp files, in-memory DB
  - Coverage requirement: all checker run() paths

Layer 3: Fixture Tests (within checker packages)
  - Project-specific test fixtures
  - Validates checker against known inputs
  - Coverage requirement: all decision branches in the checker
```

### Test File Template

```python
"""Tests for <module> — domain invariants and red-team cases."""

import pytest
from domains.<domain>.<module> import <Model>


class Test<Model>Construction:
    """Happy path: valid inputs produce valid instances."""

    def test_minimal_construction(self):
        ...

    def test_full_construction(self):
        ...


class Test<Model>Invariants:
    """Every __post_init__ validation path is tested."""

    def test_rejects_empty_required_field(self):
        with pytest.raises(ValueError, match="requires"):
            ...

    def test_rejects_invalid_enum_value(self):
        with pytest.raises(ValueError):
            ...


class Test<Model>RedTeam:
    """Adversarial inputs — boundary cases and edge conditions."""

    def test_extreme_values(self):
        ...

    def test_unicode_injection(self):
        ...
```

### Test Governance Gates

```
Gate T1: Test File Exists
  Every domain/*/models.py → must have tests/unit/<domain>/test_*.py
  Validated by: architecture-boundaries (implicit — missing test =
                not a boundary violation, but a governance gap)

Gate T2: Test Covers __post_init__
  Every __post_init__ with raise → must have a test that triggers it
  NOT YET AUTOMATED — manual review

Gate T3: No Change-Detector Tests
  Tests must assert invariants, not snapshots
  Validated by: code review (not yet automated)
  Example of FORBIDDEN test: assert len(models) == 17
  Example of CORRECT test: assert all(m.context_length > 0 for m in models)

Gate T4: Test Isolation
  Unit tests must not depend on:
    □ File system state (use tmp_path)
    □ Environment variables (use monkeypatch)
    □ Network (use mocks)
    □ Database (use in-memory SQLite if needed)
  Validated by: test runner (non-hermetic tests fail in CI)
```

---

## 6. Process Governance (Meta)

### This document is self-governing

```
extension-processes.md
  → Registered in document-registry.jsonl
  → Has last_verified + stale_after_days
  → Validated by: document-freshness checker
  → Violations of this process → create verification debt
```

### When a process step is skipped

```
If an extension is merged without following this process:
  1. receipt-integrity checker flags missing evidence
  2. document-registry checker flags unregistered files
  3. architecture-boundaries checker flags cross-boundary violations
  4. → Debt entry created in verification-debt-ledger.jsonl
  5. → Lesson extracted for learning loop
```

### Process evolution

```
This document is NOT frozen. To change a process:
  1. Propose change as CandidateRule
  2. Run through Policy Shadow evaluation
  3. Human review
  4. Update this document + update last_verified
```
