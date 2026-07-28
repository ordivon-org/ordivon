import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  ProtocolCanonicalError,
  protocolCanonicalJson,
  validateProtocolDigest,
  validateProtocolJson,
} from "../src/host-contract/canonical.ts";
import {
  WorkloadValidationError,
  validateAdmittedDecision,
  validateCompiledContext,
  validateContextBlock,
  validateDecisionCandidate,
  validateDispatchEnvelope,
  validateHostWorkloadObject,
  validateModelDecision,
  validateModelInvocationIntent,
  validateObservationEnvelope,
  validateTaskDescriptor,
  validateTaskOutcome,
  validateVerificationReceipt,
} from "../src/host-contract/validate.ts";

const vectors = JSON.parse(
  readFileSync(new URL("../fixtures/host-workload-v1/vectors.json", import.meta.url), "utf8"),
) as { cases: Array<{ caseId: string; input?: unknown }> };

function fixture<T>(caseId: string): T {
  const value = vectors.cases.find((entry) => entry.caseId === caseId)?.input;
  assert.ok(value, caseId);
  return structuredClone(value) as T;
}

function invalid(operation: () => unknown, pattern?: RegExp): void {
  assert.throws(operation, (error: unknown) => {
    assert.ok(error instanceof WorkloadValidationError || error instanceof ProtocolCanonicalError);
    if (pattern) assert.match(String(error), pattern);
    return true;
  });
}

test("Protocol canonical JSON rejects unsafe values and malformed Unicode", () => {
  assert.equal(protocolCanonicalJson({ z: 1, a: [true, null, "ok"] }), '{"a":[true,null,"ok"],"z":1}');
  invalid(() => validateProtocolJson(Number.MAX_SAFE_INTEGER + 1), /unsafe/);
  invalid(() => validateProtocolJson(1.25), /non-integer/);
  invalid(() => validateProtocolJson(undefined), /unsupported/);
  invalid(() => validateProtocolJson(Symbol("x")), /unsupported/);
  invalid(() => validateProtocolJson("\ud800"), /surrogate/);
  invalid(() => validateProtocolJson("\udc00"), /surrogate/);
  assert.doesNotThrow(() => validateProtocolJson("\ud83d\ude80"));
  invalid(() => validateProtocolDigest("sha256:ABC"), /sha256/);
});

test("TaskDescriptor and shared scalar validators reject drift", () => {
  const base = fixture<Record<string, any>>("validate-task-descriptor");
  invalid(() => validateTaskDescriptor(null));
  invalid(() => validateTaskDescriptor({ ...base, extra: true }), /fields/);
  invalid(() => validateTaskDescriptor({ ...base, schemaVersion: 2 }), /version/);
  invalid(() => validateTaskDescriptor({ ...base, taskId: "wrong" }), /task:/);
  invalid(() => validateTaskDescriptor({ ...base, goalId: "wrong" }), /goal:/);
  invalid(() => validateTaskDescriptor({ ...base, workloadId: " " }), /trimmed/);
  invalid(() => validateTaskDescriptor({ ...base, assigneeRef: 1 }), /string/);
  invalid(() => validateTaskDescriptor({ ...base, configurationDigests: "bad" }), /list/);
  invalid(() => validateTaskDescriptor({ ...base, configurationDigests: [base.configurationDigests?.[0], base.configurationDigests?.[0]] }), /unique/);
  invalid(() => validateTaskDescriptor({ ...base, domainRef: "x".repeat(513) }), /512/);
});

test("ContextBlock validates trust, ownership, freshness, refs, and payload", () => {
  const context = fixture<Record<string, any>>("validate-compiled-context");
  const block = context.payload.blocks[0] as Record<string, unknown>;
  invalid(() => validateContextBlock([]));
  invalid(() => validateContextBlock({ ...block, priority: 101 }), /priority/);
  invalid(() => validateContextBlock({ ...block, priority: -1 }), /integer/);
  invalid(() => validateContextBlock({ ...block, required: "yes" }), /boolean/);
  invalid(() => validateContextBlock({ ...block, freshness: "future" }), /freshness/);
  invalid(() => validateContextBlock({ ...block, sourceOwner: "unknown" }), /sourceOwner/);
  invalid(() => validateContextBlock({ ...block, trust: "guess" }), /trust/);
  invalid(() => validateContextBlock({ ...block, validityRefs: "bad" }), /list/);
  invalid(() => validateContextBlock({ ...block, validityRefs: [{ ref: "x", digest: block.sourceDigest }, { ref: "x", digest: block.sourceDigest }] }), /unique/);
  invalid(() => validateContextBlock({ ...block, payload: 1.5 }), /non-integer/);
});

