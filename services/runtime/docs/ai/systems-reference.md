# Ordivon Systems Reference — For AI Agents

Every system in Ordivon. Commands, purpose, substance, and how to understand it.

**Status**: CURRENT | **Date**: 2026-05-04 | **Phase**: DG-7 / EG-1

---

## 1. Checker Ecosystem (36 checkers, L3-L9)

### What It Is

A self-discovering governance checker system. Each checker lives in `checkers/<name>/`
as a self-contained package with `CHECKER.md` (YAML frontmatter) and `run.py`.
The registry auto-discovers all checkers — no manual registration.

### Commands

```bash
# Run the pr-fast baseline (12 checkers, blocks merge on failure)
uv run python scripts/run_baseline.py --pr-fast

# Run the full baseline (36 checkers, 26 hard + 10 escalation)
uv run python scripts/run_baseline.py

# Run read-only baseline (skip state-updating checkers, no JSONL writes)
uv run python scripts/run_baseline.py --read-only

# Run a single checker
uv run python checkers/<name>/run.py

# Run a specific gate by ID
uv run python -m ordivon_verify run <gate_id>

# Sync checker manifest
uv run python scripts/run_baseline.py --sync

# Show manifest
uv run python scripts/run_baseline.py --manifest
```

### Layer Map

```
L3     State Truth          [HARD]  Phase/deployment truth consistency
L3A    Current Truth        [HARD]  AGENTS.md ↔ docs consistency
L4     Coverage Governance  [HARD]  Checker declares protects_against
L4.2   Checker Maturity     [HARD]  draft→shadow→redteam→active, no self-promotion
L4.3   Owner Activation     [HARD]  Policy activation requires Owner signoff
L4.5   Entropy Telemetry    [ESC]   Measures system entropy metrics
L4.5A  Entropy Gate         [HARD]  File ceiling, import depth, growth velocity
L4A    Architecture Bound   [HARD]  Cross-boundary import detection
L5     Runtime Evidence     [HARD]  Evidence file integrity
L5A    Finance Boundary     [HARD]  Live trading language detection
L5B    Trading Fixtures     [HARD]  Trading discipline fixture validation
L5C    Coding Smoke         [HARD]  Coding discipline smoke test
L5D    Coding Fixtures      [HARD]  Coding discipline fixture validation
L5E    Protected Paths      [HARD]  Unprotected path reference detection
L5F    Dependabot Gov       [HARD]  Dependabot PR classification
L6     Document Registry    [HARD]  Document registry invariants (213 entries)
L6A    Document Freshness   [HARD]  Staleness detection
L6B    OGAP Payload         [HARD]  OGAP protocol payload validation
L6C    HAP Payload          [HARD]  HAP protocol payload validation
L7A    Verification Debt    [HARD]  Debt ledger integrity
L7B    Receipt Integrity    [HARD]  Receipt overclaim detection
L7C    Agentic Patterns     [HARD]  3 patterns: READY overclaim, C4 gate, CandidateRule promotion
L7D    Dogfood Evidence     [HARD]  Dogfood evidence integrity
L7E    Paper Dogfood Ledger [HARD]  Paper trading ledger validation
L8     Gate Manifest        [HARD]  Registry ↔ manifest consistency
L8A    Lesson Extraction    [ESC]   Lesson → CandidateRule (idempotent)
L8B    Policy Shadow        [ESC]   CandidateRule shadow evaluation
L9A    Philosophy Misuse    [HARD]  Philosophical quote verification
L9B    Philosophical Claims [HARD]  Philosophical claim validation
L9C-F  PGI Validators       [ESC]   PGI decision/evidence/failure/confidence
```

### How to Understand

- **HARD** checkers run in pr-fast. They BLOCK the PR if they fail.
- **ESCALATION** checkers run in full only. They report findings but don't block.
- **side_effects: true** checkers write JSONL ledgers or state files. They are skipped
  by `--read-only` mode. Currently 3: entropy-telemetry, lesson-extraction, policy-shadow.
