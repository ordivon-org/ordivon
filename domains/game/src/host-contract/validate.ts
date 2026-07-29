import {
  protocolBytes,
  protocolDigest,
  validateProtocolDigest,
  validateProtocolJson,
} from "./canonical.ts";
import type {
  AdmittedDecision,
  ArtifactRef,
  CompiledContextEnvelope,
  ContextBlock,
  DecisionCandidate,
  DispatchEnvelope,
  HostWorkloadObject,
  ModelDecision,
  ModelInvocationIntent,
  ObservationEnvelope,
  StateRef,
  TaskDescriptor,
  TaskOutcome,
  VerificationReceipt,
  VerificationResultItem,
} from "./model.ts";

export class WorkloadValidationError extends TypeError {
  constructor(message: string) {
    super(message);
    this.name = "WorkloadValidationError";
  }
}

export class WorkloadAdmissionError extends Error {
  readonly code:
    | "wrong_context"
    | "stale_state"
    | "invented_candidate"
    | "completed_effect"
    | "wrong_dispatch"
    | "unresolved_dispatch";

  constructor(code: WorkloadAdmissionError["code"], message: string) {
    super(message);
    this.name = "WorkloadAdmissionError";
    this.code = code;
  }
}

function fail(message: string): never {
  throw new WorkloadValidationError(message);
}

function record(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return fail(`${label} must be an object`);
  }
  return value as Record<string, unknown>;
}

function exact(value: Record<string, unknown>, fields: string[], label: string): void {
  const actual = Object.keys(value).sort();
  const expected = [...fields].sort();
  if (actual.join("|") !== expected.join("|")) {
    fail(`${label} fields differ`);
  }
}

function stringValue(value: unknown, label: string, prefix?: string): string {
  if (typeof value !== "string" || !value || value !== value.trim()) {
    return fail(`${label} must be a non-empty trimmed string`);
  }
  if (prefix && !value.startsWith(`${prefix}:`)) {
    return fail(`${label} must start with ${prefix}:`);
  }
  if (Buffer.byteLength(value) > 512) return fail(`${label} exceeds 512 UTF-8 bytes`);
  return value;
}

function nullableString(value: unknown, label: string, prefix?: string): string | null {
  return value === null ? null : stringValue(value, label, prefix);
}

function integer(value: unknown, label: string, minimum = 0): number {
  if (!Number.isSafeInteger(value) || (value as number) < minimum) {
    return fail(`${label} must be an integer >= ${minimum}`);
  }
  return value as number;
}

function digest(value: unknown, label: string): `sha256:${string}` {
  try {
    validateProtocolDigest(value, label);
  } catch (error) {
    throw new WorkloadValidationError(
      error instanceof Error ? error.message : `${label} is invalid`,
    );
  }
  return value;
}

function stringList(value: unknown, label: string, prefix?: string): string[] {
  if (!Array.isArray(value)) return fail(`${label} must be a list`);
  const output = value.map((item) => stringValue(item, `${label} item`, prefix));
  if (new Set(output).size !== output.length) return fail(`${label} entries must be unique`);
  return output;
}

function validateStateRef(value: unknown): StateRef {
  const input = record(value, "StateRef");
  exact(input, ["ref", "digest"], "StateRef");
  return {
    ref: stringValue(input.ref, "StateRef ref"),
    digest: digest(input.digest, "StateRef digest"),
  };
}

function stateRefs(value: unknown, label: string): StateRef[] {
  if (!Array.isArray(value)) return fail(`${label} must be a list`);
  const output = value.map(validateStateRef);
  const refs = output.map((item) => item.ref);
  if (new Set(refs).size !== refs.length) return fail(`${label} refs must be unique`);
  return output;
}

function validateArtifactRef(value: unknown): ArtifactRef {
  const input = record(value, "ArtifactRef");
  exact(input, ["ref", "kind", "digest"], "ArtifactRef");
  return {
    ref: stringValue(input.ref, "ArtifactRef ref"),
    kind: stringValue(input.kind, "ArtifactRef kind"),
    digest: digest(input.digest, "ArtifactRef digest"),
  };
}

function artifactRefs(value: unknown, label: string): ArtifactRef[] {
  if (!Array.isArray(value)) return fail(`${label} must be a list`);
  const output = value.map(validateArtifactRef);
  const refs = output.map((item) => item.ref);
  if (new Set(refs).size !== refs.length) return fail(`${label} refs must be unique`);
  return output;
}

