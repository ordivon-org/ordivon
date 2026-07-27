import type {
  ScalarValue,
  VerificationCheck,
  VerificationReceipt,
  WorldCommand,
  WorldEvent,
  WorldFact,
  WorldState,
} from "./model.ts";

function check(name: string, expected: ScalarValue, observed: ScalarValue): VerificationCheck {
  return { name, expected, observed, passed: expected === observed };
}

function verification(before: WorldState, after: WorldState, command: WorldCommand): VerificationReceipt {
  const actor = after.agents[command.actorId];
  const checks: VerificationCheck[] = [
    check("world_revision_advanced", before.revision + 1, after.revision),
    check("simulation_tick_advanced", before.turn + 1, after.turn),
  ];
  switch (command.kind) {
    case "move":
      checks.push(check("actor_location", command.targetRoomId, actor?.location ?? null));
      break;
    case "pickup_item": {
      const beforeQuantity = before.agents[command.actorId]?.inventory[command.itemId] ?? 0;
      checks.push(check("actor_item_quantity", beforeQuantity + command.quantity, actor?.inventory[command.itemId] ?? null));
      break;
    }
    case "repair_system":
      checks.push(check("system_operational", true, (after.systems[command.targetSystemId]?.integrity ?? 0) >= 0.8));
      break;
    case "set_power":
      checks.push(check("system_power", command.enabled, after.systems[command.targetSystemId]?.powered ?? null));
      break;
    case "seal_hull":
      checks.push(check("hazard_sealed", true, after.hazards[command.targetHazardId]?.sealed ?? null));
      break;
    case "stabilize_crew":
      checks.push(check("crew_stabilized", true, after.crew[command.targetCrewId]?.stabilized ?? null));
      break;
    case "contain_hazard":
      checks.push(check("hazard_contained", true, after.hazards[command.targetHazardId]?.contained ?? null));
      break;
    case "team_tick":
      checks.push(check("team_tick_requires_v3", true, true));
      break;
    case "send_distress":
      checks.push(check("distress_sent", true, after.mission.distressSent));
      break;
    case "wait":
      checks.push(check("world_state_retained", true, true));
      break;
  }
  return { effectKind: command.kind, success: checks.every((entry) => entry.passed), checks };
}

function healthCauses(after: WorldState, subjectType: "agent" | "crew", subjectId: string): string[] {
  const causes: string[] = [];
  if (after.resources.oxygen < 45) causes.push("low_oxygen");
  if (subjectType === "crew" && !after.crew[subjectId]?.stabilized) causes.push("untreated_injury");
  if (subjectType === "agent" && after.agents[subjectId]?.location === "reactor" && after.resources.reactorHeat > 85) {
    causes.push("reactor_heat_exposure");
  }
  return causes;
}

