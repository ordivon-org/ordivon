import { sha256 } from "../digest.ts";
import type { PrimitiveWorldCommand, WorldFact, WorldState } from "../model.ts";
import { scoreMission } from "../scoring.ts";
import type { GameStore } from "../storage.ts";
import { TeamExecutionStore } from "../team/execution-store.ts";
import type { ActionProposal, CompiledTeamContext, TeamProjection, TeamRound } from "../team/model.ts";
import { objectivesForRole } from "../team/objectives.ts";
import { doctrineForPolicy, missionFronts, missionOutcome, passiveForecast, proposalForecast } from "./experience.ts";
import { TeamStore, teamRunInitialized } from "../team/store.ts";
import type {
  ActorMissionView,
  CoordinationRoundView,
  InterventionCard,
  MissionControlView,
  MissionResourceView,
  MissionTimelineItem,
  ObjectiveMissionView,
  StationRoomView,
} from "./model.ts";

const ROOM_LAYOUT: Record<string, { x: number; y: number }> = {
  "command-center": { x: 1, y: 0 },
  "power-junction": { x: 1, y: 1 },
  storage: { x: 0, y: 2 },
  maintenance: { x: 0, y: 3 },
  "medical-bay": { x: 2, y: 2 },
  reactor: { x: 2, y: 0 },
  communications: { x: 2, y: 1 },
  "life-support": { x: 1, y: 3 },
};

function commandLabel(command: PrimitiveWorldCommand): string {
  switch (command.kind) {
    case "move": return `Move to ${command.targetRoomId}`;
    case "pickup_item": return `Pick up ${command.quantity} ${command.itemId}`;
    case "repair_system": return `Repair ${command.targetSystemId}`;
    case "set_power": return `${command.enabled ? "Power" : "Shut down"} ${command.targetSystemId}`;
    case "seal_hull": return `Seal ${command.targetHazardId}`;
    case "contain_hazard": return `Contain ${command.targetHazardId}`;
    case "stabilize_crew": return `Stabilize ${command.targetCrewId}`;
    case "send_distress": return "Transmit distress signal";
    case "wait": return "Wait";
  }
}

export function factSummary(fact: WorldFact): string {
  switch (fact.kind) {
    case "agent_moved": return `${fact.actorId} moved from ${fact.fromRoomId} to ${fact.toRoomId}`;
    case "agent_waited": return `${fact.actorId} waited`;
    case "item_picked_up": return `${fact.actorId} picked up ${fact.quantity} ${fact.itemId}`;
    case "item_consumed": return `${fact.actorId} consumed ${fact.quantity} ${fact.itemId} for ${fact.purpose}`;
    case "system_repaired": return `${fact.systemId} integrity reached ${Math.round(fact.afterIntegrity * 100)}%`;
    case "power_state_changed": return `${fact.systemId} power ${fact.powered ? "enabled" : "disabled"}`;
    case "hull_breach_sealed": return `${fact.hazardId} sealed`;
    case "hazard_contained": return `${fact.hazardId} contained by ${fact.actorId}`;
    case "crew_stabilized": return `${fact.crewId} stabilized`;
    case "distress_signal_sent": return "Distress signal transmitted";
    case "battery_consumed": return `${fact.amount} battery consumed`;
    case "oxygen_changed": return `Oxygen ${fact.before} → ${fact.after}`;
    case "reactor_heat_changed": return `Reactor heat ${fact.before} → ${fact.after}`;
    case "health_changed": return `${fact.subjectId} health ${fact.before} → ${fact.after}`;
    case "mission_succeeded": return `Mission succeeded: ${fact.reason}`;
    case "mission_failed": return `Mission failed: ${fact.reason}`;
  }
}

function resourceBand(value: number, warning: number, critical: number, inverse = false): MissionResourceView["band"] {
  if (inverse) return value >= critical ? "critical" : value >= warning ? "warning" : "stable";
  return value <= critical ? "critical" : value <= warning ? "warning" : "stable";
}

function trend(before: number | undefined, after: number, higherIsBetter = true): MissionResourceView["trend"] {
  if (before === undefined) return "unknown";
  if (before === after) return "stable";
  return (after > before) === higherIsBetter ? "improving" : "worsening";
}

