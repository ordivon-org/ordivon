# Philosophical Surface Map — PGI-1

Status: **CURRENT** | Date: 2026-05-03
Phase: PGI-1.01
Tags: `pgi`, `philosophy`, `surface-map`, `truth`, `value`, `decision`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

This map classifies where the Philosophical Governance Layer already appears
inside Ordivon, and where it is still only planned.

It is not a completion claim. It is a surface inventory for PGI execution.

Canonical source:

```text
docs/governance/philosophical-governance-layer.md
```

Implementation roadmap:

```text
docs/product/philosophical-governance-implementation-roadmap.md
```

## Surface Matrix

| Philosophical module | Existing Ordivon surface | Current maturity | PGI gap |
|----------------------|--------------------------|------------------|---------|
| Epistemology | `docs/governance/document-authority-model-dg-1.md`, `docs/governance/document-freshness-supersession-dg-1.md`, `docs/governance/evidence-ledger-model-pgi-1.md`, `src/ordivon_verify/report.py`, receipt checker | Implemented in docs and seeded as EvidenceRecord schema/validator | Pack-level integration remains deferred to PGI-2.01 and later Pack stages. |
| Logic and Argument | receipt contradiction checks, ADP detector overclaim patterns, Alpha laundering fixtures, `docs/governance/claim-argument-model-pgi-1.md`, `scripts/check_philosophical_claims.py` | Seed model + partial checker coverage | Full argument parsing and broad fallacy deck remain deferred to PGI-1.09. |
| Philosophy of Science | gate manifests, verification baselines, falsifiable stage exits in many receipts | Procedural but uneven | "What would change my mind" is not required in stage/review templates. |
| Bayesian Thinking | scattered `confidence` fields in older finance/runtime scripts | Fragmentary | No shared confidence, base-rate, calibration, or uncertainty ledger. |
| Practical Reason | decision intake models, execution-request receipts, phase gates | Domain-specific | No universal DecisionGate object spanning personal Packs and agent work. |
| Normative Ethics | NO-GO boundaries, CandidateRule-not-Policy doctrine, authority model | Strong boundary language | Ethical triad review (consequence/rule/character) is not yet templated. |
| Virtue and Cultivation | companion constitution, philosophical layer | Documented only | No Self-Cultivation Pack or character-effect review surface. |
| Autonomy | Constitution Pack ideas, NO-GO boundaries, "AI is leverage not authority" | Documented and partially enforced by overclaim detectors | Personal constitution rules are not classified as warning/gate/NO-GO/deferred. |
| Stoicism | process/outcome separation appears in finance and dogfood language | Implicit | No Control Boundary classifier for controllable vs uncontrollable factors. |
| Buddhism / Daoism | Anti-Overforce Rule in philosophical layer | Documented only | No constraint intake, stop/pause/downshift receipt, or stalled-work fixture. |
| Pragmatism | review-to-lesson-to-CandidateRule pipeline, CPR-3 dogfood | Implemented in coding/governance track | CandidateRule ethics and over-control checks are not yet formalized. |
| Extended Mind | tool truth, ADR-008 tooling strategy, AI onboarding, Verify report surfaces | Documented for tools and AI collaboration | No tool-switch gate or cognitive-tool failure map. |

## Existing Machine-Enforced Surfaces

| Surface | Enforced by | What it protects |
|---------|-------------|------------------|
| Receipt contradiction | `scripts/check_receipt_integrity.py`, `src/ordivon_verify/checks/receipts.py` | Completion claims, skipped verification, authorization laundering |
| Document metadata | `scripts/check_document_registry.py` | authority, freshness, lifecycle, semantic safety |
| Verification debt | `scripts/check_verification_debt.py`, `src/ordivon_verify/checks/debt.py` | hidden debt and unmanaged failures |
| Gate manifest | `scripts/check_verification_manifest.py`, `src/ordivon_verify/checks/gates.py` | no-op gates and weakened verification boundaries |
| Agentic pattern risk | `scripts/detect_agentic_patterns.py` | capability/authority collapse, READY overclaim, public-surface risk |
| Alpha trust fixtures | `scripts/run_alpha_casebook.py` | trust laundering regressions |

## High-Risk Missing Surfaces

| Gap | Why it matters | Routed to |
|-----|----------------|-----------|
| Claim taxonomy expansion | Seeded in PGI-1.02; without broader fixtures, narrative can still hide weak inference outside current patterns. | PGI-1.09 |
| Evidence object integration | EvidenceRecord is seeded; without Pack integration, evidence still remains fragmented in many workflows. | PGI-2.01 |
| Freshness conflict fixtures | Stale truth can stay persuasive in AI onboarding. | PGI-1.04 |
| Confidence calibration | High confidence can float free from evidence. | PGI-1.05 |
| Falsifiability prompts | Roadmaps can become unfalsifiable doctrine. | PGI-1.06 |
| Constitution boundary classification | Values can silently become active policy or remain vague slogans. | PGI-1.07 |
| Ethical triad review | Ordivon can over-optimize results, rules, or character in isolation. | PGI-1.08 |
| Philosophy misuse fixtures | Philosophy can launder overwork, gambling, avoidance, or self-judgment. | PGI-1.09 |
| DecisionGate object | High-consequence choices lack one cross-domain gate. | PGI-2.01 |
| Anti-overforce intake | "Try harder" can override body, emotion, strategy, or tooling constraints. | PGI-2.04 |
| Self-model ledger | Reviews can become isolated events instead of self/system learning. | PGI-3.01 |
| AI philosophical onboarding | AI collaborators may turn philosophy into vague motivation or overreach. | PGI-3.06 |

## Authority Boundaries

This map can classify surfaces and route gaps. It cannot authorize:

- active_enforced Policy
- live trading
- broker write operations
- auto-merge
- public release
- schema standard claims
- external side effects

## Review

PGI-1.01 confirms that Ordivon already has strong evidence/authority and
READY-not-authorization machinery. The weak spots are the newer philosophical
objects: claim taxonomy, confidence calibration, ethical triad review,
anti-overforce intake, self-model learning, and tool-switch governance.

Next executable stage:

```text
PGI-1.02 - Claim and Argument Model
```
