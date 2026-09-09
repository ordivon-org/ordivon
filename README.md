---
schema_version: 1
id: harness.start
title: Ordivon Harness
type: start
profile: organization
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-harness
audience:
  - user
  - builder
  - operator
  - agent
updated: 2026-08-12
summary: Public entry to the durable cognitive execution substrate for bounded Agent Runs, with explicit cognition, Provider and Tool continuity, recovery, evidence, and caller/domain boundaries.
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-harness
related:
  - harness.quickstart
  - harness.status
  - harness.architecture
  - harness.compatibility
  - harness.verification
  - harness.operations
  - harness.data-privacy
  - harness.releases
  - harness.authority
---
# Ordivon Harness

An Agent Run is more than one model response.

A Provider call may be interrupted. A Tool may have changed the world before its response is lost. The caller may supply new information. The Agent may decide that some evidence should remain in its current cognition while other history should not be replayed. A model may conclude that its bounded Run is finished while the caller's Task is still unresolved.

**Ordivon Harness makes that bounded Agent Run durable without taking the Agent's semantic choices away from it.**

The caller binds one exact `HarnessRunContract`. Higher-level planning, resource allocation, profile selection, retries across separate Runs, and successor creation remain caller/domain/workflow responsibilities. Harness preserves only the structural truth needed to run, pause, recover, and inspect that exact bounded Run: Provider identity, current cognition, admitted actions, Tool effects, budget, evidence, and completion proposal.

It does **not** build the Agent's world model, decide which evidence is important, or decide whether a domain objective is finally satisfied.

## Why Harness exists

Consider a Tool-bearing Run:

```text
Agent asks for a Tool effect
→ Harness admits one exact Tool intent
→ Runtime begins physical work
→ the effect may occur
→ the response path breaks
→ the Agent process disappears
```

On restart, blindly issuing the Tool again may duplicate the effect. Replaying every old message may also give the model stale or irrelevant cognition. Treating a recovered Provider response as Task completion would be a third error.

Harness therefore keeps three questions separate:

1. **What actually happened in this Run?** — canonical execution history and receipts.
2. **What should the Agent see now?** — Agent-selected cognition plus current caller/Tool context.
3. **What actions are admitted now?** — exact per-turn capabilities, Tools, budgets, and provenance.

Those answers are related, but they are not one message list.

## Responsibility boundary

Harness owns **how one admitted Agent execution attempt becomes durable, executable, and recoverable**.

```text
Canonical History       what happened in the Run
Durable Cognition       Agent-selected WorkingSet
Interaction Cognition   current caller ingress
Attempt Cognition       current Provider/Tool exchange
Execution Control       exact actions, provenance and budgets allowed now
Effects                  admitted Tool intents and bound physical evidence
```

The effective model view is compiled from current cognition and execution control. It is not a replay of complete Run history.

Other owners keep their own meaning:

| Fact or responsibility | Owner |
| --- | --- |
| caller Task, domain objective, final semantic acceptance | caller / Host / domain |
| Agent selection of current evidence and next action | Agent within delegated authority |
| bounded Run structure, Provider/Tool continuity, current cognition mechanics | Harness |
| local Workspace/Job/Attempt execution truth | Runtime |
| external-world/native occurrence truth | the external owner/provider/domain |

A Host may call Harness, but Host is not a Harness dependency and does not store Harness Run state. Harness may return a `CompletionProposal`; that proposal is **not** Host Task completion or domain truth.

## One normal Run

```text
caller authors Contract
→ Harness creates durable Run identity
→ current Working View is projected
→ Provider receives exact request-bound actions
→ Agent reasons and may:
     • conclude the bounded Run
     • call an admitted Runtime/World Tool
     • change selected durable cognition
     • promote exact caller ingress into durable cognition
     • inspect bounded cognition history when admitted
→ Harness records structural/effect evidence
→ pause, recover, or continue as needed
→ Harness emits Run Receipt + optional CompletionProposal
→ caller/domain decides what that result means
```

