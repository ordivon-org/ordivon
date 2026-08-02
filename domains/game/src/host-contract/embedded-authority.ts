import type { DatabaseSync } from "node:sqlite";

import type { ProtocolJson } from "./canonical.ts";
import { protocolCanonicalJson, protocolDigest, validateProtocolJson } from "./canonical.ts";
import type {
  DispatchEnvelope,
  ObservationEnvelope,
  TaskDescriptor,
  TaskOutcome,
  VerificationReceipt,
} from "./model.ts";
import {
  validateDispatchEnvelope,
  validateObservationEnvelope,
  validateTaskDescriptor,
  validateTaskOutcome,
  validateVerificationReceipt,
} from "./validate.ts";
import { HostContractStore, type HostContractTranscriptEntry } from "./store.ts";
import { HostStore } from "./journal.ts";

export type EmbeddedHostState = "ready" | "reconciling" | "verifying" | "result" | "completed" | "failed" | "cancelled" | "blocked";

export interface EmbeddedHostProjection {
  taskId: string;
  goalId: string;
  revision: number;
  state: EmbeddedHostState;
  descriptorDigest: `sha256:${string}`;
  dispatchDigest: `sha256:${string}` | null;
  observationDigest: `sha256:${string}` | null;
  verificationDigest: `sha256:${string}` | null;
  outcomeDigest: `sha256:${string}` | null;
}

const kind = {
  descriptor: "ordivon.host-task-descriptor",
  dispatch: "ordivon.dispatch-envelope",
  observation: "ordivon.observation-envelope",
  verification: "ordivon.verification-receipt",
  outcome: "ordivon.task-outcome",
} as const;

function same(left: unknown, right: unknown): boolean {
  return protocolCanonicalJson(left) === protocolCanonicalJson(right);
}

function requireEntry(
  contracts: HostContractStore,
  runId: string,
  taskId: string,
  contractKind: string,
): HostContractTranscriptEntry {
  const entry = contracts.latest(runId, taskId, contractKind);
  if (!entry) throw new Error(`Embedded Host Task is missing ${contractKind}: ${taskId}`);
  return entry;
}

export class EmbeddedHostAuthority {
  readonly host: HostStore;
  readonly contracts: HostContractStore;

  constructor(game: { readonly db: DatabaseSync }) {
    this.host = new HostStore(game.db);
    this.contracts = new HostContractStore(this.host);
  }

  ensureTask(runId: string, value: TaskDescriptor): EmbeddedHostProjection {
    const descriptor = validateTaskDescriptor(value);
    const retained = this.contracts.latest(runId, descriptor.taskId, kind.descriptor);
    if (retained) {
      if (!same(retained.object, descriptor)) throw new Error("Task identity is already bound to another descriptor");
      return this.projection(runId, descriptor.taskId);
    }
    this.contracts.putWireObject(
      runId,
      "host-contract.task-descriptor",
      `host-contract:${descriptor.taskId}:descriptor`,
      descriptor.taskId,
      descriptor,
    );
    return this.projection(runId, descriptor.taskId);
  }

  prepare(
    runId: string,
    taskId: string,
    effect: Record<string, ProtocolJson>,
    request: Record<string, ProtocolJson>,
    value: DispatchEnvelope,
  ): EmbeddedHostProjection {
    validateProtocolJson(effect);
    validateProtocolJson(request);
    const dispatch = validateDispatchEnvelope(value);
    const descriptor = this.descriptor(runId, taskId);
    if (dispatch.requestDigest !== protocolDigest(request)) throw new Error("Dispatch requestDigest differs from the executor request");
    const effectDigest = protocolDigest(effect);
    const requestDigest = protocolDigest(request);
    const retained = this.contracts.latest(runId, taskId, kind.dispatch);
    if (retained) {
      if (!same(retained.object, dispatch) || !same(retained.relatedDigests, [effectDigest, requestDigest].sort())) {
        throw new Error("Task already preserves another prepared Dispatch");
      }
      return this.projection(runId, taskId);
    }
    if (this.projection(runId, taskId).revision !== 1) throw new Error("Task is not ready to prepare an Effect");
    this.contracts.batch(runId, () => {
      this.host.putProtocolArtifact(String(effect.kind ?? "ordivon.effect"), effect);
      this.host.putProtocolArtifact(String(request.kind ?? "ordivon.executor-request"), request);
      this.contracts.putWireObject(
        runId,
        "host-contract.dispatch",
        `host-contract:${taskId}:dispatch`,
        taskId,
        dispatch,
        { relatedDigests: [effectDigest, requestDigest] },
      );
    });
    if (descriptor.taskId !== taskId) throw new Error("Task descriptor identity changed during prepare");
    return this.projection(runId, taskId);
  }

  recordObservation(runId: string, taskId: string, value: ObservationEnvelope): EmbeddedHostProjection {
    const observation = validateObservationEnvelope(value);
    const dispatch = this.dispatch(runId, taskId);
    if (observation.dispatchId !== dispatch.dispatchId || observation.executorId !== dispatch.executorId) {
      throw new Error("Observation is not bound to the prepared Dispatch");
    }
    return this.putStage(runId, taskId, kind.observation, "host-contract.observation", observation);
  }

  recordVerification(runId: string, taskId: string, value: VerificationReceipt): EmbeddedHostProjection {
    const verification = validateVerificationReceipt(value);
    const dispatch = this.dispatch(runId, taskId);
    const observation = this.observation(runId, taskId);
    if (verification.dispatchId !== dispatch.dispatchId) throw new Error("VerificationReceipt targets another Dispatch");
    if (verification.observationDigest !== protocolDigest(observation)) throw new Error("VerificationReceipt targets another Observation");
    return this.putStage(runId, taskId, kind.verification, "host-contract.verification", verification);
  }

