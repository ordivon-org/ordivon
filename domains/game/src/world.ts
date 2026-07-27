import { sha256 } from "./digest.ts";
import {
  ITEM_IDS,
  type ApplyResult,
  type AvailableAction,
  type ItemId,
  type RejectionCode,
  type ScalarValue,
  type StateChange,
  type WorldCommand,
  type WorldCommandDraft,
  type WorldEvent,
  type WorldState,
} from "./model.ts";
import {
  advanceEnvironment,
  assertWorldInvariants,
  ENGINEER_ID,
  evaluateMission,
  initialWorld,
  isOperational,
  POWER_JUNCTION_ID,
} from "./scenario.ts";

export { initialWorld } from "./scenario.ts";
export type {
  ApplyResult,
  AvailableAction,
  WorldCommand,
  WorldCommandDraft,
  WorldEvent,
  WorldState,
} from "./model.ts";

function reject(state: WorldState, code: RejectionCode, reason: string): ApplyResult {
  return { status: "rejected", state, code, reason };
}

function readString(value: Record<string, unknown>, key: string): string {
  const result = value[key];
  if (typeof result !== "string" || result.length < 1) {
    throw new TypeError(`${key} must be a non-empty string`);
  }
  return result;
}

function readNonNegativeInteger(value: Record<string, unknown>, key: string): number {
  const result = value[key];
  if (!Number.isSafeInteger(result) || (result as number) < 0) {
    throw new TypeError(`${key} must be a non-negative integer`);
  }
  return result as number;
}

function readPositiveInteger(value: Record<string, unknown>, key: string): number {
  const result = readNonNegativeInteger(value, key);
  if (result < 1) throw new TypeError(`${key} must be a positive integer`);
  return result;
}

function readBoolean(value: Record<string, unknown>, key: string): boolean {
  const result = value[key];
  if (typeof result !== "boolean") throw new TypeError(`${key} must be boolean`);
  return result;
}

function readItemId(value: Record<string, unknown>, key: string): ItemId {
  const result = readString(value, key);
  if (!ITEM_IDS.includes(result as ItemId)) throw new TypeError(`unsupported itemId: ${result}`);
  return result as ItemId;
}

export function parseWorldCommand(input: unknown): WorldCommand {
  if (input === null || typeof input !== "object") throw new TypeError("command must be an object");
  const value = input as Record<string, unknown>;
  const base = {
    commandId: readString(value, "commandId"),
    actorId: readString(value, "actorId"),
    expectedRevision: readNonNegativeInteger(value, "expectedRevision"),
  };

  switch (value.kind) {
    case "move":
      return { ...base, kind: "move", targetRoomId: readString(value, "targetRoomId") };
    case "pickup_item":
      return {
        ...base,
        kind: "pickup_item",
        itemId: readItemId(value, "itemId"),
        quantity: readPositiveInteger(value, "quantity"),
      };
    case "repair_system":
      return { ...base, kind: "repair_system", targetSystemId: readString(value, "targetSystemId") };
    case "set_power":
      return {
        ...base,
        kind: "set_power",
        targetSystemId: readString(value, "targetSystemId"),
        enabled: readBoolean(value, "enabled"),
      };
    case "seal_hull":
      return { ...base, kind: "seal_hull", targetHazardId: readString(value, "targetHazardId") };
    case "stabilize_crew":
      return { ...base, kind: "stabilize_crew", targetCrewId: readString(value, "targetCrewId") };
    case "send_distress":
      return { ...base, kind: "send_distress", targetSystemId: readString(value, "targetSystemId") };
    case "wait":
      return { ...base, kind: "wait" };
    default:
      throw new TypeError("unsupported command kind");
  }
}

function capabilityFor(command: WorldCommand): string {
  if (command.kind === "stabilize_crew") return "basic_first_aid";
  return command.kind;
}

