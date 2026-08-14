import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

import { sha256 } from "../src/digest.ts";
import {
  FixtureStationZeroV3AgentProvider,
  applyStationZeroV3Turn,
  assertStationZeroV3AgentDecision,
  buildStationZeroV3PlanPreview,
  createStationZeroV3Genesis,
  initialStationZeroV3CommanderOrder,
  prepareStationZeroV3Commitment,
  type StationZeroTurnBatch,
  type StationZeroV3ActionFeedback,
  type StationZeroV3AgentCandidate,
  type StationZeroV3AgentContext,
  type StationZeroV3AgentDecision,
  type StationZeroV3AgentProvider,
  type StationZeroV3AgentProviderFactory,
  type StationZeroV3CommanderOrder,
  type StationZeroV3PirateDirective,
  type StationZeroV3PlanningHead,
  type StationZeroV3PlanPreview,
  type StationZeroV3ResponsibilityFeedback,
  type StationZeroV3SwarmDirective,
  type StationZeroV3WorldState,
} from "../src/station-zero-v3/index.ts";

const OBJECTIVES: StationZeroV3CommanderOrder["primaryObjectiveId"][] = [
  "rescue-two-civilians",
  "recover-research-core",
  "eliminate-hive-alpha",
];
const POSTURES: StationZeroV3CommanderOrder["posture"][] = ["cautious", "balanced", "aggressive"];
const FORMATIONS: StationZeroV3CommanderOrder["formation"][] = ["cohesive", "split"];

interface StrategyProfile {
  profileId: string;
  objective: StationZeroV3CommanderOrder["primaryObjectiveId"];
  posture: StationZeroV3CommanderOrder["posture"];
  formation: StationZeroV3CommanderOrder["formation"];
}

interface DoctrineTreatment {
  treatmentId: string;
  factionId: "pirate" | "swarm" | null;
  directiveId: StationZeroV3PirateDirective | StationZeroV3SwarmDirective | null;
  targetObjectiveId: string | null;
  description: string;
}

interface TurnTrace {
  turn: number;
  candidateSurface: Record<string, string[]>;
  selectedActions: Record<string, string>;
  directives: Record<string, string | null>;
  commanderActions: Record<string, string[]>;
}

interface DoctrineRun {
  treatmentId: string;
  profile: StrategyProfile;
  turns: number;
  rescueOutcome: string;
  pirateOutcome: string;
  swarmOutcome: string;
  focus: { progress: number; target: number; status: string };
  enemyObjectives: Record<string, { progress: number; target: number; status: string }>;
  vector: {
    civilians: number;
    core: number;
    hive: number;
    specialistsExtracted: number;
    specialistsDead: number;
    specialistsIncapacitated: number;
  };
  traces: TurnTrace[];
}

const TREATMENTS: DoctrineTreatment[] = [
  { treatmentId: "adaptive-baseline", factionId: null, directiveId: null, targetObjectiveId: null, description: "Canonical fixture leaders choose directives from current bounded Context." },
  { treatmentId: "pirate-steal-core", factionId: "pirate", directiveId: "steal-core", targetObjectiveId: "pirate-steal-core", description: "Pirate leader holds the existing steal-core directive throughout the encounter." },
  { treatmentId: "pirate-capture-prize", factionId: "pirate", directiveId: "capture-prize", targetObjectiveId: "capture-engineer", description: "Pirate leader holds the existing capture-prize directive throughout the encounter." },
  { treatmentId: "pirate-extract-crew", factionId: "pirate", directiveId: "extract-crew", targetObjectiveId: "pirate-crew-survives", description: "Pirate leader holds the existing extract-crew directive throughout the encounter." },
  { treatmentId: "swarm-hunt-biomass", factionId: "swarm", directiveId: "hunt-biomass", targetObjectiveId: "swarm-gain-biomass", description: "Hive Alpha holds the existing hunt-biomass directive throughout the encounter." },
  { treatmentId: "swarm-infect-life-support", factionId: "swarm", directiveId: "infect-life-support", targetObjectiveId: "infect-life-support", description: "Hive Alpha holds the existing infect-life-support directive throughout the encounter." },
  { treatmentId: "swarm-preserve-hive", factionId: "swarm", directiveId: "preserve-hive", targetObjectiveId: "swarm-survives", description: "Hive Alpha holds the existing preserve-hive directive throughout the encounter." },
];

