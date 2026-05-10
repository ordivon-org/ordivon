# New AI Reading Order — DGP-4

1. `docs/ai/README.md` — Start here. What Ordivon is.
2. `docs/ai/ordivon-root-context.md` — Current system map and boundaries.
3. `docs/ai/current-phase-boundaries.md` — Active/closed/pending phases.
4. `docs/ai/new-ai-collaborator-guide.md` — How to work, how to report.
5. `docs/ai/agent-working-rules.md` — Operational rules.
6. `docs/ai/agent-output-contract.md` — Receipt/closure format.
7. `docs/governance/current-truth-entry-map.jsonl` — What can claim truth.
8. `docs/ai/onboarding-protocol-dgp-4.md` — This protocol.
9. Run: `ordivon-verify registry-index --check` — Current governance state.

Deep context (optional):
- `docs/governance/document-authority-model-dgp-3.md`
- `docs/governance/document-lifecycle-governance-dgp-2.md`
- `docs/ai/architecture-file-map.md`

DO NOT read as current truth:
- Documents with `status: closed`, `archived`, `superseded`.
- Generated views (registry-index, manifests).
- CandidateRules without PolicyActivation.
