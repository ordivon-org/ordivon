# Ordivon Agent App

`apps/agent` is the product/consumer composition surface for starting bounded Agent Runs.

The first HUX-30 slice is deliberately small:

```text
Cognitive Circuit
      +
exact caller-authored HarnessRunContract
      +
exact caller-selected adapter binding reference
      ↓
no-Tool Harness lowering
      ↓
AgentRunBinding
      ↓
HarnessAgentRun.create(...)
```

This app owns UX/composition glue only. It does not own Task truth, provider selection,
Tool discovery or authorization, Runtime execution truth, Host continuity, workflow state,
credentials, or domain completion.

HUX-30 accepts only the canonical no-Tool Harness surface and no cognition/execution
binding. Later HUX waves may add separate lowerers after real-consumer evidence; they must
not widen this function implicitly.

## Verify

```bash
mise run verify
```