function profiles(): StrategyProfile[] {
  return OBJECTIVES.flatMap((objective) => POSTURES.flatMap((posture) => FORMATIONS.map((formation) => ({
    profileId: `${objective}__${posture}__${formation}`,
    objective,
    posture,
    formation,
  }))));
}

function semanticCandidate(candidate: StationZeroV3AgentCandidate): string {
  const intent = candidate.intent;
  switch (intent.kind) {
    case "move": return `move:${intent.targetZoneId}:${candidate.label}`;
    case "attack": return `attack:${intent.abilityId}:${intent.targetActorId}:${candidate.label}`;
    case "use_ability": return `ability:${intent.abilityId}:${intent.targetActorId ?? ""}:${intent.targetZoneId ?? ""}:${intent.targetSystemId ?? ""}:${intent.targetHazardId ?? ""}:${candidate.label}`;
    case "interact": return `interact:${intent.operationId}:${intent.targetId}:${candidate.label}`;
    case "pickup": return `pickup:${intent.groundItemId}:${candidate.label}`;
    case "extract": return `extract:${candidate.label}`;
    case "guard": return `guard:${intent.protectedActorId ?? ""}:${intent.watchedZoneId ?? ""}:${candidate.label}`;
    case "wait": return `wait:${candidate.label}`;
  }
}

function commanderActionKey(action: StationZeroV3PlanPreview["factionPlans"]["pirate"]["commanderActions"][number]): string {
  return [
    action.commanderAbilityId,
    action.targetActorId ?? "",
    action.targetZoneId ?? "",
    action.targetPassageId ?? "",
    action.targetSystemId ?? "",
    action.targetFactionId ?? "",
  ].join(":");
}

function planningHead(runId: string, state: StationZeroV3WorldState): StationZeroV3PlanningHead {
  const commitment = prepareStationZeroV3Commitment(state);
  const stamp = `turn-${state.encounter.turn}`;
  return {
    schemaVersion: 1,
    kind: "ordivon.game.station-zero-v3-planning-head",
    planningId: `planning:g5-doctrine:${runId}:${state.revision}`,
    runId,
    worldRevision: state.revision,
    turn: state.encounter.turn,
    worldDigest: sha256(state),
    commitmentDigest: sha256(commitment),
    standingOrderRevision: state.encounter.activePlanRevision,
    planningRevision: 1,
    status: "open",
    submittedPlanDigests: {},
    turnBatchId: null,
    batchDigest: null,
    createdAt: stamp,
    updatedAt: stamp,
  };
}

function scanDirective(state: StationZeroV3WorldState, objective: StrategyProfile["objective"]): StationZeroV3CommanderOrder["commanderDirectiveId"] | null {
  const charges = state.factions.rescue.commanderAbilityCharges["orbital-scan"];
  const available = (charges === null || (charges !== undefined && charges > 0)) &&
    (state.factions.rescue.commanderAbilityCooldowns["orbital-scan"] ?? 0) === 0 &&
    state.factions.rescue.commandPoints >= 1;
  if (!available) return null;
  if (objective === "rescue-two-civilians" && !state.factionKnowledge.rescue.discoveredZoneIds.includes("life-console")) return "scan-life-support";
  if (objective === "recover-research-core" && !state.factionKnowledge.rescue.discoveredZoneIds.includes("reactor-console")) return "scan-reactor";
  if (objective === "eliminate-hive-alpha" && !state.factionKnowledge.rescue.discoveredZoneIds.includes("maintenance-entry")) return "scan-maintenance";
  return null;
}

class ForcedDirectiveProvider implements StationZeroV3AgentProvider {
  readonly providerId: string;
  readonly #base = new FixtureStationZeroV3AgentProvider();
  readonly treatment: DoctrineTreatment;

