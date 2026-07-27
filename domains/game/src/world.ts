import { sha256 } from "./digest.ts";

export interface RoomState {
  id: string;
  name: string;
  powered: boolean;
  oxygen: number;
  equipmentIntegrity: number;
}

export interface AgentState {
  id: string;
  name: string;
  location: string;
  capabilities: string[];
  inventory: string[];
}

export interface WorldState {
  scenarioId: string;
  revision: number;
  turn: number;
  rooms: Record<string, RoomState>;
  agents: Record<string, AgentState>;
}

export interface RestorePowerCommand {
  kind: "restore_power";
  commandId: string;
  actorId: string;
  targetId: string;
  expectedRevision: number;
}

export type WorldCommand = RestorePowerCommand;

export interface WorldEvent {
  eventId: string;
  commandId: string;
  kind: "power_restored";
  actorId: string;
  targetId: string;
  worldRevision: number;
  beforeDigest: string;
  afterDigest: string;
  observations: Array<{
    subjectId: string;
    field: string;
    before: boolean | number;
    after: boolean | number;
  }>;
}

export type ApplyResult =
  | {
      status: "accepted";
      state: WorldState;
      event: WorldEvent;
    }
  | {
      status: "rejected";
      state: WorldState;
      code:
        | "invalid_command"
        | "stale_revision"
        | "unknown_actor"
        | "unknown_target"
        | "capability_missing"
        | "tool_missing"
        | "already_powered";
      reason: string;
    };

export function initialWorld(): WorldState {
  return {
    scenarioId: "station-zero-m0",
    revision: 0,
    turn: 0,
    rooms: {
      "life-support": {
        id: "life-support",
        name: "Life Support",
        powered: false,
        oxygen: 72,
        equipmentIntegrity: 0.58,
      },
    },
    agents: {
      "engineer-01": {
        id: "engineer-01",
        name: "Engineer Imani",
        location: "life-support",
        capabilities: ["restore_power"],
        inventory: ["breaker-key"],
      },
    },
  };
}

function reject(
  state: WorldState,
  code: Extract<ApplyResult, { status: "rejected" }>['code'],
  reason: string,
): ApplyResult {
  return { status: "rejected", state, code, reason };
}

export function parseWorldCommand(input: unknown): WorldCommand {
  if (input === null || typeof input !== "object") {
    throw new TypeError("command must be an object");
  }

  const value = input as Record<string, unknown>;
  if (value.kind !== "restore_power") {
    throw new TypeError("unsupported command kind");
  }
  if (typeof value.commandId !== "string" || value.commandId.length < 1) {
    throw new TypeError("commandId must be a non-empty string");
  }
  if (typeof value.actorId !== "string" || value.actorId.length < 1) {
    throw new TypeError("actorId must be a non-empty string");
  }
  if (typeof value.targetId !== "string" || value.targetId.length < 1) {
    throw new TypeError("targetId must be a non-empty string");
  }
  if (!Number.isSafeInteger(value.expectedRevision) || (value.expectedRevision as number) < 0) {
    throw new TypeError("expectedRevision must be a non-negative integer");
  }

  return {
    kind: "restore_power",
    commandId: value.commandId,
    actorId: value.actorId,
    targetId: value.targetId,
    expectedRevision: value.expectedRevision as number,
  };
}

export function applyWorldCommand(state: WorldState, command: WorldCommand): ApplyResult {
  if (command.kind !== "restore_power") {
    return reject(state, "invalid_command", "unsupported command kind");
  }

  if (command.expectedRevision !== state.revision) {
    return reject(
      state,
      "stale_revision",
      `expected revision ${command.expectedRevision}, current revision is ${state.revision}`,
    );
  }

  const actor = state.agents[command.actorId];
  if (!actor) {
    return reject(state, "unknown_actor", `unknown actor: ${command.actorId}`);
  }

  const room = state.rooms[command.targetId];
  if (!room) {
    return reject(state, "unknown_target", `unknown target: ${command.targetId}`);
  }

  if (!actor.capabilities.includes("restore_power")) {
    return reject(state, "capability_missing", "actor lacks restore_power capability");
  }

  if (!actor.inventory.includes("breaker-key")) {
    return reject(state, "tool_missing", "breaker-key is required");
  }

  if (room.powered) {
    return reject(state, "already_powered", "target room is already powered");
  }

  const beforeDigest = sha256(state);
  const next = structuredClone(state);
  const nextRoom = next.rooms[command.targetId];
  if (!nextRoom) {
    throw new Error("validated target disappeared during deterministic transition");
  }
  next.revision += 1;
  next.turn += 1;
  nextRoom.powered = true;
  nextRoom.oxygen = Math.min(100, nextRoom.oxygen + 8);
  nextRoom.equipmentIntegrity = Math.min(1, Number((nextRoom.equipmentIntegrity + 0.02).toFixed(2)));
  const afterDigest = sha256(next);

  return {
    status: "accepted",
    state: next,
    event: {
      eventId: `event:${command.commandId}`,
      commandId: command.commandId,
      kind: "power_restored",
      actorId: command.actorId,
      targetId: command.targetId,
      worldRevision: next.revision,
      beforeDigest,
      afterDigest,
      observations: [
        { subjectId: room.id, field: "powered", before: room.powered, after: nextRoom.powered },
        { subjectId: room.id, field: "oxygen", before: room.oxygen, after: nextRoom.oxygen },
        {
          subjectId: room.id,
          field: "equipmentIntegrity",
          before: room.equipmentIntegrity,
          after: nextRoom.equipmentIntegrity,
        },
      ],
    },
  };
}