export function validateTaskDescriptor(value: unknown): TaskDescriptor {
  const input = record(value, "TaskDescriptor");
  exact(input, [
    "schemaVersion", "kind", "taskId", "goalId", "workloadId", "assigneeRef",
    "providerPolicyRef", "domainRef", "configurationDigests",
  ], "TaskDescriptor");
  if (input.schemaVersion !== 1 || input.kind !== "ordivon.host-task-descriptor") {
    return fail("TaskDescriptor version or kind is invalid");
  }
  const configurationDigests = stringList(input.configurationDigests, "configurationDigests")
    .map((item) => digest(item, "configurationDigests item"));
  return {
    schemaVersion: 1,
    kind: "ordivon.host-task-descriptor",
    taskId: stringValue(input.taskId, "TaskDescriptor taskId", "task"),
    goalId: stringValue(input.goalId, "TaskDescriptor goalId", "goal"),
    workloadId: stringValue(input.workloadId, "TaskDescriptor workloadId"),
    assigneeRef: nullableString(input.assigneeRef, "TaskDescriptor assigneeRef"),
    providerPolicyRef: nullableString(input.providerPolicyRef, "TaskDescriptor providerPolicyRef"),
    domainRef: nullableString(input.domainRef, "TaskDescriptor domainRef"),
    configurationDigests,
  };
}

export function validateContextBlock(value: unknown): ContextBlock {
  const input = record(value, "ContextBlock");
  exact(input, [
    "blockId", "kind", "priority", "required", "freshness", "sourceRef",
    "sourceOwner", "sourceDigest", "trust", "validityRefs", "payload",
  ], "ContextBlock");
  const priority = integer(input.priority, "ContextBlock priority");
  if (priority > 100) return fail("ContextBlock priority must be <= 100");
  if (typeof input.required !== "boolean") return fail("ContextBlock required must be boolean");
  if (!["current", "checkpoint", "historical"].includes(String(input.freshness))) {
    return fail("ContextBlock freshness is invalid");
  }
  if (!["host", "runtime", "domain", "provider", "human"].includes(String(input.sourceOwner))) {
    return fail("ContextBlock sourceOwner is invalid");
  }
  if (!["authoritative", "verified", "reported", "inferred"].includes(String(input.trust))) {
    return fail("ContextBlock trust is invalid");
  }
  try {
    validateProtocolJson(input.payload);
  } catch (error) {
    throw new WorkloadValidationError(error instanceof Error ? error.message : "ContextBlock payload is invalid");
  }
  return {
    blockId: stringValue(input.blockId, "ContextBlock blockId", "context-block"),
    kind: stringValue(input.kind, "ContextBlock kind"),
    priority,
    required: input.required,
    freshness: input.freshness as ContextBlock["freshness"],
    sourceRef: stringValue(input.sourceRef, "ContextBlock sourceRef"),
    sourceOwner: input.sourceOwner as ContextBlock["sourceOwner"],
    sourceDigest: digest(input.sourceDigest, "ContextBlock sourceDigest"),
    trust: input.trust as ContextBlock["trust"],
    validityRefs: stateRefs(input.validityRefs, "ContextBlock validityRefs"),
    payload: input.payload,
  };
}

export function validateDecisionCandidate(value: unknown): DecisionCandidate {
  const input = record(value, "DecisionCandidate");
  exact(input, [
    "candidateId", "kind", "summary", "proposalDigest", "effectId", "dispatchId",
    "requiredStateRefs",
  ], "DecisionCandidate");
  const kind = stringValue(input.kind, "DecisionCandidate kind") as DecisionCandidate["kind"];
  if (!["domain-action", "propose-effect", "observe-dispatch", "request-human", "wait", "finish"].includes(kind)) {
    return fail("DecisionCandidate kind is invalid");
  }
  const proposalDigest = input.proposalDigest === null
    ? null
    : digest(input.proposalDigest, "DecisionCandidate proposalDigest");
  const effectId = nullableString(input.effectId, "DecisionCandidate effectId", "effect");
  const dispatchId = nullableString(input.dispatchId, "DecisionCandidate dispatchId", "dispatch");
  if (kind === "domain-action" && (!proposalDigest || effectId || dispatchId)) {
    return fail("domain-action requires proposalDigest only");
  }
  if (kind === "propose-effect" && (!effectId || dispatchId)) {
    return fail("propose-effect requires effectId and no dispatchId");
  }
  if (kind === "observe-dispatch" && (!dispatchId || effectId || proposalDigest)) {
    return fail("observe-dispatch requires dispatchId only");
  }
  if (["request-human", "wait", "finish"].includes(kind) && (proposalDigest || effectId || dispatchId)) {
    return fail(`${kind} cannot carry proposal, Effect, or Dispatch identities`);
  }
  return {
    candidateId: stringValue(input.candidateId, "DecisionCandidate candidateId", "candidate"),
    kind,
    summary: stringValue(input.summary, "DecisionCandidate summary"),
    proposalDigest,
    effectId,
    dispatchId,
    requiredStateRefs: stateRefs(input.requiredStateRefs, "DecisionCandidate requiredStateRefs"),
  };
}

