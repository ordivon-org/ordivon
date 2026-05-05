# Agentic Pattern Source Intake & Pattern Seed Ledger (ADP-1)

> **v0 / internal mapping / reference-only.** Not binding policy. Not compliance.
> **Phase:** ADP-1 | **Risk:** AP-R0 | **Authority:** current_truth only

## Purpose

This ledger records every source that feeds into ADP-1 pattern discovery.
It is source-ledger-first: no pattern is defined until its source seeds are
recorded here. Each entry tracks freshness status, key concepts, pattern
seeds extracted, and overclaim warnings.

## Source Intake Entries

### Internal Ordivon Sources

#### SRC-001: OGAP-Z Stage Summit + Closure
- **Source type:** internal Ordivon
- **Path:** `docs/product/ordivon-governance-adapter-protocol-stage-summit-ogap-z.md`, `docs/runtime/ogap-foundation-closure-ogap-z.md`
- **Version/date:** 2026-05-01
- **Freshness:** verified-current (within Ordivon repo)
- **Key concepts:** Evidence/Authority separation, READY≠authorization, can_X≠may_X, valid payload≠approved action, adapter compatibility≠governed-approved, 6 governance decisions (READY/DEGRADED/BLOCKED/HOLD/REJECT/NO-GO)
- **Pattern seeds:** Capability-to-Authorization Collapse, READY Overclaim, Evidence Laundering, Credential Capability Confusion
- **Ordivon translation:** OGAP protocol boundaries → pattern guardrails
- **Overclaim warning:** "OGAP does not claim approval" — this is a denial, not a claim

#### SRC-002: HAP-1 Docs + Schemas + Fixtures
- **Source type:** internal Ordivon
- **Path:** `docs/architecture/harness-adapter-protocol-hap-1.md`, `docs/runtime/hap-foundation-hap-1.md`, `src/ordivon_verify/schemas/hap-*.schema.json`, `examples/hap/`
- **Version/date:** 2026-05-02
- **Freshness:** verified-current
- **Key concepts:** 10-object model (HarnessAdapterManifest through HarnessReviewRecord), capability≠authorization, task request≠approval, receipt≠approval, evidence≠approval, READY≠execution authorization, risk levels (read_only/workspace_write/shell/external_side_effect), can_read_credentials
- **Pattern seeds:** Shell Risk Escalation, Credential Capability Confusion, External Side-effect Drift, Permission Rule Drift, Protected Path Violation, Scope Creep, Approval Fatigue
- **Ordivon translation:** HAP capability surface → pattern risk classification
- **Overclaim warning:** HAP schemas are prototype/v0 only

#### SRC-003: EGB-1 Benchmark Pack
- **Source type:** internal Ordivon
- **Path:** `docs/governance/external-ai-governance-benchmark-pack-egb-1.md`, `docs/governance/external-ai-governance-benchmark-matrix-egb-1.md`, `docs/governance/external-ai-governance-gap-analysis-egb-1.md`
- **Version/date:** 2026-05-02
- **Freshness:** verified-current (internal docs); EGB-SOURCE-FRESHNESS-001 open for external source versions
- **Key concepts:** 5 external frameworks mapped, 18 Ordivon concepts cross-referenced, 7 Ordivon-native innovations without external precedent, 6 gaps identified
- **Pattern seeds:** External Benchmark Overclaim, Current Truth Drift, Capability-to-Authorization Collapse, Baseline Debt Masking
- **Ordivon translation:** External framework concepts → Ordivon control mapping
- **Overclaim warning:** EGB-1 is reference-only; compliance/certification not claimed

#### SRC-004: Verification Debt Ledger
- **Source type:** internal Ordivon
- **Path:** `docs/governance/verification-debt-ledger.jsonl`
- **Version/date:** 2026-05-02
- **Freshness:** verified-current
- **Key concepts:** Debt registration discipline, category classification (skipped_verification, pre_existing_tooling_debt, checker_degradation, etc.), severity levels, open/closed lifecycle
- **Pattern seeds:** Baseline Debt Masking, Test Omission, Current Truth Drift
- **Ordivon translation:** Debt ledger → pattern debt tracking
- **Overclaim warning:** Debt entries are evidence, not authorization