export function validateWorldCommand(
  state: WorldState,
  command: WorldCommand,
): { code: RejectionCode; reason: string } | null {
  if (state.mission.status !== "running") {
    return { code: "mission_not_running", reason: "mission is already terminal" };
  }
  if (command.expectedRevision !== state.revision) {
    return {
      code: "stale_revision",
      reason: `expected revision ${command.expectedRevision}, current revision is ${state.revision}`,
    };
  }

  const actor = state.agents[command.actorId];
  if (!actor) return { code: "unknown_actor", reason: `unknown actor: ${command.actorId}` };
  const capability = capabilityFor(command);
  if (!actor.capabilities.includes(capability)) {
    return { code: "capability_missing", reason: `actor lacks ${capability} capability` };
  }

  switch (command.kind) {
    case "move": {
      const target = state.rooms[command.targetRoomId];
      if (!target) return { code: "unknown_target", reason: `unknown room: ${command.targetRoomId}` };
      const current = state.rooms[actor.location];
      if (!current) return { code: "unknown_target", reason: `unknown actor room: ${actor.location}` };
      if (!current.neighbors.includes(target.id)) {
        return { code: "not_adjacent", reason: `${target.id} is not adjacent to ${current.id}` };
      }
      return null;
    }
    case "pickup_item": {
      const room = state.rooms[actor.location];
      if (!room) return { code: "unknown_target", reason: `unknown actor room: ${actor.location}` };
      if (room.inventory[command.itemId] < command.quantity) {
        return { code: "item_missing", reason: `${command.itemId} is not available in sufficient quantity` };
      }
      return null;
    }
    case "repair_system": {
      const system = state.systems[command.targetSystemId];
      if (!system) return { code: "unknown_target", reason: `unknown system: ${command.targetSystemId}` };
      if (actor.location !== system.roomId) {
        return { code: "wrong_location", reason: `actor must be in ${system.roomId}` };
      }
      if (isOperational(system.integrity)) {
        return { code: "already_complete", reason: `${system.id} is already operational` };
      }
      if (actor.inventory.toolkit < 1) return { code: "tool_missing", reason: "toolkit is required" };
      if (actor.inventory["spare-parts"] < system.repairParts) {
        return { code: "item_missing", reason: `${system.repairParts} spare part(s) required` };
      }
      return null;
    }
    case "set_power": {
      const system = state.systems[command.targetSystemId];
      if (!system) return { code: "unknown_target", reason: `unknown system: ${command.targetSystemId}` };
      if (actor.location !== POWER_JUNCTION_ID) {
        return { code: "wrong_location", reason: `actor must be in ${POWER_JUNCTION_ID}` };
      }
      if (actor.inventory["breaker-key"] < 1) {
        return { code: "tool_missing", reason: "breaker-key is required" };
      }
      if (system.powered === command.enabled) {
        return { code: "already_complete", reason: `${system.id} power is already ${command.enabled}` };
      }
      if (command.enabled && !isOperational(system.integrity)) {
        return { code: "system_damaged", reason: `${system.id} must be repaired before power is enabled` };
      }
      if (command.enabled && state.resources.batteryCharge < system.powerDraw) {
        return { code: "insufficient_power", reason: "battery cannot sustain one turn of this system" };
      }
      return null;
    }
    case "seal_hull": {
      const hazard = state.hazards[command.targetHazardId];
      if (!hazard) return { code: "unknown_target", reason: `unknown hazard: ${command.targetHazardId}` };
      if (actor.location !== hazard.roomId) {
        return { code: "wrong_location", reason: `actor must be in ${hazard.roomId}` };
      }
      if (hazard.sealed) return { code: "already_complete", reason: `${hazard.id} is already sealed` };
      if (actor.inventory.sealant < 1) return { code: "item_missing", reason: "sealant is required" };
      return null;
    }
    case "stabilize_crew": {
      const crew = state.crew[command.targetCrewId];
      if (!crew) return { code: "unknown_target", reason: `unknown crew: ${command.targetCrewId}` };
      if (actor.location !== crew.location) {
        return { code: "wrong_location", reason: `actor must be in ${crew.location}` };
      }
      if (crew.stabilized) return { code: "already_complete", reason: `${crew.id} is already stabilized` };
      if (actor.inventory.medkit < 1) return { code: "item_missing", reason: "medkit is required" };
      return null;
    }
    case "send_distress": {
      const system = state.systems[command.targetSystemId];
      if (!system) return { code: "unknown_target", reason: `unknown system: ${command.targetSystemId}` };
      if (system.id !== "communications") {
        return { code: "invalid_command", reason: "distress signal requires communications" };
      }
      if (actor.location !== system.roomId) {
        return { code: "wrong_location", reason: `actor must be in ${system.roomId}` };
      }
      if (state.mission.distressSent) {
        return { code: "already_complete", reason: "distress signal already sent" };
      }
      if (!system.powered || !isOperational(system.integrity)) {
        return { code: "system_damaged", reason: "communications must be operational and powered" };
      }
      return null;
    }
    case "wait":
      return null;
  }
}

