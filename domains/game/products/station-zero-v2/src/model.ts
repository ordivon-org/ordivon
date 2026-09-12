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
  contained?: boolean;
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

export interface ContainHazardCommand extends CommandBase {
  kind: "contain_hazard";
  targetHazardId: string;
}

export interface SendDistressCommand extends CommandBase {
  kind: "send_distress";
  targetSystemId: string;
}

export interface WaitCommand extends CommandBase {
  kind: "wait";
}

export type PrimitiveWorldCommand =
  | MoveCommand
  | PickupCommand
  | RepairSystemCommand
  | SetPowerCommand
  | SealHullCommand
  | StabilizeCrewCommand
  | ContainHazardCommand
  | SendDistressCommand
  | WaitCommand;

export interface TeamTickCommand extends CommandBase {
  kind: "team_tick";
  tickId: string;
  intents: PrimitiveWorldCommand[];
}

export type WorldCommand = PrimitiveWorldCommand | TeamTickCommand;

export type WorldCommandDraft = PrimitiveWorldCommand extends infer Command
  ? Command extends PrimitiveWorldCommand
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


export type WorldFact =
  | { kind: "agent_moved"; actorId: string; fromRoomId: string; toRoomId: string }
  | { kind: "agent_waited"; actorId: string }
  | { kind: "item_picked_up"; actorId: string; roomId: string; itemId: ItemId; quantity: number }
  | { kind: "item_consumed"; actorId: string; itemId: ItemId; quantity: number; purpose: string }
  | { kind: "system_repaired"; systemId: string; beforeIntegrity: number; afterIntegrity: number }
  | { kind: "power_state_changed"; systemId: string; powered: boolean }
  | { kind: "hull_breach_sealed"; hazardId: string }
  | { kind: "hazard_contained"; hazardId: string; actorId: string }
  | { kind: "crew_stabilized"; crewId: string; health: number }
  | { kind: "distress_signal_sent"; systemId: string }
  | { kind: "battery_consumed"; amount: number; poweredSystems: string[] }
  | { kind: "oxygen_changed"; before: number; after: number; causes: string[] }
  | { kind: "reactor_heat_changed"; before: number; after: number; causes: string[] }
  | { kind: "health_changed"; subjectType: "agent" | "crew"; subjectId: string; before: number; after: number; causes: string[] }
  | { kind: "mission_succeeded"; reason: string }
  | { kind: "mission_failed"; reason: string };

export interface VerificationCheck {
  name: string;
  passed: boolean;
  expected: ScalarValue;
  observed: ScalarValue;
}

export interface VerificationReceipt {
  effectKind: WorldCommand["kind"];
  success: boolean;
  checks: VerificationCheck[];
}

export interface ActorIntentReceipt {
  commandId: string;
  actorId: string;
  commandKind: PrimitiveWorldCommand["kind"];
  facts: WorldFact[];
  verification: VerificationReceipt;
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
  facts?: WorldFact[];
  verification?: VerificationReceipt;
  intentReceipts?: ActorIntentReceipt[];
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
  | "insufficient_power"
  | "conflicting_intents";

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

export interface TickIntent {
  commandSequence: number;
  command: WorldCommand;
}

export interface TickBatch {
  tickId: string;
  expectedWorldRevision: number;
  intents: TickIntent[];
}

export interface JournalEvent {
  tickId: string;
  commandSequence: number;
  simulationTick: number;
  worldRevision: number;
  event: WorldEvent;
}

export type ApplyTickResult =
  | {
      status: "accepted";
      state: WorldState;
      journalEvents: JournalEvent[];
    }
  | {
      status: "rejected";
      state: WorldState;
      code: "invalid_tick" | "stale_revision" | RejectionCode;
      reason: string;
    };