export function validateCompiledContext(value: unknown): CompiledContextEnvelope {
  const input = record(value, "CompiledContextEnvelope");
  exact(input, ["schemaVersion", "kind", "digest", "byteLength", "manifest", "payload"], "CompiledContextEnvelope");
  if (input.schemaVersion !== 1 || input.kind !== "ordivon.compiled-context-envelope") {
    return fail("CompiledContextEnvelope version or kind is invalid");
  }
  const manifest = record(input.manifest, "ContextManifest");
  exact(manifest, ["tokenBudget", "estimatedTokens", "selectedBlockIds", "omittedBlockIds"], "ContextManifest");
  const tokenBudget = integer(manifest.tokenBudget, "ContextManifest tokenBudget", 1);
  const estimatedTokens = integer(manifest.estimatedTokens, "ContextManifest estimatedTokens", 1);
  if (estimatedTokens > tokenBudget) return fail("ContextManifest estimatedTokens exceeds tokenBudget");
  const selectedBlockIds = stringList(manifest.selectedBlockIds, "ContextManifest selectedBlockIds", "context-block");
  const omittedBlockIds = stringList(manifest.omittedBlockIds, "ContextManifest omittedBlockIds", "context-block");
  if (selectedBlockIds.some((item) => omittedBlockIds.includes(item))) {
    return fail("ContextManifest selected and omitted blocks overlap");
  }
  const payload = record(input.payload, "CompiledContext");
  exact(payload, [
    "schemaVersion", "kind", "taskId", "workloadId", "stateRefs", "blocks",
    "candidates", "completedEffectIds", "unresolvedDispatchIds", "instruction",
  ], "CompiledContext");
  if (payload.schemaVersion !== 1 || payload.kind !== "ordivon.compiled-context") {
    return fail("CompiledContext version or kind is invalid");
  }
  if (!Array.isArray(payload.blocks)) return fail("CompiledContext blocks must be a list");
  const blocks = payload.blocks.map(validateContextBlock);
  const blockIds = blocks.map((item) => item.blockId);
  if (new Set(blockIds).size !== blockIds.length) return fail("CompiledContext block identities must be unique");
  if (blockIds.join("|") !== selectedBlockIds.join("|")) {
    return fail("CompiledContext selected blocks differ from manifest");
  }
  if (!Array.isArray(payload.candidates) || payload.candidates.length < 1 || payload.candidates.length > 16) {
    return fail("CompiledContext requires between 1 and 16 candidates");
  }
  const candidates = payload.candidates.map(validateDecisionCandidate);
  const candidateIds = candidates.map((item) => item.candidateId);
  if (new Set(candidateIds).size !== candidateIds.length) return fail("CompiledContext candidate identities must be unique");
  const typedPayload = {
    schemaVersion: 1 as const,
    kind: "ordivon.compiled-context" as const,
    taskId: stringValue(payload.taskId, "CompiledContext taskId", "task"),
    workloadId: stringValue(payload.workloadId, "CompiledContext workloadId"),
    stateRefs: stateRefs(payload.stateRefs, "CompiledContext stateRefs"),
    blocks,
    candidates,
    completedEffectIds: stringList(payload.completedEffectIds, "completedEffectIds", "effect"),
    unresolvedDispatchIds: stringList(payload.unresolvedDispatchIds, "unresolvedDispatchIds", "dispatch"),
    instruction: stringValue(payload.instruction, "CompiledContext instruction"),
  };
  const expectedDigest = protocolDigest(typedPayload);
  const expectedByteLength = protocolBytes(typedPayload).byteLength;
  const actualDigest = digest(input.digest, "CompiledContextEnvelope digest");
  const byteLength = integer(input.byteLength, "CompiledContextEnvelope byteLength", 1);
  if (actualDigest !== expectedDigest || byteLength !== expectedByteLength) {
    return fail("CompiledContext digest or byteLength differs from payload");
  }
  return {
    schemaVersion: 1,
    kind: "ordivon.compiled-context-envelope",
    digest: actualDigest,
    byteLength,
    manifest: { tokenBudget, estimatedTokens, selectedBlockIds, omittedBlockIds },
    payload: typedPayload,
  };
}