function previousResourceValues(store: GameStore, runId: string): Record<string, number> {
  const event = store.recentJournalEvents(1, runId).at(-1)?.event;
  const values: Record<string, number> = {};
  for (const fact of event?.facts ?? []) {
    if (fact.kind === "oxygen_changed") values.oxygen = fact.before;
    if (fact.kind === "reactor_heat_changed") values.reactorHeat = fact.before;
    if (fact.kind === "health_changed" && fact.subjectId === "crew-01") values.crewHealth = fact.before;
  }
  return values;
}

function resources(store: GameStore, runId: string, state: WorldState): MissionResourceView[] {
  const previous = previousResourceValues(store, runId);
  const crew = state.crew["crew-01"];
  return [
    { resourceId: "battery", label: "Battery", current: state.resources.batteryCharge, maximum: state.resources.batteryInitial, unit: "energy", band: resourceBand(state.resources.batteryCharge, 10, 4), trend: "worsening" },
    { resourceId: "oxygen", label: "Oxygen", current: state.resources.oxygen, maximum: 100, unit: "percent", band: resourceBand(state.resources.oxygen, 50, 25), trend: trend(previous.oxygen, state.resources.oxygen) },
    { resourceId: "reactor-heat", label: "Reactor heat", current: state.resources.reactorHeat, maximum: 100, unit: "percent", band: resourceBand(state.resources.reactorHeat, 70, 90, true), trend: trend(previous.reactorHeat, state.resources.reactorHeat, false) },
    { resourceId: "crew-health", label: crew?.name ?? "Crew health", current: crew?.health ?? 0, maximum: 100, unit: "health", band: resourceBand(crew?.health ?? 0, 40, 15), trend: trend(previous.crewHealth, crew?.health ?? 0) },
    { resourceId: "turns", label: "Turns remaining", current: Math.max(0, state.mission.turnLimit - state.turn), maximum: state.mission.turnLimit, unit: "ticks", band: resourceBand(Math.max(0, state.mission.turnLimit - state.turn), 8, 3), trend: "worsening" },
  ];
}

function station(state: WorldState): StationRoomView[] {
  return Object.values(state.rooms).map((room) => ({
    roomId: room.id,
    name: room.name,
    x: ROOM_LAYOUT[room.id]?.x ?? 0,
    y: ROOM_LAYOUT[room.id]?.y ?? 0,
    neighbors: [...room.neighbors],
    inventory: { ...room.inventory },
    actorIds: Object.values(state.agents).filter((actor) => actor.location === room.id).map((actor) => actor.id).sort(),
    crewIds: Object.values(state.crew).filter((crew) => crew.location === room.id).map((crew) => crew.id).sort(),
    systemIds: Object.values(state.systems).filter((system) => system.roomId === room.id).map((system) => system.id).sort(),
    hazardIds: Object.values(state.hazards).filter((hazard) => hazard.roomId === room.id).map((hazard) => hazard.id).sort(),
    systems: Object.values(state.systems).filter((system) => system.roomId === room.id).map((system) => ({ systemId: system.id, name: system.name, integrity: system.integrity, powered: system.powered })),
    hazards: Object.values(state.hazards).filter((hazard) => hazard.roomId === room.id).map((hazard) => ({ hazardId: hazard.id, name: hazard.name, controlled: Boolean(hazard.sealed || hazard.contained) })),
    crew: Object.values(state.crew).filter((crew) => crew.location === room.id).map((crew) => ({ crewId: crew.id, name: crew.name, health: crew.health, stabilized: crew.stabilized })),
  })).sort((a, b) => a.y - b.y || a.x - b.x || a.roomId.localeCompare(b.roomId));
}