Provider-specific wire state may exceed reconstructed semantic messages, but the current contracted product does **not** expose a generic `ProviderToolContinuation` primitive. Opaque Provider-local continuation therefore remains Provider/integration-local unless fresh direct pressure earns a bounded Harness surface.

## Status

Harness is **pre-1.0 but operational** as an independent, caller-neutral durable cognitive execution substrate. The only current writer is the Harness SQLite Journal/CAS. The former Host-backed Assignment/Runner/cutover product line was removed and has no supported compatibility path.

Current maturity and known limits live in [`docs/STATUS.md`](docs/STATUS.md). Exact evidence interpretation lives in [`docs/VERIFICATION.md`](docs/VERIFICATION.md).

## What works

The current product includes:

- immutable `HarnessRunContract` attempt authority with caller/objective/context, Provider/Adapter, Tool catalog/grant, budgets, privacy and completion contract;
- independent SQLite Journal/CAS with leases, revision fencing, backup/restore and Doctor;
- durable Provider Call claim/dispatch/completion/failure state and response-loss recovery;
- durable Tool intent, dispatch fence, receipt/observation and Runtime reconciliation boundaries;
- Agent-owned WorkingSet/WorkingView selection separated from canonical history;
- caller interaction ingress that can remain transient or be explicitly promoted by the Agent into durable cognition;
- attempt-local Tool cognition that survives recovery but expires when a successor cognition attempt commits;
- bounded historical committed-cognition inspection and exact pin re-selection;
- cross-Run reusable cognition remains caller/domain-owned: an external owner selects and verifies an exact `HarnessWorkingViewSource`, then passes it through the existing `HarnessCognitionSeedSource` path; Harness adds no reusable-reference registry, resolver or topology ontology;
- request-bound `AgentTurnRequest.tools` and Harness-native capabilities, so installed mechanisms do not silently become current action authority;
- advanced opt-in bounded ToolProgram composition: the Agent may author one linear program over only the exact Tools admitted on that turn, while every inner step remains one normal physical Tool Call with existing budget, effect evidence, recovery and UNKNOWN semantics; intermediate Tool content is mechanically consumed and only one compact program result returns to the model;
- exact request-bound action truth stays on `AgentTurnRequest`; `HarnessAgentRun.explain()` reports validated in-process Contract/process composition directly, without an aggregate capability/workbench registry;
- exact request-bound Tool working-set subtraction remains in the existing turn projection; application/domain code owns current standing and branches directly on owner-native facts rather than compiling a second InteractionContext ontology;
- historical currentness-pressure experiments remain evidence that current standing can matter to Agent action choice, but the experimental generic InteractionContext/Affordance compiler is retired from current product code;
- `HarnessAgentRun` as the supported Python handle for normal state-root → Run composition and resume, with `HarnessAgentRun.explain()` for process-local composition inspection without Provider/Runtime liveness claims;
- observation-only source retrieval remains available through the existing Runtime-backed `search_workspace` / `workspace.read` mechanics plus exact Execution Binding and digest fences; caller/domain code owns source selection, authority-publication schemas and semantic projection rather than a Harness-specific observation ontology;
- durable `inspect` is the single exact Journal/CAS read view; CLI `explain` returns that same view plus explicit proof boundaries instead of maintaining a second workbench read model;
- one exact caller-authored `HarnessRunContract` as the execution-authority waist; higher-level allocation/orchestration and experimental loop-morphology selection do not get parallel Harness control planes;
- caller-defined structured completion shapes, with optional Contract-bound local structural conformance verification while semantic/evidence admission remains outside Harness;
- explicit non-support for a generic opaque Provider-continuation primitive in the contracted current core; Provider-local continuation remains integration-local unless new direct pressure earns a bounded surface;
- conservative UNKNOWN handling: ambiguous Provider or Tool delivery is reconciled from durable evidence rather than blindly repeated.

Detailed API and compatibility contracts are linked below instead of reproduced here.

## What it does not do

Harness does not:

