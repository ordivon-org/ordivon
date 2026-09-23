# Harness UX Execution Plan R1

Date: 2026-09-23
Canonical integration: `10cdbcdb33e19d9fe7fda7d57f3d33fa3eb8022c`
Current worktree: `ws-hux40-latestmain-r2-20260923`

## Objective

Reduce ordinary Agent-run assembly and inspection friction without moving authority into UX,
Composition, Gateway, or an Agent Service replacement.

## Current wave standing

| LEGO | Scope | Standing |
| --- | --- | --- |
| HUX-00 | source baseline | canonical |
| HUX-01 | non-authority boundary | canonical for AgentRunBinding |
| HUX-02 | anti-resurrection boundary | canonical for binding/import seam |
| HUX-10 | executable documentation contract | canonical |
| HUX-11 | Quickstart/CLI parser smoke | canonical |
| HUX-12 | stable API classification | canonical |
| HUX-20 | AgentRunBinding contract | canonical |
| HUX-21 | deterministic binding digest | canonical |
| HUX-22 | machine-classified binding errors | canonical |
| HUX-23 | deletion/rebuild proof | canonical |
| HUX-30 | Circuit → no-Tool bounded Harness Run | canonical in `apps/agent` |
| HUX-31 | generic provider binding | **DEFERRED_BY_EVIDENCE** |
| HUX-32 | generic Tool-surface lowering | **DEFERRED_BY_EVIDENCE** |
| HUX-33 | generic Skill/Cognition lowering | **DEFERRED_BY_EVIDENCE** |
| HUX-34 | generic ExecutionBinding lowering | **DEFERRED_BY_EVIDENCE** |
| HUX-40 | read-only Product Run View | qualified candidate on latest-main replay; integration pending |
| HUX-41..65 | richer product/session UX | real-consumer driven only |
| HUX-70..79 | loop/store internal refactor | later; behavior remains frozen first |
| HUX-80..84 | real workload differential/failure campaign | choose only after a concrete app workload requires the relevant lowerers |

## Frozen laws

1. `AgentRunBinding` is disposable and non-authoritative.
2. Composition may bind exact owner references but may not import or reinterpret owner internals.
3. Harness remains the owner of `HarnessRunContract` semantics and independently revalidates executable composition.
4. Tool visibility, selection, admission, authorization, execution, and completion remain distinct.
5. A product facade may hide plumbing but may not weaken UNKNOWN/reconciliation/evidence boundaries.
6. A product Run view is lossy and read-only; Harness exact projections remain proof.
7. `Harness completed` / `candidate_completed` never implies caller Task or domain semantic completion.
8. No universal registry, workflow engine, Session database, or Agent Service is introduced by this program.

## Canonical HUX-30 standing

The first lowering seam lives in `apps/agent`, the product/consumer composition surface. It
depends only on the public `ordivon_composition` and `ordivon_harness.api` contracts.
Composition and Harness remain mutually independent core owners.

HUX-30 intentionally admits only a no-Tool/no-cognition/no-execution Run. Tool-bearing,
execution-bearing, and cognition-bearing bindings fail closed rather than being inferred.

The qualified HUX-30 candidate was replayed onto the concurrently evolved main, preserving the
Skills relocation to `extensions/chatgpt-skills-mcp`, and was integrated through the accepted
serialized `integrate-main.sh` path:

- previous main: `942bd3c88e754ca4edc190028f2d859c028509bc`
- canonical HUX commit: `10cdbcdb33e19d9fe7fda7d57f3d33fa3eb8022c`
- integration mode: `FAST_FORWARD`
- post-integration primary-main invariant: PASS

## Delete-custom-by-default decisions

### HUX-31 — generic ProviderBinding

Do not implement. `HarnessRunContract` already binds `providerId`, `adapterId`, and
`requestedModelId`, while `HarnessAgentRun` independently validates the realized adapter.
Revisit only if a natural provider owner exposes an immutable configuration reference that
cannot be represented by the existing Contract.

### HUX-32 — generic Tool-surface lowering

Do not implement yet. Production census found no Tool-bearing `apps/agent` consumer. The only
manual catalog/grant digest duplication outside tests is in Harness-internal acceptance/live
experiment scripts; `PluginGatewayExecutionBridgeFactory` already computes and validates its
own natural-owner Tool surface. A test fixture is not sufficient evidence for a product API.

### HUX-33 — generic Skill/Cognition lowering

Do not implement yet. External production census found zero constructors of
`HarnessCognitionSeed`, `HarnessCognitionSeedSource`, `HarnessWorkingViewSource`, or
`HarnessCognitionProfile`. Revisit when a real app consumer must translate selected Skill
material into exact cognition sources.

### HUX-34 — generic ExecutionBinding lowering

Do not implement yet. External production census found no app/domain/capability constructor.
The only manual constructor is a Harness live A/B script; the Plugin/Gateway factory already
builds the exact binding inside its natural owner.

## HUX-40 — Product Run View

The next justified UX slice is inspection rather than more assembly ontology. Existing
`ordivon-harness status/inspect/explain` surfaces intentionally expose exact forensic JSON.
`apps/agent` now adds a derived read-only view over an already validated in-process Run:

- `created` → `ready`
- `active` → `running`
- `paused` → `attention_required`
- `stopped` → `stopped`
- `completed` → `run_finished`
- `failed` → `failed`

The view preserves `nativeStatus`, exact Run/Contract identity, revision, requested model and
bounded composition-presence flags. It never infers Provider/Runtime liveness and always states
that Harness did not establish Task/domain semantic acceptance. It deliberately maps paused to
the generic `attention_required` rather than guessing `needs_input`.

## Qualification evidence

Canonical HUX-30:
- Composition AgentRunBinding tests: 9/9 passed.
- Agent App HUX-30 tests: 7/7 passed before HUX-40.
- Harness HUX regression tests: 10/10 passed.
- Full Composition owner verify: PASS.
- Full Agent App owner verify: PASS.
- Full Harness owner verify: 1065 tests + 121 subtests passed.
- Repository owner-boundary/structure/composition-architecture/docs checks: PASS.
- Repository mechanics: 62 tests passed.
- `repo:integration:test`: PASS.
- primary-main post integration: PASS.

HUX-40 latest-main qualified candidate:
- replay base: `e82ac3c19c18eb17e4d3a6df39333e0b1686739a`.
- Agent App owner verify: 23 tests passed; Ruff and format checks passed.
- Full Harness owner verify on unchanged Harness source: 1065 tests + 121 subtests passed; dependency/docs/evidence/wheel checks passed.
- latest-main Harness documentation contract: valid.
- real Harness vertical maps durable `completed` to product `run_finished`.
- exact semantic acceptance remains false in the product view.
- `git diff --check`: PASS.