function blockItems(context: CompiledTeamContext | null): string[] {
  if (!context) return [];
  const items: string[] = [];
  const local = context.blocks.find((block) => block.kind === "local")?.payload as any;
  if (local?.room?.name) items.push(`Local room: ${local.room.name}`);
  for (const system of local?.systems ?? []) items.push(`Observed ${system.name}: ${Math.round(system.integrity * 100)}% integrity, ${system.powered ? "powered" : "offline"}`);
  for (const hazard of local?.hazards ?? []) items.push(`Observed ${hazard.name}: ${hazard.sealed || hazard.contained ? "controlled" : "active"}`);
  for (const crew of local?.crew ?? []) items.push(`Observed ${crew.name}: health ${crew.health}, ${crew.stabilized ? "stabilized" : "unstabilized"}`);
  const messages = context.blocks.find((block) => block.kind === "message")?.payload as any[] | undefined;
  for (const message of messages ?? []) items.push(`Message: ${message.boundedSummary}`);
  for (const fact of context.visibleFacts.slice(-8)) items.push(`Fact: ${factSummary(fact)}`);
  return items.slice(-12);
}

function latestContext(execution: TeamExecutionStore, team: TeamStore, rounds: TeamRound[], actorId: string): CompiledTeamContext | null {
  for (const round of [...rounds].reverse()) {
    const reference = execution.findContextForActor(round.roundId, actorId);
    if (reference) return team.host.getArtifact<CompiledTeamContext>(reference.artifactDigest).content;
  }
  return null;
}

function latestProposal(execution: TeamExecutionStore, rounds: TeamRound[], actorId: string): ActionProposal | null {
  for (const round of [...rounds].reverse()) {
    const proposal = execution.findProposalForActor(round.roundId, actorId);
    if (proposal) return proposal;
  }
  return null;
}

function actors(state: WorldState, projection: TeamProjection, execution: TeamExecutionStore, team: TeamStore, rounds: TeamRound[]): ActorMissionView[] {
  return projection.profiles.map((profile) => {
    const actor = state.agents[profile.actorId];
    const task = projection.tasks.find((candidate) => candidate.actorId === profile.actorId)!;
    const context = latestContext(execution, team, rounds, profile.actorId);
    const proposal = latestProposal(execution, rounds, profile.actorId);
    const verifiedFacts = proposal?.status === "verified"
      ? rounds.slice().reverse().map((round) => execution.findObservationForRound(round.roundId)).find((observation) => observation?.verifiedIntentCommandIds.includes(proposal.command.commandId))?.facts ?? []
      : [];
    const evidence: ActorMissionView["evidence"] = [
      { stage: "observed", label: "Observed", items: blockItems(context), confidence: null },
      { stage: "assessed", label: "Assessed · unverified", items: proposal ? [proposal.rationale] : [], confidence: proposal?.confidence ?? null },
      { stage: "proposed", label: "Proposed", items: proposal?.status === "proposed" ? [commandLabel(proposal.command)] : [], confidence: null },
      { stage: "executing", label: "Executing", items: proposal && ["selected", "executed"].includes(proposal.status) ? [commandLabel(proposal.command)] : [], confidence: null },
      { stage: "verified", label: "Verified", items: verifiedFacts.slice(-8).map(factSummary), confidence: null },
    ];
    return {
      actorId: profile.actorId,
      name: actor?.name ?? profile.actorId,
      role: profile.role,
      locationRoomId: actor?.location ?? "unknown",
      locationName: state.rooms[actor?.location ?? ""]?.name ?? "Unknown",
      health: actor?.health ?? 0,
      inventory: { ...(actor?.inventory ?? {}) },
      riskPreferenceId: profile.riskPreferenceId,
      providerOrder: [...task.providerOrder],
      taskState: task.state,
      controlMode: task.control.mode,
      activeObjectiveId: task.activeObjectiveId,
      waitReason: task.wait?.reason ?? null,
      evidence,
    };
  });
}