- own Host Tasks, Assignments, commitments, `TaskOutcome`, or domain completion;
- import or require `ordivon-host`;
- own Runtime Workspace/Job/Attempt truth;
- infer external effect success from local or transport success;
- choose which evidence is semantically relevant to the Agent;
- own a global capability registry, semantic capability ranker, task-conditioned discovery service, or owner-currentness service; current affordances arrive from their actual caller/owner and never become authority merely by being retrieved;
- provide a generic Memory/RAG store, semantic ranking, automatic knowledge extraction, hidden cross-Run injection, or Harness-owned procedure evaluation/promotion service;
- own a Mandate/Profile/Strategy/Consumption layer, aggregate prior attempts into a generic selection context, choose/schedule a successor Run, or persist a second workflow/resource-allocation engine;
- turn Provider JSON Schema, cache locality, or Tool pruning into semantic policy;
- treat a model-correct Run conclusion as automatically authoritative outside the bounded Run.

If a new shared mechanism cannot survive deletion against Agent-owned choice, caller/domain ownership, or mature Provider/Runtime mechanics, it should remain deleted or local.

## Requirements

- Python 3.12;
- the exact Ordivon Protocol revision pinned by `pyproject.toml` and `uv.lock`;
- `uv` for repository workflows;
- Provider credentials only for the Provider profile actually used.

Repository checks use isolated Ruff rather than assuming it is installed inside the project environment:

```bash
uvx ruff==0.15.17 check src tests scripts
python scripts/check_dependencies.py
python scripts/check_docs.py
```

## Quick start

Set up and verify the checkout:

```bash
scripts/owner-environment bootstrap
scripts/owner-environment doctor
scripts/owner-environment test
rm -rf dist
uv build --wheel --out-dir dist
.venv/bin/python scripts/check_wheel.py "$(find dist -maxdepth 1 -type f -name '*.whl' -print -quit)"
```

The owner environment binds the exact development lint dependency separately from Harness runtime semantics; it does not reintroduce Host as a Harness dependency. `scripts/owner-environment cold-start` proves the default suite from an empty temporary venv.

Initialize an independent state root and inspect available capabilities:

```bash
ordivon-harness --state-root /var/lib/ordivon/harness store-init
ordivon-harness capabilities

```

A caller then supplies an exact Run Contract:

```bash
ordivon-harness --state-root /var/lib/ordivon/harness \
  run RUN_CONTRACT.json --message 'Start the bounded Run'

ordivon-harness --state-root /var/lib/ordivon/harness status HARNESS_RUN_ID
ordivon-harness --state-root /var/lib/ordivon/harness telemetry HARNESS_RUN_ID
ordivon-harness --state-root /var/lib/ordivon/harness inspect HARNESS_RUN_ID
ordivon-harness --state-root /var/lib/ordivon/harness explain HARNESS_RUN_ID
```

`capabilities` reports the exact generated package projection: installed built-in and specialized surfaces plus their source-owned digests and requirements. It does not search, rank, grant, or establish owner currentness. `explain` is a durable read model: it can prove Contract/Journal/CAS facts but deliberately does not invent whether an application-owned Adapter or Runtime client is currently live.

The CLI does not invent the Objective, Context, Tool grant, Provider, budget, or completion authority. See [`docs/QUICKSTART.md`](docs/QUICKSTART.md) for Contract construction, Python examples, cognition profiles, Tool-bearing Runtime clients, and structured completion.

## Public API

Use `ordivon_harness.api` for normal applications. The recommended execution handle is `HarnessAgentRun`: the caller supplies the exact Contract, Contract-bound Adapter factory, and any Runtime execution authority; Harness mechanically reconstructs the durable composition on resume. The former aggregate `ordivon_harness.capability_catalog` and generic task-conditioned capability-discovery layer are retired; exact request-bound action truth remains on `AgentTurnRequest` and process-local composition is exposed by `HarnessAgentRun.explain()`, while caller/domain current standing remains outside Harness and only exact already-admitted Tool subsets enter the existing turn projection; cross-Run knowledge/procedure selection remains external and enters Harness directly as exact cognition seed sources; bounded programmatic Tool composition/recovery lives in `ordivon_harness.tool_program*`; observation-only source retrieval uses the existing Runtime/search-read mechanics without a specialized Harness observation wrapper. These advanced mechanics are not promoted into the stable package-root facade. These projections/admission helpers do not grant authority or own external knowledge repositories/effects.

