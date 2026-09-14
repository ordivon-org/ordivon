# Adaptive Edit Gateway R2

Status: **PROTOTYPE IMPLEMENTED / INTERNAL**  
Date: 2026-09-14

## Scope

R2 proves the first replaceable Harness mechanism behind the new port-composition direction. It does **not** change the public Harness API or current default Agent Tool surface.

The prototype separates:

```text
model-facing edit codec
        -> CanonicalEditPlan
        -> existing Runtime workspace.patch
```

Runtime remains the physical mutation/reconciliation authority.

## Implemented codecs

### exact-replacement-v1

Input intent:

```text
relativePath + unique oldText + newText
```

The codec requires exactly one old-text occurrence in the exact source snapshot and mechanically computes Runtime's one-based line / Unicode-column range.

### anchored-line-v1

The Harness can project an exact source snapshot as:

```text
<line>.<content-derived-tag>  line text
```

An edit names start/end anchors plus replacement content. The codec validates both anchors against the same exact source digest and derives `expectedText` and coordinates mechanically.

This is Hashline-like but deliberately not OMP wire-format compatible. The reusable primitive is **anchored edit encoding**, not one product syntax.

## Canonical lowering

Both codecs produce the same:

- exact `relativePath`;
- full-file `expectedDigest`;
- exact Runtime text range;
- exact `expectedText`;
- replacement bytes/text.

`lower_plan_to_runtime_patch()` then derives the stable `clientRequestId` through existing `HarnessExecutionBinding.patch_request_id()` and emits the existing Runtime `workspace.patch` request.

No codec writes files directly.

## Current deliberate limits

- one semantic edit per file per compiled plan;
- existing text files only;
- no conventional unified/apply-patch codec yet;
- no public `edit_workspace` Tool yet;
- no automatic codec fallback dispatcher yet;
- no LSP WorkspaceEdit expansion yet.

These limits prevent the prototype from inventing ordering/fallback semantics before the first real Agent integration requires them.

## Next integration step

1. bind exact `workspace.read` content/digest as `SourceSnapshot` inside one Agent attempt;
2. expose an internal `edit_workspace` action using a selected codec;
3. record one normal Harness Tool intent before physical patch admission;
4. dispatch only `workspace.patch`;
5. on response loss reconcile the same request through `workspace.patch.get`;
6. only permit codec fallback while no physical patch operation has been admitted;
7. benchmark exact replacement vs anchored encoding on the existing repository-repair workload.

## Invariants already proven by the prototype

- ambiguous exact replacement fails before Runtime;
- absent source text fails before Runtime;
- no-op fails before Runtime;
- forged/stale anchor fails before Runtime;
- both codecs bind the exact source digest into Runtime Patch;
- multi-file plans lower to one Runtime Patch request;
- exact replay derives the same Runtime Patch request identity;
- ambiguous Patch response loss is reconciled only through `workspace.patch.get`;
- committed reconciliation never redispatches the Patch;
- prepared reconciliation is explicit `not_committed` and may authorize correction at a higher layer;
- `unknown` reconciliation never becomes codec-fallback authority;
- codec selection is a measured-profile input rather than a universal Hashline default.
