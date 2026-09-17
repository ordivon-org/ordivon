# Ordivon Agent Service — Evidence / Verification Decomposition R6

Status: **IMPLEMENTED / LIVE RUNTIME ARTIFACT DOGFOOD / NOT YET CANONICAL CUTOVER**
Date: 2026-09-18
Base implementation: `4a3d107d41c14ea2d34fc4ef49d7cd056e32bab9`
Architecture delta: `knowledge/graphs/ordivon-agent-service-r6-evidence-delta.json`
Acceptance receipt: `evidence/acceptance/agent-service-evidence-r6.json`

## One-sentence result

**R6 splits execution activation from semantic completion and inserts an explicit evidence pipeline so Agent Service can verify digest-bound Runtime Artifacts without becoming a second Artifact store.**

## What R5 still coupled

R5 successfully established:

```text
Task != Assignment != Runtime Job
Runtime succeeded != Task succeeded
```

But its `AssignmentActivator` still performed two different lifecycle jobs:

```text
ASSIGNED -> submit/bind Runtime Job -> RUNNING
RUNNING  -> observe Runtime -> semantic verify -> Task terminal
```

Those phases differ in trigger, failure semantics, recovery boundary and truth source. R6 therefore separates them.

## R6 execution half

```text
Task ASSIGNED
    ↓
AssignmentExecutionActivator (refined N15)
    ↓
RuntimeAdapter (N19)
    ↓
Runtime Job binding
    ↓
Task RUNNING
```

`AssignmentExecutionActivator` never checks acceptance and never marks a Task terminal.

## R6 completion half

```text
Task RUNNING
    ↓
TaskCompletionReconciler (N26)
    ↓
RuntimeJobObserver (N25)
    ↓
RuntimeEvidenceGate (N30)
    ↓ mechanical success only
EvidenceResolverRegistry (N28)
    ├── stdoutTail resolver
    └── RuntimeArtifactReader (N27)
           ↓ artifact.read
           ↓ exact artifact identity + digest
    ↓
EvidenceSemanticVerifier (refined N13)
    ↓
VerificationRecordStore (N29)
    ↓ atomic terminal transaction
Task / Assignment / ServiceEvent
```

## Five different truth classes

R6 makes five previously blurred concepts explicit:

1. **Mechanical execution truth** — Runtime owns Job/Attempt state, process exit and delivery disposition.
2. **Artifact truth** — Runtime owns retained Artifact bytes and their digest.
3. **Normalized evidence** — Agent Service converts raw evidence into acceptance-relevant facts in memory.
4. **Semantic verdict** — Agent Service decides whether the Task acceptance contract is satisfied.
5. **Verification provenance** — Agent Service durably records why a verdict was made, by reference and digest.

The fifth item is not an Artifact copy.

## VerificationRecord is deliberately not an Artifact store

The first R6 implementation stored normalized `facts.text` inside the VerificationRecord. TDD exposed that this silently copied Runtime-owned Artifact contents into Agent Service persistence.

R6 now persists only provenance such as:

```json
{
  "resolver": "runtime_artifact_text",
  "runtimeJobId": "job-...",
  "artifactId": "attempt-....stdout",
  "artifactKind": "stdout",
  "digest": "sha256:...",
  "byteLength": 27
}
```

It does not persist the Artifact text itself.

Re-verification can return to Runtime using the exact Job + Artifact identity and compare the digest.

## RuntimeArtifactReader is its own LEGO

Artifact reading was not added to `RuntimeAdapter` because the contracts are different:

```text
RuntimeAdapter
  workspace.exec / task.observe
  execution lifecycle and mechanical observation

RuntimeArtifactReader
  artifact.read
  read-only evidence retrieval
```

The production implementation is:

```text
RuntimeMcpArtifactReader
```

It uses Runtime's public MCP surface and validates:

- exact `jobId` identity;
- exact `artifactId` identity;
- requested byte offset;
- monotonic `nextOffset`;
- digest stability across chunks;
- final reassembled content digest;
- a bounded Agent Service evidence byte ceiling.

A non-EOF cursor that does not advance fails closed.

## Runtime mechanical gate

Before any domain evidence is interpreted, `RuntimeEvidenceGate` requires:

