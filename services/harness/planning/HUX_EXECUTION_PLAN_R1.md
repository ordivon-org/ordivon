# Harness UX Execution Plan R1

Date: 2026-09-23
Base: `f2ec4ec0c77fcf6b29fedd33c9145cea653cf730`
Workspace: `ws-harness-ux-f2ec-r2-20260923`

## Objective

Reduce ordinary Agent-run assembly friction without moving authority into UX, Composition, Gateway, or an Agent Service replacement.

## Current wave standing

| LEGO | Scope | Standing |
| --- | --- | --- |
| HUX-00 | source baseline | implemented candidate |
| HUX-01 | non-authority boundary | implemented for AgentRunBinding; wider product gate remains future |
| HUX-02 | anti-resurrection boundary | implemented for new binding schema/import seam; repository-wide semantic census remains future |
| HUX-10 | executable documentation contract | implemented candidate |
| HUX-11 | Quickstart/CLI parser smoke | implemented candidate |
| HUX-12 | stable API classification | implemented candidate |
| HUX-20 | AgentRunBinding contract | implemented candidate |
| HUX-21 | deterministic binding digest | implemented candidate |
| HUX-22 | machine-classified binding errors | implemented candidate |
| HUX-23 | deletion/rebuild proof | implemented candidate |
| HUX-30 | Circuit to Run lowering boundary | implemented candidate: apps/agent no-Tool consumer seam |
| HUX-31 | generic provider-binding lowering | deferred by evidence: HarnessRunContract + Harness adapter revalidation already own the stable semantics; do not duplicate without a provider-owner immutable configuration reference |
| HUX-32..38 | tool/skill/execution/completion lowering + Harness revalidation | next only where a real consumer still performs mechanical owner-reference bookkeeping |
| HUX-40..65 | presets, app facade, conversation/friendly inspect | later real-consumer driven |
| HUX-70..79 | loop/store internal refactor | later; behavior must be frozen first |
| HUX-80..84 | engineering vertical/differential/failure campaign | after first lowering slice |

## Frozen laws

1. `AgentRunBinding` is disposable and non-authoritative.
2. Composition may bind exact owner references but may not import or reinterpret owner internals.
3. Harness remains the owner of `HarnessRunContract` semantics and independently revalidates every executable composition.
4. Tool visibility, selection, admission, authorization, execution, and completion remain distinct.
5. A product facade may hide plumbing but may not weaken UNKNOWN/reconciliation/evidence boundaries.
6. No universal registry, workflow engine, session database, or Agent Service is introduced by this program.

## Convergence note

This candidate was replayed onto current main after Successor Contract R1 entered the Composition public API. Agent Run Binding must coexist with, not replace or shadow, successor-contract exports and semantics.

## HUX-30 standing

The first lowering seam lives in `apps/agent`, the product/consumer composition surface. It depends only on the public `ordivon_composition` and `ordivon_harness.api` contracts. Composition and Harness remain mutually independent core owners.

R1 intentionally admits only a no-Tool/no-cognition Run. Tool-bearing, execution-bearing, and cognition-bearing bindings fail closed into later lowerers instead of being silently inferred.

## Next executable slice

Do not implement a generic HUX-31 ProviderBinding object. Current source already binds provider/adapter/model identity in HarnessRunContract and independently validates the realized adapter. Revisit only when a provider owner exposes an immutable configuration reference that cannot be represented by the existing Contract.

The next evidence-driven candidate is HUX-32 Tool-surface assembly, because Tool bridge/factory catalog and grant digests are source-owned facts that callers currently copy mechanically. Any HUX-32 work must automate that copying without moving Tool selection or authorization into the app.

## Qualification evidence

- Composition AgentRunBinding tests: 9/9 passed.
- Agent App no-Tool vertical tests: 7/7 passed.
- Harness HUX regression tests: 10/10 passed.
- Full Composition owner verify: passed.
- Full Agent App owner verify: passed.
- Full Harness owner verify: 1065 tests + 121 subtests passed.
- Repository owner-boundary, structure, composition-architecture and architecture-doc checks: passed.
- Repository mechanics tests: 62 passed.
- `repo:integration:test`: passed.
- Cross-owner package dependencies are explicitly limited to `agent-app -> composition` and `agent-app -> harness`.
