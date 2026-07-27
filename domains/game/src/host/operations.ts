import { sha256 } from "../digest.ts";
import type { ItemId, MissionStatus, WorldCommand, WorldFact, WorldState } from "../model.ts";
import { ENGINEER_ID, isOperational, POWER_JUNCTION_ID } from "../scenario.ts";
import { applyWorldCommandV2, shortestPath } from "../world.ts";
import { analyzeOperationStrategy, type OperationStrategyAnalysis } from "./strategy.ts";

export type OperationKind =
  | "repair_system"
  | "set_power"
  | "seal_hazard"
  | "stabilize_crew"
  | "send_distress"
  | "wait";

export type OperationTarget =
  | { type: "system"; id: string }
  | { type: "hazard"; id: string }
  | { type: "crew"; id: string }
  | { type: "mission"; id: "distress" | "tick" };

export type OperationSuccessCondition =
  | { kind: "system_integrity"; systemId: string; minimum: number }
  | { kind: "system_power"; systemId: string; powered: boolean }
  | { kind: "hazard_sealed"; hazardId: string }
  | { kind: "crew_stabilized"; crewId: string }
  | { kind: "distress_sent" }
  | { kind: "tick_advanced"; minimumRevision: number };

export type SkillStep =
  | { kind: "move"; targetRoomId: string; label: string }
  | { kind: "pickup_item"; itemId: ItemId; quantity: number; label: string }
  | { kind: "repair_system"; targetSystemId: string; label: string }
  | { kind: "set_power"; targetSystemId: string; enabled: boolean; label: string }
  | { kind: "seal_hull"; targetHazardId: string; label: string }
  | { kind: "stabilize_crew"; targetCrewId: string; label: string }
  | { kind: "send_distress"; targetSystemId: "communications"; label: string }
  | { kind: "wait"; label: string };

export interface SkillPlan {
  planId: string;
  operationCandidateId: string;
  requiredWorldRevision: number;
  requiredWorldDigest: string;
  steps: SkillStep[];
}

export interface OperationProjection {
  missionStatus: MissionStatus;
  missionReason: string | null;
  revision: number;
  turn: number;
  batteryCharge: number;
  oxygen: number;
  reactorHeat: number;
  engineerHealth: number;
  crewHealth: number;
}

export interface OperationCandidate {
  operationCandidateId: string;
  kind: OperationKind;
  target: OperationTarget;
  label: string;
  successCondition: OperationSuccessCondition;
  requiredWorldRevision: number;
  requiredWorldDigest: string;
  planId: string;
  estimatedPrimitiveSteps: number;
  planPreview: string[];
  projected: OperationProjection;
  projectedTerminalFailure: boolean;
  strategy: OperationStrategyAnalysis;
}

interface OperationSpec {
  kind: OperationKind;
  target: OperationTarget;
  label: string;
  successCondition: OperationSuccessCondition;
  enabled?: boolean;
}

export class OperationCompileError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "OperationCompileError";
  }
}

function operationIdentity(state: WorldState, spec: OperationSpec): string {
  const target = `${spec.target.type}:${spec.target.id}`;
  const enabled = spec.enabled === undefined ? "" : `:${spec.enabled ? "on" : "off"}`;
  return `operation:${spec.kind}:${target}${enabled}:${sha256(state).slice(0, 16)}`;
}

function projection(state: WorldState): OperationProjection {
  return {
    missionStatus: state.mission.status,
    missionReason: state.mission.reason,
    revision: state.revision,
    turn: state.turn,
    batteryCharge: state.resources.batteryCharge,
    oxygen: state.resources.oxygen,
    reactorHeat: state.resources.reactorHeat,
    engineerHealth: state.agents[ENGINEER_ID]?.health ?? 0,
    crewHealth: state.crew["crew-01"]?.health ?? 0,
  };
}

export function materializeSkillStep(state: WorldState, step: SkillStep, commandId: string): WorldCommand {
  const base = { commandId, actorId: ENGINEER_ID, expectedRevision: state.revision };
  switch (step.kind) {
    case "move": return { ...base, kind: "move", targetRoomId: step.targetRoomId };
    case "pickup_item": return { ...base, kind: "pickup_item", itemId: step.itemId, quantity: step.quantity };
    case "repair_system": return { ...base, kind: "repair_system", targetSystemId: step.targetSystemId };
    case "set_power": return { ...base, kind: "set_power", targetSystemId: step.targetSystemId, enabled: step.enabled };
    case "seal_hull": return { ...base, kind: "seal_hull", targetHazardId: step.targetHazardId };
    case "stabilize_crew": return { ...base, kind: "stabilize_crew", targetCrewId: step.targetCrewId };
    case "send_distress": return { ...base, kind: "send_distress", targetSystemId: step.targetSystemId };
    case "wait": return { ...base, kind: "wait" };
  }
}

