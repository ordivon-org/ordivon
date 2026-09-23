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

## Future lowering boundary

R1 deliberately stops before `CognitiveCircuit -> HarnessRunContract` lowering. That next
adapter belongs at the cross-owner consumer seam and must consume public owner contracts
rather than importing owner internals into Composition.
