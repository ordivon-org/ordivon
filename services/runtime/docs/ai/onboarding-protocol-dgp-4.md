# AI Onboarding Protocol — DGP-4

Status: **CURRENT** | Date: 2026-05-09 | Phase: DGP-4
Authority: current_status | Owner: Governance

## Purpose

Define a governed, reproducible path for a new AI or new conversation to understand Ordivon's current state without wandering through stale, archived, or generated documents. This protocol is a navigation layer, not a replacement for the underlying documents.

## Mandatory Reading (in order)

1. **Start here**: `docs/ai/README.md`
   - What Ordivon is, what it does, core philosophy.

2. **Root context**: `docs/ai/ordivon-root-context.md`
   - Current system map, active packs, current phase, NO-GO map.

3. **Current phase boundaries**: `docs/ai/current-phase-boundaries.md`
   - What phase is active, what is closed, what is pending.

4. **New AI collaborator guide**: `docs/ai/new-ai-collaborator-guide.md`
   - Working conventions, receipt format, evidence rules.

5. **Agent working rules**: `docs/ai/agent-working-rules.md`
   - How agents should operate, output, and seal work.

6. **Agent output contract**: `docs/ai/agent-output-contract.md`
   - What a receipt/closure must contain.

7. **Current truth entry points**: `docs/governance/current-truth-entry-map.jsonl`
   - Machine-readable register of documents authorized to carry current truth.

8. **Registry Control Plane**: run `ordivon-verify registry-index --check`
   - Current governance system status: BLOCKED/DEGRADED/ROUTED counts.

## Deep Reading (after mandatory)

- `docs/governance/document-authority-model-dgp-3.md` — Authority model and boundaries.
- `docs/governance/document-lifecycle-governance-dgp-2.md` — Document lifecycle rules.
- `docs/ai/architecture-file-map.md` — Project structure and important files.
- `docs/ai/philosophical-onboarding-addendum-pgi-3.md` — Deeper philosophical context.
- `docs/governance/registry-object-model-rg-1.md` — Registry Control Plane object model.

## Context Map

See `docs/ai/current-context-map.json` for a machine-readable context snapshot.

## Archive / Generated View Warning

- Documents with status `closed`, `archived`, or `superseded` are historical. Do not treat as current truth.
- Generated views (e.g. `registry-index` output, `verification-gate-manifest.json`) are derived artifacts. Do not treat as source_of_truth.
- Receipts and stage summits are phase closure evidence. They are not permanent truth unless registered in the current truth entry map.

## NO-GO Boundary See `docs/ai/no-go-boundary-map.md`. Core boundaries:
- READY/PASS/CLOSED is NOT merge/release/deploy authorization.
- Owner is NOT approver.
- Generated view is NOT source of truth.
- CandidateRule is NOT Policy without PolicyActivation.
- Do NOT introduce SaaS, bot, MCP server, AI judge, or agent runner without explicit phase authorization.
- Do NOT expand Trade/Health/Finance profile packs.

## Reporting Contract

Every phase closure must include:
1. Files changed
2. Validation evidence (raw command output, not "全绿")
3. Known debts deliberately NOT fixed
4. NO-GO confirmation
5. New AI Context Check (can a new AI understand this from entry docs?)

Claim ≠ Evidence. Closure ≠ Truth. READY ≠ Authorization.
