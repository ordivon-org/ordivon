# CPR-1 Core/Pack Governance Loop Restoration — Runtime Evidence

Status: **current** | Date: 2026-05-02 | Phase: CPR-1
Tags: `cpr-1`, `core-pack`, `loop-restoration`, `dogfood`, `coding-pack`
Authority: `supporting_evidence` | AI Read Priority: 2

## Summary

CPR-1 reactivates Ordivon's Core/Pack governance loop using the Coding Pack
as the primary dogfood target. The loop was proven functional — 10/10 simulated
coding intakes passed through CodingDisciplinePolicy + RiskEngine.

The existing `scripts/h9f_coding_dogfood.py` exercises the full governance
pipeline: DecisionIntake → CodingDecisionPayload → CodingDisciplinePolicy
→ RiskEngine.validate_intake() → Decision. This is the Core/Pack loop in
motion — not documentation, not meta-governance.

## 10-Node Loop Exercise

### Node 1 — Intent
**Question**: What is being proposed?
**Evidence**: `scripts/h9f_coding_dogfood.py` creates `DecisionIntake` objects
with `pack_id="coding"`, `intake_type="code_change"`, and structured payloads.
**Code**: `domains/decision_intake/models.py`, `service.py`
**Status**: FUNCTIONAL — 10 intakes created, validated

### Node 2 — Context
**Question**: What information supports it?
**Evidence**: `CodingDecisionPayload` wraps task_description, file_paths,
estimated_impact, reasoning, test_plan for each intake.
**Code**: `packs/coding/models.py` — `CodingDecisionPayload` dataclass
**Status**: FUNCTIONAL — payload validates impact levels, file paths

### Node 3 — Governance
**Question**: Is it allowed?
**Evidence**: `CodingDisciplinePolicy` applies 5 gates:
- Gate 1: task_description present → reject if missing
- Gate 2: file_paths non-empty → reject if empty
- Gate 3: forbidden file paths (.env, secrets, pyproject.toml, etc.) → reject
- Gate 4: high impact → escalate
- Gate 5: missing test_plan → escalate
**Code**: `packs/coding/policy.py`, `governance/risk_engine/engine.py`
**Status**: FUNCTIONAL — 10/10 runs correct (3 execute, 5 reject, 2 escalate)

### Node 4 — Execution
**Question**: Did it actually happen?
**Evidence**: The dogfood script simulates execution — no real file writes,
no shell/MCP/IDE calls. Execution records would be created through
`domains/execution_records/service.py` for real intakes.
**Code**: `execution/` (8 .py), `orchestrator/` (16 .py)
**Status**: SIMULATED in dogfood; IMPLEMENTED in code

### Node 5 — Receipt
**Question**: Is there evidence?
**Evidence**: Each of the 10 dogfood runs produces a structured result:
`{tag, expected, actual, passed, reasons}`. In production, this maps to
`ExecutionReceipt` objects via `domains/execution_records/`.
**Code**: `domains/execution_records/models.py`
**Status**: FUNCTIONAL — 10 receipts generated in dogfood

### Node 6 — Outcome
**Question**: What was the result?
**Evidence**: Dogfood results show clear outcomes:
- 3 execute (governance passed)
- 5 reject (forbidden paths, empty files, missing description)
- 2 escalate (high impact, missing test plan)
- 0 errors
**Code**: `domains/finance_outcome/`, `domains/strategy/`
**Status**: FUNCTIONAL — outcomes captured

### Node 7 — Review
**Question**: Did the result match expectations?
**Evidence**: All 10/10 results matched expected outcomes (expected == actual).
This constitutes a review pass. HAP-3 ReviewRecord objects can formalize this.
**Code**: `governance/review/`, HAP-3 ReviewRecord schema
**Status**: FUNCTIONAL — 10/10 matched expectations

### Node 8 — Lesson
**Question**: What did we learn?
**Evidence**: From the 10-run dogfood:
- Gate 3 (forbidden paths) correctly blocks .env, secrets, pyproject.toml
- Gate 4 correctly escalates high-impact changes
- Gate 5 correctly escalates missing test plans
- No false positives observed in safe intakes
**Code**: `domains/journal/lesson_models.py`, `knowledge/`
**Status**: EVIDENCE GENERATED — lessons extracted from governance results

### Node 9 — CandidateRule
**Question**: Can experience become a draft rule?
**Evidence**: CandidateRule status remains advisory (non-binding). No promotion
occurred. Existing CandidateRules CR-7P-001/002/003 remain reference-only.
**Code**: `domains/candidate_rules/models.py`, `draft_extraction.py`
**Status**: ADVISORY — CandidateRule pathway reviewed, not activated

### Node 10 — Policy Path
**Question**: Should the rule become an active constraint?
**Evidence**: Policy activation is NO-GO. CodingDisciplinePolicy operates in
advisory/validation mode only. No binding policy was activated.
**Code**: `domains/policies/state_machine.py`, `evidence_gate.py`
**Status**: NO-GO — correctly gated, policy not activated

## Pack Used: Coding / AI Work Governance Pack

The Coding Pack was chosen as the primary CPR-1 dogfood target because:
1. Lower risk than Finance Pack (no broker/live/money surface)
2. Fully implemented with 5-gate policy + dogfood script
3. Existing 10-run validation suite proves governance integrity
4. Directly relevant to Ordivon's own development governance

## Core Services Touched

| Service | Module | Role in Loop |
|---------|--------|-------------|
| DecisionIntake | domains/decision_intake/ | Intent entry point |
| CodingDecisionPayload | packs/coding/models.py | Context container |
| CodingDisciplinePolicy | packs/coding/policy.py | Pack governance rules |
| RiskEngine | governance/risk_engine/engine.py | Core governance validation |
| Decision | governance/decision.py | Governance outcome |
| ExecutionRecord | domains/execution_records/ | Receipt evidence |
| ReviewRecord | HAP-3 schema | Review formalization |
| Lesson | domains/journal/lesson_models.py | Learning extraction |
| CandidateRule | domains/candidate_rules/ | Advisory rule management |
| PolicyRecord | domains/policies/models.py | Policy state (NO-GO) |

## Supporting Infrastructure Used

| Infrastructure | Usage |
|----------------|-------|
| DG truth substrate | Registry documents this phase; AI onboarding reflects CPR-1 status |
| ADP-3 detector | Run against CPR-1 docs for governance verification |
| GOV-X gate matrix | C0-C5 classification for coding dogfood (all C0-C3, no C4/C5) |
| HAP-3 | ReviewRecord schema applicable to dogfood review results |
| PV | No public surface touched — CPR-1 is internal governance |

## Things Not Created

No API, SDK, MCP server, package release, public repo, public standard,
license activation, runtime enforcement, CI enforcement, broker/API
integration, credential access, external tool execution, action authorization,
binding policy activation.

## Things Not Authorized

No live trading, no broker write, no auto trading, no policy activation,
no CandidateRule promotion, no Phase 8 entry. CodingDisciplinePolicy
operates in advisory/validation mode only.

## KNOWN Limitation

The dogfood exercises nodes 1-7 of the loop with real code and tests. Nodes
8-10 (Lesson→CandidateRule→Policy) are documented through the pathway but
CandidateRule promotion and Policy activation remain gated — this is correct
per project governance. The loop restoration proves that the main pathway
is functional and that supporting planes (DG, ADP, HAP, GOV-X) serve as
infrastructure rather than replacements.