- Each checker returns `CheckerResult(status, exit_code, findings, stats)`.
- The baseline runner aggregates all results and computes OVERALL: READY/DEGRADED/BLOCKED.

### How to Add a Checker

```
1. Create checkers/<name>/CHECKER.md with YAML frontmatter
2. Create checkers/<name>/run.py with def run() -> CheckerResult
3. Auto-discovered — no manual registration needed
4. Full process: docs/governance/extension-processes.md §4
```

---

## 2. Document Governance Pack (DG)

### What It Is

A self-governing documentation system. Every document in Ordivon is registered
in `docs/governance/document-registry.jsonl` (213 entries) with structured
metadata: doc_id, path, doc_type, authority, freshness, last_verified,
stale_after_days, related_docs/ledgers/receipts.

### Commands

```bash
# Check registry integrity
uv run python checkers/document-registry/run.py

# Check document freshness
uv run python checkers/document-freshness/run.py

# Read the registry (filter with jq)
cat docs/governance/document-registry.jsonl | python3 -c "
import json, sys
for line in sys.stdin:
    e = json.loads(line.strip())
    print(f\"{e['doc_id']:40s} {e.get('last_verified','?'):12s} {e.get('doc_type','?')}\")
"
```

### Document Types

```
root_context    — AGENTS.md, README.md (entry points)
governance_pack — Governance design docs (source_of_truth authority)
architecture    — Architecture specs and baselines
receipt         — Phase closure evidence (supporting_evidence authority)
runtime         — Runtime observation logs
stage_summit    — Stage closure declarations
ledger          — Structured data (JSONL): registry, debt, lessons, telemetry
schema          — JSON schemas
ai_onboarding   — Documents for AI agent consumption
product         — Product briefs, roadmaps, stage notes
```

### How to Understand

- `authority=source_of_truth`: this document MAKES claims. It is the authority.
- `authority=supporting_evidence`: this document SUPPORTS claims. It is evidence.
- `authority=current_status`: this document REPORTS current state.
- `freshness` + `last_verified` + `stale_after_days`: automatic staleness tracking.
- Every new doc MUST be registered. Unregistered docs trigger document-registry gate.

---

## 3. Ordivon Verify (PV)

### What It Is

The CLI frontend for governance verification. Wraps the checker registry and
baseline runner into a user-facing tool. Supports: all/gate run, JSON output,
external repo verification, CI integration.

### Commands

```bash
# Run all gates
uv run python scripts/ordivon_verify.py all

# Run all gates with JSON output
uv run python scripts/ordivon_verify.py all --json

# Run a specific gate
uv run python -m ordivon_verify run <gate_id>

# Run against external repo
uv run python scripts/ordivon_verify.py all \
  --root tests/fixtures/ordivon_verify_standard_external_repo \
  --config tests/fixtures/ordivon_verify_standard_external_repo/ordivon.verify.json

# Product quickstart dogfood
uv run python tests/fixtures/ordivon_verify_clean_external_repo/run_quickstart.py
```

### Signal Classification

```
READY     — All hard gates passed. No blocking issues found.
DEGRADED  — Warnings exist. Honest midpoint. Not failure.
BLOCKED   — Hard boundary violation. Cannot proceed without fix.
```

### How to Understand

- PV is the PRODUCT wedge (like kubectl for K8s). It's not the core governance OS.
- The core is the checker registry + domain models. PV is the CLI surface.
- PV-N1 through PV-N12: 12 sub-phases that built the private package.
- PV-Z: CLOSED — Ordivon Verify productization Stage Summit.

---

## 4. Entropy Governance (EG)

### What It Is

Anti-entropy system applying Lehman's Laws of Software Evolution. Measures
system metrics and enforces structural constraints to prevent uncontrolled
growth.

### Commands

