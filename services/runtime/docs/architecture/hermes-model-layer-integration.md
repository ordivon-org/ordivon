# Hermes Runtime Integration Into The Model Layer

This document is subordinate to the canonical structure in [architecture-baseline](./architecture-baseline.md). If wording here conflicts with the baseline, the baseline wins.

## Why This Is The Next Step

`financial-ai-os` has finished a closure pass that tightened product truthfulness, capability boundaries, and side-effect discipline. That was necessary, but it does not by itself create a learning loop.

Right now the `intelligence/` layer is still effectively a stub:

- `shared.config.settings` exposes only `reasoning_provider = "mock"`
- `intelligence/models/router.py` always returns `MockReasoningProvider`
- `orchestrator/workflows/analyze.py` can run the chain, but the AI part only produces static mock analysis

By contrast, `hermes-runtime` already provides:

- runtime provider resolution across many model backends
- smart cheap-vs-strong model routing
- agentic tool execution
- delegation and subagents
- memory providers and turn/session sync
- context-engine abstraction
- mixture-of-agents support for difficult tasks

That means Hermes should not be treated as "just another LLM client". It should become the execution-grade runtime beneath our AI-facing layer.

## The Correct Integration Point

Hermes should be integrated under `intelligence/`, not under:

- `capabilities/`
- `apps/api/`
- `governance/`
- `execution/` directly

### Recommended placement

- `intelligence/runtime/hermes_runtime_adapter.py`
- `intelligence/providers/hermes_agent_provider.py`
- `intelligence/tasks/`
- `intelligence/contracts/agent_actions.py`

### Why this layer

`intelligence/` already owns:

- prompt and model-facing behavior
- provider routing
- reusable AI task definitions

Hermes is a runtime for executing AI tasks with tools, memory, delegation, and model routing. That is a model/runtime concern, not a business capability and not a UI/API concern.

## What Hermes Should Do For Us

Hermes should become the runtime that executes bounded AI tasks and emits structured results, not the owner of business semantics.

### Hermes should own

- model/provider selection
- smart routing between cheap and strong models
- optional subagent delegation
- tool execution
- memory/session mechanics
- context compression and recall
- multi-model aggregation where justified

### PFIOS should still own

- domain objects
- workflow sequencing
- governance decision semantics
- audit persistence
- report lineage
- outcome tracking
- recommendation/review lifecycle meaning

In short:

- Hermes decides how AI work is executed
- PFIOS decides what the business objects mean and how they connect

## Target Architecture

### Current

`API -> capability -> orchestrator -> intelligence.mock -> governance -> audit/report`

### Target

`API -> capability -> orchestrator workflow -> intelligence task provider -> Hermes runtime -> structured task result -> governance -> audit/report/outcome`

## Integration Model

Do not expose the entire Hermes conversation model to PFIOS.

Instead, wrap Hermes as a bounded task runtime with explicit task contracts.

### Task types to support first

1. `analysis.generate`
2. `recommendation.refine`
3. `review.draft`
4. `report.summarize`
5. `lesson.extract`

Each task should have:

- structured input contract
- structured output contract
- action record
- upstream references
- downstream references
- runtime metadata

## The Missing Object We Need

Before Hermes can create durable accumulation, PFIOS needs an explicit AI action record.

### Introduce `AgentAction`

Suggested fields:

- `action_id`
- `task_type`
- `actor_type` = `ai`
- `actor_runtime` = `hermes`
- `provider`
- `model`
- `session_id`
- `status`
- `started_at`
- `completed_at`
- `reason`
- `idempotency_key`
- `input_summary`
- `input_refs`
- `output_summary`
- `output_refs`
- `tool_trace_ref`
- `memory_write_refs`
- `delegation_trace`
- `error`
- `metadata`

This object should sit in PFIOS state/domain storage, not inside Hermes.

Hermes may generate runtime traces, but PFIOS must persist the business-facing action record.

## Recommended First Implementation Slice

### Phase 1: Replace Mock Analysis With A Hermes-backed Provider

Goal: keep the workflow shape unchanged while swapping the reasoning engine from static mock output to an agentic runtime-backed provider.

### New files

- `intelligence/providers/hermes_agent_provider.py`
- `intelligence/runtime/hermes_runtime_adapter.py`
- `intelligence/contracts/agent_actions.py`

### Existing files to update

- `shared/config/settings.py`
  - add `reasoning_provider = "hermes" | "mock"`
  - add Hermes config such as runtime path, model, provider, base URL, API mode
- `intelligence/models/router.py`
  - route to `HermesAgentProvider` when configured
- `intelligence/engine.py`
  - keep interface stable, still returning `AnalysisResult`
- `orchestrator/workflows/analyze.py`
  - after AI analysis returns, persist an `AgentAction`
  - thread `agent_action_id` into audit/report metadata
