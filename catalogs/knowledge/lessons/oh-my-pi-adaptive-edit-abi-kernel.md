# Oh My Pi Adaptive Edit ABI Kernel — extracted design and prototype specification

Status: **REGISTERED / PROTOTYPE-READY**  
Registered: 2026-09-14

## One-sentence model

**An Adaptive Edit ABI lets the model express the semantic source change through a protocol suited to that model, while deterministic infrastructure owns parsing, stale-source detection, normalization and exact lowering to a stronger physical mutation primitive.**

## Problem

Models often know *what* code should change while failing at mechanical encodings such as unified-diff hunk arithmetic, line drift, escaping or exact context reproduction.

A coding harness therefore should not make one edit syntax part of semantic truth.

OMP demonstrates multiple edit modes (`hashline`, `apply_patch`, `patch`, `replace`) and selects the active wire contract using model/configuration context. The important primitive is **protocol negotiation**, not Hashline itself.

## Ordivon ownership

```text
Harness owns:
  edit protocol selection
  parser/normalizer
  model-visible diagnostics
  semantic edit intent correlation

Runtime owns:
  exact Workspace state
  digest/expected-text fences
  physical mutation
  patch receipt
  response-loss reconciliation
```

No edit codec may replace `workspace.patch` as physical truth.

## Architectural laws

1. **Edit protocol != physical mutation protocol.**
2. **Model chooses semantic content; infrastructure owns mechanical translation.**
3. **A stale or unseen source basis fails closed or is uniquely recoverable; it is never silently guessed.**
4. **Protocol fallback is allowed only before any physical commit.**
5. **After an uncertain physical commit, reconcile the original operation; never try another codec under a new identity.**
6. **Edit mode is selected by measured model/profile performance, not fashion.**
7. **All protocols lower to one canonical exact edit plan.**

## Minimal data model

```ts
type EditProtocol = "anchored" | "replace" | "apply_patch";

type SourceSnapshot = {
  workspaceId: string;
  path: string;
  digest: string;
  visibleRanges?: Array<{startLine:number; endLine:number}>;
  shortTag?: string;          // convenience only, never physical authority
};

type SemanticEditRequest = {
  requestId: string;
  protocol: EditProtocol;
  payload: string | object;
  snapshots: SourceSnapshot[];
};

type CanonicalEdit = {
  path: string;
  expectedDigest: string;
  edits: Array<{
    startLine: number;
    startColumn: number;
    endLine: number;
    endColumn: number;
    expectedText: string;
    replacementText: string;
  }>;
};

type EditPlan = {
  requestId: string;
  protocol: EditProtocol;
  files: CanonicalEdit[];
  warnings: string[];
};
```

The exact Runtime DTO may differ. The key property is that every model-facing protocol converges onto the same exact before-state + replacement semantics.

## Protocol A: anchored/hashline-like editing

Minimum syntax for a prototype:

```text
[path#TAG]
PUT 10.=12:
+replacement line 1
+replacement line 2
```

Required behavior:

- `TAG` maps to one previously exposed source snapshot;
- line anchors refer to that snapshot, not a moving intermediate file;
- multiple operations for the same path are normalized against the same original snapshot;
- overlapping regions are rejected;
- unobserved/elided regions may be rejected when the observation layer tracks visibility;
- exact current digest is checked before Runtime commit.

A four-character tag can improve model ergonomics, but `expectedDigest` remains the real identity.

## Protocol B: exact replacement

Minimum request:

```json
{
  "path": "src/a.ts",
  "oldText": "exact unique source",
  "newText": "replacement"
}
```

Rules:

- target must exist exactly once;
- complete file digest is still carried to Runtime;
- zero matches -> stale/incorrect source;
- multiple matches -> ambiguous edit;
- no-op -> explicit error.

This is already strongly supported by historical Ordivon evidence and should remain the baseline comparator.

## Protocol C: conventional patch

Keep unified/apply-patch only where a model/profile demonstrates reliable formatting or an external producer already emits patch format.

Parser responsibilities:

- parse and validate every file/hunk before physical mutation;
- resolve exact old text against the current bound snapshot;
- convert to `CanonicalEdit[]`;
- reject ambiguous/fuzzy application unless an explicitly proven deterministic algorithm yields one unique result.

