# Security Platform Baseline

Status: **DOCUMENTED**
Date: 2026-04-28
Phase: 3.13
Tags: `security`, `platform`, `gates`, `codeql`, `bandit`, `gitleaks`

## 1. Purpose

Define the Security Platform as a sub-platform within the Ordivon Verification
Platform. Document which security tools are currently active, their gate
classification, and the proposed placement of future tools (CodeQL, Dependabot,
Scorecard) within the 4-tier CI gate system.

## 2. Why Security Is a Verification Platform Sub-Platform

Security tools share the same CI integration pattern as verification tools:
- Read-only analysis of code or dependencies
- Exit-code-based pass/fail
- Human-review-required for escalation findings

They differ from governance tools (RiskEngine, packs) because:
- They detect vulnerabilities, not classify governance intents
- Their output is scanner-specific, not severity-protocol uniform
- Their false positive rate is higher than governance classification

Security sits alongside L4 (Architecture), L5 (Runtime Evidence), L7 (Eval
Corpus) within the Verification Platform, not as its own top-level platform.

## 3. Current Security Gates

### 3.1 Gitleaks (Secret Detection)

| Property | Value |
|----------|-------|
| CI job | `secret-scan` in `ci.yml` |
| Trigger | Push to main, pull_request to main |
| Permissions | `contents: read`, `pull-requests: read` |
| Gate class | **Hard** — secrets in code blocks merge |
| Tool | `gitleaks/gitleaks-action@v2` |

### 3.2 Bandit (Python AST Security)

| Property | Value |
|----------|-------|
| CI job | `python-security` in `security.yml` |
| Trigger | Push to main, pull_request, weekly schedule |
| Permissions | `contents: read` |
| Gate class | **Advisory** — AST-level, may have false positives |
| Tool | `pnpm scan:security` (wraps Bandit) |

### 3.3 pip-audit (Dependency Vulnerabilities)

| Property | Value |
|----------|-------|
| CI job | `python-security` in `security.yml` |
| Trigger | Push to main, pull_request, weekly schedule |
| Permissions | `contents: read` |
| Gate class | **Advisory** — point-in-time; vulns may be patched upstream |
| Tool | `pip-audit` |

### 3.4 pip upgrade (CVE-2026-3219 Mitigation)

| Property | Value |
|----------|-------|
| CI job | `python-security` in `security.yml` |
| Purpose | Upgrade pip to patched version in CI |
| Gate class | Hard — CI must not run with vulnerable pip |

## 4. Security Gate Classification

### Hard Gate (fail → block)

| Gate | Rationale |
|------|-----------|
| Gitleaks secret scan | Secrets in code = immediate risk; must block merge |
| Pip CVE mitigation | Running CI with vulnerable pip = unacceptable |

### Escalation Gate (fail → warn, review required)

| Gate | Rationale |
|------|-----------|
| CodeQL security alerts (future) | Requires baseline tuning; false positives possible |
| Dependabot critical alerts (future) | Requires human dependency decision |

### Advisory Gate (fail → record, never block)

| Gate | Rationale |
|------|-----------|
| Bandit | Python AST patterns; moderate false positive rate |
| pip-audit | Point-in-time snapshot; vulns may be patched |
| OpenSSF Scorecard (future) | Aggregate posture; not a per-PR gate |
| Semgrep custom rules (future) | Rule-specific false positive profiles |

## 5. Proposed Gate Levels

| Gate Level | Security Tools | Trigger | Est. Time |
|-----------|---------------|---------|-----------|
| PR Fast Gate | Gitleaks | Every PR push | ~5s |
| PR Full Gate | Gitleaks, Bandit, pip-audit | Every PR push | ~60s |
| Main Branch Gate | Gitleaks, Bandit, pip-audit, CodeQL | Push to main | ~3m |
| Scheduled Deep Gate | All above + Scorecard | Weekly cron | ~5m |

## 6. Tool Placement Matrix

| Tool | PR Fast | PR Full | Main Branch | Scheduled Deep | Status |
|------|---------|---------|-------------|----------------|--------|
| Gitleaks | ✅ Hard | ✅ Hard | ✅ Hard | ✅ Hard | ✅ Adopted |
| Bandit | — | Advisory | Advisory | Advisory | ✅ Adopted |
| pip-audit | — | Advisory | Advisory | Advisory | ✅ Adopted |
| pip CVE patch | — | — | Hard | Hard | ✅ Adopted |
| CodeQL | — | — | Escalation → Hard | Escalation → Hard | 📋 Plan |
| Dependabot | — | — | Escalation | Escalation | 📋 Plan |
| OpenSSF Scorecard | — | — | — | Advisory | 📋 Plan |
| Semgrep | — | — | — | Advisory | 🔮 Evaluate later |
| Trivy | — | — | — | Advisory | 🔮 Evaluate later |
| OPA / Conftest | — | — | — | — | 🔮 Evaluate later |

## 7. Why Not All Tools Belong in PR Fast Gate

PR Fast Gate must complete in < 2 minutes. Security tools with:
- High CI runtime (CodeQL: 2-5 min)
- Moderate false positive rate (Bandit, pip-audit)
- External network dependencies (pip-audit)
- Baseline tuning required before hardening (CodeQL, Semgrep)

...should NOT block developer velocity in every PR push. They belong in Main
Branch Gate (where merge already happened) or Scheduled Deep Gate (where cost
is amortized).

**Alert fatigue risk**: If every security advisory fires on every PR, developers
learn to ignore security. The classification system (Hard → block, Escalation →
review, Advisory → record) prevents desensitization.

## 8. Evidence Requirements

Security tool outputs are evidence. For tools already in CI:
- Bandit/pip-audit: workflow log is evidence
- Gitleaks: workflow log is evidence

Future tools should follow the same pattern as Repo Governance:
- JSON output for machine readability
- Artifact upload for audit retention
- Decision recorded in workflow summary

No security tool currently writes to Ordivon Evidence Platform (ExecutionReceipt,
AuditEvent). This is acceptable — security evidence lives in CI artifacts, not
in Ordivon DB. If a security finding triggers a governance action (escalate →
Review → CandidateRule), that action IS recorded in the Evidence Platform.

## 9. Relationship to Repo Governance

Security tools and Repo Governance complement each other:

| Layer | Tool | Role |
|-------|------|------|
| Security detection | Gitleaks, Bandit, CodeQL | Find vulnerabilities |
| Governance classification | RiskEngine + CodingDisciplinePolicy | Classify whether PR is acceptable given findings |
| Security decision | Human review or policy | Accept risk, fix issue, or reject |
| Evidence | CI artifacts + AuditEvent | Traceable record |

Ordivon does not auto-fix or auto-block based on security findings alone.
Security findings inform governance classification, not replace it.

## 10. Next Steps

1. CodeQL onboarding plan (`docs/runtime/codeql-onboarding-plan.md`)
2. Dependabot configuration with governance gate
3. OpenSSF Scorecard as informational badge
4. Semgrep evaluation after CandidateRule→Policy matures