#### SRC-005: Ordivon Governance Controls (Composite)
- **Source type:** internal Ordivon
- **Path:** Phase execution history, Stage Summits, pr-fast baseline, coverage governance, receipt integrity, architecture checker
- **Version/date:** ongoing
- **Freshness:** verified-current
- **Key concepts:** Stage Gate, Closure Predicate, NO-GO Ladder, Boundary Confirmation, Authority Impact, Risk Level, Runtime Evidence, Execution Receipt, Review Record, CandidateRule (advisory), Document Registry, New AI Context Check, Public Wedge Audit
- **Pattern seeds:** Review Bypass, CandidateRule Premature Promotion, Baseline Debt Masking, Instruction Truncation, Current Truth Drift
- **Ordivon translation:** Native controls → pattern detection and response
- **Overclaim warning:** CandidateRule is advisory only

### External AI Governance Benchmark Sources

#### SRC-006: OpenAI Preparedness Framework v2
- **Source type:** external AI governance benchmark
- **Version/date:** v2, external source update date 2025-04-15
- **Freshness:** verified-current (source freshness checked during ADP-1)
- **Key concepts:** Capability threshold evaluation, risk categories (low/medium/high/critical), safeguards per level, deployment gate, safety scorecard, post-deployment monitoring
- **Pattern seeds:** Capability-to-Authorization Collapse, Shell Risk Escalation, Approval Fatigue
- **Ordivon translation:** Capability threshold → AP risk ladder; deployment gate → Stage Gate
- **Overclaim warning:** Reference only. Not OpenAI-compliant. Not endorsed by OpenAI.

#### SRC-007: Anthropic Responsible Scaling Policy v3.x
- **Source type:** external AI governance benchmark
- **Version/date:** v3.0 (2026-02-24), v3.1 text updates
- **Freshness:** verified-current (source freshness checked during ADP-1)
- **Key concepts:** AI Safety Levels (ASL-1 through ASL-4), deployment standards per ASL, security standards per ASL, model capability evaluation, proportional/iterative/exportable governance
- **Pattern seeds:** Capability-to-Authorization Collapse, Permission Rule Drift, Approval Fatigue
- **Ordivon translation:** ASL scaling → AP risk ladder; proportional governance → Governance Pack Lifecycle
- **Overclaim warning:** Reference only. Not Anthropic-compliant. Not endorsed by Anthropic.

#### SRC-008: Google DeepMind Frontier Safety Framework
- **Source type:** external AI governance benchmark
- **Version/date:** Initial May 2024, continuously updated
- **Freshness:** verified-current (source freshness checked during ADP-1)
- **Key concepts:** Severe harm capability identification, dangerous capability evaluation, capability monitoring, mitigations, deployment decision process, frontier risk domains
- **Pattern seeds:** Shell Risk Escalation, External Side-effect Drift, Evidence Laundering
- **Ordivon translation:** Severe harm capability → High-impact Capability Registry; deployment decision → Stage Gate + Authority Impact
- **Overclaim warning:** Reference only. Not DeepMind-compliant.

#### SRC-009: NIST AI RMF 1.0 + Generative AI Profile
- **Source type:** external AI governance benchmark
- **Version/date:** RMF 1.0 (Jan 2023), GAI Profile (Jul 2024), RMF revision in progress
- **Freshness:** verified-current (source freshness checked during ADP-1)
- **Key concepts:** Govern/Map/Measure/Manage, 9 trustworthy AI characteristics, GAI Profile: 12 risks mapped to 13 actions
- **Pattern seeds:** Evidence Laundering, Review Bypass, Current Truth Drift, Test Omission
- **Ordivon translation:** Govern→Governance Core; Map→CandidateRule; Measure→Evidence Gate; Manage→Policy Lifecycle
- **Overclaim warning:** Reference only. Not NIST-compliant.

#### SRC-010: ISO/IEC 42001:2023
- **Source type:** external AI governance benchmark
- **Version/date:** 2023-12
- **Freshness:** verified-current
- **Key concepts:** AI management system, organizational accountability, lifecycle process governance, risk/opportunity management, continual improvement (PDCA), documentation/auditability
- **Pattern seeds:** Current Truth Drift, Baseline Debt Masking, Review Bypass
- **Ordivon translation:** Management system → Document Governance Pack; auditability → Receipt Integrity + Document Registry
- **Overclaim warning:** Reference only. Not ISO-compliant. Not ISO-certified.