function consumeItem(state: WorldState, actorId: string, itemId: ItemId, quantity: number): void {
  const actor = state.agents[actorId];
  if (!actor) throw new Error("validated actor disappeared");
  actor.inventory[itemId] -= quantity;
  state.resources.consumedItems[itemId] += quantity;
}

function applyActionMutation(state: WorldState, command: WorldCommand): void {
  const actor = state.agents[command.actorId];
  if (!actor) throw new Error("validated actor disappeared");

  switch (command.kind) {
    case "move":
      actor.location = command.targetRoomId;
      break;
    case "pickup_item": {
      const room = state.rooms[actor.location];
      if (!room) throw new Error("validated room disappeared");
      room.inventory[command.itemId] -= command.quantity;
      actor.inventory[command.itemId] += command.quantity;
      break;
    }
    case "repair_system": {
      const system = state.systems[command.targetSystemId];
      if (!system) throw new Error("validated system disappeared");
      consumeItem(state, actor.id, "spare-parts", system.repairParts);
      system.integrity = Math.min(1, Number((system.integrity + 0.55).toFixed(2)));
      break;
    }
    case "set_power": {
      const system = state.systems[command.targetSystemId];
      if (!system) throw new Error("validated system disappeared");
      system.powered = command.enabled;
      break;
    }
    case "seal_hull": {
      const hazard = state.hazards[command.targetHazardId];
      if (!hazard) throw new Error("validated hazard disappeared");
      consumeItem(state, actor.id, "sealant", 1);
      hazard.sealed = true;
      break;
    }
    case "stabilize_crew": {
      const crew = state.crew[command.targetCrewId];
      if (!crew) throw new Error("validated crew disappeared");
      consumeItem(state, actor.id, "medkit", 1);
      crew.stabilized = true;
      crew.health = Math.min(100, crew.health + 12);
      break;
    }
    case "send_distress":
      state.mission.distressSent = true;
      break;
    case "wait":
      break;
  }
}

function flattenScalars(value: unknown, path: string, output: Map<string, ScalarValue>): void {
  if (value === null || typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    output.set(path, value);
    return;
  }
  if (Array.isArray(value)) {
    output.set(path, JSON.stringify(value));
    return;
  }
  if (typeof value === "object") {
    for (const [key, child] of Object.entries(value as Record<string, unknown>)) {
      flattenScalars(child, path ? `${path}.${key}` : key, output);
    }
  }
}

function diffState(before: WorldState, after: WorldState): StateChange[] {
  const beforeMap = new Map<string, ScalarValue>();
  const afterMap = new Map<string, ScalarValue>();
  flattenScalars(before, "", beforeMap);
  flattenScalars(after, "", afterMap);
  const paths = [...new Set([...beforeMap.keys(), ...afterMap.keys()])].sort();
  const changes: StateChange[] = [];
  for (const path of paths) {
    const previous = beforeMap.get(path) ?? null;
    const next = afterMap.get(path) ?? null;
    if (previous !== next) changes.push({ path, before: previous, after: next });
  }
  return changes;
}

