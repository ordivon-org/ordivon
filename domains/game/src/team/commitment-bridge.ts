import { protocolDigest, type ProtocolJson } from "../host-contract/canonical.ts";
import { EmbeddedHostAuthority, type EmbeddedHostProjection } from "../host-contract/embedded-authority.ts";
import type {
  DispatchEnvelope,
  ObservationEnvelope,
  TaskDescriptor,
  VerificationReceipt,
} from "../host-contract/model.ts";
import type {
  ActionProposal,
  TeamDispatch,
  TeamEffect,
  TeamObservation,
  TeamRound,
  TeamTickPlan,
} from "./model.ts";
import { TeamStore, coordinatorTaskId } from "./store.ts";

export type TeamCommitmentProjection = Pick<
  EmbeddedHostProjection,
  "state" | "verificationDigest"
>;

function protocolSafe(value: unknown): ProtocolJson {
  if (value === null || typeof value === "boolean" || typeof value === "string") return value;
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new TypeError("non-finite Team value cannot enter Protocol");
    return Number.isSafeInteger(value) ? value : value.toString();
  }
  if (Array.isArray(value)) return value.map(protocolSafe);
  if (typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .filter(([, item]) => item !== undefined)
        .map(([key, item]) => [key, protocolSafe(item)]),
    );
  }
  throw new TypeError(`unsupported Team value: ${typeof value}`);
}

function authorityTaskId(roundId: string): string {
  return `task:team-round:${roundId.slice("team-round:".length)}`;
}

function wireEffectId(effectId: string): string {
  return effectId.startsWith("effect:") ? effectId : `effect:${effectId}`;
}

function wireDispatchId(dispatchId: string): string {
  return dispatchId.startsWith("dispatch:") ? dispatchId : `dispatch:${dispatchId}`;
}

/**
 * Game-owned consumer bridge for the current embedded commitment implementation.
 *
 * Team/domain code speaks only in Team Round/Effect/Dispatch/Observation terms.
 * Generic Host wire objects remain quarantined here so a current external Host
 * adapter can replace this implementation without changing gameplay semantics.
 */
export class EmbeddedTeamCommitmentBridge {
  readonly team: TeamStore;
  readonly authority: EmbeddedHostAuthority;

  constructor(team: TeamStore) {
    this.team = team;
    this.authority = new EmbeddedHostAuthority(team.game);
  }

  projection(runId: string, roundId: string): TeamCommitmentProjection {
    return this.authority.projection(runId, authorityTaskId(roundId));
  }

  verify(runId: string): void {
    this.authority.verify(runId);
  }

  contractTranscript(runId: string): Array<{
    sequence: number;
    contractKind: string;
    contractDigest: string;
    subjectRef: string;
    relatedDigests: string[];
  }> {
    return this.authority.contracts.transcript(runId).map((entry) => ({
      sequence: entry.sequence,
      contractKind: entry.contractKind,
      contractDigest: entry.contractDigest,
      subjectRef: entry.subjectRef,
      relatedDigests: [...entry.relatedDigests],
    }));
  }

  dispatchCount(runId: string): number {
    return this.authority.listDispatches(runId).length;
  }

  observationCount(runId: string): number {
    return this.authority.listObservations(runId).length;
  }

  prepare(dispatch: TeamDispatch, effect: TeamEffect, plan: TeamTickPlan): TeamCommitmentProjection {
    const taskId = authorityTaskId(dispatch.roundId);
    const descriptor: TaskDescriptor = {
      schemaVersion: 1,
      kind: "ordivon.host-task-descriptor",
      taskId,
      goalId: this.team.getGoal(dispatch.runId).goalId,
      workloadId: "ordivon.game.team-tick.v1",
      assigneeRef: `coordinator:${coordinatorTaskId(dispatch.runId)}`,
      providerPolicyRef: null,
      domainRef: `game-run:${dispatch.runId}`,
      configurationDigests: [protocolDigest(protocolSafe(plan))],
    };
    this.authority.ensureTask(dispatch.runId, descriptor);

    const request = {
      schemaVersion: 1,
      kind: "ordivon.game.team-tick-request",
      runId: dispatch.runId,
      roundId: dispatch.roundId,
      tickPlan: protocolSafe(plan),
    } satisfies ProtocolJson;
    const wireEffect = {
      schemaVersion: 1,
      kind: "ordivon.game.team-tick-effect",
      ...protocolSafe(effect) as Record<string, ProtocolJson>,
      effectId: wireEffectId(effect.effectId),
    } satisfies ProtocolJson;
    const envelope: DispatchEnvelope = {
      schemaVersion: 1,
      kind: "ordivon.dispatch-envelope",
      dispatchId: wireDispatchId(dispatch.dispatchId),
      effectId: wireEffectId(effect.effectId),
      executorId: "executor:game-world-v1",
      requestDigest: protocolDigest(request),
      idempotencyKey: dispatch.commandId,
      requiredStateRefs: [{
        ref: `game-world:${dispatch.runId}`,
        digest: effect.requiredWorldDigest.startsWith("sha256:")
          ? effect.requiredWorldDigest as `sha256:${string}`
          : `sha256:${effect.requiredWorldDigest}`,
      }],
      expectedObservationKind: "ordivon.game.team-tick-observation.v1",
    };
    return this.authority.prepare(
      dispatch.runId,
      taskId,
      wireEffect,
      request as Record<string, ProtocolJson>,
      envelope,
    );
  }

