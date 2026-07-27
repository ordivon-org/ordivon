export const ITEM_IDS = [
  "toolkit",
  "breaker-key",
  "spare-parts",
  "sealant",
  "medkit",
] as const;

export type ItemId = (typeof ITEM_IDS)[number];
export type Inventory = Record<ItemId, number>;

export function inventory(values: Partial<Inventory> = {}): Inventory {
  return {
    toolkit: values.toolkit ?? 0,
    "breaker-key": values["breaker-key"] ?? 0,
    "spare-parts": values["spare-parts"] ?? 0,
    sealant: values.sealant ?? 0,
    medkit: values.medkit ?? 0,
  };
}

export type MissionStatus = "running" | "victory" | "failure";

export interface RoomState {
  id: string;
  name: string;
  neighbors: string[];
  inventory: Inventory;
}

export interface AgentState {
  id: string;
  name: string;
  location: string;
  health: number;
  capabilities: string[];
  inventory: Inventory;
}

export interface CrewState {
  id: string;
  name: string;
  location: string;
  health: number;
  stabilized: boolean;
}

export interface SystemState {
  id: string;
  name: string;
  roomId: string;
  integrity: number;
  powered: boolean;
  powerDraw: number;
  repairParts: number;
}

export interface HazardState {
  id: string;
  name: string;
  roomId: string;
  sealed: boolean;
}

export interface StationResources {
  batteryInitial: number;
  batteryCharge: number;
  energyConsumed: number;
  oxygen: number;
  reactorHeat: number;
  initialItems: Inventory;
  consumedItems: Inventory;
}

export interface MissionState {
  status: MissionStatus;
  reason: string | null;
  distressSent: boolean;
  turnLimit: number;
}

export interface WorldState {
  schemaVersion: 2;
  scenarioId: string;
  seed: string;
  revision: number;
  turn: number;
  rooms: Record<string, RoomState>;
  agents: Record<string, AgentState>;
  crew: Record<string, CrewState>;
  systems: Record<string, SystemState>;
  hazards: Record<string, HazardState>;
  resources: StationResources;
  mission: MissionState;
}

interface CommandBase {
  commandId: string;
  actorId: string;
  expectedRevision: number;
}

export interface MoveCommand extends CommandBase {
  kind: "move";
  targetRoomId: string;
}

export interface PickupCommand extends CommandBase {
  kind: "pickup_item";
  itemId: ItemId;
  quantity: number;
}

export interface RepairSystemCommand extends CommandBase {
  kind: "repair_system";
  targetSystemId: string;
}

export interface SetPowerCommand extends CommandBase {
  kind: "set_power";
  targetSystemId: string;
  enabled: boolean;
}

export interface SealHullCommand extends CommandBase {
  kind: "seal_hull";
  targetHazardId: string;
}

export interface StabilizeCrewCommand extends CommandBase {
  kind: "stabilize_crew";
  targetCrewId: string;
}

export interface SendDistressCommand extends CommandBase {
  kind: "send_distress";
  targetSystemId: string;
}

export interface WaitCommand extends CommandBase {
  kind: "wait";
}

export type WorldCommand =
  | MoveCommand
  | PickupCommand
  | RepairSystemCommand
  | SetPowerCommand
  | SealHullCommand
  | StabilizeCrewCommand
  | SendDistressCommand
  | WaitCommand;

export type WorldCommandDraft = WorldCommand extends infer Command
  ? Command extends WorldCommand
    ? Omit<Command, "commandId">
    : never
  : never;

export interface AvailableAction {
  actionId: string;
  label: string;
  command: WorldCommandDraft;
}

export type ScalarValue = string | number | boolean | null;

export interface StateChange {
  path: string;
  before: ScalarValue;
  after: ScalarValue;
}

export interface WorldEvent {
  eventId: string;
  commandId: string;
  commandKind: WorldCommand["kind"];
  actorId: string;
  worldRevision: number;
  turn: number;
  beforeDigest: string;
  afterDigest: string;
  changes: StateChange[];
  missionStatus: MissionStatus;
  missionReason: string | null;
}

export type RejectionCode =
  | "invalid_command"
  | "mission_not_running"
  | "stale_revision"
  | "unknown_actor"
  | "unknown_target"
  | "capability_missing"
  | "tool_missing"
  | "item_missing"
  | "not_adjacent"
  | "wrong_location"
  | "already_complete"
  | "system_damaged"
  | "insufficient_power";

export type ApplyResult =
  | {
      status: "accepted";
      state: WorldState;
      event: WorldEvent;
    }
  | {
      status: "rejected";
      state: WorldState;
      code: RejectionCode;
      reason: string;
    };
