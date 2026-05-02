# Agentic Pattern Governance Mapping (ADP-1)

> **v0 / internal mapping / reference-only.** Not binding policy.
> **Phase:** ADP-1 | **Risk:** AP-R0

## 1. HAP Object Mapping

Every ADP-1 pattern maps to HAP objects. This table shows which HAP objects
are affected by which patterns, and how the HAP schema could evolve to
support pattern detection.

| HAP Object | Patterns | Detection Potential | Schema Evolution |
|-----------|----------|---------------------|------------------|
| **HarnessAdapterManifest** | AP-COL, AP-DRF, AP-EBO | Manifest must include authority_statement; external references require safe-language | Add safe-language field |
| **HarnessCapability** | AP-COL, AP-CRED, AP-EXT, AP-MCP | Every capability boolean must have corresponding boundary block | Add capability-to-boundary consistency check |
| **HarnessRiskProfile** | AP-SHE, AP-CRED, AP-EXT | risk_level must match consumed capabilities | Add risk-capability consistency constraint |
| **HarnessTaskRequest** | AP-FAT, AP-SCP, AP-PPV, AP-INS | Task scope must be explicit; requested_capabilities must match boundary | Add scope field |
| **HarnessTaskPlan** | AP-SCP, AP-TST | Plan steps must not exceed task request scope | Add plan-to-request scope diff |
| **HarnessBoundaryDeclaration** | AP-DRF, AP-FAT, AP-PPV, AP-CRED, AP-EXT, AP-SHE, AP-MCP | Boundary must block capabilities; drift detection needed | Add boundary change audit |
| **HarnessExecutionReceipt** | AP-SCP, AP-PPV, AP-TST, AP-EVL | files_changed must match scope; skipped_checks must be declared | Add scope-diff field |
| **HarnessEvidenceBundle** | AP-EVL, AP-TST | evidence_quality must not be self_reported for critical claims | Add evidence quality linter |
| **HarnessResultSummary** | AP-RDY, AP-BDM | READY must include authority denial; failures must be classified | Add classification field |
| **HarnessReviewRecord** | AP-REV, AP-CRP, AP-FAT | Review must exist for requires_review_for items; CandidateRule must be non-binding | Add CandidateRule binding flag |

## 2. EGB Gap Mapping

Each pattern maps to EGB-1 gaps:

| EGB Gap | Patterns | Relationship |
|---------|----------|-------------|
| Capability-scaled governance | AP-COL, AP-SHE, AP-CRED, AP-MCP | These patterns are symptoms of unscaled governance; formal AP risk ladder addresses them |
| Systematic risk taxonomy | AP-DRF, AP-PPV, AP-EXT, AP-SCP, AP-MCP | Pattern taxonomy is a first step toward systematic risk classification |
| Deployment authorization | AP-COL, AP-SHE, AP-RDY, AP-CRP | READY≠authorization addresses this; formal deployment gate remains deferred |
| Post-deployment monitoring | (none directly) | ADP-1 is pre-deployment taxonomy |
| Organizational accountability | AP-INS, AP-REV, AP-CTD | Review Record and AI Context Check address accountability at project scale |
| External audit trail | AP-EVL, AP-BDM, AP-CTD | Evidence quality and baseline classification build audit trail foundations |
| Source freshness | AP-EBO | External benchmark overclaim is mitigated by safe-language + source freshness tracking |

## 3. Ordivon Control Mapping

How ADP-1 patterns would interact with Ordivon governance controls if
implemented (all are currently taxonomy-only in ADP-1):

### Stage Gate Impact

| Control Point | Patterns | Gate Action |
|--------------|----------|-------------|
| Pre-execution | AP-COL, AP-DRF, AP-PPV, AP-CRED, AP-EXT | BLOCKED if capability consumed without boundary |
| Pre-merge | AP-RDY, AP-REV, AP-CRP | BLOCKED if READY claimed as authorization or review missing |
| Pre-CLOSED | AP-CTD, AP-BDM, AP-TST | BLOCKED if truth sources contradictory or failures unclassified |