The current execution path is deliberately one waist:

```text
caller/domain/workflow/resource allocator
→ exact HarnessRunContract
→ HarnessAgentRun
```

Cross-Run budgeting, profile discovery, resource reallocation, successor selection, and retry policy remain with their actual caller/domain/workflow or mature external orchestrator. Harness does not maintain a second Mandate/Profile/Strategy/Consumption/CompiledAttempt authority above the Run Contract.

Use `ordivon_harness.api` as the supported application facade. Advanced integrations import the explicit owner modules for Store, Continuity, Provider, Runtime, or recovery primitives; the duplicate `ordivon_harness.core` aggregation facade and historical `Standalone*` aliases are retired. Historical names remain documented in the changelog rather than kept as live compatibility surfaces.

Exact supported exports and upgrade expectations are owned by [`docs/COMPATIBILITY.md`](docs/COMPATIBILITY.md), not by this summary.

## Operator interface

Operators normally need five questions:

```bash
ordivon-harness --state-root /var/lib/ordivon/harness status HARNESS_RUN_ID
ordivon-harness --state-root /var/lib/ordivon/harness telemetry HARNESS_RUN_ID
ordivon-harness --state-root /var/lib/ordivon/harness inspect HARNESS_RUN_ID
ordivon-harness --state-root /var/lib/ordivon/harness recover HARNESS_RUN_ID
ordivon-harness --state-root /var/lib/ordivon/harness doctor
```

`telemetry` is a read-only projection over exact Harness state: it normalizes usage, budget remainder, Provider cache hit/miss counters when present, and recovery/UNKNOWN context. Cache metrics are measurement only; they never become cognition or semantic policy. `inspect` remains the exact deeper evidence escape hatch.

Recovery is evidence-driven. A dispatched operation with uncertain physical outcome is not automatically safe to repeat. `doctor` is the authority-wide history replay; normal Run reopen validates the relevant Run before new execution.

See [`docs/OPERATIONS.md`](docs/OPERATIONS.md) for backup/restore, cancellation, concurrent worker fencing, Provider/Tool UNKNOWN, and escalation.

## Documentation map

Choose the document for the job you have:

| Need | Read |
| --- | --- |
| understand why Harness exists and where it stops | this README |
| perform a first Run | [`docs/QUICKSTART.md`](docs/QUICKSTART.md) |
| understand semantic ownership and internal state domains | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| inspect current maturity and known limits | [`docs/STATUS.md`](docs/STATUS.md) |
| look up supported API/dependency compatibility | [`docs/COMPATIBILITY.md`](docs/COMPATIBILITY.md) |
| decide what a receipt or experiment actually proves | [`docs/VERIFICATION.md`](docs/VERIFICATION.md) |
| operate, recover, back up, cancel or diagnose | [`docs/OPERATIONS.md`](docs/OPERATIONS.md) |
| understand retention and private-content authority | [`docs/DATA_AND_PRIVACY.md`](docs/DATA_AND_PRIVACY.md) |
| understand release/deprecation rules | [`docs/RELEASES.md`](docs/RELEASES.md) |
| inspect which document owns which fact | [`docs/authority.md`](docs/authority.md) |
| inspect research derivation and historical closeouts | linked research/closeout documents and `evidence/index.json` |

Research phases remain valuable evidence, but a reader does not need to learn their numbering before understanding the current product.

## Security and data

The Run Contract privacy policy is execution authority. Default `metadata-only` continuity can preserve identities, digests, causal/effect receipts and budgets without retaining exact model or Tool content. Exact model/Tool recovery across process loss requires the corresponding private-content authority; Harness does not recover forbidden content from a hidden second store.

Tool and Provider effect fencing remains independent of content retention. A digest-only durable Provider Call can still block duplicate physical dispatch after response loss.

See [`docs/DATA_AND_PRIVACY.md`](docs/DATA_AND_PRIVACY.md) and [`SECURITY.md`](SECURITY.md).

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
