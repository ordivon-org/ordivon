import type { PrimitiveWorldCommand, WorldState } from "../model.ts";
import { applyWorldTick } from "../world.ts";
import type { ActionProposal, AuthorityPolicyMode } from "../team/model.ts";
import type {
  DoctrineId,
  MissionFrontView,
  MissionOutcomeView,
  ObjectiveMissionView,
  TickForecast,
} from "./model.ts";

export interface DoctrineDefinition {
  doctrineId: DoctrineId;
  label: string;
  description: string;
  authorityPolicyMode: AuthorityPolicyMode;
}

export const DOCTRINES: DoctrineDefinition[] = [
  {
    doctrineId: "delegated-response",
    label: "Delegated response",
    description: "Specialists execute routine and high-risk work unless an existing hard safety rule requires Mission Control.",
    authorityPolicyMode: "autonomous",
  },
  {
    doctrineId: "critical-approval",
    label: "Critical approval",
    description: "Routine work proceeds automatically; power changes, hazard control, and rescue transmission require Mission Control.",
    authorityPolicyMode: "supervised",
  },
  {
    doctrineId: "strict-control",
    label: "Strict control",
    description: "High-risk changes require Mission Control and prohibited critical shutdowns remain blocked.",
    authorityPolicyMode: "locked",
  },
];

export function policyForDoctrine(doctrineId: DoctrineId | undefined): AuthorityPolicyMode {
  return DOCTRINES.find((entry) => entry.doctrineId === doctrineId)?.authorityPolicyMode ?? "supervised";
}

export function doctrineForPolicy(policyMode: AuthorityPolicyMode | null | undefined): DoctrineId {
  return DOCTRINES.find((entry) => entry.authorityPolicyMode === policyMode)?.doctrineId ?? "critical-approval";
}

function resourceValues(state: WorldState): Record<string, { label: string; value: number }> {
  return {
    battery: { label: "Battery", value: state.resources.batteryCharge },
    oxygen: { label: "Oxygen", value: state.resources.oxygen },
    "reactor-heat": { label: "Reactor heat", value: state.resources.reactorHeat },
    "crew-health": { label: state.crew["crew-01"]?.name ?? "Crew health", value: state.crew["crew-01"]?.health ?? 0 },
    turns: { label: "Turns remaining", value: Math.max(0, state.mission.turnLimit - state.turn) },
  };
}

function causesFor(resourceId: string, before: WorldState, after: WorldState): string[] {
  if (resourceId === "battery") {
    return Object.values(before.systems).filter((system) => system.powered).map((system) => `${system.name} power draw`);
  }
  if (resourceId === "oxygen") {
    const causes = ["baseline station consumption"];
    const breach = before.hazards["maintenance-breach"];
    if (!breach?.sealed && !breach?.contained) causes.push("uncontrolled hull breach");
    if (before.systems["life-support"]?.powered) causes.push("life support circulation");
    return causes;
  }
  if (resourceId === "reactor-heat") {
    return [before.systems.cooling?.powered ? "powered reactor cooling" : "cooling unavailable"];
  }
  if (resourceId === "crew-health") {
    const causes = [];
    if (!before.crew["crew-01"]?.stabilized) causes.push("untreated injury");
    if (before.resources.oxygen < 25) causes.push("critical oxygen");
    return causes;
  }
  if (resourceId === "turns") return ["one World Tick elapsed"];
  return [];
}

function objectiveSnapshot(state: WorldState): Record<string, boolean> {
  const breach = state.hazards["maintenance-breach"];
  return {
    "cooling-operational": (state.systems.cooling?.integrity ?? 0) >= 0.8,
    "cooling-powered": Boolean(state.systems.cooling?.powered) || state.resources.reactorHeat <= 20,
    "breach-controlled": Boolean(breach?.sealed || breach?.contained),
    "crew-stabilized": Boolean(state.crew["crew-01"]?.stabilized),
    "life-support-operational": (state.systems["life-support"]?.integrity ?? 0) >= 0.8,
    "life-support-powered": Boolean(state.systems["life-support"]?.powered),
    "communications-operational": (state.systems.communications?.integrity ?? 0) >= 0.8,
    "communications-powered": Boolean(state.systems.communications?.powered),
    "distress-sent": state.mission.distressSent,
  };
}

