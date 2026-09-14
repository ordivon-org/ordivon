# Adaptive Edit Gateway R2

Status: **AGENT-FACING INTERNAL PATH WIRED / DURABLE EFFECT BACKEND WIRED / MECHANICAL BENCHMARK PASS**
Date: 2026-09-14

## Scope

R2 proves the first replaceable Harness mechanism behind the new port-composition direction. It does **not** change the public Harness API or current default Agent Tool surface.

The current internal path is:

```text
read_workspace
        -> exact Runtime content + digest
        -> Harness-generated line anchors
        -> edit_workspace(sourceDigest + selected codec)
        -> fresh source fence check
        -> CanonicalEditPlan
        -> existing durable Runtime workspace.patch / workspace.patch.get
```

Runtime remains the physical mutation/reconciliation authority. Harness owns the Agent-facing encoding, Run authority, Tool intent/receipt, and recovery interpretation.

## Implemented codecs

### exact-replacement-v1

Input intent:

```text
relativePath + sourceDigest + unique oldText + newText
```

The codec requires exactly one old-text occurrence in the exact source snapshot and mechanically computes Runtime's one-based line / Unicode-column range.

### anchored-line-v1

Editable reads now return Harness-generated anchors for every line. An edit names start/end anchors plus replacement content. The codec validates both anchors against the exact re-read source snapshot and derives `expectedText` and coordinates mechanically.

This is Hashline-like but deliberately not OMP wire-format compatible. The reusable primitive is **anchored edit encoding**, not one product syntax.

## Exact source snapshot fencing

`edit_workspace` requires the exact `sourceDigest` returned by `read_workspace`.

Before any durable Patch intent is admitted, the internal `AdaptiveEditRuntimeBridge` performs a fresh complete `workspace.read` of the requested path and requires:

```text
observed current digest == edit_workspace.sourceDigest
```

If the file changed, the Tool fails as model-correctable before `workspace.patch` admission. The source digest is therefore an edit precondition, not mutation authority; path authority still comes from the exact Run Tool Grant.

Editable read observations also include:

```text
editSnapshot.relativePath
editSnapshot.sourceDigest
editSnapshot.lineAnchors[]
editSnapshot.codecs[]
```

The model does not calculate anchor hashes itself.

## Canonical lowering

Both codecs produce the same Runtime-native representation:

- exact `relativePath`;
- full-file `expectedDigest`;
- exact Runtime text range;
- exact `expectedText`;
- replacement text.

`lower_plan_to_runtime_patch()` derives the stable `clientRequestId` through existing `HarnessExecutionBinding.patch_request_id()` and emits the existing Runtime `workspace.patch` request.

No codec writes files directly.

## Durable effect integration

The existing `SQLiteHarnessRuntimeBridge` had dormant `patch_workspace -> workspace.patch` lowering but previously admitted only `workspace.exec` and `workspace.read`. R2 completes the generic physical backend without changing the default Tool surface:

- `workspace.patch` is admitted only when the concrete bridge declares `WORKSPACE_CHANGE_POSSIBLE`;
- the normal Harness Tool intent/fence/receipt chain remains authoritative for the Agent Run;
- the original logical Tool identity remains `edit_workspace`, even though the physical Runtime operation is `workspace.patch`;
- a direct Runtime Patch receipt becomes an ordinary Tool Observation;
- ambiguous delivery is reconciled only through `workspace.patch.get`;
- `prepared` becomes a model-correctable rejected observation because Runtime has proven the before-state;
- `unknown` remains UNKNOWN and cannot authorize redispatch or codec fallback;
- the default observation-only bridge cannot patch even if a caller accidentally supplies a patch-shaped Tool definition.

A complete scripted Agent loop now passes:

```text
read_workspace -> edit_workspace -> candidate_completed
```

## Mechanical benchmark

`scripts/check_adaptive_edit_r2_benchmark.py` is a deterministic ACI benchmark. It deliberately makes **no** model-quality, token-efficiency, latency, or broad repository-repair success claim.

### Existing repository-repair fixture

For `HARNESS-REPO-REPAIR-001`, both codecs encode the known semantic repair and produce the oracle bytes:

```text
exact-replacement-v1  -> oracle PASS
anchored-line-v1      -> oracle PASS
Runtime file patch    -> identical for both codecs
fuzzy matching        -> none
human byte repair     -> none
```

### Repeated-text addressing falsifier

For a file containing two identical `value = 1` lines where only the second should change:

```text
exact-replacement-v1 -> fail closed: ambiguous oldText
anchored-line-v1     -> exact second-line edit PASS
```

This gives adaptive selection a concrete mechanical basis: exact replacement is simpler for unique text; anchored addressing is useful when text identity alone is insufficient.

### Stale-anchor falsifier

An anchor generated from a previous source snapshot is rejected against changed current content.

Historical P2 evidence remains contextual rather than replayed benchmark data: it recorded two malformed Agent-authored unified diffs rejected before materialization followed by successful exact-oldText/newText encoding.

## Current deliberate limits

- one semantic edit per file per compiled plan;
- existing UTF-8 text files only;
- no conventional unified/apply-patch codec yet;
- `edit_workspace` is internal composition only, not part of the default public Tool surface;
- no automatic codec fallback dispatcher yet;
- no live model-profile performance table yet;
- no LSP WorkspaceEdit expansion yet.

These limits prevent the prototype from inventing ordering/fallback semantics before evidence requires them.

## Next integration step

1. run the same edit tasks through real Provider/model trials with exact fixed budgets;
2. record per-model protocol success, correction turns, observation bytes, tokens, and latency;
3. only permit automatic codec selection from measured profile evidence;
4. add a mature conventional patch donor only if it can compile to `CanonicalEditPlan` without owning physical writes;
5. route LSP `WorkspaceEdit` through the same canonical edit boundary;
6. promote a generic edit-provider port only if a second implementation needs the same boundary.

## Invariants already proven

- ambiguous exact replacement fails before Runtime;
- absent source text fails before Runtime;
- no-op fails before Runtime;
- forged/stale anchor fails before Runtime;
- stale `sourceDigest` fails before Patch admission;
- both codecs bind the exact source digest into Runtime Patch;
- multi-file canonical plans lower to one Runtime Patch request;
- exact replay derives the same Runtime Patch request identity;
- ambiguous Patch response loss is reconciled only through `workspace.patch.get`;
- committed reconciliation never redispatches the Patch;
- prepared reconciliation is explicit `not_committed` and may authorize correction at a higher layer;
- `unknown` reconciliation never becomes codec-fallback authority;
- the generic durable Tool bridge preserves `WORKSPACE_CHANGE_POSSIBLE` consequence through Patch intent/receipt;
- complete Agent-loop execution preserves Run Contract authority;
- codec selection is a measured-profile input rather than a universal Hashline default.
