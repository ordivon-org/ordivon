import { canonicalJson, sha256 } from "../digest.ts";
import type { ItemId, PrimitiveWorldCommand, WorldFact, WorldState } from "../model.ts";
import type { GameStore } from "../storage.ts";
import { listAvailableActions, materializeAction } from "../world.ts";
import { evaluateAuthority } from "./authority.ts";
import type {
  ActorProfile,
  AuthorityPolicyMode,
  CompiledTeamContext,
  TeamActionCandidate,
  TeamContextBlock,
  TeamMessage,
  TeamTaskProjection,
} from "./model.ts";
import { objectivesForRole, objectiveStatus } from "./objectives.ts";

function tokens(value: unknown): number {
  return Math.max(1, Math.ceil(Buffer.byteLength(canonicalJson(value)) / 4));
}

function block(
  blockId: string,
  kind: TeamContextBlock["kind"],
  priority: number,
  required: boolean,
  freshness: TeamContextBlock["freshness"],
  source: unknown,
  payload: unknown,
): TeamContextBlock {
  return { blockId, kind, priority, required, freshness, sourceDigest: sha256(source), payload, estimatedTokens: tokens(payload) };
}

function publicWorld(state: WorldState): unknown {
  return {
    mission: state.mission,
    telemetry: {
      tick: state.turn,
      oxygen: state.resources.oxygen,
      reactorHeat: state.resources.reactorHeat,
      batteryCharge: state.resources.batteryCharge,
    },
    publicAlarms: {
      breach: !(state.hazards["maintenance-breach"]?.sealed || state.hazards["maintenance-breach"]?.contained),
      cooling: (state.systems.cooling?.integrity ?? 0) < 0.8,
      lifeSupport: (state.systems["life-support"]?.integrity ?? 0) < 0.8,
      communications: (state.systems.communications?.integrity ?? 0) < 0.8,
      crewInjury: state.crew["crew-01"]?.stabilized !== true,
    },
  };
}

function localWorld(state: WorldState, actorId: string): unknown {
  const actor = state.agents[actorId];
  if (!actor) throw new Error(`unknown team actor: ${actorId}`);
  const room = state.rooms[actor.location];
  if (!room) throw new Error(`unknown actor room: ${actor.location}`);
  return {
    actor,
    room: { id: room.id, name: room.name, neighbors: room.neighbors, inventory: room.inventory },
    coLocatedAgents: Object.values(state.agents).filter((candidate) => candidate.location === actor.location).map((candidate) => ({ id: candidate.id, health: candidate.health })),
    systems: Object.values(state.systems).filter((system) => system.roomId === actor.location),
    hazards: Object.values(state.hazards).filter((hazard) => hazard.roomId === actor.location),
    crew: Object.values(state.crew).filter((member) => member.location === actor.location),
  };
}

export function factVisibleToActor(fact: WorldFact, state: WorldState, actorId: string): boolean {
  const actor = state.agents[actorId];
  if (!actor) return false;
  switch (fact.kind) {
    case "agent_moved":
    case "agent_waited":
    case "item_picked_up":
    case "item_consumed": return fact.actorId === actorId;
    case "health_changed": return fact.subjectId === actorId || fact.subjectType === "crew";
    case "system_repaired":
    case "power_state_changed": return state.systems[fact.systemId]?.roomId === actor.location;
    case "hull_breach_sealed": return state.hazards[fact.hazardId]?.roomId === actor.location;
    case "hazard_contained": return fact.actorId === actorId || state.hazards[fact.hazardId]?.roomId === actor.location;
    case "crew_stabilized": return state.crew[fact.crewId]?.location === actor.location;
    case "distress_signal_sent":
    case "battery_consumed":
    case "oxygen_changed":
    case "reactor_heat_changed":
    case "mission_succeeded":
    case "mission_failed": return true;
  }
}

function visibleFacts(store: GameStore, runId: string, actorId: string, state: WorldState): WorldFact[] {
  const facts = store.events(runId).flatMap((event) => event.facts ?? []).slice(-64);
  return facts.filter((fact) => factVisibleToActor(fact, state, actorId));
}

const missionItemCapability: Partial<Record<ItemId, string>> = {
  "spare-parts": "repair_system",
  sealant: "seal_hull",
  medkit: "basic_first_aid",
  "breaker-key": "set_power",
  toolkit: "repair_system",
};

/**
 * Team Actors may only claim a mission item when their current capability set
 * can consume it. Primitive World pickup remains general; this is the bounded
 * Game coordination frontier that prevents locally legal but unrecoverable
 * critical-item capture while no transfer/release operation exists.
 */
export function actorCanClaimMissionItem(
  state: WorldState,
  actorId: string,
  itemId: ItemId,
): boolean {
  const requiredCapability = missionItemCapability[itemId];
  if (!requiredCapability) return true;
  return state.agents[actorId]?.capabilities.includes(requiredCapability) ?? false;
}