### Checker Opportunities

| Checker | Patterns Detected | Implementation Complexity |
|---------|-------------------|---------------------------|
| Capability-Boundary consistency | AP-COL, AP-CRED, AP-EXT | Low — schema validation |
| Permission rule consistency | AP-DRF | Low — intersection check |
| Boundary drift detection | AP-FAT | Medium — diff-based |
| Scope-to-execution diff | AP-SCP, AP-PPV | Medium — file path matching |
| Evidence quality linter | AP-EVL | Low — field check |
| READY disclaimer validator | AP-RDY | Low — string check |
| Review completeness | AP-REV | Low — field count check |
| Truth source cross-reference | AP-CTD | Medium — multi-file consistency |
| Baseline diff + classification | AP-BDM | Medium — historical comparison |
| Safe-language lint | AP-EBO | Low — regex |
| MCP tool allowlist | AP-MCP | Medium — schema + runtime |
| CandidateRule binding flag | AP-CRP | Low — field check |

## 4. CandidateRule Summary (All NON-BINDING)

| ID | Pattern | Rule |
|----|---------|------|
| CR-ADP-001 | AP-COL | Capability declarations must include authority denial |
| CR-ADP-002 | AP-FAT | Boundary scope expansion requires Stage Gate escalation |
| CR-ADP-003 | AP-DRF | Permission rules must be audited at each Stage Gate |
| CR-ADP-004 | AP-INS | AI onboarding must pass New AI Context Check at phase boundaries |
| CR-ADP-005 | AP-PPV | Protected paths must be explicitly named in task scope |
| CR-ADP-006 | AP-SHE | Shell execution requires AP-R3 classification and escalation |
| CR-ADP-007 | AP-CRED | can_read_credentials is capability, not access; blocked by default |
| CR-ADP-008 | AP-EXT | External calls require AP-R4 classification and tool allowlist |
| CR-ADP-009 | AP-EVL | Evidence must reach machine_verified quality for READY |
| CR-ADP-010 | AP-RDY | READY must include execution authorization denial |
| CR-ADP-011 | AP-REV | Review required for requires_review_for items before READY |
| CR-ADP-012 | AP-CTD | Truth sources must be consistent at phase boundaries |
| CR-ADP-013 | AP-SCP | Agent must operate within declared task scope |
| CR-ADP-014 | AP-TST | Skipped verification must be declared with justification |
| CR-ADP-015 | AP-BDM | New failures must be classified with baseline evidence |
| CR-ADP-016 | AP-CRP | CandidateRule is advisory; promotion requires 4 criteria |
| CR-ADP-017 | AP-EBO | External references require safe-language disclaimer |
| CR-ADP-018 | AP-MCP | MCP servers require tool allowlists |

**All 18 CandidateRule suggestions are NON-BINDING and ADVISORY ONLY.**
Promotion to Policy requires: ≥2 weeks observation, ≥3 real interceptions,
documented bypass conditions, stakeholder sign-off.

## 5. Future Schema/Eval Implications

| Implication | Priority | Effort | Phase Candidate |
|------------|----------|--------|-----------------|
| Capability-boundary consistency schema constraint | High | Low | HAP-2 |
| READY disclaimer field required in ResultSummary | High | Low | HAP-2 |
| Safe-language lint rule in overclaim scan | High | Low | EGB-2 |
| Boundary drift detection (diff-based) | Medium | Medium | HAP-2 |
| Scope-to-execution diff checker | Medium | Medium | ADP-2 |
| Evidence quality linter | Medium | Low | ADP-2 |
| Truth source cross-reference checker | Medium | Medium | DG extension |
| Baseline diff + classification checker | Medium | Medium | COV extension |
| MCP tool allowlist schema + validator | Medium | Medium | HAP-2 |
| CandidateRule binding flag + promotion tracker | Low | Low | Policy extension |
| Review completeness checker | Low | Low | HAP-2 |
| Permission rule consistency checker | Low | Low | ADP-2 |

*Phase: ADP-1 | Mapping is internal and advisory only.*
