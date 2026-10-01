# Agent-Native Cognitive Environment F7 Qualification R1

Status: **QUALIFIED FOR NARROW APPS/AGENT CANDIDATE RETENTION / NOT QUALIFIED FOR GATEWAY OR NEW SERVICE PROMOTION**

Date: 2026-10-01

## 1. Exact carrier and currentness

Evaluation source main: `85a1863dacc8968cf0f43a5e0d0fcd6af3d415e6`.

Frozen candidate bytes were copied from `ws-agent-native-space-r21-reframe-r1-20261001` before live evaluation:

- `cognitive_projection_r1.py`: `sha256:370fc216fe87ccbc88d0403a44092960502f5976806dde9d3a014dce512b341e`
- `cognitive_orientation_r1.py`: `sha256:0f3924bab6f15f9106d293dc64d850d358091b73e609ac71a16310d971394996`
- `cognitive_delta_r1.py`: `sha256:c83295405f5aaa4630d9d4ef77c01c250e1a474a3f689c08f27f317bca6895e3`

The carrier is experimental evidence only; it is not canonical source.

## 2. Requirement-selection conclusion

Fresh source census established:

- `HarnessRunContract.context_refs` already carries exact caller-selected Context references.
- `HarnessWorkingSetSpec` is explicitly Agent-owned current selection state.
- Working View deliberately does not perform discovery, ranking, RAG, or relevance repair.
- Harness lowering explicitly selects and grants nothing.

Therefore Effect-style `R` / context requirements already have a natural representation.

The separate two-consumer binding qualification passed:

- exact selected ref + exact owner digest -> `BOUND_CURRENT`;
- namespace-shaped `work:blender-exit-zero` without owner readback -> `UNKNOWN_OWNER_BINDING`;
- digest mismatch -> `STALE_OR_DIFFERENT_OBJECT`;
- two bindings for one exact ref -> `AMBIGUOUS_OWNER_BINDING`;
- an unselected owner readback does not enter the result.

Disposition:

- requirement selection -> **REUSE** Harness RunContract / Agent WorkingSet;
- owner binding -> **pure reconciliation** over explicit refs + owner readbacks;
- automatic relevance-selector service -> **REJECT/HOLD**;
- new ContextRequirement service -> **DELETE**;
- global owner registry -> **DELETE**.

This does not solve autonomous discovery. Discovery remains a separate owner/method problem.

## 3. Mechanical representation result

Preflight Job: `job-01a0f803-c45a-7a80-9086-b372624f54c0` — PASS.

Context bytes:

| Consumer | A raw | B exact projection | C orientation |
| --- | ---: | ---: | ---: |
| Living Recursive View | 5,448 | 6,027 | 4,283 |
| Browser effect reconciliation | 8,779 | 9,890 | 6,134 |

Exact projection is a proof/currentness envelope, not a compression layer. It is larger than raw in both current cases.

Compact orientation is the first layer that reduces model-visible context while retaining exact expansion refs.

## 4. Live fresh-Agent A/B/C

Preregistered corpus:
`sha256:dae05b5c8552ae1cd39740accce5da32719b5dab9350784e615e96395303002e`.

Live Runtime Job:
`job-01a0f803-f20e-7123-962d-44086042fda1`.

Provider: current Harness-configured `deepseek-v4-flash`.

18/18 calls completed.

| Treatment | Accuracy | Critical | Currentness | Next action | Mean prompt tokens | Mean context bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A raw | 6/6 | 3/3 | 2/2 | 2/2 | 2732.333 | 7113.5 |
| B exact | 6/6 | 3/3 | 2/2 | 2/2 | 3073.333 | 7958.5 |
| C orientation | 6/6 | 3/3 | 2/2 | 2/2 | 2334.333 | 5208.5 |

Preregistered classification:
**positive_compact_nonregression**.

The result supports only a bounded claim: on these two current real Work contexts and this model, the orientation representation preserved all tested answers while reducing model-visible prompt/context cost relative to raw and exact-projection treatments.

It does not establish cross-model/cross-domain superiority.

## 5. Executed runner provenance

The live experiment actually executed runner bytes:

`sha256:b9117eddd98259d3281f962118c4f5592ed0985b3913b1c25d90936aa8ef08c2`

Those exact bytes are retained at:

`docs/architecture/evidence/agent-native-f7-carrier-r1/run_live_r1.executed.py`.