export function validateModelInvocationIntent(value: unknown): ModelInvocationIntent {
  const input = record(value, "ModelInvocationIntent");
  exact(input, [
    "schemaVersion", "kind", "invocationId", "taskId", "contextDigest",
    "contextObjectDigest", "providerPolicyRef",
  ], "ModelInvocationIntent");
  if (input.schemaVersion !== 1 || input.kind !== "ordivon.model-invocation-intent") {
    return fail("ModelInvocationIntent version or kind is invalid");
  }
  return {
    schemaVersion: 1,
    kind: "ordivon.model-invocation-intent",
    invocationId: stringValue(input.invocationId, "ModelInvocationIntent invocationId", "invocation"),
    taskId: stringValue(input.taskId, "ModelInvocationIntent taskId", "task"),
    contextDigest: digest(input.contextDigest, "ModelInvocationIntent contextDigest"),
    contextObjectDigest: digest(input.contextObjectDigest, "ModelInvocationIntent contextObjectDigest"),
    providerPolicyRef: stringValue(input.providerPolicyRef, "ModelInvocationIntent providerPolicyRef"),
  };
}

export function validateModelDecision(value: unknown): ModelDecision {
  const input = record(value, "ModelDecision");
  exact(input, [
    "schemaVersion", "kind", "invocationId", "contextDigest", "candidateId",
    "providerId", "confidencePermille", "rationale",
  ], "ModelDecision");
  if (input.schemaVersion !== 1 || input.kind !== "ordivon.model-decision") {
    return fail("ModelDecision version or kind is invalid");
  }
  const confidencePermille = integer(input.confidencePermille, "ModelDecision confidencePermille");
  if (confidencePermille > 1000) return fail("ModelDecision confidencePermille must be <= 1000");
  return {
    schemaVersion: 1,
    kind: "ordivon.model-decision",
    invocationId: stringValue(input.invocationId, "ModelDecision invocationId", "invocation"),
    contextDigest: digest(input.contextDigest, "ModelDecision contextDigest"),
    candidateId: nullableString(input.candidateId, "ModelDecision candidateId", "candidate"),
    providerId: stringValue(input.providerId, "ModelDecision providerId"),
    confidencePermille,
    rationale: stringValue(input.rationale, "ModelDecision rationale"),
  };
}

export function validateAdmittedDecision(value: unknown): AdmittedDecision {
  const input = record(value, "AdmittedDecision");
  exact(input, [
    "schemaVersion", "kind", "contextDigest", "candidate", "providerId",
    "confidencePermille", "rationale",
  ], "AdmittedDecision");
  if (input.schemaVersion !== 1 || input.kind !== "ordivon.admitted-decision") {
    return fail("AdmittedDecision version or kind is invalid");
  }
  const confidencePermille = integer(input.confidencePermille, "AdmittedDecision confidencePermille");
  if (confidencePermille > 1000) return fail("AdmittedDecision confidencePermille must be <= 1000");
  return {
    schemaVersion: 1,
    kind: "ordivon.admitted-decision",
    contextDigest: digest(input.contextDigest, "AdmittedDecision contextDigest"),
    candidate: input.candidate === null ? null : validateDecisionCandidate(input.candidate),
    providerId: stringValue(input.providerId, "AdmittedDecision providerId"),
    confidencePermille,
    rationale: stringValue(input.rationale, "AdmittedDecision rationale"),
  };
}

export function validateDispatchEnvelope(value: unknown): DispatchEnvelope {
  const input = record(value, "DispatchEnvelope");
  exact(input, [
    "schemaVersion", "kind", "dispatchId", "effectId", "executorId", "requestDigest",
    "idempotencyKey", "requiredStateRefs", "expectedObservationKind",
  ], "DispatchEnvelope");
  if (input.schemaVersion !== 1 || input.kind !== "ordivon.dispatch-envelope") {
    return fail("DispatchEnvelope version or kind is invalid");
  }
  return {
    schemaVersion: 1,
    kind: "ordivon.dispatch-envelope",
    dispatchId: stringValue(input.dispatchId, "DispatchEnvelope dispatchId", "dispatch"),
    effectId: stringValue(input.effectId, "DispatchEnvelope effectId", "effect"),
    executorId: stringValue(input.executorId, "DispatchEnvelope executorId"),
    requestDigest: digest(input.requestDigest, "DispatchEnvelope requestDigest"),
    idempotencyKey: stringValue(input.idempotencyKey, "DispatchEnvelope idempotencyKey"),
    requiredStateRefs: stateRefs(input.requiredStateRefs, "DispatchEnvelope requiredStateRefs"),
    expectedObservationKind: stringValue(input.expectedObservationKind, "DispatchEnvelope expectedObservationKind"),
  };
}

