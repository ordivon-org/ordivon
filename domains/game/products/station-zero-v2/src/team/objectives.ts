import type { WorldState } from "../model.ts";
import type { ActorRole, ObjectiveGraph, ObjectiveStatus } from "./model.ts";

export const TEAM_OBJECTIVE_GRAPH: ObjectiveGraph = {
  schemaVersion: 1,
  kind: "ordivon.game.objective-graph",
  rootObjectiveId: "verified-rescue",
  nodes: [
    { objectiveId: "cooling-operational", label: "Repair cooling", visibility: "public", allOf: [], anyOf: [], requiredCapabilities: ["repair_system"], satisfactionPredicateId: "system:cooling:operational", priorityClass: "critical" },
    { objectiveId: "cooling-powered", label: "Power cooling while heat requires it", visibility: "public", allOf: ["cooling-operational"], anyOf: [], requiredCapabilities: ["set_power"], satisfactionPredicateId: "system:cooling:safe", priorityClass: "critical" },
    { objectiveId: "breach-sealed", label: "Seal the maintenance breach", visibility: "public", allOf: [], anyOf: [], requiredCapabilities: ["seal_hull"], satisfactionPredicateId: "hazard:maintenance-breach:sealed", priorityClass: "high" },
    { objectiveId: "breach-contained", label: "Contain the maintenance breach", visibility: "public", allOf: [], anyOf: [], requiredCapabilities: ["contain_hazard"], satisfactionPredicateId: "hazard:maintenance-breach:contained", priorityClass: "high" },
    { objectiveId: "breach-controlled", label: "Control the maintenance breach", visibility: "public", allOf: [], anyOf: [["breach-sealed"], ["breach-contained"]], requiredCapabilities: [], satisfactionPredicateId: "hazard:maintenance-breach:controlled", priorityClass: "critical" },
    { objectiveId: "crew-stabilized", label: "Stabilize the injured crew member", visibility: "public", allOf: [], anyOf: [], requiredCapabilities: ["basic_first_aid"], satisfactionPredicateId: "crew:crew-01:stabilized", priorityClass: "high" },
    { objectiveId: "life-support-operational", label: "Repair life support", visibility: "public", allOf: [], anyOf: [], requiredCapabilities: ["repair_system"], satisfactionPredicateId: "system:life-support:operational", priorityClass: "high" },
    { objectiveId: "life-support-powered", label: "Power life support", visibility: "public", allOf: ["life-support-operational"], anyOf: [], requiredCapabilities: ["set_power"], satisfactionPredicateId: "system:life-support:powered", priorityClass: "critical" },
    { objectiveId: "communications-operational", label: "Repair communications", visibility: "public", allOf: [], anyOf: [], requiredCapabilities: ["repair_system"], satisfactionPredicateId: "system:communications:operational", priorityClass: "normal" },
    { objectiveId: "communications-powered", label: "Power communications", visibility: "public", allOf: ["communications-operational"], anyOf: [], requiredCapabilities: ["set_power"], satisfactionPredicateId: "system:communications:powered", priorityClass: "normal" },
    { objectiveId: "distress-sent", label: "Transmit the distress signal", visibility: "public", allOf: ["communications-powered"], anyOf: [], requiredCapabilities: ["send_distress"], satisfactionPredicateId: "mission:distress-sent", priorityClass: "high" },
    { objectiveId: "verified-rescue", label: "Stabilize Station Zero and request rescue", visibility: "public", allOf: ["breach-controlled", "crew-stabilized", "life-support-powered", "communications-powered", "distress-sent"], anyOf: [], requiredCapabilities: [], satisfactionPredicateId: "mission:victory", priorityClass: "critical" },
  ],
};

function operational(state: WorldState, systemId: string): boolean {
  return (state.systems[systemId]?.integrity ?? 0) >= 0.8;
}

export function objectiveSatisfied(state: WorldState, objectiveId: string): boolean {
  const breach = state.hazards["maintenance-breach"];
  switch (objectiveId) {
    case "cooling-operational": return operational(state, "cooling");
    case "cooling-powered": return operational(state, "cooling") && (state.systems.cooling?.powered === true || state.resources.reactorHeat <= 20);
    case "breach-sealed": return breach?.sealed === true;
    case "breach-contained": return breach?.contained === true;
    case "breach-controlled": return breach?.sealed === true || breach?.contained === true;
    case "crew-stabilized": return state.crew["crew-01"]?.stabilized === true;
    case "life-support-operational": return operational(state, "life-support");
    case "life-support-powered": return operational(state, "life-support") && state.systems["life-support"]?.powered === true;
    case "communications-operational": return operational(state, "communications");
    case "communications-powered": return operational(state, "communications") && state.systems.communications?.powered === true;
    case "distress-sent": return state.mission.distressSent;
    case "verified-rescue": return state.mission.status === "victory";
    default: throw new Error(`unknown Objective: ${objectiveId}`);
  }
}

export function objectiveStatus(state: WorldState): ObjectiveStatus[] {
  return TEAM_OBJECTIVE_GRAPH.nodes.map((node) => ({
    objectiveId: node.objectiveId,
    satisfied: objectiveSatisfied(state, node.objectiveId),
    visible: node.visibility === "public",
  }));
}

export function objectivesForRole(role: ActorRole): string[] {
  switch (role) {
    case "engineer": return ["cooling-operational", "cooling-powered", "breach-sealed", "life-support-operational", "life-support-powered", "communications-operational", "communications-powered", "distress-sent"];
    case "medic": return ["crew-stabilized"];
    case "security": return ["breach-contained"];
    case "coordinator": return TEAM_OBJECTIVE_GRAPH.nodes.map((node) => node.objectiveId);
  }
}

export function nextObjectiveForRole(state: WorldState, role: ActorRole): string | null {
  return objectivesForRole(role).find((objectiveId) => !objectiveSatisfied(state, objectiveId)) ?? null;
}