function objectives(projection: TeamProjection): ObjectiveMissionView[] {
  const status = new Map(projection.objectiveStatus.map((entry) => [entry.objectiveId, entry]));
  const superseded = new Set<string>();
  for (const parent of projection.objectives.nodes) {
    if (status.get(parent.objectiveId)?.satisfied !== true || parent.anyOf.length === 0) continue;
    const alternatives = parent.anyOf.flat();
    if (!alternatives.some((id) => status.get(id)?.satisfied === true)) continue;
    for (const objectiveId of alternatives) {
      if (status.get(objectiveId)?.satisfied !== true) superseded.add(objectiveId);
    }
  }
  return projection.objectives.nodes.map((node) => {
    const satisfied = status.get(node.objectiveId)?.satisfied === true;
    const dependenciesSatisfied = node.allOf.every((id) => status.get(id)?.satisfied) && node.anyOf.every((group) => group.some((id) => status.get(id)?.satisfied));
    const assigned = projection.tasks.filter((task) => task.activeObjectiveId === node.objectiveId).map((task) => task.actorId).filter((id): id is string => Boolean(id));
    return {
      objectiveId: node.objectiveId,
      label: node.label,
      priority: node.priorityClass,
      status: satisfied ? "satisfied" : superseded.has(node.objectiveId) ? "superseded" : assigned.length ? "active" : dependenciesSatisfied ? "available" : "blocked",
      dependencies: [...node.allOf],
      alternatives: node.anyOf.map((group) => [...group]),
      actorIds: assigned,
    };
  });
}

function urgency(state: WorldState): string {
  const turns = state.mission.turnLimit - state.turn;
  if (state.mission.status !== "running") return state.mission.reason ?? state.mission.status;
  if (state.resources.reactorHeat >= 90) return "Reactor heat is critical.";
  if (state.resources.oxygen <= 25) return "Oxygen is critical.";
  if (turns <= 3) return `${turns} turns remain.`;
  if (state.resources.oxygen <= 50 || state.resources.reactorHeat >= 70) return "Station risk is rising.";
  return "Mission remains controllable.";
}

function consequence(proposal: ActionProposal): string {
  switch (proposal.command.kind) {
    case "pickup_item": return `Moves ${proposal.command.quantity} ${proposal.command.itemId} into ${proposal.actorId}'s inventory.`;
    case "repair_system": return "Consumes one spare part if the World preconditions still hold.";
    case "seal_hull": return "Consumes sealant and irreversibly seals the breach if admitted.";
    case "contain_hazard": return "Controls the breach through Security containment without sealing it.";
    case "set_power": return `${proposal.command.enabled ? "Enables" : "Disables"} power draw for ${proposal.command.targetSystemId}.`;
    case "stabilize_crew": return "Consumes a medkit and stops untreated injury loss if admitted.";
    case "send_distress": return "Can complete the verified rescue requirement when all prerequisites hold.";
    case "move": return "Changes only the Actor's room before the environment advances.";
    case "wait": return "Consumes one shared World Tick without direct progress.";
  }
}

