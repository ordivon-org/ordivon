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

## Live model-specific profile

`scripts/run_adaptive_edit_r2_live_ab.py` now provides an explicit, opt-in live Provider A/B runner. Ordinary regression tests import and test its treatment fencing and Runtime-shaped in-memory fixture but do not contact DeepSeek.

The first corrected live profile used:

```text
provider/model:      deepseek / deepseek-flash
task:                HARNESS-REPO-REPAIR-001
max model calls:     6
max tool calls:      8
max total tokens:    64,000
replicates/codec:    5
```

The semantic acceptance gate was the existing visible suite plus hidden verifier. Exact oracle bytes were auxiliary only.

Observed corrected outcomes:

```text
exact-replacement-v1:
  hidden verifier       5/5
  candidate_completed   5/5
  rejected observations 0
  total model calls     22
  total tool calls      27
  total tokens          89,864

anchored-line-v1:
  hidden verifier       4/5
  candidate_completed   3/5
  rejected observations 1
  total model calls     26
  total tool calls      33
  total tokens          114,992
```

For this **model + task + date only**, `exact-replacement-v1` is therefore the provisional preferred codec. Its corrected runs used about 21.86% fewer tokens in aggregate than the anchored treatment.

This is deliberately **not** a global default. The deterministic repeated-text falsifier still proves a case where exact replacement must fail closed as ambiguous while anchored addressing succeeds. The right interpretation is model/task-specific profiling plus structural fallback capability, not universal preference for either protocol.

The evidence is retained in:

```text
evidence/adaptive-edit-r2-live-ab-deepseek-flash-20260914.json
```

with canonical payload digest:

```text
sha256:e36864e2487a555289cfb0df0481b3c8c00ad9d4a7cf7593ca298f20082ea0ec
```

A preceding 24k-token pilot is retained as diagnostic-only evidence. It is explicitly excluded from treatment standing because Harness's conservative Provider request-token upper-bound preflight prevented the fourth Provider turn in all four pilot runs. The corrected profile uses identical 64k token authority for both treatments.

One isolated DeepSeek response also violated the Adapter's finish-reason invariant. The invariant was not weakened. Four subsequent wire-shape responses and two formal Adapter invocations were normal, so the anomalous sample is retained without claiming a persistent API-shape drift.

## Current deliberate limits

- one semantic edit per file per compiled plan;
- existing UTF-8 text files only;
- no conventional unified/apply-patch codec yet;
- `edit_workspace` is internal composition only, not part of the default public Tool surface;
- no automatic codec fallback dispatcher yet;
- only one live model/task profile exists, so no global selection policy is authorized;
- no LSP WorkspaceEdit expansion yet.

These limits prevent the prototype from inventing ordering/fallback semantics before evidence requires them.

## Next integration step

1. add additional task families, especially edits with repeated textual targets and multi-region changes;
2. add additional model/provider profiles under the same fixed-budget protocol;
3. permit automatic codec selection only from explicit profile evidence and structural applicability checks;
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

## Second live profile — repeated-target addressing

R2 now has a second task family designed to pressure edit addressing rather than broad repair reasoning:

```text
HARNESS-EDIT-ADDRESSING-002
```

The model-visible file contains two identical `return False` lines. Only `beta_enabled()` may become `True`; `alpha_enabled()` must remain `False`. The visible suite checks beta, while the hidden verifier additionally protects alpha and the public function surface. Exact replacement is not artificially disabled: the Agent may widen `oldText` to include unique surrounding context.

Using the same DeepSeek Flash limits as the first corrected profile:

```text
max model calls:     6
max tool calls:      8
max total tokens:    64,000
replicates/codec:    5
```

Primary corrected results:

```text
exact-replacement-v1:
  hidden verifier       5/5
  candidate_completed   5/5
  rejected observations 0
  total model calls     20
  total tool calls      25
  total tokens          51,266
  oracle-exact          5/5

anchored-line-v1:
  hidden verifier       5/5
  candidate_completed   5/5
  rejected observations 0
  total model calls     20
  total tool calls      25
  total tokens          52,336
  oracle-exact          4/5
```

The aggregate token difference is only 2.05%, with no model-call, Tool-call, correction, visible-pass, hidden-pass, or candidate-completion advantage. The standing is therefore:

```text
deepseek-flash + HARNESS-EDIT-ADDRESSING-002 + 2026-09-14
    -> NO_CLEAR_WINNER_BOTH_VIABLE
```

This materially narrows the first profile's interpretation. `deepseek-flash` should **not** be treated as globally preferring exact replacement merely because exact won on `HARNESS-REPO-REPAIR-001`. Repeated local text also does not imply exact replacement is unusable: on this task the model consistently widened exact context and reached the correct edit. Anchored addressing remains independently valuable because it exposes direct location semantics and the deterministic ambiguity falsifier still proves cases where a too-narrow exact replacement must fail closed.

The second profile is retained in:

```text
evidence/adaptive-edit-r2-live-ab-deepseek-flash-addressing-20260914.json
```

with canonical payload digest:

```text
sha256:fb3c3ff88821c0300ee87110e06a9abadfd3a065c2bc4cc1a46777ec647613cc
```

The first task-2 live attempt completed all six Provider runs successfully but exposed a live-runner reporting defect: float-valued summary means violated Harness canonical JSON before report persistence. The runner now records integer totals plus `meansTimes10`, and an offline test requires the complete summary carrier to pass canonical encoding before future live use. That diagnostic attempt is excluded from the primary profile.

### Selection consequence

The evidence now supports a two-factor decision rule rather than a universal codec ranking:

```text
structural applicability
        +
model/task profile evidence
        -> codec preference, if any
```

If the profile has no meaningful winner, both codecs remain available and the narrowest mechanically valid representation should be selected without inventing a performance preference.