export function validateObservationEnvelope(value: unknown): ObservationEnvelope {
  const input = record(value, "ObservationEnvelope");
  exact(input, [
    "schemaVersion", "kind", "dispatchId", "executorId", "status", "payloadDigest",
    "evidenceRefs",
  ], "ObservationEnvelope");
  if (input.schemaVersion !== 1 || input.kind !== "ordivon.observation-envelope") {
    return fail("ObservationEnvelope version or kind is invalid");
  }
  if (!["accepted", "running", "succeeded", "failed", "rejected", "unknown"].includes(String(input.status))) {
    return fail("ObservationEnvelope status is invalid");
  }
  return {
    schemaVersion: 1,
    kind: "ordivon.observation-envelope",
    dispatchId: stringValue(input.dispatchId, "ObservationEnvelope dispatchId", "dispatch"),
    executorId: stringValue(input.executorId, "ObservationEnvelope executorId"),
    status: input.status as ObservationEnvelope["status"],
    payloadDigest: digest(input.payloadDigest, "ObservationEnvelope payloadDigest"),
    evidenceRefs: artifactRefs(input.evidenceRefs, "ObservationEnvelope evidenceRefs"),
  };
}

function validateVerificationResultItem(value: unknown): VerificationResultItem {
  const input = record(value, "VerificationResultItem");
  exact(input, ["subjectRef", "decisionDigest", "status", "reason", "evidenceDigest"], "VerificationResultItem");
  if (!["succeeded", "failed", "rejected", "not-selected"].includes(String(input.status))) {
    return fail("VerificationResultItem status is invalid");
  }
  return {
    subjectRef: stringValue(input.subjectRef, "VerificationResultItem subjectRef"),
    decisionDigest: digest(input.decisionDigest, "VerificationResultItem decisionDigest"),
    status: input.status as VerificationResultItem["status"],
    reason: nullableString(input.reason, "VerificationResultItem reason"),
    evidenceDigest: digest(input.evidenceDigest, "VerificationResultItem evidenceDigest"),
  };
}

export function validateVerificationReceipt(value: unknown): VerificationReceipt {
  const input = record(value, "VerificationReceipt");
  exact(input, [
    "schemaVersion", "kind", "dispatchId", "method", "accepted", "observationDigest",
    "resultItems",
  ], "VerificationReceipt");
  if (input.schemaVersion !== 1 || input.kind !== "ordivon.verification-receipt") {
    return fail("VerificationReceipt version or kind is invalid");
  }
  if (typeof input.accepted !== "boolean") return fail("VerificationReceipt accepted must be boolean");
  if (!Array.isArray(input.resultItems)) return fail("VerificationReceipt resultItems must be a list");
  const resultItems = input.resultItems.map(validateVerificationResultItem);
  const subjects = resultItems.map((item) => item.subjectRef);
  if (new Set(subjects).size !== subjects.length) return fail("VerificationReceipt result item subjects must be unique");
  return {
    schemaVersion: 1,
    kind: "ordivon.verification-receipt",
    dispatchId: stringValue(input.dispatchId, "VerificationReceipt dispatchId", "dispatch"),
    method: stringValue(input.method, "VerificationReceipt method"),
    accepted: input.accepted,
    observationDigest: digest(input.observationDigest, "VerificationReceipt observationDigest"),
    resultItems,
  };
}

export function validateTaskOutcome(value: unknown): TaskOutcome {
  const input = record(value, "TaskOutcome");
  exact(input, [
    "schemaVersion", "kind", "taskId", "goalId", "status", "verificationDigest",
    "artifactRefs",
  ], "TaskOutcome");
  if (input.schemaVersion !== 1 || input.kind !== "ordivon.task-outcome") {
    return fail("TaskOutcome version or kind is invalid");
  }
  if (!["completed", "failed", "cancelled", "blocked"].includes(String(input.status))) {
    return fail("TaskOutcome status is invalid");
  }
  return {
    schemaVersion: 1,
    kind: "ordivon.task-outcome",
    taskId: stringValue(input.taskId, "TaskOutcome taskId", "task"),
    goalId: stringValue(input.goalId, "TaskOutcome goalId", "goal"),
    status: input.status as TaskOutcome["status"],
    verificationDigest: input.verificationDigest === null
      ? null
      : digest(input.verificationDigest, "TaskOutcome verificationDigest"),
    artifactRefs: artifactRefs(input.artifactRefs, "TaskOutcome artifactRefs"),
  };
}