export function deriveInterventions(state: WorldState, projection: TeamProjection, proposals: ActionProposal[]): InterventionCard[] {
  const cards: InterventionCard[] = [];
  const authorityById = new Map(projection.authorityDecisions.map((decision) => [decision.decisionId, decision]));
  const grantedProposalIds = new Set(projection.authorityGrants
    .filter((grant) => grant.consumedAtTick === null && grant.expiresAtTick >= state.turn)
    .map((grant) => grant.proposalId));
  for (const proposal of proposals.filter((entry) => entry.status === "proposed" && entry.authorityOutcome === "require-human" && !grantedProposalIds.has(entry.proposalId))) {
    const decision = authorityById.get(proposal.authorityDecisionId);
    cards.push({
      cardId: `authority:${proposal.proposalId}`,
      kind: "authority-request",
      severity: decision?.attributes.target.criticality === "critical" ? "critical" : "warning",
      actorIds: [proposal.actorId],
      title: `${proposal.actorId} requests authority`,
      explanation: decision?.reason ?? "This Proposal requires explicit human authority.",
      consequence: consequence(proposal),
      urgency: urgency(state),
      expiresAtTick: state.turn + 2,
      commands: [{ action: "approve", proposalId: proposal.proposalId }, { action: "deny", proposalId: proposal.proposalId }],
      evidenceRefs: [proposal.proposalId, proposal.authorityDecisionId],
      forecast: proposalForecast(state, proposal),
    });
  }

  const engineerTask = projection.tasks.find((task) => task.role === "engineer");
  const engineerNeedsParts = engineerTask?.control.mode === "active" && ["cooling-operational", "life-support-operational", "communications-operational"].some((id) => projection.objectiveStatus.find((status) => status.objectiveId === id)?.satisfied === false);
  for (const proposal of proposals.filter((entry) => entry.status === "proposed" && entry.command.kind === "pickup_item" && entry.command.itemId === "spare-parts")) {
    const actor = state.agents[proposal.actorId];
    if (engineerNeedsParts && !actor?.capabilities.includes("repair_system") && proposal.actorId !== engineerTask?.actorId) {
      cards.push({
        cardId: `resource-mismatch:${proposal.proposalId}`,
        kind: "resource-mismatch",
        severity: "critical",
        actorIds: [proposal.actorId, engineerTask?.actorId ?? "engineer-01"],
        title: "Scarce repair parts may be claimed by the wrong specialist",
        explanation: `${proposal.actorId} cannot repair systems while Engineer still has unsatisfied repair objectives.`,
        consequence: consequence(proposal),
        urgency: urgency(state),
        expiresAtTick: state.turn,
        commands: [{ action: "deny", proposalId: proposal.proposalId }, { action: "pause", actorId: proposal.actorId }],
        evidenceRefs: [proposal.proposalId],
        forecast: proposalForecast(state, proposal),
      });
    }
  }

  const hazard = proposals.filter((proposal) => proposal.status === "proposed" && ["seal_hull", "contain_hazard"].includes(proposal.command.kind));
  if (hazard.some((proposal) => proposal.command.kind === "seal_hull") && hazard.some((proposal) => proposal.command.kind === "contain_hazard")) {
    cards.push({
      cardId: `redundant:${hazard.map((proposal) => proposal.proposalId).sort().join(":")}`,
      kind: "redundant-action",
      severity: "warning",
      actorIds: hazard.map((proposal) => proposal.actorId),
      title: "Two specialists propose alternative breach controls",
      explanation: "Sealing and containment both satisfy breach control; executing both may spend extra time or equipment.",
      consequence: "The deterministic Tick selector will admit only a compatible subset.",
      urgency: urgency(state),
      expiresAtTick: state.turn,
      commands: hazard.map((proposal) => ({ action: "deny", proposalId: proposal.proposalId })),
      evidenceRefs: hazard.map((proposal) => proposal.proposalId),
    });
  }

  for (const task of projection.tasks.filter((task) => task.actorId && task.wait && (task.wait.kind === "provider" || task.wait.kind === "conflict" || task.control.mode === "paused" || task.state === "blocked"))) {
    cards.push({
      cardId: `wait:${task.taskId}:${task.revision}`,
      kind: task.wait?.kind === "provider" ? "provider-failure" : "task-wait",
      severity: task.wait?.kind === "provider" ? "warning" : "info",
      actorIds: [task.actorId!],
      title: `${task.actorId} is waiting`,
      explanation: task.wait!.reason,
      consequence: "This specialist will not contribute a verified action until the wait clears or the player intervenes.",
      urgency: urgency(state),
      expiresAtTick: null,
      commands: task.control.mode === "paused" ? [{ action: "resume", actorId: task.actorId! }] : [],
      evidenceRefs: [task.taskId, task.wait!.subjectId],
    });
  }
  for (const message of projection.messages.filter((message) => message.status === "pending")) {
    cards.push({
      cardId: `message:${message.messageId}`,
      kind: "message-pending",
      severity: "warning",
      actorIds: [message.senderActorId, ...message.pendingActorIds],
      title: "Team message has not been delivered",
      explanation: message.boundedSummary,
      consequence: "Recipients will not receive this information in their Context until delivery succeeds.",
      urgency: `Expires at Tick ${message.expiryTick}.`,
      expiresAtTick: message.expiryTick,
      commands: [],
      evidenceRefs: [message.messageId],
    });
  }
  if (state.mission.status === "running" && (state.resources.oxygen <= 35 || state.resources.reactorHeat >= 80 || state.mission.turnLimit - state.turn <= 5)) {
    cards.push({
      cardId: `risk:${state.revision}`,
      kind: "mission-risk",
      severity: state.resources.oxygen <= 25 || state.resources.reactorHeat >= 90 ? "critical" : "warning",
      actorIds: [],
      title: "Mission risk is approaching a terminal threshold",
      explanation: urgency(state),
      consequence: "Another low-value Tick may make the rescue goal unreachable.",
      urgency: urgency(state),
      expiresAtTick: state.turn,
      commands: [],
      evidenceRefs: [`world-revision:${state.revision}`],
    });
  }
  return cards.sort((a, b) => ({ critical: 0, warning: 1, info: 2 }[a.severity] - { critical: 0, warning: 1, info: 2 }[b.severity]) || a.cardId.localeCompare(b.cardId));
}