function executeStep(state: WorldState, step: SkillStep, commandId: string): WorldState {
  const result = applyWorldCommandV2(state, materializeSkillStep(state, step, commandId));
  if (result.status !== "accepted") {
    throw new OperationCompileError(`skill step rejected: ${result.code}: ${result.reason}`);
  }
  return result.state;
}

function appendPath(
  state: WorldState,
  steps: SkillStep[],
  targetRoomId: string,
  operationId: string,
): WorldState {
  const actor = state.agents[ENGINEER_ID];
  if (!actor) throw new OperationCompileError("Engineer is missing");
  const path = shortestPath(state, actor.location, targetRoomId);
  if (!path) throw new OperationCompileError(`no path to ${targetRoomId}`);
  let current = state;
  for (const roomId of path.slice(1)) {
    const step: SkillStep = {
      kind: "move",
      targetRoomId: roomId,
      label: `Move to ${state.rooms[roomId]?.name ?? roomId}`,
    };
    steps.push(step);
    current = executeStep(current, step, `compile:${operationId}:${steps.length - 1}`);
    if (current.mission.status !== "running" && roomId !== targetRoomId) break;
  }
  return current;
}

function acquireItem(
  state: WorldState,
  steps: SkillStep[],
  itemId: ItemId,
  required: number,
  operationId: string,
): WorldState {
  const actor = state.agents[ENGINEER_ID];
  if (!actor) throw new OperationCompileError("Engineer is missing");
  const missing = Math.max(0, required - actor.inventory[itemId]);
  if (missing === 0) return state;
  const locations = Object.values(state.rooms)
    .filter((room) => room.inventory[itemId] >= missing)
    .map((room) => {
      const path = shortestPath(state, actor.location, room.id);
      return path ? { room, distance: path.length - 1 } : null;
    })
    .filter((entry): entry is { room: WorldState["rooms"][string]; distance: number } => entry !== null)
    .sort((left, right) => left.distance - right.distance || left.room.id.localeCompare(right.room.id));
  const selected = locations[0];
  if (!selected) throw new OperationCompileError(`${missing} × ${itemId} is unavailable`);
  let current = appendPath(state, steps, selected.room.id, operationId);
  if (current.mission.status !== "running") return current;
  const pickup: SkillStep = {
    kind: "pickup_item",
    itemId,
    quantity: missing,
    label: `Pick up ${missing} × ${itemId}`,
  };
  steps.push(pickup);
  current = executeStep(current, pickup, `compile:${operationId}:${steps.length - 1}`);
  return current;
}

