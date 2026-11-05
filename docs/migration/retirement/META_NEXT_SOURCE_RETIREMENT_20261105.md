# Meta / Next source retirement (candidate, 2026-11-05)

Source baseline: `cdc9e41a0b4dc8bee63412ac1b38d6b4a58d941f` (`main` at workspace creation).

## Meaning and proof boundary

The top-level `meta/` directory and `next` repository Owner have been removed **in this candidate SourceCut**. This receipt does not certify installation, deployed service replacement, consumer effect-equivalence, or a protected-main publication. Historical `meta/next/` references in immutable source-cut evidence and migration receipts continue to identify their original Git objects, not live paths. Historical Git owners are not re-registered.

## Native destination consumers

- Authority registration/discovery: `catalogs/authorities/` with its own CLI, tests and `authority-catalog:verify` route.
- Composition and cross-domain binding: `packages/composition/` with test-bound publication and security gate adapters.
- Reasoning Waist: `packages/composition/scripts/check_reasoning_waist_r1.py` with optional locked `reasoning` dependencies and native smoke.
- Research data lifecycle: `studies/data-lifecycle/`, including the experimental Episode Store, source queries, bounded projection and frozen historical evidence.
- Learning authorization-oriented experiment: `studies/learning/chaoxing-autosign-mvp/`, with safe fake-provider tests.
- Game frozen protocol: `profiles/domains/game/`; agent-interest experiment: `domains/game/research/autonomous-interest-r7/`.
- Historical Next documentation, superseded plans and unconsumed files: removed from working tree; recoverable through Git history.

## Verification

`repo:ci` includes native Authority Catalog, Learning and Data Lifecycle checks. `composition:verify` includes the migrated Reasoning Waist smoke. Structure R2, dependency boundaries, SQL dialect, architecture source inventory and historical provenance validators must all remain enforced. An exact SourceCut-bound test must be run on a committed candidate revision, not on uncommitted working tree bytes.

This is **source retirement**, not a declaration that the current externally installed Ordivon gateway, Skills MCP, or other durable stores have been migrated or restarted. External consumer names such as `project-ordivon-next` remain compatibility aliases pending a separate installed-consumer cutover; their spelling alone does not reinstate a Next Owner.