```bash
# Measure entropy metrics
uv run python checkers/entropy-telemetry/run.py

# Check entropy gates (pr-fast — blocks on violation)
uv run python checkers/entropy-gate/run.py

# Read telemetry history
cat docs/governance/entropy-telemetry.jsonl | python3 -c "
import json, sys
for line in sys.stdin:
    s = json.loads(line.strip())
    m = s.get('metrics',{})
    print(f\"{s['timestamp'][:19]}  files={m.get('total_files',{}).get('value','?')}  checkers={m.get('checkers_count',{}).get('value','?')}  stale={m.get('stale_docs',{}).get('value','?')}\")
"
```

### Gates

| Gate | Threshold | Hardness |
|------|-----------|----------|
| file_ceiling | total_files < 2500 | BLOCKED |
| freshness_slo | stale_docs < 10% | DEGRADED |
| coverage_minimum | checkers/sqrt(files) > 0.5 | DEGRADED |
| growth_velocity | < 10%/month | BLOCKED |
| import_depth | max depth < 6 | BLOCKED |
| debt_ceiling | open debt < 100 | DEGRADED |

### Current State (2026-05-04)

```
total_files: 1124    (threshold: 2500 — 55% remaining)
checkers: 33         (coverage ratio: 0.98 — well above 0.5)
stale_docs: 0        (0% — all fresh)
debt_entries: 3      (well below 100)
import_depth: 2      (well below 6)
growth_velocity: 0%/mo (insufficient history)
```

---

## 5. Governance Loop (Checker→Lesson→CandidateRule→Shadow→Review)

### What It Is

The Ordivon governance learning loop. Checker findings become structured
lessons. Lessons become CandidateRule proposals. CandidateRules get shadow
evaluated. Shadow evidence informs human activation review.

### Pipeline

```
Checker finds violations (400+ across all checkers)
  ↓
Lesson recorded in lesson-ledger.jsonl (5 lessons, 2 rule_candidate type)
  ↓
CandidateRule extracted (2 drafts: CR-bcf8bbacda0e, CR-32b58468bcb5)
  ↓
Shadow evaluation (Policy Shadow Runner, 10 red-team scenarios)
  ↓
Evidence accumulation in shadow-evaluation-log.jsonl
  ↓
PolicyEvidenceGate → READY_FOR_HUMAN_ACTIVATION_REVIEW
  ↓
Human review → accept/reject
```

### Commands

```bash
# Extract lessons → CandidateRules
uv run python checkers/lesson-extraction/run.py

# Run shadow evaluation
uv run python checkers/policy-shadow/run.py

# View CandidateRule drafts
cat docs/governance/candidate-rule-drafts.jsonl

# View shadow evaluation log
cat docs/governance/shadow-evaluation-log.jsonl

# View lessons
cat docs/governance/lesson-ledger.jsonl
```

### Key Files

```
docs/governance/lesson-ledger.jsonl           — 5 lessons from checker findings
docs/governance/candidate-rule-drafts.jsonl   — 2 extracted CandidateRules
docs/governance/shadow-evaluation-log.jsonl   — Shadow evaluation results
docs/governance/lesson-extraction-log.jsonl   — Extraction idempotency log
```

### How to Understand

- Lessons are EVIDENCE, not complaints. They document what the system learned.
- CandidateRules are ADVISORY, not active. They propose what COULD become policy.
- Shadow evaluation tests rules against a red-team corpus BEFORE activation.
- The loop closes when a human reviews shadow evidence and decides to activate.

---

## 6. Checker Maturity Model

### What It Is

State machine for checker lifecycle. Inspired by Rust RFC FCP (individual
veto) and K8s KEP (graduation stages with independent review).

### States

```
draft ──→ shadow_tested ──→ red_teamed ──→ active
  ↑           ↑                ↑             ↑
  创建       Shadow评估通过    红队审查通过   Owner批准
           (独立审查者)      (独立审查者)   (不可自推)
```

### Rules

- **No self-promotion**: author ≠ changed_by for any promotion.
- **Evidence required**: each transition requires specific evidence refs.
- **Independent review**: promotion evidence must come from different person.
- **Rollback allowed**: owner can demote their own checker (active→draft).

### Commands