  constructor(treatment: DoctrineTreatment) {
    this.treatment = treatment;
    this.providerId = `research-doctrine:${treatment.treatmentId}`;
  }

  async decide(context: StationZeroV3AgentContext): Promise<StationZeroV3AgentDecision> {
    if (!this.treatment.factionId || context.factionId !== this.treatment.factionId) return this.#base.decide(context);
    const leaderActorId = this.treatment.factionId === "pirate" ? "pirate-captain-veyra" : "hive-alpha";
    if (context.actor.actorId !== leaderActorId) return this.#base.decide(context);

    // Research-only counterfactual: alter only the bounded cue consumed by the canonical fixture leader selector.
    // Candidate identities and legal surface remain byte-for-byte those from the real Context.
    const counterfactual = structuredClone(context);
    if (this.treatment.factionId === "pirate") {
      if (this.treatment.directiveId === "steal-core") {
        counterfactual.actor.inventoryItemIds = counterfactual.actor.inventoryItemIds.filter((itemId) => itemId !== "research-core");
        counterfactual.known.actors = counterfactual.known.actors.map((actor) => actor.actorId === "engineer-imani" ? { ...actor, observedLifeState: "active" } : actor);
      } else if (this.treatment.directiveId === "capture-prize") {
        counterfactual.actor.inventoryItemIds = counterfactual.actor.inventoryItemIds.filter((itemId) => itemId !== "research-core");
        counterfactual.known.actors = counterfactual.known.actors.map((actor) => actor.actorId === "engineer-imani" ? { ...actor, observedLifeState: "incapacitated" } : actor);
      } else if (this.treatment.directiveId === "extract-crew") {
        if (!counterfactual.actor.inventoryItemIds.includes("research-core")) counterfactual.actor.inventoryItemIds.push("research-core");
      }
    } else {
      if (this.treatment.directiveId === "preserve-hive") {
        counterfactual.actor.health = Math.min(counterfactual.actor.health, Math.max(1, Math.floor(counterfactual.actor.maximumHealth * 0.3)));
      } else {
        counterfactual.actor.health = counterfactual.actor.maximumHealth;
        if (this.treatment.directiveId === "infect-life-support" && !counterfactual.known.systemIds.includes("life-support")) {
          counterfactual.known.systemIds.push("life-support");
        }
        if (this.treatment.directiveId === "hunt-biomass") {
          counterfactual.known.systemIds = counterfactual.known.systemIds.filter((systemId) => systemId !== "life-support");
        }
      }
    }
    const counterfactualBase = { ...counterfactual, contextDigest: "" };
    counterfactual.contextDigest = sha256(counterfactualBase);
    const chosen = await this.#base.decide(counterfactual);
    const rebound: StationZeroV3AgentDecision = {
      ...chosen,
      contextId: context.contextId,
      contextDigest: context.contextDigest,
      actorId: context.actor.actorId,
      factionId: context.factionId,
      directiveId: this.treatment.directiveId,
      providerId: this.providerId,
      rationale: `Research-only forced existing directive ${this.treatment.directiveId}; Candidate remained admitted by the unmodified real Context. ${chosen.rationale}`,
    };
    assertStationZeroV3AgentDecision(context, rebound);
    return rebound;
  }
}

function providerFactory(treatment: DoctrineTreatment): StationZeroV3AgentProviderFactory {
  if (treatment.factionId === null) return () => new FixtureStationZeroV3AgentProvider();
  return () => new ForcedDirectiveProvider(treatment);
}