test("DecisionCandidate enforces kind-specific identity combinations", () => {
  const context = fixture<Record<string, any>>("validate-compiled-context");
  const domain = context.payload.candidates[0] as Record<string, unknown>;
  const wait = context.payload.candidates[1] as Record<string, unknown>;
  invalid(() => validateDecisionCandidate(null));
  invalid(() => validateDecisionCandidate({ ...domain, kind: "invented" }), /kind/);
  invalid(() => validateDecisionCandidate({ ...domain, proposalDigest: null }), /domain-action/);
  invalid(() => validateDecisionCandidate({ ...domain, effectId: "effect:x" }), /domain-action/);
  invalid(() => validateDecisionCandidate({ ...wait, proposalDigest: domain.proposalDigest }), /cannot carry/);
  invalid(() => validateDecisionCandidate({ ...wait, kind: "propose-effect", effectId: null }), /propose-effect/);
  assert.doesNotThrow(() => validateDecisionCandidate({ ...wait, kind: "propose-effect", effectId: "effect:x" }));
  invalid(() => validateDecisionCandidate({ ...wait, kind: "observe-dispatch", dispatchId: null }), /observe-dispatch/);
  assert.doesNotThrow(() => validateDecisionCandidate({ ...wait, kind: "observe-dispatch", dispatchId: "dispatch:x" }));
  assert.doesNotThrow(() => validateDecisionCandidate({ ...wait, kind: "request-human" }));
  assert.doesNotThrow(() => validateDecisionCandidate({ ...wait, kind: "finish" }));
});

test("CompiledContext rejects manifest and payload inconsistencies", () => {
  const base = fixture<Record<string, any>>("validate-compiled-context");
  invalid(() => validateCompiledContext(null));
  invalid(() => validateCompiledContext({ ...base, kind: "wrong" }), /version/);
  invalid(() => validateCompiledContext({ ...base, manifest: null }), /object/);
  invalid(() => validateCompiledContext({ ...base, manifest: { ...base.manifest, estimatedTokens: base.manifest.tokenBudget + 1 } }), /exceeds/);
  invalid(() => validateCompiledContext({ ...base, manifest: { ...base.manifest, omittedBlockIds: [...base.manifest.selectedBlockIds] } }), /overlap/);
  invalid(() => validateCompiledContext({ ...base, payload: { ...base.payload, blocks: "bad" } }), /blocks/);
  invalid(() => validateCompiledContext({ ...base, payload: { ...base.payload, blocks: [...base.payload.blocks, base.payload.blocks[0]] } }), /unique/);
  invalid(() => validateCompiledContext({ ...base, manifest: { ...base.manifest, selectedBlockIds: [] } }), /differ/);
  invalid(() => validateCompiledContext({ ...base, payload: { ...base.payload, candidates: [] } }), /between/);
  invalid(() => validateCompiledContext({ ...base, payload: { ...base.payload, candidates: [...base.payload.candidates, base.payload.candidates[0]] } }), /unique/);
  invalid(() => validateCompiledContext({ ...base, byteLength: base.byteLength + 1 }), /byteLength/);
  invalid(() => validateCompiledContext({ ...base, digest: "sha256:" + "0".repeat(64) }), /digest/);
});

test("remaining wire validators reject versions, status drift, and duplicate results", () => {
  const invocation = fixture<Record<string, unknown>>("validate-model-invocation-intent");
  invalid(() => validateModelInvocationIntent({ ...invocation, invocationId: "wrong" }), /invocation:/);
  invalid(() => validateModelInvocationIntent({ ...invocation, kind: "wrong" }), /version/);

  const decision = fixture<Record<string, unknown>>("validate-model-decision");
  invalid(() => validateModelDecision({ ...decision, confidencePermille: 1001 }), /1000/);
  invalid(() => validateModelDecision({ ...decision, rationale: "" }), /non-empty/);

  const admitted = fixture<Record<string, unknown>>("validate-admitted-decision");
  invalid(() => validateAdmittedDecision({ ...admitted, candidate: "bad" }), /object/);
  invalid(() => validateAdmittedDecision({ ...admitted, confidencePermille: -1 }), /integer/);

  const dispatch = fixture<Record<string, unknown>>("validate-dispatch-envelope");
  invalid(() => validateDispatchEnvelope({ ...dispatch, dispatchId: "bad" }), /dispatch:/);
  invalid(() => validateDispatchEnvelope({ ...dispatch, requiredStateRefs: "bad" }), /list/);

  const observation = fixture<Record<string, unknown>>("validate-observation-envelope");
  invalid(() => validateObservationEnvelope({ ...observation, status: "done" }), /status/);
  invalid(() => validateObservationEnvelope({ ...observation, evidenceRefs: [{ ref: "x", kind: "k", digest: observation.payloadDigest }, { ref: "x", kind: "k", digest: observation.payloadDigest }] }), /unique/);

  const verification = fixture<Record<string, any>>("validate-verification-receipt");
  invalid(() => validateVerificationReceipt({ ...verification, accepted: 1 }), /boolean/);
  invalid(() => validateVerificationReceipt({ ...verification, resultItems: [{ ...verification.resultItems[0], status: "unknown" }] }), /status/);
  invalid(() => validateVerificationReceipt({ ...verification, resultItems: [verification.resultItems[0], verification.resultItems[0]] }), /unique/);

  const outcome = fixture<Record<string, unknown>>("validate-task-outcome");
  invalid(() => validateTaskOutcome({ ...outcome, status: "succeeded" }), /status/);
  invalid(() => validateTaskOutcome({ ...outcome, artifactRefs: "bad" }), /list/);

  invalid(() => validateHostWorkloadObject({ schemaVersion: 1, kind: "unknown" }), /unsupported/);
});
