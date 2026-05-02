# External AI Governance Benchmark Matrix (EGB-1)

> **v0 / reference-only / internal comparison.** Not compliance. Not certification.

## 1. External-to-Ordivon Concept Mapping

### OpenAI Preparedness Framework

| External Concept | Ordivon Target | Match Type | Gap |
|-----------------|---------------|------------|-----|
| Capability threshold evaluation | Capability Threshold Gate | Direct parallel | Ordivon threshold is phase-defined, not scorecard-based |
| Risk category (low/med/high/critical) | Risk Level (R0-R5) | Direct parallel | Ordivon has 6 levels; OpenAI has 4 |
| Safeguards / mitigations | Boundary Declaration + NO-GO Ladder | Direct parallel | Ordivon boundary is per-phase; OpenAI is per-model |
| Deployment gate | Stage Gate | Direct parallel | Ordivon gate is phase-local; OpenAI is pre-deployment global |
| Safety report / scorecard | Safety Receipt / Trust Report | Strong parallel | Ordivon receipt is evidence, not authorization |
| Post-deployment monitoring | Runtime Evidence + Review Record | Direct parallel | Ordivon evidence is continuous, not post-hoc |

### Anthropic Responsible Scaling Policy

| External Concept | Ordivon Target | Match Type | Gap |
|-----------------|---------------|------------|-----|
| AI Safety Levels (ASL-1 through ASL-4) | Capability-Scaled Governance / Risk Ladder | Strong parallel | Ordivon risk ladder is implicit in phase design, not explicit ASL |
| Deployment standards per ASL | Stage Escalation | Partial parallel | Ordivon escalation is per-phase, not per-capability-level |
| Security standards per ASL | Boundary Declaration + NO-GO | Strong parallel | Ordivon NO-GO is binary; ASL is graduated |
| Model capability evaluation | Evidence Gate / Closure Predicate | Direct parallel | Ordivon evaluation is per-phase, not per-model |
| Risk report | Trust Report / Stage Summit | Strong parallel | Ordivon summit includes non-risk dimensions |
| Proportional governance | Governance Pack Lifecycle | Direct parallel | Both emphasize scaling governance with capability |

### Google DeepMind Frontier Safety Framework

| External Concept | Ordivon Target | Match Type | Gap |
|-----------------|---------------|------------|-----|
| Severe harm capability identification | High-impact Capability Registry | Direct parallel | Ordivon registry is ad-hoc; DeepMind has systematic taxonomy |
| Dangerous capability evaluation | Severe Risk Watchlist | Concept target | Ordivon watchlist concept exists but not formalized |
| Capability monitoring | Runtime Evidence Checker | Strong parallel | Ordivon monitoring is checker-based; DeepMind is model-card-based |
| Mitigations | Boundary Declaration + NO-GO | Direct parallel | Same as OpenAI/Anthropic mapping |
| Deployment decision process | Stage Gate + Authority Impact | Direct parallel | Ordivon authority impact is a documentation field; DeepMind is process |
| Frontier risk domains | Pack-specific risk classification | Partial parallel | Ordivon packs (Finance, Coding, Document) are domain-specific, not risk-domain-specific |

### NIST AI RMF

| External Concept | Ordivon Target | Match Type | Gap |
|-----------------|---------------|------------|-----|
| Govern function | Governance Core + Document Governance Pack | Direct parallel | Ordivon governance is more code-enforced; RMF is process-enforced |
| Map function | CandidateRule Discovery + Architecture Checker | Partial parallel | Ordivon mapping is automated; RMF is organizational |
| Measure function | Evidence Gate + Runtime Evidence Checker + Eval Corpus | Strong parallel | Ordivon measurement is checker-driven; RMF is methodology-driven |
| Manage function | Policy Lifecycle + Review Record + Verification Baseline | Direct parallel | Ordivon management has machine-enforceable gates |
| Trustworthy AI characteristics (9) | Trust Report + Receipt/Debt/Gate triad | Partial parallel | Ordivon trust is evidence-grounded; RMF characteristics are aspirational |
| GAI Profile risk/action mapping | External Benchmark Layer | Concept target | Ordivon has no structured risk/action mapping |