function feedbackFrom(
  preview: StationZeroV3PlanPreview,
  resolution: Extract<ReturnType<typeof applyStationZeroV3Turn>, { status: "accepted" }>["resolution"],
): { action: Record<string, StationZeroV3ActionFeedback>; responsibility: Record<string, StationZeroV3ResponsibilityFeedback> } {
  const action: Record<string, StationZeroV3ActionFeedback> = {};
  const responsibility: Record<string, StationZeroV3ResponsibilityFeedback> = {};
  for (const context of preview.contexts.filter((entry) => entry.factionId === "rescue")) {
    const agent = preview.agentDecisions.find((entry) => entry.actorId === context.actor.actorId);
    const policy = preview.policyDecisions.find((entry) => entry.actorId === context.actor.actorId);
    const candidateId = agent?.candidateId ?? policy?.candidateId ?? null;
    const candidate = candidateId ? context.candidates.find((entry) => entry.candidateId === candidateId) : null;
    if (!candidate) throw new Error(`selected Candidate missing for ${context.actor.actorId}`);
    const retained = resolution.intentResolutions.find((entry) => entry.actorId === context.actor.actorId && entry.intentId === candidate.intent.intentId);
    if (!retained) throw new Error(`Intent Resolution missing for ${context.actor.actorId}`);
    action[context.actor.actorId] = {
      turnSequence: resolution.turnAfter - 1,
      planningId: preview.planningId,
      candidateLabel: candidate.label,
      intent: structuredClone(candidate.intent),
      status: retained.status,
      reason: retained.reason,
    };
    if (context.responsibility) {
      responsibility[context.actor.actorId] = {
        turnSequence: resolution.turnAfter - 1,
        planningId: preview.planningId,
        responsibility: structuredClone(context.responsibility),
        candidateId: candidate.candidateId,
        candidateLabel: candidate.label,
        intent: structuredClone(candidate.intent),
        status: retained.status,
        reason: retained.reason,
      };
    }
  }
  return { action, responsibility };
}

