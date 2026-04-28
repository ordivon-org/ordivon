# Repo Governance Pack — Architecture

Status: **DESIGN**
Date: 2026-04-28
Phase: 3.1
Tags: `architecture`, `repo-governance`, `pack`, `adapter`

## 1. Position in Core / Pack / Adapter Architecture

```
                        ┌─────────────────────┐
                        │   Ordivon Core       │
                        │   (governance/)       │
                        │   RiskEngine          │
                        │   severity protocol   │
                        └──────────┬──────────┘
                                   │ pack_policy parameter
              ┌────────────────────┼────────────────────┐
              │                    │                    │
     ┌────────┴────────┐  ┌───────┴────────┐  ┌───────┴────────┐
     │  Finance Pack    │  │  Coding Pack   │  │ Repo Gov Pack  │
     │  (trading)       │  │  (code_change) │  │  (repo_intent) │
     └────────┬────────┘  └───────┬────────┘  └───────┬────────┘
              │                    │                    │
              └────────────────────┼────────────────────┘
                                   │
                         ┌─────────┴──────────┐
                         │  Adapters           │
                         │  CLI / GHA / IDE    │
                         │  (future: MCP)      │
                         └────────────────────┘
```

Repo Governance Pack is a third Pack alongside Finance and Coding.
It uses the same severity protocol. Core does not know it exists.

## 2. Relationship to Coding Pack

The Coding Pack (`packs/coding/`) validates a single code change intent.
The Repo Governance Pack validates a repository-level workflow:

| Scope | Coding Pack | Repo Governance Pack |
|-------|------------|---------------------|
| Unit of intake | Single code change | Repository workflow (PR, task, branch) |
| Forbidden paths | Project-level config files | Protected branches, CI config, secrets |
| Risk classification | File-level impact (low/medium/high) | Workflow-level impact |
| Receipt | Governance decision | CI result + governance decision |

They are complementary: Coding Pack governs *what the AI does to files*.
Repo Governance Pack governs *how the team manages AI contributions*.

## 3. Severity Protocol

Same protocol as Finance and Coding:

```
Reason object:
  .severity: "reject" | "escalate"
  .message: str

RiskEngine.validate_intake(intake, pack_policy=RepoDisciplinePolicy())
  → GovernanceDecision(decision="execute"|"escalate"|"reject")
```

Core never imports `packs.repo_governance`. It only reads `.severity` and `.message`.

## 4. Intake → Governance → Receipt → Review → Lesson → CandidateRule Mapping

| Ordivon Concept | Repo Governance Mapping |
|-----------------|------------------------|
| Intake | CLI input: task_description, file_paths, impact, test_plan |
| Governance | RepoDisciplinePolicy → execute/escalate/reject |
| Receipt | JSON output: decision + reasons + timestamp |
| Outcome | CI result (pass/fail) |
| Review | Structured postmortem on CI failure |
| Lesson | Extracted learning from Review |
| CandidateRule(draft) | Proposed new repo governance rule |
| PolicyProposal(draft) | (Future) Proposed rule → Policy activation |

## 5. Permission Tiers

| Tier | Scope | Governance |
|------|-------|-----------|
| read | View files, diffs, logs | Default allowed |
| propose | Create PR, suggest changes | Structured Intake required |
| write | Modify non-protected files | File-level governance |
| sensitive_write | Modify configs, CI, migrations | Escalate or reject |
| policy_change | Modify governance rules, forbidden paths | Human approval required |

## 6. Evidence Model

```
Intake
  → GovernanceDecision (execute/escalate/reject + reasons)
  → CI Receipt (test results, lint results, coverage)
  → Outcome (CI pass/fail)
  → Review (postmortem on failure)
  → Lesson (extracted from Review)
  → CandidateRule(draft)
```

The runtime evidence checker (`scripts/check_runtime_evidence.py`) will be
extended to validate Repo Governance evidence chains.

## 7. Adapter Strategy

Adapters connect Ordivon governance to external tools. They are Adapter-layer
components — they cannot write Core truth directly.

| Adapter | Input | Output | Status |
|---------|-------|--------|--------|
| CLI | Command-line arguments | JSON governance decision | Phase 3.2 |
| GitHub Actions | PR metadata | CI annotation + governance decision | Future |
| IDE | Editor context | Inline governance feedback | Future |
| MCP | Tool invocation metadata | Governance classification | Future |

### Adapter Invariants

All adapters must respect:
- Adapter output is evidence, not truth.
- Adapter cannot write Core truth directly.
- Tool permission is configuration, not prompt instruction.
- Read is default; write requires explicit governance approval.
- Every adapter action produces a Receipt.

## 8. Execution Boundary

The Repo Governance Pack does NOT execute:

- No shell commands
- No file writes
- No git operations (commit, push, merge)
- No CI trigger
- No IDE modification

It only *classifies*. Execution is the responsibility of the human or the
CI system, informed by the governance decision.

## 9. Relationship to Existing Artifacts

| Artifact | Relationship |
|----------|-------------|
| `governance/risk_engine/engine.py` | Unchanged — receives pack_policy parameter |
| `packs/coding/policy.py` | Complementary — governs single changes, not workflows |
| `scripts/check_runtime_evidence.py` | Will be extended with Repo Gov evidence checks |
| `scripts/audit_runtime_evidence_db.py` | Will validate Repo Gov evidence chains |
| `docs/architecture/repo-governance-baseline.md` | The 12-layer matrix — this Pack fills L8/L9/L11 gaps |
