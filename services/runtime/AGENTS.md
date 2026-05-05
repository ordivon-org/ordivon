# Ordivon — AI Agent Entry Point

Ordivon is a **governance operating system**, not a trading bot, AI wrapper, or generic dashboard.

## Quick Navigation

```
docs/ai/new-ai-collaborator-guide.md          New AI collaborator practical guide
docs/ai/README.md                        AI onboarding start
docs/ai/ordivon-root-context.md          Identity + governance doctrine
docs/ai/current-phase-boundaries.md      Active/deferred/NO-GO boundaries
docs/ai/agent-output-contract.md         Required output shape for every AI task
docs/architecture/ordivon-core-pack-adapter-ontology.md  Canonical Core/Pack/Adapter ontology
docs/architecture/ordivon-moat-and-product-identity.md  What is inalienable, what is not, where the moat is
docs/architecture/ordivon-companion-governance-constitution.md  Companion governance origin and highest constitution
docs/governance/philosophical-governance-layer.md  Philosophical operating layer for truth, value, action, pain, and self-evolution
docs/product/philosophical-governance-implementation-roadmap.md  PGI 3x10 implementation roadmap for philosophical governance
docs/governance/README.md                Document Governance Pack (accepted)
docs/runbooks/ordivon-agent-operating-doctrine.md  Full doctrine
docs/runtime/ordivon-value-philosophy.md Why not a trading bot
docs/governance/verification-signal-classification.md  Classify checker failures before acting

── Extension & Governance Systems (NEW) ──
docs/governance/extension-processes.md        How to extend Core/Pack/Adapter/Checker/Test — PEP+RFC+KEP inspired
docs/governance/entropy-governance-design.md   Anti-entropy system design (Lehman's Laws applied)
docs/governance/entropy-telemetry.jsonl        Entropy metrics ledger (timestamped snapshots)
docs/governance/checker-maturity-ledger.jsonl  Checker maturity state transitions
docs/governance/policy-activation-ledger.jsonl Policy activation owner signoffs
docs/governance/candidate-rule-drafts.jsonl    Extracted CandidateRules from lessons (2 drafts)
docs/governance/shadow-evaluation-log.jsonl    Policy Shadow Runner evaluation results
docs/governance/lesson-ledger.jsonl            Lessons from checker findings (5 lessons)

── Governance Pipeline (CATLASS) ──
stage-templates/doc-governance.yaml            Stage template: doc-governance pipeline
scripts/run_stage.py                           Stage runner — governance pipeline executor
docs/runtime/waves-a-e-dogfood-receipt.md      Dogfood receipt — first CATLASS stage run

── Architecture ──
docs/architecture/harness-adapter-protocol-hap-1.md   HAP v0 protocol architecture
docs/runtime/hap-foundation-hap-1.md                HAP foundation evidence
docs/product/harness-adapter-protocol-stage-notes-hap-1.md  HAP-1 stage notes
docs/governance/external-ai-governance-benchmark-pack-egb-1.md  External governance benchmarks
docs/ai/external-benchmark-reading-guide.md         EGB-1 AI reading guide
docs/governance/agentic-pattern-taxonomy-adp-1.md   Agentic pattern taxonomy (18 patterns)
docs/runtime/ordivon-system-summit-oss-1.md        OSS-1 system summit and re-centering audit
docs/runtime/core-pack-governance-loop-gap-analysis-oss-1.md  Core/Pack loop node-level gap analysis
docs/architecture/ordivon-system-classification-audit-oss-1.md  OSS-1 L0-L10 asset map
docs/ai/codebase-deep-analysis-2026-05-02.md       Source-doc consistency audit + red-team repair map
docs/product/alpha-roadmap.md                      Full Alpha roadmap and trust flywheel
docs/product/alpha-0-evidence-of-governed-work.md  Alpha-0 product direction: agent work trust audit
docs/runtime/alpha-0-casebook.md                   Governed AI coding work casebook
```

## Current Status — Phase 7P: CLOSED | DG Pack: CLOSED | PV-NZ: CLOSED | COV-1R: CLOSED | COV-2: CLOSED | OGAP-Z: CLOSED | HAP-1: CLOSED | EGB-1: CLOSED | ADP-1: CLOSED | HAP-2: CLOSED | GOV-X: CLOSED | ADP-2: CLOSED | HAP-3: CLOSED | ADP-2R: CLOSED | ADP-3: CLOSED | DG-1: CLOSED | OSS-1: CLOSED | CPR-1: CLOSED | CPR-2: CLOSED | CPR-3: CLOSED | EG-1: ACTIVE | Alpha-0: ACTIVE
Next: Alpha-0 Evidence of Governed Work — AI coding agent trust audit