### ISO/IEC 42001

| External Concept | Ordivon Target | Match Type | Gap |
|-----------------|---------------|------------|-----|
| AI management system | System Documentation Governance Pack | Strong parallel | Ordivon governance is distributed across packs |
| Organizational accountability | Ownership + Reviewer Roles | Partial parallel | Ordivon ownership is per-document/per-phase; 42001 is organizational |
| Lifecycle process governance | Phase Lifecycle + Stage Gate | Direct parallel | Ordivon phases are explicitly governed; 42001 is process-documented |
| Risk and opportunity management | Risk Engine + Verification Debt | Partial parallel | Ordivon debt is declarative; 42001 expects systematic risk treatment |
| Continual improvement (PDCA) | CandidateRule → Policy feedback loop | Strong parallel | Ordivon improvement is rule-driven; 42001 is process-driven |
| Documentation and auditability | Document Registry + Receipt Integrity | Direct parallel | Ordivon documentation is machine-checked |

## 2. Ordivon Concept Coverage Matrix

Ordivon internal concepts and which external frameworks address them:

| Ordivon Concept | OpenAI PF | Anthropic RSP | DeepMind FSF | NIST RMF | ISO 42001 |
|----------------|-----------|---------------|-------------|----------|-----------|
| Stage Gate | ✅ | ✅ | ✅ | ⚠️ partial | ⚠️ partial |
| Closure Predicate | ❌ | ❌ | ❌ | ❌ | ❌ |
| Boundary Confirmation | ✅ | ✅ | ✅ | ⚠️ partial | ⚠️ partial |
| NO-GO Ladder | ❌ | ❌ | ❌ | ❌ | ❌ |
| Risk Level (R0-R5) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Authority Impact | ❌ | ❌ | ❌ | ⚠️ partial | ✅ |
| Runtime Evidence | ✅ | ⚠️ partial | ✅ | ✅ | ✅ |
| Execution Receipt | ❌ | ❌ | ❌ | ❌ | ⚠️ partial |
| Review Record | ❌ | ❌ | ❌ | ✅ | ✅ |
| Candidate Rule | ❌ | ❌ | ❌ | ❌ | ❌ |
| Document Registry | ❌ | ❌ | ❌ | ❌ | ✅ |
| New AI Context Check | ❌ | ❌ | ❌ | ❌ | ❌ |
| Public Wedge Audit | ❌ | ❌ | ❌ | ❌ | ❌ |
| Architecture Checker | ❌ | ❌ | ❌ | ❌ | ❌ |
| Eval Corpus | ✅ | ✅ | ✅ | ✅ | ❌ |
| Coverage Governance | ❌ | ❌ | ❌ | ❌ | ❌ |
| Verification Baseline | ❌ | ❌ | ❌ | ❌ | ❌ |
| Harness Adapter Protocol | ❌ | ❌ | ❌ | ❌ | ❌ |

Legend: ✅ = strong alignment | ⚠️ partial = partial/near-match | ❌ = no external coverage

## 3. External Framework Coverage Assessment

| Framework | Ordivon Concepts Covered | Coverage % | Strongest Alignment |
|-----------|-------------------------|------------|---------------------|
| OpenAI PF | 5/18 | 28% | Risk Level, Stage Gate |
| Anthropic RSP | 4/18 | 22% | Stage Gate, Boundary |
| DeepMind FSF | 5/18 | 28% | Risk Level, Runtime Evidence |
| NIST AI RMF | 6/18 | 33% | Risk/Review/Evidence |
| ISO 42001 | 7/18 | 39% | Documentation, Lifecycle |

**Key finding:** No external framework covers Ordivon-unique concepts:
- Closure Predicate
- NO-GO Ladder
- Candidate Rule → Policy lifecycle
- New AI Context Check
- Public Wedge Audit
- Architecture Checker
- Coverage Governance

These are Ordivon-native innovations without external precedent.

*Phase: EGB-1 | Internal comparison only. No compliance claim.*