export function validateHostWorkloadObject(value: unknown): HostWorkloadObject {
  try {
    validateProtocolJson(value);
  } catch (error) {
    throw new WorkloadValidationError(error instanceof Error ? error.message : "Host workload object is invalid");
  }
  const input = record(value, "Host workload wire object");
  switch (input.kind) {
    case "ordivon.host-task-descriptor": return validateTaskDescriptor(input);
    case "ordivon.compiled-context-envelope": return validateCompiledContext(input);
    case "ordivon.model-invocation-intent": return validateModelInvocationIntent(input);
    case "ordivon.model-decision": return validateModelDecision(input);
    case "ordivon.admitted-decision": return validateAdmittedDecision(input);
    case "ordivon.dispatch-envelope": return validateDispatchEnvelope(input);
    case "ordivon.observation-envelope": return validateObservationEnvelope(input);
    case "ordivon.verification-receipt": return validateVerificationReceipt(input);
    case "ordivon.task-outcome": return validateTaskOutcome(input);
    default: return fail(`unsupported Host workload object kind: ${String(input.kind)}`);
  }
}

function currentStateMap(value: ReadonlyMap<string, string> | StateRef[]): Map<string, string> {
  if (value instanceof Map) return new Map(value);
  return new Map(stateRefs(value, "currentStateRefs").map((item) => [item.ref, item.digest]));
}

export function admitModelDecision(
  contextValue: unknown,
  decisionValue: unknown,
  options: {
    currentStateRefs: ReadonlyMap<string, string> | StateRef[];
    completedEffectIds?: string[];
    unresolvedDispatchIds?: string[];
  },
): AdmittedDecision {
  const context = validateCompiledContext(contextValue);
  const decision = validateModelDecision(decisionValue);
  if (decision.contextDigest !== context.digest) {
    throw new WorkloadAdmissionError("wrong_context", "Decision targets another Context");
  }
  const current = currentStateMap(options.currentStateRefs);
  for (const stateRef of context.payload.stateRefs) {
    if (current.get(stateRef.ref) !== stateRef.digest) {
      throw new WorkloadAdmissionError("stale_state", "Context state reference is stale");
    }
  }
  let candidate: DecisionCandidate | null = null;
  if (decision.candidateId !== null) {
    const matches = context.payload.candidates.filter((item) => item.candidateId === decision.candidateId);
    if (matches.length !== 1) {
      throw new WorkloadAdmissionError("invented_candidate", "Decision selected an unknown candidate");
    }
    candidate = matches[0]!;
    for (const stateRef of candidate.requiredStateRefs) {
      if (current.get(stateRef.ref) !== stateRef.digest) {
        throw new WorkloadAdmissionError("stale_state", "Candidate state reference is stale");
      }
    }
    const completed = new Set([
      ...context.payload.completedEffectIds,
      ...(options.completedEffectIds ?? []),
    ]);
    if (candidate.effectId && completed.has(candidate.effectId)) {
      throw new WorkloadAdmissionError("completed_effect", "Decision repeats a completed Effect");
    }
    const unresolved = new Set([
      ...context.payload.unresolvedDispatchIds,
      ...(options.unresolvedDispatchIds ?? []),
    ]);
    if (candidate.kind === "observe-dispatch") {
      if (!candidate.dispatchId || !unresolved.has(candidate.dispatchId)) {
        throw new WorkloadAdmissionError("wrong_dispatch", "Decision observes another Dispatch");
      }
    } else if (unresolved.size > 0 && ["domain-action", "propose-effect", "finish"].includes(candidate.kind)) {
      throw new WorkloadAdmissionError("unresolved_dispatch", "Unresolved Dispatch forbids new progress");
    }
  }
  const admitted: AdmittedDecision = {
    schemaVersion: 1,
    kind: "ordivon.admitted-decision",
    contextDigest: context.digest,
    candidate,
    providerId: decision.providerId,
    confidencePermille: decision.confidencePermille,
    rationale: decision.rationale,
  };
  return validateAdmittedDecision(admitted);
}
