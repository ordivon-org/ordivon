import { sha256 } from "../../src/digest.ts";
import type { AvailableAction, WorldEvent, WorldState } from "../../src/model.ts";
import { ENGINEER_ID, initialTeamWorld, isOperational, POWER_JUNCTION_ID } from "../../src/scenario.ts";
import { applyWorldCommand, listAvailableActions, materializeAction, shortestPath } from "../../src/world.ts";

export interface ScriptedPolicy {
  name: string;
  choose(state: WorldState): AvailableAction | null;
}

export interface PolicyRun {
  policy: string;
  state: WorldState;
  events: WorldEvent[];
  digest: string;
}

function findAction(
  state: WorldState,
  predicate: (action: AvailableAction) => boolean,
): AvailableAction | null {
  return listAvailableActions(state, ENGINEER_ID).find(predicate) ?? null;
}

function moveToward(state: WorldState, targetRoomId: string): AvailableAction | null {
  const actor = state.agents[ENGINEER_ID];
  if (!actor) return null;
  const path = shortestPath(state, actor.location, targetRoomId);
  const nextRoom = path?.[1];
  if (!nextRoom) return null;
  return findAction(
    state,
    (action) => action.command.kind === "move" && action.command.targetRoomId === nextRoom,
  );
}

function actAt(
  state: WorldState,
  roomId: string,
  predicate: (action: AvailableAction) => boolean,
): AvailableAction | null {
  const actor = state.agents[ENGINEER_ID];
  if (!actor) return null;
  if (actor.location !== roomId) return moveToward(state, roomId);
  return findAction(state, predicate);
}

export const recoveryPolicy: ScriptedPolicy = {
  name: "recovery",
  choose(state) {
    const actor = state.agents[ENGINEER_ID];
    const cooling = state.systems.cooling;
    const lifeSupport = state.systems["life-support"];
    const communications = state.systems.communications;
    const breach = state.hazards["maintenance-breach"];
    const casualty = state.crew["crew-01"];
    if (!actor || !cooling || !lifeSupport || !communications || !breach || !casualty) return null;

    if (!isOperational(cooling.integrity)) {
      return actAt(
        state,
        cooling.roomId,
        (action) => action.command.kind === "repair_system" && action.command.targetSystemId === cooling.id,
      );
    }
    const coolingThreshold = lifeSupport.powered ? 70 : 20;
    if (!cooling.powered && state.resources.reactorHeat > coolingThreshold) {
      return actAt(
        state,
        POWER_JUNCTION_ID,
        (action) =>
          action.command.kind === "set_power" &&
          action.command.targetSystemId === cooling.id &&
          action.command.enabled,
      );
    }

    const remainingRepairParts = [lifeSupport, communications]
      .filter((system) => !isOperational(system.integrity))
      .reduce((total, system) => total + system.repairParts, 0);
    const needsSpareParts = actor.inventory["spare-parts"] < remainingRepairParts;
    const needsSealant = !breach.sealed && actor.inventory.sealant < 1;
    if (needsSpareParts || needsSealant) {
      if (actor.location !== "storage") return moveToward(state, "storage");
      if (needsSpareParts) {
        return findAction(
          state,
          (action) => action.command.kind === "pickup_item" && action.command.itemId === "spare-parts",
        );
      }
      return findAction(
        state,
        (action) => action.command.kind === "pickup_item" && action.command.itemId === "sealant",
      );
    }

    if (!breach.sealed) {
      return actAt(
        state,
        breach.roomId,
        (action) => action.command.kind === "seal_hull" && action.command.targetHazardId === breach.id,
      );
    }

    if (!isOperational(lifeSupport.integrity)) {
      return actAt(
        state,
        lifeSupport.roomId,
        (action) =>
          action.command.kind === "repair_system" && action.command.targetSystemId === lifeSupport.id,
      );
    }
    if (!lifeSupport.powered) {
      return actAt(
        state,
        POWER_JUNCTION_ID,
        (action) =>
          action.command.kind === "set_power" &&
          action.command.targetSystemId === lifeSupport.id &&
          action.command.enabled,
      );
    }
    if (cooling.powered && state.resources.reactorHeat <= 20) {
      return actAt(
        state,
        POWER_JUNCTION_ID,
        (action) =>
          action.command.kind === "set_power" &&
          action.command.targetSystemId === cooling.id &&
          !action.command.enabled,
      );
    }

    if (!casualty.stabilized) {
      if (actor.inventory.medkit < 1) {
        if (actor.location !== "medical-bay") return moveToward(state, "medical-bay");
        return findAction(
          state,
          (action) => action.command.kind === "pickup_item" && action.command.itemId === "medkit",
        );
      }
      return actAt(
        state,
        casualty.location,
        (action) => action.command.kind === "stabilize_crew" && action.command.targetCrewId === casualty.id,
      );
    }

    if (!isOperational(communications.integrity)) {
      return actAt(
        state,
        communications.roomId,
        (action) =>
          action.command.kind === "repair_system" && action.command.targetSystemId === communications.id,
      );
    }
    if (!communications.powered) {
      return actAt(
        state,
        POWER_JUNCTION_ID,
        (action) =>
          action.command.kind === "set_power" &&
          action.command.targetSystemId === communications.id &&
          action.command.enabled,
      );
    }
    if (!state.mission.distressSent) {
      return actAt(
        state,
        communications.roomId,
        (action) => action.command.kind === "send_distress",
      );
    }

    return findAction(state, (action) => action.command.kind === "wait");
  },
};

export const communicationsFirstPolicy: ScriptedPolicy = {
  name: "communications-first",
  choose(state) {
    const communications = state.systems.communications;
    if (!communications) return null;
    if (!isOperational(communications.integrity)) {
      return actAt(
        state,
        communications.roomId,
        (action) =>
          action.command.kind === "repair_system" && action.command.targetSystemId === communications.id,
      );
    }
    if (!communications.powered) {
      return actAt(
        state,
        POWER_JUNCTION_ID,
        (action) =>
          action.command.kind === "set_power" &&
          action.command.targetSystemId === communications.id &&
          action.command.enabled,
      );
    }
    if (!state.mission.distressSent) {
      return actAt(state, communications.roomId, (action) => action.command.kind === "send_distress");
    }
    return findAction(state, (action) => action.command.kind === "wait");
  },
};

export function runPolicy(
  policy: ScriptedPolicy,
  genesis: WorldState = initialTeamWorld(),
  maximumSteps = 64,
): PolicyRun {
  let state = structuredClone(genesis);
  const events: WorldEvent[] = [];

  for (let step = 0; step < maximumSteps && state.mission.status === "running"; step += 1) {
    const action = policy.choose(state);
    if (!action) throw new Error(`${policy.name} produced no action at revision ${state.revision}`);
    const command = materializeAction(action, `${policy.name}:${step}:${action.actionId}`);
    const result = applyWorldCommand(state, command);
    if (result.status !== "accepted") {
      throw new Error(`${policy.name} selected rejected action: ${result.code}: ${result.reason}`);
    }
    state = result.state;
    events.push(result.event);
  }

  if (state.mission.status === "running") {
    throw new Error(`${policy.name} exceeded ${maximumSteps} steps without a terminal outcome`);
  }
  return { policy: policy.name, state, events, digest: sha256(state) };
}