export function applyWorldCommand(state: WorldState, command: WorldCommand): ApplyResult {
  assertWorldInvariants(state);
  const validation = validateWorldCommand(state, command);
  if (validation) return reject(state, validation.code, validation.reason);

  const beforeDigest = sha256(state);
  const next = structuredClone(state);
  applyActionMutation(next, command);
  next.revision += 1;
  next.turn += 1;
  advanceEnvironment(next);
  evaluateMission(next);
  assertWorldInvariants(next);
  const afterDigest = sha256(next);

  const event: WorldEvent = {
    eventId: `event:${command.commandId}`,
    commandId: command.commandId,
    commandKind: command.kind,
    actorId: command.actorId,
    worldRevision: next.revision,
    turn: next.turn,
    beforeDigest,
    afterDigest,
    changes: diffState(state, next),
    missionStatus: next.mission.status,
    missionReason: next.mission.reason,
  };

  return { status: "accepted", state: next, event };
}

function draft<T extends WorldCommandDraft>(command: T): T {
  return command;
}

export function materializeAction(action: AvailableAction, commandId: string): WorldCommand {
  return { ...action.command, commandId } as WorldCommand;
}

export function listAvailableActions(state: WorldState, actorId = ENGINEER_ID): AvailableAction[] {
  const actor = state.agents[actorId];
  if (!actor || state.mission.status !== "running") return [];
  const actions: AvailableAction[] = [];
  const add = (actionId: string, label: string, command: WorldCommandDraft): void => {
    const complete = materializeAction({ actionId, label, command }, `candidate:${actionId}`);
    if (!validateWorldCommand(state, complete)) actions.push({ actionId, label, command });
  };
  const base = { actorId, expectedRevision: state.revision };
  const room = state.rooms[actor.location];
  if (!room) return [];

  for (const neighborId of [...room.neighbors].sort()) {
    add(`move:${neighborId}`, `Move to ${state.rooms[neighborId]?.name ?? neighborId}`, draft({ ...base, kind: "move", targetRoomId: neighborId }));
  }
  for (const itemId of ITEM_IDS) {
    const quantity = room.inventory[itemId];
    if (quantity > 0) {
      add(`pickup:${itemId}:${quantity}`, `Pick up ${quantity} × ${itemId}`, draft({ ...base, kind: "pickup_item", itemId, quantity }));
    }
  }
  for (const system of Object.values(state.systems).sort((a, b) => a.id.localeCompare(b.id))) {
    if (system.roomId === actor.location) {
      add(`repair:${system.id}`, `Repair ${system.name}`, draft({ ...base, kind: "repair_system", targetSystemId: system.id }));
    }
    if (actor.location === POWER_JUNCTION_ID) {
      add(
        `power:${system.id}:${!system.powered}`,
        `${system.powered ? "Disable" : "Enable"} power: ${system.name}`,
        draft({ ...base, kind: "set_power", targetSystemId: system.id, enabled: !system.powered }),
      );
    }
  }
  for (const hazard of Object.values(state.hazards)) {
    if (hazard.roomId === actor.location) {
      add(`seal:${hazard.id}`, `Seal ${hazard.name}`, draft({ ...base, kind: "seal_hull", targetHazardId: hazard.id }));
    }
  }
  for (const crew of Object.values(state.crew)) {
    if (crew.location === actor.location) {
      add(`stabilize:${crew.id}`, `Stabilize ${crew.name}`, draft({ ...base, kind: "stabilize_crew", targetCrewId: crew.id }));
    }
  }
  if (actor.location === "communications") {
    add(
      "distress:communications",
      "Send verified distress signal",
      draft({ ...base, kind: "send_distress", targetSystemId: "communications" }),
    );
  }
  add("wait", "Wait one turn", draft({ ...base, kind: "wait" }));
  return actions;
}

export function shortestPath(state: WorldState, start: string, target: string): string[] | null {
  if (start === target) return [start];
  const queue: string[][] = [[start]];
  const visited = new Set([start]);
  while (queue.length > 0) {
    const path = queue.shift();
    if (!path) break;
    const room = state.rooms[path[path.length - 1] ?? ""];
    if (!room) continue;
    for (const neighbor of room.neighbors) {
      if (visited.has(neighbor)) continue;
      const next = [...path, neighbor];
      if (neighbor === target) return next;
      visited.add(neighbor);
      queue.push(next);
    }
  }
  return null;
}