export function forecastCommands(state: WorldState, commands: PrimitiveWorldCommand[], summary: string): TickForecast {
  const result = applyWorldTick(state, {
    tickId: `forecast:${state.revision}:${commands.map((command) => command.commandId).join(":") || "wait"}`,
    expectedWorldRevision: state.revision,
    intents: commands.map((command, commandSequence) => ({ commandSequence, command })),
  });
  if (result.status === "rejected") {
    return {
      status: "unavailable",
      fromRevision: state.revision,
      resultingRevision: null,
      summary,
      resources: [],
      actorChanges: [],
      objectiveChanges: [],
      irreversibleEffects: [],
      terminal: null,
      unavailableReason: result.reason,
    };
  }
  const after = result.state;
  const beforeResources = resourceValues(state);
  const afterResources = resourceValues(after);
  const resources = Object.entries(beforeResources).map(([resourceId, before]) => ({
    resourceId,
    label: before.label,
    before: before.value,
    after: afterResources[resourceId]?.value ?? before.value,
    delta: (afterResources[resourceId]?.value ?? before.value) - before.value,
    causes: causesFor(resourceId, state, after),
  }));
  const actorChanges = Object.values(state.agents).map((actor) => {
    const next = after.agents[actor.id] ?? actor;
    return {
      actorId: actor.id,
      locationBefore: actor.location,
      locationAfter: next.location,
      healthBefore: actor.health,
      healthAfter: next.health,
    };
  }).filter((entry) => entry.locationBefore !== entry.locationAfter || entry.healthBefore !== entry.healthAfter);
  const beforeObjectives = objectiveSnapshot(state);
  const afterObjectives = objectiveSnapshot(after);
  const objectiveChanges = Object.keys(afterObjectives).filter((key) => !beforeObjectives[key] && afterObjectives[key]);
  const irreversibleEffects = commands.flatMap((command) => {
    if (command.kind === "seal_hull") return ["The breach is permanently sealed and one sealant charge is consumed."];
    if (command.kind === "repair_system") return [`One spare part is consumed to repair ${command.targetSystemId}.`];
    if (command.kind === "stabilize_crew") return ["One medkit is consumed to stabilize the casualty."];
    if (command.kind === "send_distress") return ["A verified external rescue signal is transmitted."];
    return [];
  });
  return {
    status: "available",
    fromRevision: state.revision,
    resultingRevision: after.revision,
    summary,
    resources,
    actorChanges,
    objectiveChanges,
    irreversibleEffects,
    terminal: after.mission.status === "running" ? null : { status: after.mission.status, reason: after.mission.reason ?? after.mission.status },
    unavailableReason: null,
  };
}

export function passiveForecast(state: WorldState): TickForecast {
  const commands = Object.values(state.agents).map((actor, index): PrimitiveWorldCommand => ({
    kind: "wait",
    commandId: `forecast-wait:${state.revision}:${index}:${actor.id}`,
    actorId: actor.id,
    expectedRevision: state.revision,
  }));
  return forecastCommands(state, commands, "If the team spends one Tick without changing station state");
}

export function proposalForecast(state: WorldState, proposal: ActionProposal): TickForecast {
  return forecastCommands(state, [proposal.command], `${proposal.actorId} executes the proposed action`);
}

function firstUnresolved(objectives: ObjectiveMissionView[], ids: string[]): string | null {
  return objectives.find((objective) => ids.includes(objective.objectiveId) && !["satisfied", "superseded"].includes(objective.status))?.label ?? null;
}