After outcomes were frozen, the working runner was Ruff-formatted to
`sha256:61f8b930d9ca51faa44e042f9b76aaf5382112eddb6c1bcc4ebfad965cd8a250`.
The formatted version passed the same frozen preflight. It is not substituted for the executed carrier in evidence claims.

## 5. Independent scoring audit

Audit Job:
`job-01a0f805-8000-7083-9c4b-2204e81fa28d`.

Audit digest:
`sha256:9c64a369ef14c25827334375e3c3421d54d0b03f7fce265b32e0ed363281e97c`.

The audit independently re-read frozen gold labels and raw 18 result rows. It recomputed 6/6 accuracy for A/B/C, 3/3 C critical accuracy, and the prompt-token ordering:

`C < A < B`.

No runner-only scoring claim is required.

## 6. Owner/currentness fault learned during evaluation

The Browser consumer exposed a live owner/projection divergence:

- direct Windows Runtime owner currently reported `windows_native available=true`;
- Gateway `execution.windows` projection reported `configured=false / available=false / owner endpoint is not configured`.

Correct interpretation:
Gateway routing currentness and Windows Runtime physical availability are distinct truths.

The fresh model answered the corresponding currentness and safe-next-action questions correctly in all three treatments.

This is evidence that owner-qualified currentness is useful and that projection must not collapse owner boundaries.

## 7. Promotion decision

### KEEP

- `AgentCognitiveProjection` as a narrow exact derived proof/currentness envelope in the apps/agent composition layer.
- owner-qualified `VersionVector` / delta semantics.
- `AgentOrientationView` as a compact progressive-disclosure model view.

### NARROW

- `orient` does not currently justify a new stateful Tool/service. It is a pure view over an exact projection.
- `delta` remains the existing F2 function.
- `frontier` remains Host Work semantic frontier unless a separate Recursive LEGO diagnosis is actually run.
- `reenter` remains CrossOwnerReentry/Continuation.
- `requirements` is existing RunContract/WorkingSet selection + binding status, not inferred requirements.
- `explain(ref)` remains HOLD until a qualified owner/relation/provenance provider exists.

### MERGE / REUSE

- context requirements -> Harness RunContract / WorkingSet;
- current source/live observation -> Living Recursive View / natural owners;
- lifetime/recovery -> Harness/provider/apps-agent;
- effect commitment -> existing Runtime/provider Effect Commit seams;
- collaboration/rendering -> Host SWF.

### DELETE / REJECT

- automatic relevance-selector service;
- ContextRequirement service;
- GlobalSemanticCursor;
- UniversalAgentScope / AgentSupervisor;
- global mutable cognition/owner registry;
- new generic ActionProposal/Effect framework;
- rewriting Host Space as cognition truth owner.

### HOLD

- Gateway/public cognitive capability.
- Composition-waist promotion.

Reason: the benchmark used two real Work contexts, but there are not yet two independent production code consumers of the new projection contract. Current evidence justifies keeping/narrowing the apps/agent candidate, not widening its authority/surface.

## 8. Remaining minimal frontier

1. Existing implementation owner should consume this evidence and reconcile the dirty F1/F2/orientation candidate.
2. Re-run apps/agent owner tests and current-main fence on the exact integration candidate.
3. If a second real code consumer later appears, reassess promotion to a shared Composition waist.
4. Only expose Gateway derived capabilities after real northbound consumer pressure; do not publish merely because this benchmark is positive.
5. Autonomous owner/source discovery remains a separate Living View / domain-owner frontier, not an excuse to create a global selector.

## 9. Evidence

- preregistration: `sha256:c1b03fae8821cf39b19cf2af58859e34728bd8051c32c198e38abe2ca8713fcf`
- corpus: `sha256:dae05b5c8552ae1cd39740accce5da32719b5dab9350784e615e96395303002e`
- raw live result: `sha256:cfd5f4add75ac489c79a4bfaebc72d3a48917f56ab1d6320e589d831cff0c295`
- live summary: `sha256:6e931a06d118db3b4b2dff83b9ffd98b89eaf08d5c6a76dcee4f992d1e13009a`
- independent audit: `sha256:9c64a369ef14c25827334375e3c3421d54d0b03f7fce265b32e0ed363281e97c`
- requirement binding: `sha256:bb27535cd922f288a0bd7f18275dc0e26dadcc1883cfc1e7b572c2ce31958e4e`

## 10. Non-claims

- no source promotion has occurred;
- no Gateway surface has been created;
- no Host schema changed;
- no effect was executed by the experiment;
- owner-endpoint discovery was supplied rather than benchmarked;
- two Work contexts and one model do not establish universal behavioral superiority.