```bash
# Check maturity gate
uv run python checkers/checker-maturity/run.py

# Domain model tests
uv run python -m pytest tests/unit/checker_maturity/ -v
```

### Domain Model

```python
from domains.checker_maturity import (
    CheckerMaturityRecord,
    CheckerMaturityStateMachine,
    MaturityLevel,
)

# All existing checkers are grandfathered as maturity=active.
# New checkers must follow the promotion path.
```

---

## 7. Owner Activation

### What It Is

Policy activation veto system. No Policy can be activated to active_shadow
or active_enforced without the named Owner's explicit signoff.

### Rules

- `PolicyRecord.owner` must be set (not None) before activation.
- Owner must sign `policy-activation-ledger.jsonl` with action="approve".
- The signoff must come from the declared owner (not someone else).
- Owner's ❌ is absolute (Rust RFC FCP pattern).

### Commands

```bash
# Check owner gate
uv run python checkers/owner-activation/run.py
```

---

## 8. Extension Processes

### What It Is

Defined processes for extending every Ordivon layer. Each layer has a
checklist with verification gates. Not optional — gates enforce compliance.

Document: `docs/governance/extension-processes.md`

### Layers Covered

```
Universal Gates (5): Document Registration, Architecture Boundary,
                     Receipt Integrity, Entropy Gate, Freshness

Core Extension (5 steps): Design doc → Domain model → Tests →
                          Registry integration → Verification

Pack Extension (5 steps): Manifest → Domain models → Checkers →
                          Policy → CI integration

Adapter Extension (4 steps): Protocol compliance → Registry →
                             Boundary isolation → Security audit

Checker Extension (8 steps): Package → Frontmatter → run.py →
    Auto-discovery → Hardness → Red-team → Maturity promotion →
    Owner activation

Test Governance (4 gates): File exists, __post_init__ coverage,
                           No change-detector tests, Test isolation
```

### How to Understand

Every step has: checklist items + which checker validates it + BLOCKED/DEGRADED.
Skipping a step → checker flags it → PR blocked. Process is enforced, not advisory.

---

## 9. Policy Shadow Runner

### What It Is

Adversarial evaluation of CandidateRules before activation. Runs every draft
CandidateRule against a fixed corpus of 10 red-team governance scenarios.

### Commands

```bash
# Run shadow evaluation
uv run python checkers/policy-shadow/run.py

# View fixture corpus
cat checkers/policy-shadow/fixtures/shadow_cases.json
```

### Shadow Cases

```
RT-001: Clean dependabot → would_recommend_merge
RT-002: React + CI fail → would_hold
RT-003: Stale evidence → would_hold
RT-004: Human deps: title → would_escalate
RT-005: CodeQL solo → would_escalate
RT-008: Scope mismatch → no_match
RT-009: CI fail non-react → would_hold
RT-010: Unknown actor → would_escalate
RT-011: AI agent → would_escalate
GT-012: Human + test plan → would_execute
```

---

## 10. Governance Pipeline (CATLASS)

### What It Is

Ordivon's governance kernel template layer. Stage templates encode complete
governance pipelines: pre-flight checks, boundary enforcement, verification
gates, receipt generation, registry updates, and AI onboarding handoff into
one executable YAML definition.

### Commands

```bash
uv run python scripts/run_stage.py --template stage-templates/doc-governance.yaml --stage-id <id>
uv run python scripts/run_stage.py --template stage-templates/doc-governance.yaml --stage-id <id> --non-interactive
uv run python scripts/run_stage.py --template stage-templates/doc-governance.yaml --stage-id <id> --dry-run
```

### Key Files

```
stage-templates/doc-governance.yaml            — Document governance stage template
scripts/run_stage.py                           — Stage runner (pipeline executor)
```

---

## 11. Debt Ledger

### What It Is

Tracks known governance debt that is acknowledged but not yet remediated.
Debt is not failure — it's honest accounting of known gaps.

### Commands

```bash
# Check debt ledger
uv run python checkers/verification-debt/run.py

# View debt ledger
cat docs/governance/verification-debt-ledger.jsonl
```

