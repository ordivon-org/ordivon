# Ordivon Agent App

`apps/agent` is the product/consumer composition surface for starting bounded Agent Runs.

The first HUX-30 slice is deliberately small:

```text
Cognitive Circuit
      +
exact caller-selected Harness inputs
      ↓
no-Tool HarnessRunContract lowering
      +
exact caller-selected adapter binding reference
      ↓
no-Tool Harness binding lowering
      ↓
AgentRunBinding
      ↓
HarnessAgentRun.create(...)
```

This app owns UX/composition glue only. It does not own Task truth, provider selection,
Tool discovery or authorization, Runtime execution truth, Host continuity, workflow state,
credentials, or domain completion.

HUX-30 accepts only the canonical no-Tool Harness surface and no cognition/execution
binding. C06 adds only a deterministic consumer-side projection from a resolved Circuit plus
explicit caller selections into the public HarnessRunContract. It derives the exact Circuit
and objective references plus canonical no-Tool digests; it does not select a Provider, model,
adapter, budget, context, privacy policy, Tool, authority, or domain outcome. Later HUX waves may add separate lowerers after real-consumer evidence; they must
not widen this function implicitly.

## Product Run view

HUX-40 adds a lossy read-only projection over an already validated `HarnessAgentRun`:

```text
Harness exact status + composition projection
                  ↓
        Ordivon Agent Run View
ready / running / attention_required / stopped / run_finished / failed
```

`run_finished` means only that the bounded Harness Run reached its durable terminal
state. The product view always reports that Harness has not established Task/domain
semantic acceptance, and it never probes Provider or Runtime liveness. The exact Harness
projection remains the proof surface.

## Verify

```bash
mise run verify
```
