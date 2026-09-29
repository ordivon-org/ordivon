# Agent Run Binding R1 — Non-authoritative Run Assembly Projection

Date: 2026-09-23
Status: **R1 MECHANICAL CONTRACT**

## Decision

`AgentRunBinding` is a disposable, deterministic task-local projection that binds exact
caller-selected component identities for one prospective Agent Run.

It exists to remove human digest/reference bookkeeping without moving authority into
Composition.

```text
already-compiled Cognitive Circuit
        +
exact Harness Run Contract identity
        +
exact Provider adapter binding
        +
optional Tool / execution / cognition bindings
        ↓
AgentRunBinding
        ↓
owner-specific consumer revalidation
```

## What it owns

Only mechanical binding structure:

- exact source Cognitive Circuit reference;
- exact Run Contract reference;
- exact adapter binding reference;
- optional exact Tool binding reference;
- optional exact execution binding reference;
- zero or more exact cognition binding references;
- explicit unresolved-input identifiers;
- one canonical binding digest.

## What it does not own

It does not:

- interpret or validate `HarnessRunContract` semantics;
- discover or rank Providers;
- discover or grant Tools;
- select Skills;
- authorize credentials or execution;
- dispatch work;
- own Runtime Job/Attempt truth;
- own Host/Task/workflow/session truth;
- establish Tool/provider availability;
- establish verification closure or domain acceptance.

`readyForHarness=true` means only that this projection has no declared unresolved inputs. A
Harness-facing consumer still independently validates its own contract/binding semantics.

## Deletion law

Deleting this projection must not destroy any canonical owner truth. Given the same exact
input references, recompilation produces the same `bindingDigest`.

## Cross-owner lowering boundary

Composition still stops before `CognitiveCircuit -> HarnessRunContract` lowering. The bounded
C06 implementation lives in `apps/agent`, where the product-side consumer may project a
resolved Circuit plus exact caller-selected fields into the public Harness owner contract.
That adapter derives only the exact Circuit/objective references and canonical no-Tool
digests; it owns no Provider/model selection, Tool discovery/grant, authority, workflow,
Runtime effect, or domain verdict.
