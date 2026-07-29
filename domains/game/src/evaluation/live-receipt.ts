import { mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

import { sha256 } from "../digest.ts";
import type { AgentHost } from "../host/engine.ts";
import type { GameStore } from "../storage.ts";

export type LiveEvaluationPhase = "started" | "running" | "partial" | "completed" | "failed";
export type LiveEvaluationTerminationKind =
  | "none"
  | "domain_terminal"
  | "evaluation_timeout"
  | "external_signal"
  | "cancelled"
  | "provider_failure"
  | "evaluation_failure";

export interface LiveEvaluationSpec {
  evaluationId: string;
  mode: string;
  sourceRevision: string;
  startedAt: string;
  wallClockLimitMs: number | null;
  maximumSteps: number;
  databasePath: string;
  databaseRetained: boolean;
  recoveryOfReceiptDigest: string | null;
}

export interface LiveEvaluationTermination {
  kind: LiveEvaluationTerminationKind;
  reason: string | null;
  signal: "SIGINT" | "SIGTERM" | null;
  errorName: string | null;
  errorCode: string | null;
}

export interface LiveEvaluationReceipt {
  schemaVersion: 1;
  kind: "ordivon.game.live-evaluation-receipt";
  phase: LiveEvaluationPhase;
  evaluation: LiveEvaluationSpec & { capturedAt: string; elapsedMs: number };
  termination: LiveEvaluationTermination;
  run: {
    runId: string;
    goalStatus: string;
    taskPhase: string;
    blockers: string[];
    activeAttemptId: string | null;
    activeAttemptStatus: string | null;
    completedAttemptCount: number;
    hostStepCount: number | null;
  };
  world: {
    missionStatus: string;
    missionReason: string | null;
    turn: number;
    revision: number;
    digest: string;
  };
  authority: {
    effectCount: number;
    dispatchCount: number;
    observationCount: number;
    hostJournalCount: number;
    hostJournalTerminalDigest: string | null;
  };
  replay: { verified: true; digest: string };
  provider: {
    invocationsStarted: number;
    decisionsCompleted: number;
    failed: number;
    interrupted: number;
    callsDigest: string;
    latestCall: Record<string, unknown> | null;
  };
}

export interface LiveEvaluationReceiptEnvelope {
  schemaVersion: 1;
  kind: "ordivon.game.live-evaluation-receipt-envelope";
  receiptDigest: string;
  receipt: LiveEvaluationReceipt;
}

export class LiveEvaluationInterruption extends Error {
  readonly kind: "evaluation_timeout" | "external_signal" | "cancelled";
  readonly signal: "SIGINT" | "SIGTERM" | null;
  constructor(
    kind: LiveEvaluationInterruption["kind"],
    message: string,
    signal: LiveEvaluationInterruption["signal"] = null,
  ) {
    super(message);
    this.name = "LiveEvaluationInterruption";
    this.kind = kind;
    this.signal = signal;
  }
}

function callStatus(call: Record<string, unknown>): string {
  return typeof call.status === "string" ? call.status : "unknown";
}

export function captureLiveEvaluationReceipt(input: {
  phase: LiveEvaluationPhase;
  spec: LiveEvaluationSpec;
  game: GameStore;
  agent: AgentHost;
  providerCalls: Array<Record<string, unknown>>;
  hostStepCount: number | null;
  termination?: Partial<LiveEvaluationTermination>;
  now?: Date;
}): LiveEvaluationReceipt {
  const runId = input.game.activeRunId;
  input.agent.host.verifyJournal(runId);
  input.game.verifyStream(runId);
  const replay = input.game.verifyReplay(runId);
  const state = input.game.loadState(runId);
  const projection = input.agent.projection(runId);
  const active = projection.task.activeAttemptId
    ? projection.attempts.find((attempt) => attempt.attemptId === projection.task.activeAttemptId) ?? null
    : null;
  const journal = input.agent.host.listJournal(runId);
  const capturedAt = (input.now ?? new Date()).toISOString();
  const statuses = input.providerCalls.map(callStatus);
  const termination: LiveEvaluationTermination = {
    kind: input.termination?.kind ?? "none",
    reason: input.termination?.reason ?? null,
    signal: input.termination?.signal ?? null,
    errorName: input.termination?.errorName ?? null,
    errorCode: input.termination?.errorCode ?? null,
  };
  return {
    schemaVersion: 1,
    kind: "ordivon.game.live-evaluation-receipt",
    phase: input.phase,
    evaluation: {
      ...input.spec,
      capturedAt,
      elapsedMs: Math.max(0, Date.parse(capturedAt) - Date.parse(input.spec.startedAt)),
    },
    termination,
    run: {
      runId,
      goalStatus: projection.goal.status,
      taskPhase: projection.task.phase,
      blockers: [...projection.task.blockers],
      activeAttemptId: active?.attemptId ?? null,
      activeAttemptStatus: active?.status ?? null,
      completedAttemptCount: projection.task.completedAttemptIds.length,
      hostStepCount: input.hostStepCount,
    },
    world: {
      missionStatus: state.mission.status,
      missionReason: state.mission.reason,
      turn: state.turn,
      revision: state.revision,
      digest: sha256(state),
    },
    authority: {
      effectCount: input.agent.authority.listEffects(runId).length,
      dispatchCount: input.agent.authority.listDispatches(runId).length,
      observationCount: input.agent.authority.listObservations(runId).length,
      hostJournalCount: journal.length,
      hostJournalTerminalDigest: journal.at(-1)?.recordDigest ?? null,
    },
    replay: { verified: replay.verified, digest: replay.digest },
    provider: {
      invocationsStarted: input.providerCalls.length,
      decisionsCompleted: statuses.filter((status) => status === "succeeded").length,
      failed: statuses.filter((status) => status === "failed").length,
      interrupted: statuses.filter((status) => status === "interrupted").length,
      callsDigest: sha256(input.providerCalls),
      latestCall: input.providerCalls.at(-1) ? structuredClone(input.providerCalls.at(-1)!) : null,
    },
  };
}

export function envelopeLiveEvaluationReceipt(receipt: LiveEvaluationReceipt): LiveEvaluationReceiptEnvelope {
  return {
    schemaVersion: 1,
    kind: "ordivon.game.live-evaluation-receipt-envelope",
    receiptDigest: sha256(receipt),
    receipt,
  };
}

export function writeLiveEvaluationReceipt(
  path: string,
  receipt: LiveEvaluationReceipt,
): LiveEvaluationReceiptEnvelope {
  const envelope = envelopeLiveEvaluationReceipt(receipt);
  mkdirSync(dirname(path), { recursive: true });
  const temporary = `${path}.${process.pid}.tmp`;
  writeFileSync(temporary, JSON.stringify(envelope, null, 2) + "\n", { mode: 0o600 });
  renameSync(temporary, path);
  return envelope;
}

export function readLiveEvaluationReceipt(path: string): LiveEvaluationReceiptEnvelope {
  const value = JSON.parse(readFileSync(path, "utf8")) as LiveEvaluationReceiptEnvelope;
  if (
    value.schemaVersion !== 1 ||
    value.kind !== "ordivon.game.live-evaluation-receipt-envelope" ||
    value.receipt?.kind !== "ordivon.game.live-evaluation-receipt" ||
    value.receiptDigest !== sha256(value.receipt)
  ) {
    throw new Error("live evaluation receipt envelope is invalid or digest-mismatched");
  }
  return value;
}