function compileSpec(state: WorldState, spec: OperationSpec): { candidate: OperationCandidate; plan: SkillPlan; projectedState: WorldState } {
  const operationCandidateId = operationIdentity(state, spec);
  const steps: SkillStep[] = [];
  let current = structuredClone(state);
  const executeFinal = (step: SkillStep): void => {
    if (current.mission.status !== "running") return;
    steps.push(step);
    current = executeStep(current, step, `compile:${operationCandidateId}:${steps.length - 1}`);
  };

  switch (spec.kind) {
    case "repair_system": {
      if (spec.target.type !== "system") throw new OperationCompileError("repair target must be a system");
      const system = current.systems[spec.target.id];
      if (!system) throw new OperationCompileError(`unknown system: ${spec.target.id}`);
      current = acquireItem(current, steps, "spare-parts", system.repairParts, operationCandidateId);
      if (current.mission.status === "running") current = appendPath(current, steps, system.roomId, operationCandidateId);
      executeFinal({ kind: "repair_system", targetSystemId: system.id, label: `Repair ${system.name}` });
      break;
    }
    case "set_power": {
      if (spec.target.type !== "system" || spec.enabled === undefined) {
        throw new OperationCompileError("power target or state is missing");
      }
      const system = current.systems[spec.target.id];
      if (!system) throw new OperationCompileError(`unknown system: ${spec.target.id}`);
      current = appendPath(current, steps, POWER_JUNCTION_ID, operationCandidateId);
      executeFinal({ kind: "set_power", targetSystemId: system.id, enabled: spec.enabled, label: `${spec.enabled ? "Enable" : "Disable"} ${system.name}` });
      break;
    }
    case "seal_hazard": {
      if (spec.target.type !== "hazard") throw new OperationCompileError("seal target must be a hazard");
      const hazard = current.hazards[spec.target.id];
      if (!hazard) throw new OperationCompileError(`unknown hazard: ${spec.target.id}`);
      const futureRepairParts = Object.values(current.systems)
        .filter((system) => system.id !== "cooling" && !isOperational(system.integrity))
        .reduce((total, system) => total + system.repairParts, 0);
      if (futureRepairParts > 0) {
        current = acquireItem(current, steps, "spare-parts", futureRepairParts, operationCandidateId);
      }
      if (current.mission.status === "running") {
        current = acquireItem(current, steps, "sealant", 1, operationCandidateId);
      }
      if (current.mission.status === "running") current = appendPath(current, steps, hazard.roomId, operationCandidateId);
      executeFinal({ kind: "seal_hull", targetHazardId: hazard.id, label: `Seal ${hazard.name}` });
      break;
    }
    case "stabilize_crew": {
      if (spec.target.type !== "crew") throw new OperationCompileError("stabilize target must be crew");
      const crew = current.crew[spec.target.id];
      if (!crew) throw new OperationCompileError(`unknown crew: ${spec.target.id}`);
      current = acquireItem(current, steps, "medkit", 1, operationCandidateId);
      if (current.mission.status === "running") current = appendPath(current, steps, crew.location, operationCandidateId);
      executeFinal({ kind: "stabilize_crew", targetCrewId: crew.id, label: `Stabilize ${crew.name}` });
      break;
    }
    case "send_distress": {
      current = appendPath(current, steps, "communications", operationCandidateId);
      executeFinal({ kind: "send_distress", targetSystemId: "communications", label: "Send verified distress signal" });
      break;
    }
    case "wait":
      executeFinal({ kind: "wait", label: "Wait one simulation Tick" });
      break;
  }

  if (steps.length === 0) throw new OperationCompileError("operation produced no skill steps");
  const worldDigest = sha256(state);
  const plan: SkillPlan = {
    planId: `plan:${sha256({ operationCandidateId, steps })}`,
    operationCandidateId,
    requiredWorldRevision: state.revision,
    requiredWorldDigest: worldDigest,
    steps,
  };
  const candidate: OperationCandidate = {
    operationCandidateId,
    kind: spec.kind,
    target: spec.target,
    label: spec.label,
    successCondition: spec.successCondition,
    requiredWorldRevision: state.revision,
    requiredWorldDigest: worldDigest,
    planId: plan.planId,
    estimatedPrimitiveSteps: steps.length,
    planPreview: steps.map((step) => step.label),
    projected: projection(current),
    projectedTerminalFailure: current.mission.status === "failure",
    strategy: analyzeOperationStrategy(state, current, steps.length),
  };
  return { candidate, plan, projectedState: current };
}

function specs(state: WorldState): OperationSpec[] {
  if (state.mission.status !== "running" || !state.agents[ENGINEER_ID]) return [];
  const output: OperationSpec[] = [];
  for (const system of Object.values(state.systems).sort((a, b) => a.id.localeCompare(b.id))) {
    if (!isOperational(system.integrity)) {
      output.push({
        kind: "repair_system",
        target: { type: "system", id: system.id },
        label: `Repair ${system.name}`,
        successCondition: { kind: "system_integrity", systemId: system.id, minimum: 0.8 },
      });
    } else {
      output.push({
        kind: "set_power",
        target: { type: "system", id: system.id },
        label: `${system.powered ? "Disable" : "Enable"} ${system.name}`,
        enabled: !system.powered,
        successCondition: { kind: "system_power", systemId: system.id, powered: !system.powered },
      });
    }
  }
  for (const hazard of Object.values(state.hazards).sort((a, b) => a.id.localeCompare(b.id))) {
    if (!hazard.sealed) {
      output.push({
        kind: "seal_hazard",
        target: { type: "hazard", id: hazard.id },
        label: `Seal ${hazard.name}`,
        successCondition: { kind: "hazard_sealed", hazardId: hazard.id },
      });
    }
  }
  for (const crew of Object.values(state.crew).sort((a, b) => a.id.localeCompare(b.id))) {
    if (!crew.stabilized) {
      output.push({
        kind: "stabilize_crew",
        target: { type: "crew", id: crew.id },
        label: `Stabilize ${crew.name}`,
        successCondition: { kind: "crew_stabilized", crewId: crew.id },
      });
    }
  }
  const communications = state.systems.communications;
  if (communications?.powered && isOperational(communications.integrity) && !state.mission.distressSent) {
    output.push({
      kind: "send_distress",
      target: { type: "mission", id: "distress" },
      label: "Send verified distress signal",
      successCondition: { kind: "distress_sent" },
    });
  }
  output.push({
    kind: "wait",
    target: { type: "mission", id: "tick" },
    label: "Wait one simulation Tick",
    successCondition: { kind: "tick_advanced", minimumRevision: state.revision + 1 },
  });
  return output;
}