function roundPhase(round: TeamRound, proposals: ActionProposal[]): CoordinationRoundView["phase"] {
  if (round.status === "blocked") return round.blocker === "authority_required" ? "authority" : "blocked";
  if (round.status === "completed") return "verified";
  if (round.tickPlanId || ["planned", "dispatched", "observed"].includes(round.status)) return "committing";
  if (proposals.length > 0 && round.resolvedActorIds.length === round.contextIds.length) return "proposal-review";
  return "preparing";
}

function currentRound(state: WorldState, execution: TeamExecutionStore, rounds: TeamRound[]): CoordinationRoundView | null {
  const round = rounds.at(-1);
  if (!round) return null;
  const proposals = execution.listProposals(round.roundId);
  const plan = round.tickPlanId ? execution.getTickPlan(round.tickPlanId) : null;
  return {
    roundId: round.roundId,
    worldRevision: round.worldRevision,
    phase: roundPhase(round, proposals),
    actors: proposals.map((proposal) => ({
      actorId: proposal.actorId,
      proposalId: proposal.proposalId,
      action: commandLabel(proposal.command),
      status: proposal.status,
      authority: proposal.authorityOutcome,
      rationale: proposal.rationale,
      confidence: proposal.confidence,
      forecast: proposal.worldRevision === state.revision ? proposalForecast(state, proposal) : null,
    })),
    selectedProposalIds: plan?.selectedProposalIds ?? [],
    rejectedProposalIds: plan?.rejectedProposalIds ?? proposals.filter((proposal) => proposal.status === "rejected").map((proposal) => proposal.proposalId),
    blocker: round.blocker,
  };
}

export function missionTimelineItems(execution: TeamExecutionStore, rounds: TeamRound[]): MissionTimelineItem[] {
  return rounds.map((round) => {
    const proposals = execution.listProposals(round.roundId);
    const observation = execution.findObservationForRound(round.roundId);
    const facts = (observation?.facts ?? []).slice(-8).map(factSummary);
    const status: MissionTimelineItem["status"] = round.status === "completed" ? "verified" : round.status === "blocked" ? "blocked" : facts.some((fact) => fact.startsWith("Mission ")) ? "terminal" : "in-progress";
    return {
      cursor: `${round.worldRevision}:${round.roundId}`,
      worldRevision: round.worldRevision,
      turn: observation ? round.worldRevision + 1 : round.worldRevision,
      status,
      summary: round.status === "completed" ? `${observation?.verifiedIntentCommandIds.length ?? 0} verified actions` : round.blocker ?? round.status,
      actorActions: proposals.map((proposal) => `${proposal.actorId}: ${commandLabel(proposal.command)} · ${proposal.status}`),
      facts,
    };
  });
}