### Current Open Debt: 3 entries

All pre-existing, classified, and tracked.

---

## Quick Command Reference (All-in-One)

```bash
# ── Verification ─────────────────────────────────
uv run python scripts/run_baseline.py --pr-fast     # PR gate (12 checkers)
uv run python scripts/run_baseline.py               # Full baseline (36 checkers)
uv run python scripts/run_baseline.py --read-only   # Read-only (skips JSONL-writing checkers)
uv run python -m ordivon_verify run <gate_id>        # Single gate

# ── Testing ──────────────────────────────────────
scripts/run_tests.sh                                 # Full test suite
uv run python -m pytest tests/unit/<domain>/ -v      # Specific domain tests

# ── Document Governance ──────────────────────────
uv run python checkers/document-registry/run.py      # Registry integrity
uv run python checkers/document-freshness/run.py     # Freshness check

# ── Entropy Governance ───────────────────────────
uv run python checkers/entropy-telemetry/run.py      # Measure entropy
uv run python checkers/entropy-gate/run.py           # Check gates

# ── Learning Loop ────────────────────────────────
uv run python checkers/lesson-extraction/run.py      # Extract CandidateRules
uv run python checkers/policy-shadow/run.py          # Shadow evaluation

# ── Maturity + Ownership ─────────────────────────
uv run python checkers/checker-maturity/run.py       # Maturity gate
uv run python checkers/owner-activation/run.py       # Owner gate

# ── Formatting ───────────────────────────────────
uv run ruff format --preview .                       # Ruff format
```

---

## Key Files Map (Updated)

```
AGENTS.md                                    ← Root entry point
docs/ai/systems-reference.md                ← THIS DOCUMENT
docs/ai/new-ai-collaborator-guide.md         ← Working guide
docs/ai/current-phase-boundaries.md          ← Phase timeline + boundaries
docs/ai/agent-output-contract.md             ← Required output format
docs/governance/extension-processes.md       ← How to extend any layer
docs/governance/entropy-governance-design.md  ← Anti-entropy system design
docs/governance/document-registry.jsonl      ← 197 registered documents
docs/governance/entropy-telemetry.jsonl      ← Entropy metrics
docs/governance/candidate-rule-drafts.jsonl  ← CandidateRule proposals
docs/governance/shadow-evaluation-log.jsonl  ← Shadow evaluation results
docs/governance/lesson-ledger.jsonl          ← Lessons from checker findings
docs/governance/verification-debt-ledger.jsonl ← Known debt tracking
docs/governance/checker-maturity-ledger.jsonl ← Maturity state transitions
docs/governance/policy-activation-ledger.jsonl ← Owner signoffs
checkers/                                    ← 33 self-contained checker packages
src/ordivon_verify/                          ← Checker registry + runner
domains/                                     ← Domain models (pure dataclasses)
scripts/run_baseline.py                      ← Baseline runner (primary entry)
scripts/ordivon_verify.py                    ← Ordivon Verify CLI
```

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Ordivon Governance OS                     │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │ Checker  │→│ Lesson   │→│Candidate │→│  Shadow    │ │
│  │ Ecosystem│  │ Ledger   │  │  Rules   │  │ Evaluation │ │
│  │ (33个)   │  │ (5条)    │  │ (2条)    │  │ (10场景)   │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────┬──────┘ │
│                                                   │        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │        │
│  │ Entropy  │  │ Maturity │  │  Owner   │        │        │
│  │Governance│  │  Model   │  │   Veto   │        │        │
│  │(L4.5/5A) │  │ (L4.2)   │  │ (L4.3)   │        │        │
│  └──────────┘  └──────────┘  └──────────┘        │        │
│                                                   ▼        │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              Human Activation Review                  │ │
│  │         (PolicyEvidenceGate → READY / BLOCKED)       │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              Extension Processes                      │ │
│  │  Core (5步) │ Pack (5步) │ Adapter (4步)              │ │
│  │  Checker (8步) │ Test (4门)                           │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```