export function compileOperationFrontier(state: WorldState): OperationCandidate[] {
  const compiled: Array<{ candidate: OperationCandidate; projectedState: WorldState }> = [];
  for (const spec of specs(state)) {
    try { compiled.push(compileSpec(state, spec)); }
    catch (error) {
      if (!(error instanceof OperationCompileError)) throw error;
    }
  }
  const candidates = compiled.map(({ candidate, projectedState }) => {
    const continuations: OperationCandidate[] = [];
    if (projectedState.mission.status === "running") {
      for (const continuationSpec of specs(projectedState)) {
        try { continuations.push(compileSpec(projectedState, continuationSpec).candidate); }
        catch (error) {
          if (!(error instanceof OperationCompileError)) throw error;
        }
      }
    }
    const preferred = [...continuations].sort((left, right) =>
      left.strategy.strategicScore - right.strategy.strategicScore ||
      left.operationCandidateId.localeCompare(right.operationCandidateId))[0] ?? null;
    const projectedVictory = continuations.find((continuation) => continuation.strategy.projectedVictory) ?? null;
    const lookaheadBonus = projectedVictory ? 400_000 : 0;
    return {
      ...candidate,
      strategy: {
        ...candidate.strategy,
        strategicScore: candidate.strategy.strategicScore - lookaheadBonus,
        oneStepLookahead: {
          projectedVictoryOperationId: projectedVictory?.operationCandidateId ?? null,
          projectedVictoryLabel: projectedVictory?.label ?? null,
          preferredContinuationOperationId: preferred?.operationCandidateId ?? null,
          preferredContinuationLabel: preferred?.label ?? null,
        },
        summary: projectedVictory
          ? `This Operation enables projected victory on the next strategic Operation: ${projectedVictory.label}.`
          : candidate.strategy.summary,
      },
    };
  });
  return candidates
    .sort((left, right) =>
      left.strategy.strategicScore - right.strategy.strategicScore ||
      left.operationCandidateId.localeCompare(right.operationCandidateId))
    .map((candidate, index) => ({
      ...candidate,
      strategy: { ...candidate.strategy, strategicRank: index + 1 },
    }));
}

export function compileSkillPlan(state: WorldState, candidate: OperationCandidate): SkillPlan {
  if (candidate.requiredWorldRevision !== state.revision || candidate.requiredWorldDigest !== sha256(state)) {
    throw new OperationCompileError("operation candidate is stale");
  }
  const spec: OperationSpec = {
    kind: candidate.kind,
    target: candidate.target,
    label: candidate.label,
    successCondition: candidate.successCondition,
    ...(candidate.successCondition.kind === "system_power" ? { enabled: candidate.successCondition.powered } : {}),
  };
  const compiled = compileSpec(state, spec);
  if (compiled.candidate.operationCandidateId !== candidate.operationCandidateId || compiled.plan.planId !== candidate.planId) {
    throw new OperationCompileError("operation candidate no longer compiles identically");
  }
  return compiled.plan;
}

export function simulateSkillPlan(state: WorldState, plan: SkillPlan): { state: WorldState; facts: WorldFact[] } {
  if (plan.requiredWorldRevision !== state.revision || plan.requiredWorldDigest !== sha256(state)) {
    throw new OperationCompileError("skill plan is stale");
  }
  let current = structuredClone(state);
  const facts: WorldFact[] = [];
  for (const [index, step] of plan.steps.entries()) {
    if (current.mission.status !== "running") break;
    const result = applyWorldCommandV2(current, materializeSkillStep(current, step, `simulate:${plan.planId}:${index}`));
    if (result.status !== "accepted") throw new OperationCompileError(`${result.code}: ${result.reason}`);
    current = result.state;
    facts.push(...(result.event.facts ?? []));
  }
  return { state: current, facts };
}

export function operationSucceeded(state: WorldState, condition: OperationSuccessCondition): boolean {
  switch (condition.kind) {
    case "system_integrity": return (state.systems[condition.systemId]?.integrity ?? 0) >= condition.minimum;
    case "system_power": return state.systems[condition.systemId]?.powered === condition.powered;
    case "hazard_sealed": return state.hazards[condition.hazardId]?.sealed === true;
    case "crew_stabilized": return state.crew[condition.crewId]?.stabilized === true;
    case "distress_sent": return state.mission.distressSent;
    case "tick_advanced": return state.revision >= condition.minimumRevision;
  }
}