```text
semanticCompletionEvaluated == false
executionTerminal == true
status == succeeded
deliveryDisposition == committed
```

Non-terminal evidence leaves the Task RUNNING.

A Runtime failure creates a durable **mechanical-stage verification record** and Task failure. Semantic evidence cannot override a failed mechanical execution just because stdout happened to contain a desired marker.

## Semantic verifier is now pure

`EvidenceSemanticVerifier` no longer understands Runtime Job states. It receives:

```text
Task acceptance contract
+
normalized EvidenceBundle
```

and returns only:

```text
accepted / rejected
reason
```

This is the seam future domain verifiers can replace.

## Current resolvers

R6 retains the two R5 bounded-output contracts for compatibility:

```text
stdout_contains
stdout_equals
```

and adds the first exact retained-artifact contract:

```text
runtime_artifact_text_contains
```

Example:

```json
{
  "kind": "runtime_artifact_text_contains",
  "artifactKind": "stdout",
  "value": "EXPECTED_MARKER"
}
```

The resolver requires exactly one matching Runtime Artifact descriptor. Zero or multiple matches fail closed rather than guessing.

## Atomic semantic closure

One completion transaction contains:

```text
VerificationRecord creation
TASK_VERIFIED event
Task terminal transition
Assignment terminal transition
TASK_SUCCEEDED / TASK_FAILED event
```

Failure of the VerificationRecord write rolls back the Task/Assignment terminal transition and semantic event history.

Replay after completion sees the existing unique Assignment verification and does not duplicate verdicts or terminal events.

## Live production Runtime evidence

R6 was dogfooded against the production Runtime MCP, not a copied Registry implementation.

### Live A — Artifact semantic success

A Task required `runtime_artifact_text_contains(stdout, R6_ARTIFACT_EVIDENCE_OK)`.

Runtime produced a normal successful Job. Agent Service ignored the bounded stdout tail as the acceptance source, selected the Runtime `stdout` Artifact descriptor, fetched it through `artifact.read`, verified its SHA-256 digest and completed the Task from that evidence.

Result:

```text
Task = SUCCEEDED
verification stage = semantic
TASK_VERIFIED -> TASK_SUCCEEDED
```

### Live B — Artifact exists but semantic mismatch

Runtime mechanically succeeded and produced a valid stdout Artifact, but the Artifact did not contain the requested marker.

Result:

```text
Task = FAILED
reason = acceptance:runtime_artifact_text_contains:not_satisfied
verification stage = semantic
```

This proves Artifact presence/digest validity is not semantic success.

### Live C — Agent Service reconstruction

A Task was activated and bound to one Runtime Job. Agent Service was then closed and rebuilt from the same SQLite state before semantic completion.

The reconstructed service retained the exact same `runtimeJobId`, fetched the Runtime Artifact, verified it and converged the Task to `SUCCEEDED`.

No second Runtime Job was created.

### Live D — no raw Artifact duplication

A final production Runtime Task emitted marker `R6_NO_RAW_ARTIFACT_COPY_OK`. The Task succeeded through the digest-bound Artifact resolver.

The persisted VerificationRecord contained only Job/Artifact identity, kind, digest, byte length and resolver. A serialization check confirmed the marker/raw Artifact content was absent from the Agent Service receipt.

## Why this matters for other capability packs

R6 turns verification into a plug point rather than a Runtime special case:

```text
Engineering
  test report / build artifact / diff evidence resolver

Research
  dataset / statistical output / claim-evidence resolver

Artifact
  rendered PDF/PPTX / layout QA resolver

Game
  replay / telemetry / screenshot / mechanics acceptance resolver

Security
  scanner report / reproduction receipt / mitigation regression resolver
```

Each can supply an evidence resolver and semantic verifier while leaving Task assignment, Runtime execution and terminal transactions unchanged.

## Next decomposition boundary

After R6, Goal/DAG/Board can be built above a durable Task truth instead of inventing their own completion semantics:

```text
GoalStore
  ↓
TaskGraph / dependency edges
  ↓
Task readiness projector
  ↓
existing R5/R6 Task execution and verification
  ↓
Goal convergence
  ↓
BoardProjector
```

Board should remain a projection of semantic events, never a second Task/Goal state owner.
