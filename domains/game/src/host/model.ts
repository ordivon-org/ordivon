import { randomUUID } from "node:crypto";

import type { MissionStatus } from "../model.ts";

export type GoalStatus = "active" | "succeeded" | "failed" | "cancelled";
export type TaskPhase = "ready" | "active" | "reconciling" | "blocked" | "succeeded" | "failed" | "cancelled";
export type AttemptStatus =
  | "context_pending"
  | "provider_pending"
  | "decision_recorded"
  | "executing"
  | "reconciling"
  | "verifying"
  | "succeeded"
  | "blocked"
  | "failed"
  | "cancelled";

export interface GoalSuccessCondition {
  missionStatus: "victory";
  missionReason: "rescue_signal_verified";
}

export interface AgentGoal {
  goalId: string;
  runId: string;
  actorId: "engineer-01";
  statement: string;
  successCondition: GoalSuccessCondition;
  status: GoalStatus;
  revision: number;
  createdAt: string;
  updatedAt: string;
}

export interface AgentTask {
  taskId: string;
  goalId: string;
  runId: string;
  actorId: "engineer-01";
  phase: TaskPhase;
  revision: number;
  activeAttemptId: string | null;
  completedAttemptIds: string[];
  blockers: string[];
  providerOrder: string[];
  createdAt: string;
  updatedAt: string;
}

export interface AgentAttempt {
  attemptId: string;
  taskId: string;
  runId: string;
  attemptNumber: number;
  revision: number;
  status: AttemptStatus;
  providerId: string | null;
  contextDigest: string | null;
  decisionDigest: string | null;
  operationCandidateId: string | null;
  skillStepIndex: number;
  skillStepCount: number;
  blocker: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface HostArtifact<T = unknown> {
  digest: string;
  kind: string;
  content: T;
  byteLength: number;
  createdAt: string;
}

export interface HostJournalEvent<T = unknown> {
  runId: string;
  sequence: number;
  eventId: string;
  eventType: string;
  payload: T;
  previousDigest: string;
  recordDigest: string;
  createdAt: string;
}

export interface AgentProjection {
  goal: AgentGoal;
  task: AgentTask;
  attempts: AgentAttempt[];
}

export function goalIdFor(runId: string): string {
  return `goal:${runId.slice("run:".length)}:verified-rescue`;
}

export function taskIdFor(runId: string): string {
  return `task:${runId.slice("run:".length)}:engineer-recovery`;
}

export function newAttemptId(runId: string): string {
  return `attempt:${runId.slice("run:".length)}:${randomUUID()}`;
}

export function terminalGoalStatus(status: MissionStatus): GoalStatus {
  if (status === "victory") return "succeeded";
  if (status === "failure") return "failed";
  return "active";
}

export function terminalTaskPhase(status: MissionStatus): TaskPhase {
  if (status === "victory") return "succeeded";
  if (status === "failure") return "failed";
  return "ready";
}