async function runTreatment(treatment: DoctrineTreatment, profile: StrategyProfile): Promise<DoctrineRun> {
  const runId = `run:g5-doctrine:${treatment.treatmentId}:${profile.profileId}`;
  let state = createStationZeroV3Genesis(`g5-doctrine:${profile.profileId}`, "fixed-genesis");
  let previousOrder: StationZeroV3CommanderOrder | null = null;
  let actionFeedback: Record<string, StationZeroV3ActionFeedback> = {};
  let responsibilityFeedback: Record<string, StationZeroV3ResponsibilityFeedback> = {};
  const traces: TurnTrace[] = [];

  while (state.encounter.status === "running") {
    const planning = planningHead(runId, state);
    const fresh = initialStationZeroV3CommanderOrder(runId, planning, state, previousOrder);
    const scan = scanDirective(state, profile.objective);
    const order: StationZeroV3CommanderOrder = {
      ...fresh,
      primaryObjectiveId: profile.objective,
      posture: profile.posture,
      formation: profile.formation,
      retreatHealthThreshold: 0.3,
      lethalForce: "permitted",
      collateralPolicy: "forbidden",
      lootPolicy: "mission-only",
      protectedActorId: null,
      priorityTargetActorId: null,
      ...(scan ? { commanderDirectiveId: scan } : {}),
    };
    const preview = await buildStationZeroV3PlanPreview({
      state,
      planning,
      orderRevision: 1,
      order,
      orderDigest: sha256(order),
      providerFactory: providerFactory(treatment),
      responsibilityFeedbackByActor: responsibilityFeedback,
      actionFeedbackByActor: actionFeedback,
    });

    const candidateSurface: Record<string, string[]> = {};
    for (const context of preview.contexts) candidateSurface[context.actor.actorId] = context.candidates.map(semanticCandidate).sort();
    const selectedActions: Record<string, string> = {};
    for (const decision of preview.agentDecisions) {
      const context = preview.contexts.find((entry) => entry.contextId === decision.contextId)!;
      selectedActions[decision.actorId] = semanticCandidate(context.candidates.find((entry) => entry.candidateId === decision.candidateId)!);
    }
    for (const decision of preview.policyDecisions) {
      const context = preview.contexts.find((entry) => entry.actor.actorId === decision.actorId)!;
      selectedActions[decision.actorId] = semanticCandidate(context.candidates.find((entry) => entry.candidateId === decision.candidateId)!);
    }
    const directives = Object.fromEntries(preview.agentDecisions.map((decision) => [decision.actorId, decision.directiveId]));
    const commanderActions = {
      pirate: preview.factionPlans.pirate.commanderActions.map(commanderActionKey).sort(),
      swarm: preview.factionPlans.swarm.commanderActions.map(commanderActionKey).sort(),
    };
    traces.push({ turn: state.encounter.turn, candidateSurface, selectedActions, directives, commanderActions });

    const commitment = prepareStationZeroV3Commitment(state);
    const batch: StationZeroTurnBatch = {
      turnBatchId: `batch:g5-doctrine:${treatment.treatmentId}:${profile.profileId}:${state.encounter.turn}`,
      expectedWorldRevision: state.revision,
      expectedTurn: state.encounter.turn,
      factionPlans: [preview.factionPlans.rescue, preview.factionPlans.pirate, preview.factionPlans.swarm],
    };
    const applied = applyStationZeroV3Turn(commitment, batch);
    if (applied.status !== "accepted") throw new Error(`Turn rejected for ${treatment.treatmentId}/${profile.profileId}: ${applied.reason}`);
    const feedback = feedbackFrom(preview, applied.resolution);
    actionFeedback = feedback.action;
    responsibilityFeedback = feedback.responsibility;
    previousOrder = order;
    state = applied.state;
  }

  const focus = state.factions.rescue.objectiveProgress[profile.objective]!;
  const specialists = Object.values(state.actors).filter((actor) => actor.factionId === "rescue");
  const coreExtracted = specialists.some((actor) => actor.lifeState === "extracted" && actor.inventoryItemIds.includes("research-core"));
  return {
    treatmentId: treatment.treatmentId,
    profile,
    turns: state.encounter.turn,
    rescueOutcome: state.factions.rescue.outcome,
    pirateOutcome: state.factions.pirate.outcome,
    swarmOutcome: state.factions.swarm.outcome,
    focus: { progress: focus.progress, target: focus.target, status: focus.status },
    enemyObjectives: Object.fromEntries(
      ["pirate", "swarm"].flatMap((factionId) => Object.entries(state.factions[factionId as "pirate" | "swarm"].objectiveProgress))
        .map(([objectiveId, progress]) => [objectiveId, { progress: progress.progress, target: progress.target, status: progress.status }]),
    ),
    vector: {
      civilians: Object.values(state.actors).filter((actor) => actor.kind === "civilian" && actor.lifeState === "extracted").length,
      core: coreExtracted ? 1 : 0,
      hive: state.actors["hive-alpha"]?.lifeState === "dead" ? 1 : 0,
      specialistsExtracted: specialists.filter((actor) => actor.lifeState === "extracted").length,
      specialistsDead: specialists.filter((actor) => actor.lifeState === "dead").length,
      specialistsIncapacitated: specialists.filter((actor) => actor.lifeState === "incapacitated").length,
    },
    traces,
  };
}