function selectActions(
  runId: string,
  state: WorldState,
  profile: ActorProfile,
  contextSeed: string,
  policyMode: AuthorityPolicyMode,
): TeamActionCandidate[] {
  const actor = state.agents[profile.actorId];
  if (!actor) return [];
  const worldDigest = sha256(state);
  const actions = listAvailableActions(state, profile.actorId)
    .filter((action) => action.command.kind !== "pickup_item" ||
      actorCanClaimMissionItem(state, profile.actorId, action.command.itemId))
    .sort((left, right) => Number(left.actionId === "wait") - Number(right.actionId === "wait") || left.actionId.localeCompare(right.actionId))
    .slice(0, 8);
  return actions.map((action) => {
    const commandId = `team-command:${sha256({ runId, actorId: profile.actorId, worldRevision: state.revision, actionId: action.actionId })}`;
    const command = materializeAction(action, commandId);
    if (command.kind === "team_tick") throw new Error("actor candidate cannot be team_tick");
    const actionCandidateId = `team-action:${sha256({ contextSeed, actionId: action.actionId, command })}`;
    const authority = evaluateAuthority(runId, profile, actor.capabilities, actionCandidateId, contextSeed, worldDigest, state, command, policyMode);
    return {
      actionCandidateId,
      actionId: action.actionId,
      label: action.label,
      actorId: profile.actorId,
      worldDigest,
      worldRevision: state.revision,
      command,
      objectiveIds: objectivesForRole(profile.role),
      authorityOutcome: authority.outcome,
      authorityDecisionId: authority.decisionId,
    };
  });
}

export interface TeamContextInput {
  store: GameStore;
  runId: string;
  task: TeamTaskProjection;
  profile: ActorProfile;
  goal: unknown;
  messages: TeamMessage[];
  policyMode: AuthorityPolicyMode;
  tokenBudget?: number;
}

export function compileTeamContext(input: TeamContextInput): CompiledTeamContext {
  const tokenBudget = input.tokenBudget ?? 4_000;
  if (!Number.isSafeInteger(tokenBudget) || tokenBudget < 256) throw new TypeError("team Context token budget must be an integer of at least 256");
  const state = input.store.loadState(input.runId);
  const worldDigest = sha256(state);
  const seed = sha256({ runId: input.runId, taskId: input.task.taskId, taskRevision: input.task.revision, worldDigest, policyMode: input.policyMode });
  const facts = visibleFacts(input.store, input.runId, input.profile.actorId, state);
  const deliveredMessages = input.messages.filter((message) => message.deliveredActorIds.includes(input.profile.actorId) && message.status !== "expired");
  const allBlocks: TeamContextBlock[] = [
    block(`team-block:${input.task.taskId}:goal`, "goal", 100, true, "checkpoint", input.goal, input.goal),
    block(`team-block:${input.task.taskId}:task`, "task", 100, true, "current", input.task, input.task),
    block(`team-block:${input.task.taskId}:world`, "world", 100, true, "current", state, publicWorld(state)),
    block(`team-block:${input.task.taskId}:local`, "local", 100, true, "current", state, localWorld(state, input.profile.actorId)),
    block(`team-block:${input.task.taskId}:objectives`, "objective", 95, true, "current", state, objectiveStatus(state).filter((status) => objectivesForRole(input.profile.role).includes(status.objectiveId))),
    block(`team-block:${input.task.taskId}:messages`, "message", 80, false, "current", deliveredMessages, deliveredMessages),
    block(`team-block:${input.task.taskId}:facts`, "evidence", 70, false, "historical", facts, facts),
  ];
  const required = allBlocks.filter((entry) => entry.required).sort((a, b) => a.blockId.localeCompare(b.blockId));
  const optional = allBlocks.filter((entry) => !entry.required).sort((a, b) => b.priority - a.priority || a.estimatedTokens - b.estimatedTokens || a.blockId.localeCompare(b.blockId));
  const selected = [...required];
  const estimate = (blocks: TeamContextBlock[], actions: TeamActionCandidate[]) => tokens({ blocks, actions });
  const actions = selectActions(input.runId, state, input.profile, seed, input.policyMode);
  if (estimate(selected, actions) > tokenBudget) throw new Error("required team Context exceeds token budget");
  const omitted: TeamContextBlock[] = [];
  for (const candidate of optional) {
    if (estimate([...selected, candidate], actions) <= tokenBudget) selected.push(candidate);
    else omitted.push(candidate);
  }
  const payload = {
    schemaVersion: 1 as const,
    kind: "ordivon.game.team-context" as const,
    runId: input.runId,
    taskId: input.task.taskId,
    actorId: input.profile.actorId,
    worldDigest,
    worldRevision: state.revision,
    blocks: selected,
    allowedActions: actions,
    visibleFacts: facts,
  };
  const contextId = `team-context:${sha256(payload)}`;
  const byteLength = Buffer.byteLength(canonicalJson({ ...payload, contextId }));
  return {
    ...payload,
    contextId,
    manifest: {
      tokenBudget,
      estimatedTokens: estimate(selected, actions),
      selectedBlockIds: selected.map((entry) => entry.blockId),
      omittedBlockIds: omitted.map((entry) => entry.blockId),
    },
    byteLength,
  };
}