export function missionFronts(
  state: WorldState,
  objectives: ObjectiveMissionView[],
  forecast: TickForecast,
): MissionFrontView[] {
  const next = new Map(forecast.resources.map((entry) => [entry.resourceId, entry.after]));
  const heatAfter = next.get("reactor-heat") ?? state.resources.reactorHeat;
  const oxygenAfter = next.get("oxygen") ?? state.resources.oxygen;
  const crewAfter = next.get("crew-health") ?? state.crew["crew-01"]?.health ?? 0;
  const turnsAfter = next.get("turns") ?? Math.max(0, state.mission.turnLimit - state.turn);
  const statusFor = (resolved: boolean, critical: boolean, risk: boolean): MissionFrontView["status"] =>
    resolved ? "resolved" : critical ? "critical" : risk ? "at-risk" : "stable";
  const breach = state.hazards["maintenance-breach"];
  const reactorResolved = (state.systems.cooling?.integrity ?? 0) >= 0.8 && (state.systems.cooling?.powered || state.resources.reactorHeat <= 20);
  const crewResolved = Boolean(state.crew["crew-01"]?.stabilized);
  const habitationResolved = Boolean(breach?.sealed || breach?.contained) && (state.systems["life-support"]?.integrity ?? 0) >= 0.8 && Boolean(state.systems["life-support"]?.powered);
  const rescueResolved = state.mission.distressSent;
  return [
    {
      frontId: "reactor",
      label: "Reactor stability",
      status: statusFor(reactorResolved, heatAfter >= 90, heatAfter >= 70),
      objectiveIds: ["cooling-operational", "cooling-powered"],
      responsibleActorIds: ["engineer-01"],
      primaryBlocker: firstUnresolved(objectives, ["cooling-operational", "cooling-powered"]),
      forecast: reactorResolved ? "Cooling can hold the reactor within verified limits." : `No-change forecast: reactor heat ${state.resources.reactorHeat} → ${heatAfter}.`,
    },
    {
      frontId: "crew",
      label: "Crew survival",
      status: statusFor(crewResolved, crewAfter <= 15, crewAfter <= 40),
      objectiveIds: ["crew-stabilized"],
      responsibleActorIds: ["medic-01"],
      primaryBlocker: firstUnresolved(objectives, ["crew-stabilized"]),
      forecast: crewResolved ? "Navigator Sato is stabilized." : `No-change forecast: casualty health ${state.crew["crew-01"]?.health ?? 0} → ${crewAfter}.`,
    },
    {
      frontId: "habitation",
      label: "Station habitability",
      status: statusFor(habitationResolved, oxygenAfter <= 25, oxygenAfter <= 50),
      objectiveIds: ["breach-controlled", "life-support-operational", "life-support-powered"],
      responsibleActorIds: ["security-01", "engineer-01"],
      primaryBlocker: firstUnresolved(objectives, ["breach-controlled", "life-support-operational", "life-support-powered"]),
      forecast: habitationResolved ? "The breach is controlled and life support is online." : `No-change forecast: oxygen ${state.resources.oxygen} → ${oxygenAfter}.`,
    },
    {
      frontId: "rescue",
      label: "Rescue contact",
      status: statusFor(rescueResolved, turnsAfter <= 3, turnsAfter <= 8),
      objectiveIds: ["communications-operational", "communications-powered", "distress-sent"],
      responsibleActorIds: ["engineer-01"],
      primaryBlocker: firstUnresolved(objectives, ["communications-operational", "communications-powered", "distress-sent"]),
      forecast: rescueResolved ? "A verified distress signal has been transmitted." : `${turnsAfter} mission Ticks remain after the next no-change Tick.`,
    },
  ];
}

export function missionOutcome(state: WorldState): MissionOutcomeView | null {
  if (state.mission.status === "running") return null;
  const casualty = state.crew["crew-01"];
  const breach = state.hazards["maintenance-breach"];
  const victory = state.mission.status === "victory";
  const facts = [
    (casualty?.health ?? 0) > 0 ? `Navigator Sato survived with ${casualty?.health ?? 0}% health.` : "Navigator Sato was lost.",
    casualty?.stabilized ? "The casualty was stabilized." : "The casualty remained unstable.",
    breach?.sealed ? "The hull breach was permanently sealed." : breach?.contained ? "The hull breach remained under containment." : "The hull breach remained uncontrolled.",
    (state.systems.cooling?.integrity ?? 0) >= 0.8 ? "Reactor cooling was restored." : "Reactor cooling remained damaged.",
    state.systems["life-support"]?.powered ? "Life support remained powered." : "Life support was offline.",
    state.mission.distressSent ? "A verified rescue signal was transmitted." : "No verified rescue signal was transmitted.",
  ];
  const nearMisses = [
    state.resources.batteryCharge <= 8 ? `Battery reserve ended at ${state.resources.batteryCharge}.` : null,
    state.resources.oxygen <= 40 ? `Oxygen reserve ended at ${state.resources.oxygen}%.` : null,
    state.resources.reactorHeat >= 80 ? `Reactor heat ended at ${state.resources.reactorHeat}%.` : null,
    casualty && casualty.health <= 25 ? `Navigator Sato ended at ${casualty.health}% health.` : null,
  ].filter((entry): entry is string => Boolean(entry));
  return {
    headline: victory ? "Rescue signal verified" : "Mission failed",
    summary: victory ? "The team stabilized Station Zero long enough to request rescue." : `Station Zero reached a terminal condition: ${state.mission.reason ?? "unknown"}.`,
    facts,
    nearMisses,
  };
}