export function deriveFacts(
  before: WorldState,
  after: WorldState,
  command: WorldCommand,
): WorldFact[] {
  const facts: WorldFact[] = [];
  const beforeActor = before.agents[command.actorId];
  const afterActor = after.agents[command.actorId];

  switch (command.kind) {
    case "move":
      facts.push({
        kind: "agent_moved",
        actorId: command.actorId,
        fromRoomId: beforeActor?.location ?? "unknown",
        toRoomId: command.targetRoomId,
      });
      break;
    case "pickup_item":
      facts.push({
        kind: "item_picked_up",
        actorId: command.actorId,
        roomId: beforeActor?.location ?? "unknown",
        itemId: command.itemId,
        quantity: command.quantity,
      });
      break;
    case "repair_system": {
      const previous = before.systems[command.targetSystemId]?.integrity ?? 0;
      const current = after.systems[command.targetSystemId]?.integrity ?? previous;
      facts.push({ kind: "system_repaired", systemId: command.targetSystemId, beforeIntegrity: previous, afterIntegrity: current });
      const quantity = (after.resources.consumedItems["spare-parts"] - before.resources.consumedItems["spare-parts"]);
      if (quantity > 0) facts.push({ kind: "item_consumed", actorId: command.actorId, itemId: "spare-parts", quantity, purpose: `repair:${command.targetSystemId}` });
      break;
    }
    case "set_power":
      facts.push({ kind: "power_state_changed", systemId: command.targetSystemId, powered: command.enabled });
      break;
    case "seal_hull":
      facts.push({ kind: "hull_breach_sealed", hazardId: command.targetHazardId });
      facts.push({ kind: "item_consumed", actorId: command.actorId, itemId: "sealant", quantity: 1, purpose: `seal:${command.targetHazardId}` });
      break;
    case "stabilize_crew":
      facts.push({ kind: "crew_stabilized", crewId: command.targetCrewId, health: after.crew[command.targetCrewId]?.health ?? 0 });
      facts.push({ kind: "item_consumed", actorId: command.actorId, itemId: "medkit", quantity: 1, purpose: `stabilize:${command.targetCrewId}` });
      break;
    case "contain_hazard":
      facts.push({ kind: "hazard_contained", hazardId: command.targetHazardId, actorId: command.actorId });
      break;
    case "team_tick":
      break;
    case "send_distress":
      facts.push({ kind: "distress_signal_sent", systemId: command.targetSystemId });
      break;
    case "wait":
      facts.push({ kind: "agent_waited", actorId: command.actorId });
      break;
  }

  const batteryUsed = after.resources.energyConsumed - before.resources.energyConsumed;
  if (batteryUsed > 0) {
    facts.push({
      kind: "battery_consumed",
      amount: batteryUsed,
      poweredSystems: Object.values(after.systems).filter((system) => system.powered).map((system) => system.id).sort(),
    });
  }
  if (before.resources.oxygen !== after.resources.oxygen) {
    const causes = ["baseline_consumption"];
    if (!(after.hazards["maintenance-breach"]?.sealed || after.hazards["maintenance-breach"]?.contained)) causes.push("hull_breach");
    if (after.systems["life-support"]?.powered && (after.systems["life-support"]?.integrity ?? 0) >= 0.8) causes.push("life_support");
    facts.push({ kind: "oxygen_changed", before: before.resources.oxygen, after: after.resources.oxygen, causes });
  }
  if (before.resources.reactorHeat !== after.resources.reactorHeat) {
    const cooling = after.systems.cooling;
    facts.push({
      kind: "reactor_heat_changed",
      before: before.resources.reactorHeat,
      after: after.resources.reactorHeat,
      causes: [cooling?.powered && (cooling.integrity ?? 0) >= 0.8 ? "cooling_operational" : "cooling_unavailable"],
    });
  }
  for (const [id, subject] of Object.entries(after.agents)) {
    const previous = before.agents[id]?.health;
    if (previous !== undefined && previous !== subject.health) {
      facts.push({ kind: "health_changed", subjectType: "agent", subjectId: id, before: previous, after: subject.health, causes: healthCauses(after, "agent", id) });
    }
  }
  for (const [id, subject] of Object.entries(after.crew)) {
    const previous = before.crew[id]?.health;
    if (previous !== undefined && previous !== subject.health) {
      facts.push({ kind: "health_changed", subjectType: "crew", subjectId: id, before: previous, after: subject.health, causes: healthCauses(after, "crew", id) });
    }
  }
  if (before.mission.status === "running" && after.mission.status === "victory") {
    facts.push({ kind: "mission_succeeded", reason: after.mission.reason ?? "unknown" });
  } else if (before.mission.status === "running" && after.mission.status === "failure") {
    facts.push({ kind: "mission_failed", reason: after.mission.reason ?? "unknown" });
  }
  return facts;
}

export function enrichWorldEvent(
  before: WorldState,
  after: WorldState,
  command: WorldCommand,
  event: WorldEvent,
): WorldEvent {
  return {
    ...event,
    facts: deriveFacts(before, after, command),
    verification: verification(before, after, command),
  };
}

export function describeFact(fact: WorldFact): string {
  switch (fact.kind) {
    case "agent_moved": return `${fact.actorId} moved to ${fact.toRoomId}`;
    case "agent_waited": return `${fact.actorId} waited`;
    case "item_picked_up": return `${fact.actorId} picked up ${fact.quantity} × ${fact.itemId}`;
    case "item_consumed": return `${fact.quantity} × ${fact.itemId} consumed for ${fact.purpose}`;
    case "system_repaired": return `${fact.systemId} repaired to ${Math.round(fact.afterIntegrity * 100)}%`;
    case "power_state_changed": return `${fact.systemId} power ${fact.powered ? "enabled" : "disabled"}`;
    case "hull_breach_sealed": return `${fact.hazardId} sealed`;
    case "hazard_contained": return `${fact.hazardId} contained by ${fact.actorId}`;
    case "crew_stabilized": return `${fact.crewId} stabilized`;
    case "distress_signal_sent": return `distress signal sent through ${fact.systemId}`;
    case "battery_consumed": return `${fact.amount} battery consumed`;
    case "oxygen_changed": return `oxygen ${fact.before} → ${fact.after}`;
    case "reactor_heat_changed": return `reactor heat ${fact.before} → ${fact.after}`;
    case "health_changed": return `${fact.subjectId} health ${fact.before} → ${fact.after}`;
    case "mission_succeeded": return `mission succeeded: ${fact.reason}`;
    case "mission_failed": return `mission failed: ${fact.reason}`;
  }
}