pr-fast: 12/12 PASS | full: 36/36 ALL PASS (26 hard + 10 escalation) | 3 open debt | Phase 8: DEFERRED
Phase 6: Design + Finance Observation — COMPLETE
**Phase 7P: Alpaca Paper Dogfood — CLOSED** (Stage Summit published)
**DG Pack: CLOSED** — Document Governance Pack, 18 sub-phases, Stage Summit published
**PV-1: PROPOSAL** — Ordivon Verify CLI product contract (docs only)
**PV-2: COMPLETE** — Ordivon Verify CLI skeleton (35 tests, 4 checkers wrapped)
**PV-3: COMPLETE** — External fixture dogfood + minimal config mode
**PV-4: COMPLETE** — Trust report polish (76 tests, rich output)
**PV-5: COMPLETE** — Agent skill + CI adoption pack
**PV-6: COMPLETE** — Agent skill dogfood (scenarios A-D validated)
**PV-7: COMPLETE** — Clean external fixture READY path
**PV-8: COMPLETE** — Standard external fixture (governance files → READY)
**PV-9: COMPLETE** — GitHub Action example dogfood
**PV-10: COMPLETE** — Public README / landing copy drafts
**PV-11: COMPLETE** — Public packaging boundary (private core + public wedge)
**PV-12: COMPLETE** — Package extraction plan
**PV-Z: CLOSED** — Ordivon Verify productization Stage Summit
**PV-N1: CLOSED** — Private package prototype (src/ordivon_verify/ created, script wrapper preserved)
**PV-N2: CLOSED** — Schema extraction (5 JSON schemas + 29 tests, no private references)
**PV-N2H: CLOSED** — DG coverage hardening + legacy identity hygiene (VD-005 closed, coverage plane implemented)
**PV-N3: CLOSED** — Public quickstart dogfood (example fixture READY, 14 tests)
**PV-N4: CLOSED** — Private package install smoke (console entrypoint, 16 tests)
**PV-N5: CLOSED** — Release readiness audit (17 blockers across 4 tiers)
**PV-N6: CLOSED** — Secret + Private Reference Audit Dry Run (0 blocking findings)
**PV-N7: CLOSED** — Local public repo dry-run (16 copied, 0 missing required)
**PV-N8: CLOSED** — Local build artifact smoke (wheel built, 244 private paths — BLOCKED for public publish)
**OGAP-1: CLOSED** — Protocol semantics + object model
**OGAP-2: CLOSED** — Schemas + local validator
**OGAP-3: CLOSED** — Adapter fixture dogfood
**OGAP-Z: CLOSED** — Protocol foundation Stage Summit
<!-- PV status legend: CLOSED=no open work, COMPLETE=sealed, ACTIVE=in progress, DEFERRED=not started -->

Paper dogfood proved governance pipeline integrity, not profitability.
3 completed round trips. 4 refusals. 0 boundary violations.
204 backend tests. 57 frontend tests. 36/36 baseline (26 hard + 10 escalation).

Checker ecosystem: 36 checkers (26 hard, 10 escalation) across L3-L10.
Governance loop: Checker→Lesson→CandidateRule→Shadow→Review — fully closed.
Entropy governance: telemetry + gates, Lehman's Laws applied.
Extension processes: Core/Pack/Adapter/Checker/Test — PEP+RFC+KEP inspired.
Maturity model: draft→shadow_tested→red_teamed→active, no self-promotion.
Owner veto: Policy activation requires named owner + explicit signoff.
CandidateRules: 2 drafts (freshness, receipt overclaim). Phase 8: DEFERRED.

**pr-fast**: 12/12 hard gates. **full**: 36/36 ALL PASS (26 hard + 10 escalation). 3 open debt.
**Current center**: Alpha-0 Evidence of Governed Work + EG-1 CATLASS MVP (stage templates + runner).
**Next**: expand stage template library, integrate with Ordivon Verify.

## Critical Boundaries

- Live trading: PHASE 8 DEFERRED (requires Stage Gate)
- Broker write API: NO-GO
- Policy activation: NO-GO
- Auto-trading: NO-GO
- CandidateRule to Policy: NO-GO
- Document Governance Pack: design-only, no code enforcement
- OGAP: protocol foundation only — no API, no SDK, no MCP server, no public standard
- Financial/broker/live action: NO-GO
- READY ≠ approval: valid OGAP payloads do not authorize execution