function equalStringArrays(left: string[] = [], right: string[] = []): boolean {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

function compare(
  baseline: DoctrineRun,
  treatment: DoctrineRun,
  factionId: "pirate" | "swarm",
  targetObjectiveId: string,
) {
  const leaderId = factionId === "pirate" ? "pirate-captain-veyra" : "hive-alpha";
  const factionActors = factionId === "pirate"
    ? ["pirate-captain-veyra", "pirate-hacker-nyx", "pirate-raider-holt"]
    : ["hive-alpha", "swarm-stalker", "swarm-drone"];
  const firstBaseline = baseline.traces[0]!;
  const firstTreatment = treatment.traces[0]!;
  const firstTurnCandidateSurfaceEqual = factionActors.every((actorId) =>
    equalStringArrays(firstBaseline.candidateSurface[actorId], firstTreatment.candidateSurface[actorId]));

  let directiveComparisons = 0;
  let directiveChanged = 0;
  let selectedComparisons = 0;
  let selectedChanged = 0;
  let commanderComparisons = 0;
  let commanderChanged = 0;
  const turns = Math.max(baseline.traces.length, treatment.traces.length);
  for (let index = 0; index < turns; index += 1) {
    const left = baseline.traces[index];
    const right = treatment.traces[index];
    if (!left || !right) continue;
    directiveComparisons += 1;
    if ((left.directives[leaderId] ?? null) !== (right.directives[leaderId] ?? null)) directiveChanged += 1;
    for (const actorId of factionActors) {
      selectedComparisons += 1;
      if ((left.selectedActions[actorId] ?? "<missing>") !== (right.selectedActions[actorId] ?? "<missing>")) selectedChanged += 1;
    }
    commanderComparisons += 1;
    if (!equalStringArrays(left.commanderActions[factionId], right.commanderActions[factionId])) commanderChanged += 1;
  }

  const baselineTargetObjective = baseline.enemyObjectives[targetObjectiveId]!;
  const treatmentTargetObjective = treatment.enemyObjectives[targetObjectiveId]!;
  const targetObjectiveProgressDelta = treatmentTargetObjective.progress - baselineTargetObjective.progress;
  const targetObjectiveCompletionImproved = baselineTargetObjective.status !== "completed" && treatmentTargetObjective.status === "completed";

  const strategicConsequenceChanged = JSON.stringify({
    focus: baseline.focus,
    vector: baseline.vector,
    outcomes: [baseline.rescueOutcome, baseline.pirateOutcome, baseline.swarmOutcome],
  }) !== JSON.stringify({
    focus: treatment.focus,
    vector: treatment.vector,
    outcomes: [treatment.rescueOutcome, treatment.pirateOutcome, treatment.swarmOutcome],
  });

  return {
    firstTurnCandidateSurfaceEqual,
    firstTurnDirectiveChanged: (firstBaseline.directives[leaderId] ?? null) !== (firstTreatment.directives[leaderId] ?? null),
    firstTurnSelectedChanged: factionActors.filter((actorId) =>
      (firstBaseline.selectedActions[actorId] ?? "<missing>") !== (firstTreatment.selectedActions[actorId] ?? "<missing>")).length,
    firstTurnCommanderChanged: !equalStringArrays(firstBaseline.commanderActions[factionId], firstTreatment.commanderActions[factionId]),
    directiveChangedRate: directiveComparisons ? directiveChanged / directiveComparisons : 0,
    selectedChangedRate: selectedComparisons ? selectedChanged / selectedComparisons : 0,
    commanderChangedRate: commanderComparisons ? commanderChanged / commanderComparisons : 0,
    strategicConsequenceChanged,
    targetObjectiveId,
    baselineTargetObjective,
    treatmentTargetObjective,
    targetObjectiveProgressDelta,
    targetObjectiveCompletionImproved,
    baselineFocus: baseline.focus,
    treatmentFocus: treatment.focus,
    baselineVector: baseline.vector,
    treatmentVector: treatment.vector,
    baselineOutcomes: [baseline.rescueOutcome, baseline.pirateOutcome, baseline.swarmOutcome],
    treatmentOutcomes: [treatment.rescueOutcome, treatment.pirateOutcome, treatment.swarmOutcome],
  };
}

const allProfiles = profiles();
const runs: DoctrineRun[] = [];
for (const treatment of TREATMENTS) {
  for (const profile of allProfiles) {
    const run = await runTreatment(treatment, profile);
    runs.push(run);
    console.log(JSON.stringify({
      kind: "ordivon.game.station-zero-v3-enemy-doctrine-progress",
      treatmentId: treatment.treatmentId,
      profileId: profile.profileId,
      focus: `${run.focus.progress}/${run.focus.target}`,
      rescueOutcome: run.rescueOutcome,
      pirateOutcome: run.pirateOutcome,
      swarmOutcome: run.swarmOutcome,
      vector: run.vector,
    }));
  }
}

const baselineByProfile = new Map(runs.filter((run) => run.treatmentId === "adaptive-baseline").map((run) => [run.profile.profileId, run]));
const comparisons = TREATMENTS.filter((treatment) => treatment.factionId !== null).map((treatment) => {
  const rows = runs.filter((run) => run.treatmentId === treatment.treatmentId).map((run) => ({
    profileId: run.profile.profileId,
    ...compare(baselineByProfile.get(run.profile.profileId)!, run, treatment.factionId!, treatment.targetObjectiveId!),
  }));
  const firstTurnCandidateStableProfiles = rows.filter((row) => row.firstTurnCandidateSurfaceEqual).length;
  const firstTurnDirectiveChangedProfiles = rows.filter((row) => row.firstTurnDirectiveChanged).length;
  const firstTurnSelectedChangedProfiles = rows.filter((row) => row.firstTurnSelectedChanged > 0).length;
  const firstTurnCommanderChangedProfiles = rows.filter((row) => row.firstTurnCommanderChanged).length;
  const directiveChangedRate = rows.reduce((sum, row) => sum + row.directiveChangedRate, 0) / rows.length;
  const selectedChangedRate = rows.reduce((sum, row) => sum + row.selectedChangedRate, 0) / rows.length;
  const commanderChangedRate = rows.reduce((sum, row) => sum + row.commanderChangedRate, 0) / rows.length;
  const strategicConsequenceChangedProfiles = rows.filter((row) => row.strategicConsequenceChanged).length;
  const targetObjectiveImprovedProfiles = rows.filter((row) => row.targetObjectiveProgressDelta > 0 || row.targetObjectiveCompletionImproved).length;
  const targetObjectiveRegressedProfiles = rows.filter((row) => row.targetObjectiveProgressDelta < 0).length;
  const focusChangedProfiles = rows.filter((row) => JSON.stringify(row.baselineFocus) !== JSON.stringify(row.treatmentFocus)).length;
  const vectorChangedProfiles = rows.filter((row) => JSON.stringify(row.baselineVector) !== JSON.stringify(row.treatmentVector)).length;
  const admitted = firstTurnCandidateStableProfiles === rows.length &&
    directiveChangedRate >= 0.2 &&
    (selectedChangedRate >= 0.1 || commanderChangedRate >= 0.1) &&
    strategicConsequenceChangedProfiles > 0 &&
    targetObjectiveImprovedProfiles > 0;
  return {
    treatmentId: treatment.treatmentId,
    factionId: treatment.factionId,
    directiveId: treatment.directiveId,
    description: treatment.description,
    firstTurnCandidateStableProfiles,
    firstTurnDirectiveChangedProfiles,
    firstTurnSelectedChangedProfiles,
    firstTurnCommanderChangedProfiles,
    directiveChangedRate,
    selectedChangedRate,
    commanderChangedRate,
    strategicConsequenceChangedProfiles,
    targetObjectiveImprovedProfiles,
    targetObjectiveRegressedProfiles,
    focusChangedProfiles,
    vectorChangedProfiles,
    admitted,
    rows,
  };
});

const axisAdmitted = comparisons.some((entry) => entry.admitted);
const summary = {
  schemaVersion: 1,
  kind: "ordivon.game.station-zero-v3-g5-enemy-doctrine-axis",
  hypothesis: "Enemy doctrine is a production-worthy outer axis when an existing legal directive changes selection/command and later authoritative consequence without requiring a new legality or World contract.",
  treatments: TREATMENTS,
  profiles: allProfiles.length,
  runCount: runs.length,
  admissionRule: {
    firstTurnCandidateSurfaceStableForAllProfiles: true,
    directiveChangedRateAtLeast: 0.2,
    selectedOrCommanderChangedRateAtLeast: 0.1,
    strategicConsequenceChangedProfilesAtLeast: 1,
    targetObjectiveImprovedProfilesAtLeast: 1,
  },
  axisAdmitted,
  comparisons,
};
const outputDirectory = resolve("artifacts/evaluations");
mkdirSync(outputDirectory, { recursive: true });
const outputPath = resolve(outputDirectory, `station-zero-v3-g5-enemy-doctrine-axis-${Date.now()}.json`);
writeFileSync(outputPath, `${JSON.stringify({ ...summary, runs }, null, 2)}\n`);
console.log(JSON.stringify({ ...summary, outputPath }, null, 2));