  complete(runId: string, taskId: string, value: TaskOutcome): EmbeddedHostProjection {
    const outcome = validateTaskOutcome(value);
    const descriptor = this.descriptor(runId, taskId);
    const verification = requireEntry(this.contracts, runId, taskId, kind.verification);
    const verificationReceipt = validateVerificationReceipt(verification.object);
    if (outcome.taskId !== taskId || outcome.goalId !== descriptor.goalId) throw new Error("TaskOutcome targets another Task or Goal");
    if (outcome.verificationDigest !== verification.contractDigest) throw new Error("TaskOutcome targets another VerificationReceipt");
    if (outcome.status === "completed" && !verificationReceipt.accepted) {
      throw new Error("completed TaskOutcome requires an accepted VerificationReceipt");
    }
    return this.putStage(runId, taskId, kind.outcome, "host-contract.task-outcome", outcome);
  }

  projection(runId: string, taskId: string): EmbeddedHostProjection {
    const descriptorEntry = requireEntry(this.contracts, runId, taskId, kind.descriptor);
    const descriptor = validateTaskDescriptor(descriptorEntry.object);
    const dispatch = this.contracts.latest(runId, taskId, kind.dispatch);
    const observation = this.contracts.latest(runId, taskId, kind.observation);
    const verification = this.contracts.latest(runId, taskId, kind.verification);
    const outcome = this.contracts.latest(runId, taskId, kind.outcome);
    const revision = 1 + Number(Boolean(dispatch)) + Number(Boolean(observation)) + Number(Boolean(verification)) + Number(Boolean(outcome));
    let state: EmbeddedHostState = dispatch ? "reconciling" : "ready";
    if (observation) state = "verifying";
    if (verification) state = "result";
    if (outcome) state = validateTaskOutcome(outcome.object).status;
    return {
      taskId,
      goalId: descriptor.goalId,
      revision,
      state,
      descriptorDigest: descriptorEntry.contractDigest,
      dispatchDigest: dispatch?.contractDigest ?? null,
      observationDigest: observation?.contractDigest ?? null,
      verificationDigest: verification?.contractDigest ?? null,
      outcomeDigest: outcome?.contractDigest ?? null,
    };
  }

  verify(runId: string): void {
    this.host.verifyJournal(runId);
    for (const entry of this.contracts.transcript(runId)) protocolDigest(entry.object);
  }

  listDispatches(runId: string): DispatchEnvelope[] {
    return this.contracts.transcript(runId)
      .filter((entry) => entry.contractKind === kind.dispatch)
      .map((entry) => validateDispatchEnvelope(entry.object));
  }

  listObservations(runId: string): ObservationEnvelope[] {
    return this.contracts.transcript(runId)
      .filter((entry) => entry.contractKind === kind.observation)
      .map((entry) => validateObservationEnvelope(entry.object));
  }

  listEffects(runId: string): Record<string, ProtocolJson>[] {
    const effects = new Map<string, Record<string, ProtocolJson>>();
    for (const entry of this.contracts.transcript(runId).filter((item) => item.contractKind === kind.dispatch)) {
      for (const digest of entry.relatedDigests) {
        const artifact = this.host.getProtocolArtifact<ProtocolJson>(digest);
        if (
          artifact.content !== null &&
          typeof artifact.content === "object" &&
          !Array.isArray(artifact.content) &&
          typeof artifact.content.effectId === "string"
        ) {
          effects.set(artifact.content.effectId, artifact.content);
        }
      }
    }
    return [...effects.values()];
  }

  descriptor(runId: string, taskId: string): TaskDescriptor {
    return validateTaskDescriptor(requireEntry(this.contracts, runId, taskId, kind.descriptor).object);
  }

  dispatch(runId: string, taskId: string): DispatchEnvelope {
    return validateDispatchEnvelope(requireEntry(this.contracts, runId, taskId, kind.dispatch).object);
  }

  observation(runId: string, taskId: string): ObservationEnvelope {
    return validateObservationEnvelope(requireEntry(this.contracts, runId, taskId, kind.observation).object);
  }

  verification(runId: string, taskId: string): VerificationReceipt {
    return validateVerificationReceipt(requireEntry(this.contracts, runId, taskId, kind.verification).object);
  }

  relatedObjects(runId: string, taskId: string): Array<{ digest: `sha256:${string}`; kind: string; content: ProtocolJson }> {
    const dispatch = requireEntry(this.contracts, runId, taskId, kind.dispatch);
    return dispatch.relatedDigests.map((digest) => {
      const artifact = this.host.getProtocolArtifact<ProtocolJson>(digest);
      return { digest, kind: artifact.kind, content: artifact.content };
    });
  }

  private putStage<T extends ObservationEnvelope | VerificationReceipt | TaskOutcome>(
    runId: string,
    taskId: string,
    contractKind: string,
    eventType: string,
    value: T,
  ): EmbeddedHostProjection {
    const retained = this.contracts.latest(runId, taskId, contractKind);
    if (retained) {
      if (!same(retained.object, value)) throw new Error(`Task already preserves another ${contractKind}`);
      return this.projection(runId, taskId);
    }
    this.contracts.putWireObject(
      runId,
      eventType,
      `host-contract:${taskId}:${eventType.slice("host-contract.".length)}`,
      taskId,
      value,
    );
    return this.projection(runId, taskId);
  }
}