## Protocol selection

Prototype selector:

```ts
function chooseProtocol(profile: ModelProfile, task: EditTask): EditProtocol {
  if (profile.measuredEditWinner) return profile.measuredEditWinner;
  if (task.requiresLargeMove && profile.patchReliable) return "apply_patch";
  if (profile.anchorReliable) return "anchored";
  return "replace";
}
```

Do not use user-agent/model-name hardcoding as the final mechanism. Persist benchmark results keyed by meaningful model/profile identity.

Suggested score:

```text
score = semantic_success_rate
      - syntax_failure_rate * penalty
      - correction_turns * penalty
      - output_tokens * small_penalty
```

Correctness dominates token efficiency.

## Control flow

```text
1. Harness reads source through exact Workspace observation.
2. Harness records SourceSnapshot(digest, optional visible ranges/tag).
3. Selector chooses model-facing EditProtocol.
4. Model emits SemanticEditRequest.
5. Protocol parser validates syntax and source references.
6. Normalizer builds CanonicalEdit[] against immutable snapshot text.
7. Optional LSP stage expands semantic rename/code action into additional CanonicalEdits.
8. Harness calls Runtime workspace.patch with exact before digests and stable clientRequestId.
9. If response is certain, project result to Agent.
10. If response is uncertain, call workspace.patch.get; never regenerate/re-dispatch as a new edit.
11. Re-read diagnostics/diff for verification.
```

## Multi-file atomicity

OMP prepares multi-section syntax before writes but an OS write failure can still leave a landed prefix. Ordivon already has a stronger opportunity: lower the complete normalized set into Runtime's atomic multi-file Patch boundary when supported.

The Harness gateway MUST therefore avoid reimplementing a weaker writer.

## LSP integration

LSP is an optional semantic expansion stage, especially for:

- symbol rename;
- file rename (`workspace/willRenameFiles` / `didRenameFiles` semantics);
- code actions;
- format/diagnostic feedback.

LSP does not become source truth. Any returned `WorkspaceEdit` is normalized into exact current Workspace edits before Runtime commit.

## Recovery classes

| Failure | Safe action |
|---|---|
| protocol syntax invalid | same semantic attempt may be re-encoded before commit |
| snapshot tag unknown | re-read source then ask model again |
| source digest changed | re-observe and reassess semantic intent |
| ambiguous replacement | request narrower target |
| normalized no-op | report no-op; do not commit |
| Runtime patch not committed | same request may be safely retried per Runtime guidance |
| Runtime commit unknown | reconcile same `clientRequestId` |
| Runtime committed | never fallback to another codec |

## Minimal prototype stack

- existing Ordivon Harness or a thin test driver;
- existing Runtime `workspace.read` + `workspace.patch` + `workspace.patch.get`;
- one anchored parser;
- exact replacement parser;
- protocol selector;
- benchmark harness;
- optional LSP adapter later.

No new database is required for the first prototype; benchmark results may be fixtures until repeated use justifies persistent selection data.

## Acceptance experiment

Use the same model, same repository states and same edit tasks under three protocols:

1. exact replace baseline;
2. unified/apply patch;
3. anchored/hashline-like.

Measure:

- syntactic admission rate;
- exact lowering rate;
- semantic test-pass rate;
- stale-source rejection correctness;
- correction turns;
- output tokens;
- Runtime Tool calls;
- multi-file success;
- response-loss recovery correctness.

### Mandatory falsifiers

- mutate source after read and before edit: stale edit must not silently land;
- duplicate `oldText`: replace must fail ambiguous;
- deliberately lose Runtime response after commit: gateway must reconcile rather than redispatch;
- invalid first codec before commit: fallback may occur without duplicate physical write.

## Project-study acceptance

### One-sentence test

PASS: OMP's edit subsystem is best understood as an adaptive Agent-facing codec layer over exact source snapshots, not as a single magic patch language.

### Prototype test

PASS: the structures, parser responsibilities, lowering boundary and recovery rules above are sufficient to build an anchored + replacement prototype on current Runtime Patch.

## Verdict

**PASS — HIGHEST-PRIORITY OMP MECHANISM. BUILD AS A HARNESS ADAPTER OVER RUNTIME PATCH.**
