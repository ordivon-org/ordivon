# Ordivon — AI Agent Entry Point

Ordivon is a **governance operating system**, not a trading bot, AI wrapper, or generic dashboard.

## Quick Navigation

```
docs/ai/ordivon-macro-structure.md         ← Full system architecture (READ THIS FIRST)
docs/ai/new-ai-collaborator-guide.md       New AI collaborator practical guide
docs/ai/README.md                     AI onboarding start
docs/ai/ordivon-root-context.md       Identity + governance doctrine
docs/ai/current-phase-boundaries.md   Active/deferred/NO-GO boundaries
docs/ai/agent-output-contract.md      Required output shape for every AI task
docs/ai/current-system-map.md         Current system state overview
docs/ai/no-go-boundary-map.md         Hard boundaries for AI operation
docs/ai/new-ai-reading-order.md       10-step mandatory reading path
docs/ai/onboarding-protocol-dgp-4.md     Governed AI onboarding protocol

── Constitution & Philosophy ──
docs/architecture/ordivon-companion-governance-constitution.md  Companion governance origin
docs/governance/philosophical-governance-layer.md  Philosophical operating layer
docs/architecture/ordivon-core-pack-adapter-ontology.md  Canonical Core/Pack/Adapter ontology
docs/architecture/ordivon-moat-and-product-identity.md  Inalienable assets and moat

── Registry Control Plane (DGP-1 / RCP) ──
ordivon-verify registry-index --check     Current reconciler state (CLI)
ordivon-verify document-governance --check  Document governance hard gate (CI)
docs/governance/registry-object-model-rg-1.md  RegistryObject model
docs/governance/current-truth-entry-map.jsonl  Authoritative truth register (188 entries)
docs/governance/owner-routing-rules.jsonl      Path-inheritance owner routing (10 rules)

── Document Governance Pack (DGP-2 → DGP-9) ──
docs/governance/document-lifecycle-governance-dgp-2.md   Lifecycle state machine
docs/governance/document-authority-model-dgp-3.md        Authority boundaries
docs/governance/document-medium-authority-dgp-6.md        Medium/format authority
docs/governance/document-metabolism-dgp-7.md              Archive/tombstone rules
docs/governance/phase-receipt-standard-dgp-5.md           Receipt standard
docs/governance/stage-summit-standard-dgp-5.md            Stage summit standard
docs/product/document-governance-pack-stage-summit.md     DGP-S: final compression

── Legacy Governance (LGC-0 → LGC-S) ──
docs/governance/legacy-cleanup-risk-matrix-dgp-lgc-0.md  Freeze: 26 dirs, 209 terms
docs/product/legacy-governance-stage-summit-dgp-lgc-s.md  LGC-S: governed legacy seal
docs/governance/architecture-baseline-bridge-plan-dgp-lgc-5a.md  Bridge doc status
```

## Current Status — DGP-S: CLOSED | LGC-S: CLOSED | DGP-1→DGP-9: CLOSED

**Registry Control Plane**: 1221 objects, 0 BLOCKED, 0 DEGRADED, 269 ROUTED, 13 reconciler checks
**Document Governance**: 10 phases (DGP-1→DGP-9 + DGP-E1), CLOSED. 436 doc-registry entries, 30 JSON schemas
**Legacy Governance**: 13 phases (LGC-0→LGC-5F + LGC-S), CLOSED_AS_GOVERNED_LEGACY. 0 deletions, 0 behavior changes

Previous eras: Phase 7P CLOSED | DG Pack v1 CLOSED | PV-NZ CLOSED | OGAP-Z CLOSED | HAP/EGB/ADP lines CLOSED
Active: Alpha-0 | Next: MR-0 Main Reality Freeze

## Operational Commands

```
ordivon-verify document-governance --check   # CI hard gate (BLOCKED > 0 → exit 1)
ordivon-verify registry-index --check        # Reconciler status
ordivon-verify registry-index --snapshot     # Write index snapshot
ordivon-verify registry-index --diff         # Compare vs last snapshot
```

## Critical Boundaries

- Live trading: DEFERRED (requires Stage Gate)
- Policy activation: NO-GO
- CandidateRule to Policy: NO-GO without PolicyActivation
- Document governance PASS is NOT merge/release/deploy authorization
- Generated view is NOT source_of_truth
- Owner is NOT approver
- Archive is NOT current truth
- alembic migrations are do-not-edit by default
- policies/trading_limits.yaml is outside DGP scope (requires Trading Pack)
- Legacy directories are legacy_inactive — re-entry requires manifest conditions
- 26 legacy dirs are governed, not deleted
- PFIOS/AegisOS legacy terms are governed legacy context, not current Ordivon naming