export function createMissionControlView(store: GameStore, runId = store.activeRunId): MissionControlView {
  const metadata = store.getRun(runId);
  const state = store.loadState(runId);
  const digest = sha256(state);
  const initialized = teamRunInitialized(store, runId);
  const baseResources = resources(store, runId, state);
  const noChangeForecast = passiveForecast(state);
  if (!initialized) {
    return {
      schemaVersion: 1, initialized: false,
      generatedFrom: { worldRevision: state.revision, worldDigest: digest, goalRevision: 0, configurationRevision: 0 },
      run: { runId, scenarioId: metadata.scenarioId, scenarioVersion: metadata.scenarioVersion, scenarioCaseId: metadata.scenarioCaseId, rulesetVersion: metadata.rulesetVersion, genesisDigest: metadata.genesisDigest, evaluatedInputsDigest: metadata.evaluatedInputsDigest, createdWithBuild: metadata.createdWithBuild, turn: state.turn, turnLimit: state.mission.turnLimit, status: "setup" },
      configuration: null,
      mission: { title: "Station Zero", reason: null, turnsRemaining: state.mission.turnLimit - state.turn, objectiveProgress: { resolved: 0, satisfied: 0, superseded: 0, total: 12 }, urgency: urgency(state), score: null, scoreComponents: null },
      resources: baseResources,
      station: { rooms: station(state), communicationAvailable: false },
      actors: [], objectives: [], currentRound: null, inbox: [], timeline: [],
      experience: {
        mode: "play",
        doctrineId: "critical-approval",
        fronts: missionFronts(state, [], noChangeForecast),
        passiveForecast: noChangeForecast,
        activeInterventionId: null,
        outcome: null,
      },
      controls: { canPrepare: false, canCommit: false, canConfigure: true, canRun: false, canAdvanceOne: false },
    };
  }
  const team = new TeamStore(store);
  const execution = new TeamExecutionStore(team);
  const projection = team.projection(runId, false);
  const rounds = execution.listRounds(runId);
  const latestRound = rounds.at(-1);
  const latestProposals = latestRound ? execution.listProposals(latestRound.roundId) : [];
  const objectiveViews = objectives(projection);
  const satisfied = objectiveViews.filter((objective) => objective.status === "satisfied").length;
  const superseded = objectiveViews.filter((objective) => objective.status === "superseded").length;
  const score = state.mission.status === "running" ? null : scoreMission(state);
  const roundView = currentRound(state, execution, rounds);
  const inbox = deriveInterventions(state, projection, latestProposals);
  const actionable = inbox.find((card) => card.commands.length > 0 || card.kind === "provider-failure");
  return {
    schemaVersion: 1,
    initialized: true,
    generatedFrom: { worldRevision: state.revision, worldDigest: digest, goalRevision: projection.goal.revision, configurationRevision: projection.configuration.revision },
    run: { runId, scenarioId: metadata.scenarioId, scenarioVersion: metadata.scenarioVersion, scenarioCaseId: metadata.scenarioCaseId, rulesetVersion: metadata.rulesetVersion, genesisDigest: metadata.genesisDigest, evaluatedInputsDigest: metadata.evaluatedInputsDigest, createdWithBuild: metadata.createdWithBuild, turn: state.turn, turnLimit: state.mission.turnLimit, status: state.mission.status },
    configuration: { authorityPolicyMode: projection.configuration.authorityPolicyMode },
    mission: { title: "Station Zero emergency response", reason: state.mission.reason, turnsRemaining: Math.max(0, state.mission.turnLimit - state.turn), objectiveProgress: { resolved: satisfied + superseded, satisfied, superseded, total: objectiveViews.length }, urgency: urgency(state), score: score?.total ?? null, scoreComponents: score?.components ?? null },
    resources: baseResources,
    station: { rooms: station(state), communicationAvailable: Boolean(state.systems.communications?.powered && state.systems.communications.integrity >= 0.8) },
    actors: actors(state, projection, execution, team, rounds),
    objectives: objectiveViews,
    currentRound: roundView,
    inbox,
    timeline: missionTimelineItems(execution, rounds.slice(-12).reverse()),
    experience: {
      mode: "play",
      doctrineId: doctrineForPolicy(projection.configuration.authorityPolicyMode),
      fronts: missionFronts(state, objectiveViews, noChangeForecast),
      passiveForecast: noChangeForecast,
      activeInterventionId: actionable?.cardId ?? null,
      outcome: missionOutcome(state),
    },
    controls: {
      canPrepare: state.mission.status === "running" && (!roundView || roundView.phase === "verified" || roundView.phase === "blocked"),
      canCommit: state.mission.status === "running" && Boolean(roundView && ["proposal-review", "authority", "committing"].includes(roundView.phase)),
      canConfigure: state.mission.status === "running",
      canRun: state.mission.status === "running",
      canAdvanceOne: state.mission.status === "running",
    },
  };
}

export function missionControlEncodedSize(view: MissionControlView): number {
  return Buffer.byteLength(JSON.stringify(view));
}