### Coding-Agent / Harness / Tool-Surface Sources

#### SRC-011: OpenAI Codex CLI Permissions Model
- **Source type:** coding-agent documentation
- **Version/date:** Codex CLI docs (observed 2026-05)
- **Freshness:** freshness-pending (observed version; official latest not confirmed)
- **Key concepts:** Permission levels (allow/ask/deny), sandbox modes, tool allowlists, workspace boundaries, credential access controls
- **Pattern seeds:** Permission Rule Drift, Approval Fatigue, Credential Capability Confusion, Protected Path Violation
- **Ordivon translation:** allow/ask/deny → HarnessBoundaryDeclaration; sandbox → risk_level
- **Overclaim warning:** Codex permission model is a product feature, not a governance standard. Reference only.

#### SRC-012: Claude Code Permissions + Settings
- **Source type:** coding-agent documentation
- **Version/date:** Claude Code docs (observed 2026-05)
- **Freshness:** freshness-pending
- **Key concepts:** Permission modes, tool gates, CLAUDE.md instruction file, workspace trust
- **Pattern seeds:** Instruction Truncation, Permission Rule Drift, Scope Creep, Protected Path Violation
- **Ordivon translation:** CLAUDE.md → New AI Context Check; tool gates → HarnessBoundaryDeclaration
- **Overclaim warning:** Reference only. Not Anthropic-endorsed.

#### SRC-013: MCP Authorization Specification
- **Source type:** MCP/tooling documentation
- **Version/date:** MCP spec (observed 2026-05)
- **Freshness:** freshness-pending
- **Key concepts:** Tool authorization, capability declaration, server trust model, proxy/transport authorization, confused deputy risks
- **Pattern seeds:** MCP Tool Injection, Credential Capability Confusion, External Side-effect Drift, Permission Rule Drift
- **Ordivon translation:** MCP authorization → OGAP capability-manifest + HAP HarnessCapability
- **Overclaim warning:** Reference only. Not MCP-spec-compliant.

#### SRC-014: GitHub Copilot Agent Firewall / Allowlist
- **Source type:** coding-agent documentation
- **Version/date:** Copilot docs (observed 2026-05)
- **Freshness:** freshness-pending
- **Key concepts:** Agent firewall rules, file path allowlists, tool restrictions, org-level policy
- **Pattern seeds:** Protected Path Violation, Permission Rule Drift, Shell Risk Escalation
- **Ordivon translation:** Firewall rules → Architecture Checker + Protected Path detection
- **Overclaim warning:** Reference only. Not GitHub-endorsed.

## Summary Statistics

| Category | Count | Freshness-verified | Freshness-pending |
|----------|-------|-------------------|-------------------|
| Internal Ordivon | 5 | 5 | 0 |
| External AI governance | 5 | 5 | 0 |
| Coding-agent / tool-surface | 4 | 0 | 4 |
| **Total** | **14** | **10** | **4** |

## Pattern Seed Frequency

| Pattern Seed | Source Count | Top Sources |
|-------------|-------------|-------------|
| Capability-to-Authorization Collapse | 4 | SRC-001, 002, 006, 007 |
| Permission Rule Drift | 5 | SRC-002, 007, 011, 012, 013 |
| Credential Capability Confusion | 4 | SRC-001, 002, 011, 013 |
| Shell Risk Escalation | 4 | SRC-002, 006, 008, 014 |
| External Side-effect Drift | 3 | SRC-002, 008, 013 |
| Current Truth Drift | 5 | SRC-003, 004, 005, 009, 010 |
| Baseline Debt Masking | 4 | SRC-003, 004, 005, 010 |
| Review Bypass | 3 | SRC-005, 009, 010 |
| Evidence Laundering | 3 | SRC-001, 008, 009 |
| Approval Fatigue | 3 | SRC-002, 006, 011 |

*Phase: ADP-1 | Source-ledger-first. Patterns defined in taxonomy doc.*
