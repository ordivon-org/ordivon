# External AI Governance Benchmark Pack v0 (EGB-1)

> **v0 / reference-only / internal comparison.** Not compliance. Not certification.
> Not endorsement. Not partnership. Not public standard.
> **Status:** OPEN — EGB-1

## Identity

EGB = **External Governance Benchmark Pack.**

EGB-1 establishes a controlled reference layer that compares Ordivon governance
concepts against public frontier-AI and AI-management frameworks from leading
organizations and standards bodies.

EGB-1 does not:
- Claim Ordivon is compliant with any external framework.
- Claim certification, endorsement, partnership, or equivalence.
- Turn external benchmarks into binding policy.
- Present external frameworks as legal advice.

## Safe-Language Clause

> External benchmark references are used for internal comparison, gap analysis,
> and governance design inspiration only. They do not imply certification,
> compliance, endorsement, partnership, equivalence, production readiness, or
> public-standard status.

## Distinction Ladder

EGB-1 distinguishes eight relationship levels:

| Level | Term | Allowed in EGB-1? |
|-------|------|-------------------|
| 1 | **Reference** | ✅ Yes — cite and summarize |
| 2 | **Inspiration** | ✅ Yes — design influence |
| 3 | **Internal mapping** | ✅ Yes — map to Ordivon concepts |
| 4 | **Gap analysis** | ✅ Yes — identify differences |
| 5 | **Internal policy candidate** | ❌ No — requires policy phase |
| 6 | **Binding policy** | ❌ No — requires governance activation |
| 7 | **Compliance claim** | ❌ No — forbidden |
| 8 | **Certification claim** | ❌ No — forbidden |

## Primary External References

### 1. OpenAI Preparedness Framework

**Source:** OpenAI Preparedness Framework (Beta), December 2023.
**Scope:** Evaluates frontier AI models for catastrophic risks across four
categories (cybersecurity, CBRN, persuasion, model autonomy) before
deployment. Defines capability thresholds (low/medium/high/critical) and
required mitigations per level.

**Key concepts:**
- Capability threshold: scorecard-based evaluation determining risk category
- Risk category: low / medium / high / critical
- Safeguards / mitigations: required controls per risk level
- Deployment gate: must pass safety evaluation before deployment
- Safety report / scorecard: documented evaluation results
- Monitoring after deployment: post-deployment surveillance

**Ordivon mapping:**
- Capability threshold → Capability Threshold Gate
- Risk category → Risk Level (R0-R5)
- Safeguards → Mitigations / Boundary Declaration
- Deployment gate → Stage Gate
- Safety report → Safety Receipt / Trust Report
- Post-deployment monitoring → Runtime Evidence / Review Record

### 2. Anthropic Responsible Scaling Policy

**Source:** Anthropic Responsible Scaling Policy (RSP), September 2023,
updated October 2024.
**Scope:** Defines AI Safety Levels (ASL-1 through ASL-4) with increasing
security and deployment requirements. Requires capability evaluations,
risk reporting, and proportional governance.

**Key concepts:**
- AI Safety Levels (ASL): scaling model (ASL-1 → ASL-4)
- Deployment standards: requirements per ASL
- Security standards: controls per ASL
- Model capability evaluation: before training and deployment
- Risk report: documented assessment
- Proportional / iterative / exportable: governance design principles

**Ordivon mapping:**
- ASL scaling → Capability-Scaled Governance / Risk Ladder
- Deployment standards → Stage Escalation
- Security standards → Boundary Declaration + NO-GO Ladder
- Capability evaluation → Evidence Gate / Closure Predicate
- Risk report → Trust Report / Stage Summit
- Proportional governance → Governance Pack Lifecycle

### 3. Google DeepMind Frontier Safety Framework

**Source:** Google DeepMind Frontier Safety Framework, May 2024.
**Scope:** Identifies "severe harm" capability thresholds for frontier
models. Defines capability identification, evaluation, monitoring,
mitigation, and deployment decision processes.

**Key concepts:**
- Severe harm capability identification: what can cause catastrophic harm
- Dangerous capability evaluation: threshold testing
- Capability monitoring: ongoing surveillance
- Mitigations: required controls
- Deployment decision process: gating mechanism
- Frontier model risk domains: CBRN, cybersecurity, autonomy

**Ordivon mapping:**
- Severe harm capability → High-impact Capability Registry
- Dangerous capability thresholds → Severe Risk Watchlist
- Capability monitoring → Runtime Evidence Checker
- Mitigations → Boundary Declaration + NO-GO
- Deployment decision → Stage Gate + Authority Impact
- Risk domains → Pack-specific risk classification

### 4. NIST AI Risk Management Framework

**Source:** NIST AI RMF 1.0, January 2023. NIST AI 600-1 Generative AI
Profile, July 2024.
**Scope:** Voluntary framework for managing AI risks across the lifecycle.
Defines four core functions (Govern, Map, Measure, Manage) and trustworthy
AI characteristics. The Generative AI Profile maps 12 risks to 13 actor
actions.

**Key concepts:**
- Govern: organizational risk culture and accountability
- Map: context and risk identification
- Measure: risk assessment and analysis
- Manage: risk treatment and monitoring
- Trustworthy AI characteristics: valid, reliable, safe, secure, resilient,
  accountable, transparent, explainable, interpretable, privacy-enhanced,
  fair with harmful bias managed
- GAI Profile: 12 risks mapped to 13 actions across AI lifecycle

**Ordivon mapping:**
- Govern → Governance Core + Document Governance Pack
- Map → CandidateRule Discovery + Architecture Checker
- Measure → Evidence Gate + Runtime Evidence Checker + Eval Corpus
- Manage → Policy Lifecycle + Review Record + Verification Baseline
- Trustworthy characteristics → Trust Report + Receipt/Debt/Gate triad
- GAI risk/action mapping → External Benchmark Layer

### 5. ISO/IEC 42001 AI Management System

**Source:** ISO/IEC 42001:2023, December 2023.
**Scope:** International standard for AI management systems. Defines
requirements for establishing, implementing, maintaining, and improving
an AI management system within an organization.

**Key concepts:**
- AI management system: organizational structure for AI governance
- Organizational accountability: defined roles and responsibilities
- Lifecycle process governance: AI system lifecycle management
- Risk and opportunity management: identification, assessment, treatment
- Continual improvement: Plan-Do-Check-Act cycle
- Documentation and auditability: evidence trails and review

**Ordivon mapping:**
- AI management system → System Documentation Governance Pack
- Organizational accountability → Ownership + Reviewer Roles
- Lifecycle governance → Phase Lifecycle + Stage Gate
- Risk/opportunity management → Risk Engine + Verification Debt
- Continual improvement → Candidate Rule → Policy feedback loop
- Documentation/auditability → Document Registry + Receipt Integrity

## Reference Posture (Repeated)

All five frameworks are used as internal comparison benchmarks only.

Ordivon does not claim:
- Compliance with OpenAI Preparedness Framework
- Compliance with Anthropic RSP
- Compliance with Google DeepMind FSF
- Compliance with NIST AI RMF
- Compliance with ISO/IEC 42001
- Certification by any organization
- Endorsement by any organization
- Partnership with any organization
- Equivalence to any framework
- Public standard status
- Production readiness based on these benchmarks

## Next Phase

EGB-2 (Benchmark Update Cadence + Source Registry) or ADP-1 (Agentic
Pattern Governance Mapping). EGB-2 establishes regular update cadence
for this benchmark pack. ADP-1 uses EGB-1 gap findings as design input.

*Phase: EGB-1 | Risk: R0 | Authority impact: current_truth only*
