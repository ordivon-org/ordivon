# External AI Governance Gap Analysis (EGB-1)

> **v0 / reference-only.** Identifies gaps between Ordivon governance and
> external benchmarks. Gaps are observations, not defects. Some gaps reflect
> Ordivon-native innovations without external precedent.

## 1. Gaps: Ordivon vs External Benchmarks

### 1.1 Explicit Capability-Scaled Governance

**Gap:** Anthropic RSP and DeepMind FSF define explicit capability levels
(ASL-1→4, capability thresholds) that gate deployment. Ordivon's risk
ladder (R0-R5) is implicit in phase design but not formalized as a
capability-scaled governance system.

**Severity:** Medium
**Impact:** Ordivon cannot currently assert that governance requirements
scale with system capability. Risk levels exist but the mapping from risk
to required controls is not systematized.

**Recommendation:** Formalize Capability-Scaled Governance in a future
GOV-X phase. Define explicit control requirements per risk level.

### 1.2 Deployment Authorization Process

**Gap:** OpenAI PF, Anthropic RSP, and DeepMind FSF all define explicit
deployment authorization processes. Ordivon's Stage Gate + Authority
Impact are documentation fields, not process steps.

**Severity:** Low
**Impact:** Ordivon gates are phase-local and verification-driven. External
frameworks typically require organizational sign-off processes. This gap
is acceptable at Ordivon's current maturity but would become a blocker
before any production deployment.

**Recommendation:** Keep Authority Impact as a documentation field for
now. Formalize deployment authorization in a future phase when production
deployment is in scope.

### 1.3 Systematic Risk Taxonomy

**Gap:** DeepMind FSF defines systematic risk domains (CBRN, cybersecurity,
autonomy). NIST AI RMF defines trustworthy AI characteristics. Ordivon
lacks a systematic risk taxonomy — risks are classified per-phase but
not cross-referenced.

**Severity:** Medium-Low
**Impact:** Ordivon's risk classification is domain-specific (Finance,
Coding, Document). Cross-domain risk patterns may be missed.

**Recommendation:** Create a cross-domain risk taxonomy in a future
GOV-X phase. Map existing phase-level risks to a common taxonomy.

### 1.4 Post-Deployment Monitoring

**Gap:** OpenAI PF and DeepMind FSF define explicit post-deployment
monitoring requirements. Ordivon's Runtime Evidence Checker provides
ongoing verification but lacks post-deployment-specific surveillance.

**Severity:** Low
**Impact:** Post-deployment monitoring is not currently in Ordivon's
scope (no deployments exist). This gap is acceptable at current maturity.

**Recommendation:** Defer until production deployment is in scope.

### 1.5 Organizational Accountability

**Gap:** ISO 42001 requires defined organizational accountability
structures. NIST RMF Govern function expects organizational risk culture.
Ordivon's accountability is per-document (owner field) and per-phase
(reviewer roles), not organizational.

**Severity:** Low
**Impact:** Acceptable for a project-scale governance system. Would be
a gap for enterprise adoption.

**Recommendation:** Defer. Not in current scope.

### 1.6 External Audit Trail

**Gap:** ISO 42001 requires auditability of management system decisions.
NIST RMF Manage function expects auditable risk treatment decisions.
Ordivon's Receipt Integrity + Document Registry provide internal
auditability but not external (third-party) auditability.

**Severity:** Low
**Impact:** Ordivon's evidence trails are machine-checkable but not
designed for external auditor consumption. Acceptable at current maturity.

**Recommendation:** Keep internal auditability as-is. Consider external
audit trail formatting in a future enterprise pack phase.

## 2. Ordivon-Native Innovations (No External Precedent)

These concepts have no equivalent in any external framework. They are
Ordivon-unique innovations:

| Concept | Why No External Equivalent | Value |
|---------|---------------------------|-------|
| **Closure Predicate** | External frameworks define deployment gates but not phase-level closure checklists | Prevents "done creep" — phase can only close when all conditions are met |
| **NO-GO Ladder** | External frameworks define risk levels but not permanent prohibitions | Prevents boundary erosion — some actions are permanently out of scope |
| **CandidateRule → Policy** | External frameworks have policy but not the advisory → binding lifecycle | Allows observation before enforcement; prevents premature policy activation |
| **New AI Context Check** | No external framework accounts for AI agents reading governance docs | Prevents AI misinterpretation of project state, phase status, authorization levels |
| **Public Wedge Audit** | External frameworks don't address public/private code separation | Enables open-source governance tools without exposing private core |
| **Architecture Checker** | External frameworks define principles, not machine-enforced boundary checks | Machine-verifiable architecture boundaries; cannot accidentally violate Core/Pack separation |
| **Coverage Governance** | External frameworks define scope but not checker-coverage contracts | Every checker declares universe, discovery method, exclusions — prevents "passes but misses everything" |

## 3. Strengths: Where Ordivon Exceeds Benchmarks

| Area | Ordivon Strength | External Weakness |
|------|-----------------|-------------------|
| Machine-enforceable gates | pr-fast baseline runs 12 gates automatically | External frameworks are primarily process documents |
| Evidence-grounded trust | Trust Report is computed from receipts, not declared | External frameworks rely on self-reported risk assessments |
| Receipt/Debt/Gate triad | Every action has receipt, debt declaration, gate status | No external framework ties these three together |
| Phase-level precision | Each phase has explicit Allowed/Forbidden/Verification | External frameworks define organization-level policy |
| Dogfood-first verification | Governance is proven on itself before being offered externally | External frameworks are designed for others, not self-applied |
| AI-native design | Governance docs are written for AI agents to read and execute | External frameworks target human readers |

## 4. Recommended Future Phases from Gap Analysis

| Priority | Phase | Rationale |
|----------|-------|-----------|
| High | ADP-1 | Agentic Pattern Governance — EGB-1 gap findings inform pattern design |
| Medium | GOV-X | Capability-Scaled Governance + Risk Taxonomy formalization |
| Medium | EGB-2 | Benchmark update cadence + source registry |
| Low | Enterprise Pack | Organizational accountability, external audit trail |
| Deferred | Production Deployment | Post-deployment monitoring, deployment authorization process |

## 5. Safe-Language Confirmation

EGB-1 confirms:
- ✅ No compliance claims with any external framework
- ✅ No certification claims
- ✅ No endorsement claims
- ✅ No partnership claims
- ✅ No equivalence claims
- ✅ No public standard status claims
- ✅ No production readiness claims
- ✅ External frameworks are referenced for internal comparison only
- ✅ Gaps are identified as observations, not defects
- ✅ Ordivon-native innovations are identified without overclaim

*Phase: EGB-1 | Gap analysis is internal observation only. No compliance claim.*