  relatedEffect(round: TeamRound): TeamEffect {
    if (!round.effectId) throw new Error(`Team Round omitted Effect identity: ${round.roundId}`);
    const artifact = this.authority
      .relatedObjects(round.runId, authorityTaskId(round.roundId))
      .find((item) => item.kind === "ordivon.game.team-tick-effect");
    if (!artifact || typeof artifact.content !== "object" || artifact.content === null || Array.isArray(artifact.content)) {
      throw new Error(`Team Effect Artifact is missing: ${round.effectId}`);
    }
    const { schemaVersion: _schemaVersion, kind: _kind, ...effect } = artifact.content;
    const projection = this.projection(round.runId, round.roundId);
    const status = projection.state === "failed"
      ? "rejected"
      : projection.state === "ready"
        ? "prepared"
        : projection.state === "reconciling"
          ? "dispatched"
          : "succeeded";
    return {
      ...(effect as unknown as TeamEffect),
      effectId: round.effectId,
      status,
      updatedAt: round.updatedAt,
    };
  }

  findObservation(round: TeamRound): TeamObservation | null {
    if (!round.dispatchId) return null;
    let envelope: ObservationEnvelope;
    try {
      envelope = this.authority.observation(round.runId, authorityTaskId(round.roundId));
    } catch {
      return null;
    }
    const evidence = envelope.evidenceRefs[0];
    if (!evidence) return null;
    const artifact = this.team.evidence.getProtocolArtifact<ProtocolJson>(evidence.digest);
    if (typeof artifact.content !== "object" || artifact.content === null || Array.isArray(artifact.content)) return null;
    const { schemaVersion: _schemaVersion, kind: _kind, ...value } = artifact.content;
    return value as unknown as TeamObservation;
  }

  recordObservation(observation: TeamObservation): TeamCommitmentProjection {
    const payload = {
      schemaVersion: 1,
      kind: "ordivon.game.team-tick-observation.v1",
      ...protocolSafe(observation) as Record<string, ProtocolJson>,
    } satisfies ProtocolJson;
    const artifact = this.team.evidence.putProtocolArtifact("ordivon.game.team-tick-observation.v1", payload);
    const envelope: ObservationEnvelope = {
      schemaVersion: 1,
      kind: "ordivon.observation-envelope",
      dispatchId: wireDispatchId(observation.dispatchId),
      executorId: "executor:game-world-v1",
      status: observation.verificationSuccess ? "succeeded" : "rejected",
      payloadDigest: protocolDigest(payload),
      evidenceRefs: [{
        ref: observation.worldEventId,
        kind: "game-world-event",
        digest: artifact.digest as `sha256:${string}`,
      }],
    };
    return this.authority.recordObservation(
      observation.runId,
      authorityTaskId(observation.roundId),
      envelope,
    );
  }

  complete(round: TeamRound, proposals: ActionProposal[]): TeamCommitmentProjection {
    const taskId = authorityTaskId(round.roundId);
    const observation = this.findObservation(round);
    if (!observation) throw new Error(`Team Round has no authority Observation: ${round.roundId}`);
    const envelope = this.authority.observation(round.runId, taskId);
    const verified = new Set(observation.verifiedIntentCommandIds);
    const receipt: VerificationReceipt = {
      schemaVersion: 1,
      kind: "ordivon.verification-receipt",
      dispatchId: envelope.dispatchId,
      method: "game-team-tick.v1",
      accepted: observation.verificationSuccess,
      observationDigest: protocolDigest(envelope),
      resultItems: proposals.map((proposal) => ({
        subjectRef: proposal.actorTaskId,
        decisionDigest: protocolDigest(protocolSafe(proposal)),
        status: verified.has(proposal.command.commandId) ? "succeeded" : "rejected",
        reason: verified.has(proposal.command.commandId) ? null : proposal.rejectionReason ?? "not_executed",
        evidenceDigest: envelope.payloadDigest,
      })),
    };
    const verifiedProjection = this.authority.recordVerification(round.runId, taskId, receipt);
    return this.authority.complete(round.runId, taskId, {
      schemaVersion: 1,
      kind: "ordivon.task-outcome",
      taskId,
      goalId: this.team.getGoal(round.runId).goalId,
      status: observation.verificationSuccess ? "completed" : "failed",
      verificationDigest: verifiedProjection.verificationDigest!,
      artifactRefs: [],
    });
  }

  reject(dispatch: TeamDispatch, reason: string): TeamCommitmentProjection {
    const taskId = authorityTaskId(dispatch.roundId);
    const projection = this.authority.projection(dispatch.runId, taskId);
    if (projection.state !== "reconciling") return projection;
    const payload = {
      schemaVersion: 1,
      kind: "ordivon.game.team-tick-rejection",
      reason,
    } satisfies ProtocolJson;
    const observation: ObservationEnvelope = {
      schemaVersion: 1,
      kind: "ordivon.observation-envelope",
      dispatchId: wireDispatchId(dispatch.dispatchId),
      executorId: "executor:game-world-v1",
      status: "rejected",
      payloadDigest: protocolDigest(payload),
      evidenceRefs: [],
    };
    this.authority.recordObservation(dispatch.runId, taskId, observation);
    const receipt: VerificationReceipt = {
      schemaVersion: 1,
      kind: "ordivon.verification-receipt",
      dispatchId: observation.dispatchId,
      method: "game-team-tick.v1",
      accepted: false,
      observationDigest: protocolDigest(observation),
      resultItems: [],
    };
    const verified = this.authority.recordVerification(dispatch.runId, taskId, receipt);
    return this.authority.complete(dispatch.runId, taskId, {
      schemaVersion: 1,
      kind: "ordivon.task-outcome",
      taskId,
      goalId: this.team.getGoal(dispatch.runId).goalId,
      status: "failed",
      verificationDigest: verified.verificationDigest!,
      artifactRefs: [],
    });
  }
}