- `governance/audit/*`
  - include `agent_action_id` in audit payload when analysis came from Hermes

### Hermes adapter responsibilities

- launch or invoke Hermes runtime in a controlled way
- pass a bounded task payload instead of an open-ended conversation
- collect:
  - chosen model/provider
  - task output
  - tool execution metadata
  - memory/delegation metadata if available
- normalize into a PFIOS-side structured result

### Provider responsibilities

`HermesAgentProvider.analyze(ctx)` should still return a domain `AnalysisResult`, but with metadata like:

- `provider = "hermes"`
- `runtime_provider`
- `runtime_model`
- `agent_action_id`
- `task_type = "analysis.generate"`

## How Hermes Should Be Invoked

There are three possible approaches.

### Option A: subprocess runtime wrapper

PFIOS shells out to Hermes with a dedicated task payload and reads back structured JSON.

Pros:

- fastest to prove
- least invasive to Hermes
- keeps runtime isolated

Cons:

- weaker structured observability unless we standardize output carefully

### Option B: Python-side adapter using Hermes internals

PFIOS imports Hermes modules directly and uses its runtime/provider resolution/tool stack in-process.

Pros:

- richest metadata access
- easier to capture session IDs, delegation, memory hooks

Cons:

- tighter dependency coupling
- more fragile against Hermes internal changes

### Option C: service boundary

Run Hermes as a dedicated runtime service and call it through a local RPC/API boundary.

Pros:

- strongest operational separation
- good for future multi-agent scaling

Cons:

- most setup overhead now

### Recommendation

Start with **Option A**, but shape the adapter API so it can later move to Option B or C without changing orchestrator contracts.

## Why Not Use Hermes Everywhere Immediately

If Hermes is injected too high in the stack, it will blur semantics again.

Bad pattern:

- capability calls Hermes directly
- Hermes decides business lifecycle meaning
- audit/report/outcome become post-hoc guesses

Good pattern:

- orchestrator declares a task
- intelligence provider runs Hermes
- Hermes returns a bounded result
- PFIOS persists domain objects and action lineage

## The Learning Loop We Actually Want

The target is not "Hermes can answer more flexibly".

The target is:

`Hermes action -> persisted AgentAction -> recommendation/review/audit/report/outcome linkage -> lesson extraction -> future task improvement`

This is what turns runtime intelligence into system accumulation.

## Minimal Closed Loop After Integration

### Analyze flow

1. user/API triggers analyze
2. orchestrator builds context
3. Hermes-backed provider executes `analysis.generate`
4. PFIOS stores `AgentAction`
5. PFIOS stores `AnalysisResult`
6. governance evaluates
7. recommendation may be created
8. audit records reference both analysis and action
9. report references the same lineage
10. later outcome/review can attribute success/failure back to the originating AI action

## What To Build Immediately After Phase 1

### Phase 2: agent action persistence

Add persistent storage and repository/service support for `AgentAction`.

### Phase 3: review and lesson extraction tasks

Use Hermes for:

- review draft generation
- lesson candidate extraction
- report synthesis

Each must write another `AgentAction`.

### Phase 4: outcome feedback

When outcome closes the loop, write feedback against:

- `recommendation_id`
- `analysis_id`
- `agent_action_id`
- `task_type`
- `model/provider`

That makes performance statistically attributable.

## Concrete Recommendation

The next engineering move should be:

1. add a Hermes-backed provider under `intelligence/`
2. keep the current orchestrator workflow shape
3. introduce `AgentAction` persistence immediately with the provider rollout
4. wire `agent_action_id` into audit/report metadata
5. only then expand Hermes into review/report/lesson tasks

This keeps the first step small enough to land while still moving toward the real goal:

`an AI runtime that can execute work, accumulate evidence, and become part of the system's learning flywheel instead of remaining a stateless text generator.`

## Current Default Runtime Binding

The repository is now wired so PFIOS can call Hermes through the local bridge without importing Hermes internals.

### Current defaults

- `PFIOS_REASONING_PROVIDER=hermes`
- `PFIOS_HERMES_BASE_URL=http://127.0.0.1:9120/pfios/v1`
- `PFIOS_HERMES_DEFAULT_PROVIDER=gemini`
- `PFIOS_HERMES_DEFAULT_MODEL=google/gemini-3.1-pro-preview`

On the Hermes side the bridge reports and uses:

- `HERMES_PFIOS_PROVIDER=gemini`
- `HERMES_PFIOS_MODEL=google/gemini-3.1-pro-preview`

This means the remaining operational requirement is just:

1. start Hermes bridge
2. point PFIOS at Hermes
3. let PFIOS call Hermes over HTTP for `analysis.generate`

No extra provider-specific wiring is required inside PFIOS as long as Hermes already has the Gemini credentials configured.
