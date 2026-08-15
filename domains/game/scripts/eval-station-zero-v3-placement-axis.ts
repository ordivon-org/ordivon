import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

import { sha256 } from "../src/digest.ts";
import {
  applyStationZeroV3Turn,
  assertStationZeroV3World,
  buildStationZeroV3PlanPreview,
  createStationZeroV3Genesis,
  fixtureStationZeroV3AgentProviderFactory,
  initialStationZeroV3CommanderOrder,
  prepareStationZeroV3Commitment,
  type StationZeroTurnBatch,
  type StationZeroV3ActionFeedback,
  type StationZeroV3AgentCandidate,
  type StationZeroV3CommanderOrder,
  type StationZeroV3PlanningHead,
  type StationZeroV3PlanPreview,
  type StationZeroV3ResponsibilityFeedback,
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

interface PlacementVariant {
  variantId: string;
  target: "civilian" | "core" | null;
  description: string;
  mutate(state: StationZeroV3WorldState): void;
}

interface TurnTrace {
  turn: number;
  candidateSurface: Record<string, string[]>;
  selectedActions: Record<string, string>;
  rescueIntentReasons: Record<string, number>;
}

interface PlacementRun {
  variantId: string;
  profile: StrategyProfile;
  turns: number;
  rescueOutcome: string;
  pirateOutcome: string;
  swarmOutcome: string;
  terminalReason: string | null;
  focus: { progress: number; target: number; status: string };
  vector: {
    civilians: number;
    core: number;
    pirateCore: number;
    hive: number;
    specialistsExtracted: number;
    specialistsDead: number;
    specialistsIncapacitated: number;
  };
  rescueIntentReasons: Record<string, number>;
  traces: TurnTrace[];
}

function moveActor(state: StationZeroV3WorldState, actorId: string, zoneId: string): void {
  const actor = state.actors[actorId];
  if (!actor) throw new TypeError(`Placement treatment references unknown Actor ${actorId}`);
  if (!state.zones[zoneId]) throw new TypeError(`Placement treatment references unknown Zone ${zoneId}`);
  actor.position.zoneId = zoneId;
  for (const knowledge of Object.values(state.factionKnowledge)) {
    const retained = knowledge.knownActors[actorId];
    if (retained) retained.lastKnownZoneId = zoneId;
  }
}

const VARIANTS: PlacementVariant[] = [
  {
    variantId: "baseline",
    target: null,
    description: "Canonical civilian and Research Core placement.",
    mutate() {},
  },
  {
    variantId: "civilian-swap-rooms",
    target: "civilian",
    description: "Navigator Sato and Researcher Kade exchange their Medical Bay and Life Support positions.",
    mutate(state) {
      moveActor(state, "civilian-sato", "life-console");
      moveActor(state, "civilian-kade", "med-ward");
    },
  },
  {
    variantId: "civilians-cluster-med",
    target: "civilian",
    description: "Both civilians begin in the Medical Ward.",
    mutate(state) {
      moveActor(state, "civilian-kade", "med-ward");
    },
  },
  {
    variantId: "civilians-cluster-life",
    target: "civilian",
    description: "Both civilians begin at the Life Support Console.",
    mutate(state) {
      moveActor(state, "civilian-sato", "life-console");
    },
  },
  {
    variantId: "core-reactor-cover",
    target: "core",
    description: "Research Core shifts within the Reactor from Console to Shielded Machinery.",
    mutate(state) {
      state.groundItems["ground:research-core"]!.zoneId = "reactor-cover";
    },
  },
  {
    variantId: "core-junction-cover",
    target: "core",
    description: "Research Core moves to Junction Machinery on the central Rescue route.",
    mutate(state) {
      state.groundItems["ground:research-core"]!.zoneId = "junction-cover";
    },
  },
  {
    variantId: "core-crate-cover",
    target: "core",
    description: "Research Core moves to Cargo Crates near the Pirate extraction route.",
    mutate(state) {
      state.groundItems["ground:research-core"]!.zoneId = "crate-cover";
    },
  },
];

function profiles(): StrategyProfile[] {
  return OBJECTIVES.flatMap((objective) => POSTURES.flatMap((posture) => FORMATIONS.map((formation) => ({
    profileId: `${objective}__${posture}__${formation}`,
    objective,
    posture,
    formation,
  }))));
}

function increment(target: Record<string, number>, key: string): void {
  target[key] = (target[key] ?? 0) + 1;
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

function planningHead(runId: string, state: StationZeroV3WorldState): StationZeroV3PlanningHead {
  const commitment = prepareStationZeroV3Commitment(state);
  const stamp = `turn-${state.encounter.turn}`;
  return {
    schemaVersion: 1,
    kind: "ordivon.game.station-zero-v3-planning-head",
    planningId: `planning:g5-placement:${runId}:${state.revision}`,
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

function feedbackFrom(
  preview: StationZeroV3PlanPreview,
  resolution: Extract<ReturnType<typeof applyStationZeroV3Turn>, { status: "accepted" }>["resolution"],
): {
  action: Record<string, StationZeroV3ActionFeedback>;
  responsibility: Record<string, StationZeroV3ResponsibilityFeedback>;
} {
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

async function runPlacementVariant(variant: PlacementVariant, profile: StrategyProfile): Promise<PlacementRun> {
  const runId = `run:g5-placement:${variant.variantId}:${profile.profileId}`;
  let state = createStationZeroV3Genesis(`g5-placement:${profile.profileId}`);
  variant.mutate(state);
  assertStationZeroV3World(state);

  let previousOrder: StationZeroV3CommanderOrder | null = null;
  let actionFeedback: Record<string, StationZeroV3ActionFeedback> = {};
  let responsibilityFeedback: Record<string, StationZeroV3ResponsibilityFeedback> = {};
  const rescueIntentReasons: Record<string, number> = {};
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
    const orderDigest = sha256(order);
    const preview = await buildStationZeroV3PlanPreview({
      state,
      planning,
      orderRevision: 1,
      order,
      orderDigest,
      providerFactory: fixtureStationZeroV3AgentProviderFactory,
      responsibilityFeedbackByActor: responsibilityFeedback,
      actionFeedbackByActor: actionFeedback,
    });

    const candidateSurface: Record<string, string[]> = {};
    for (const context of preview.contexts) {
      candidateSurface[context.actor.actorId] = context.candidates.map(semanticCandidate).sort();
    }
    const selectedActions: Record<string, string> = {};
    for (const decision of preview.agentDecisions) {
      const context = preview.contexts.find((entry) => entry.contextId === decision.contextId)!;
      const candidate = context.candidates.find((entry) => entry.candidateId === decision.candidateId)!;
      selectedActions[decision.actorId] = semanticCandidate(candidate);
    }
    for (const decision of preview.policyDecisions) {
      const context = preview.contexts.find((entry) => entry.actor.actorId === decision.actorId)!;
      const candidate = context.candidates.find((entry) => entry.candidateId === decision.candidateId)!;
      selectedActions[decision.actorId] = semanticCandidate(candidate);
    }

    const commitment = prepareStationZeroV3Commitment(state);
    const batch: StationZeroTurnBatch = {
      turnBatchId: `batch:g5-placement:${variant.variantId}:${profile.profileId}:${state.encounter.turn}`,
      expectedWorldRevision: state.revision,
      expectedTurn: state.encounter.turn,
      factionPlans: [preview.factionPlans.rescue, preview.factionPlans.pirate, preview.factionPlans.swarm],
    };
    const applied = applyStationZeroV3Turn(commitment, batch);
    if (applied.status !== "accepted") throw new Error(`Turn rejected for ${variant.variantId}/${profile.profileId}: ${applied.reason}`);

    const turnReasons: Record<string, number> = {};
    const rescueActors = new Set(Object.values(state.actors).filter((actor) => actor.factionId === "rescue").map((actor) => actor.actorId));
    for (const retained of applied.resolution.intentResolutions.filter((entry) => rescueActors.has(entry.actorId))) {
      increment(rescueIntentReasons, retained.reason);
      increment(turnReasons, retained.reason);
    }
    traces.push({ turn: state.encounter.turn, candidateSurface, selectedActions, rescueIntentReasons: turnReasons });

    const feedback = feedbackFrom(preview, applied.resolution);
    actionFeedback = feedback.action;
    responsibilityFeedback = feedback.responsibility;
    previousOrder = order;
    state = applied.state;
  }

  const focus = state.factions.rescue.objectiveProgress[profile.objective]!;
  const specialists = Object.values(state.actors).filter((actor) => actor.factionId === "rescue");
  const coreExtracted = specialists.some((actor) => actor.lifeState === "extracted" && actor.inventoryItemIds.includes("research-core"));
  const pirateCoreExtracted = Object.values(state.actors).some((actor) => actor.factionId === "pirate" && actor.lifeState === "extracted" && actor.inventoryItemIds.includes("research-core"));
  return {
    variantId: variant.variantId,
    profile,
    turns: state.encounter.turn,
    rescueOutcome: state.factions.rescue.outcome,
    pirateOutcome: state.factions.pirate.outcome,
    swarmOutcome: state.factions.swarm.outcome,
    terminalReason: state.encounter.reason,
    focus: { progress: focus.progress, target: focus.target, status: focus.status },
    vector: {
      civilians: Object.values(state.actors).filter((actor) => actor.kind === "civilian" && actor.lifeState === "extracted").length,
      core: coreExtracted ? 1 : 0,
      pirateCore: pirateCoreExtracted ? 1 : 0,
      hive: state.actors["hive-alpha"]?.lifeState === "dead" ? 1 : 0,
      specialistsExtracted: specialists.filter((actor) => actor.lifeState === "extracted").length,
      specialistsDead: specialists.filter((actor) => actor.lifeState === "dead").length,
      specialistsIncapacitated: specialists.filter((actor) => actor.lifeState === "incapacitated").length,
    },
    rescueIntentReasons,
    traces,
  };
}

function jaccard(left: string[], right: string[]): number {
  const a = new Set(left);
  const b = new Set(right);
  const union = new Set([...a, ...b]);
  if (union.size === 0) return 1;
  let intersection = 0;
  for (const value of a) if (b.has(value)) intersection += 1;
  return intersection / union.size;
}

function compare(baseline: PlacementRun, treatment: PlacementRun, target: "civilian" | "core") {
  const turns = Math.max(baseline.traces.length, treatment.traces.length);
  let candidateComparisons = 0;
  let candidateChanged = 0;
  let selectedComparisons = 0;
  let selectedChanged = 0;
  const candidateJaccards: number[] = [];
  for (let index = 0; index < turns; index += 1) {
    const left = baseline.traces[index];
    const right = treatment.traces[index];
    const actors = new Set([
      ...Object.keys(left?.candidateSurface ?? {}),
      ...Object.keys(right?.candidateSurface ?? {}),
    ]);
    for (const actorId of actors) {
      const leftCandidates = left?.candidateSurface[actorId] ?? [];
      const rightCandidates = right?.candidateSurface[actorId] ?? [];
      const similarity = jaccard(leftCandidates, rightCandidates);
      candidateJaccards.push(similarity);
      candidateComparisons += 1;
      if (similarity < 1) candidateChanged += 1;
      const leftSelected = left?.selectedActions[actorId] ?? "<missing>";
      const rightSelected = right?.selectedActions[actorId] ?? "<missing>";
      selectedComparisons += 1;
      if (leftSelected !== rightSelected) selectedChanged += 1;
    }
  }
  const strategicConsequenceChanged = JSON.stringify({
    focus: baseline.focus,
    vector: baseline.vector,
    rescueOutcome: baseline.rescueOutcome,
    pirateOutcome: baseline.pirateOutcome,
    swarmOutcome: baseline.swarmOutcome,
  }) !== JSON.stringify({
    focus: treatment.focus,
    vector: treatment.vector,
    rescueOutcome: treatment.rescueOutcome,
    pirateOutcome: treatment.pirateOutcome,
    swarmOutcome: treatment.swarmOutcome,
  });
  const anyResolutionChanged = strategicConsequenceChanged || JSON.stringify(baseline.rescueIntentReasons) !== JSON.stringify(treatment.rescueIntentReasons);
  const objectiveRelevantChanged = target === "civilian"
    ? baseline.vector.civilians !== treatment.vector.civilians
    : baseline.vector.core !== treatment.vector.core || baseline.vector.pirateCore !== treatment.vector.pirateCore;
  return {
    candidateComparisons,
    candidateChanged,
    candidateChangedRate: candidateComparisons ? candidateChanged / candidateComparisons : 0,
    minimumCandidateJaccard: candidateJaccards.length ? Math.min(...candidateJaccards) : 1,
    selectedComparisons,
    selectedChanged,
    selectedChangedRate: selectedComparisons ? selectedChanged / selectedComparisons : 0,
    strategicConsequenceChanged,
    anyResolutionChanged,
    objectiveRelevantChanged,
    baselineFocus: baseline.focus,
    treatmentFocus: treatment.focus,
    baselineVector: baseline.vector,
    treatmentVector: treatment.vector,
    baselineOutcomes: [baseline.rescueOutcome, baseline.pirateOutcome, baseline.swarmOutcome],
    treatmentOutcomes: [treatment.rescueOutcome, treatment.pirateOutcome, treatment.swarmOutcome],
  };
}

const allProfiles = profiles();
const runs: PlacementRun[] = [];
for (const variant of VARIANTS) {
  for (const profile of allProfiles) {
    const run = await runPlacementVariant(variant, profile);
    runs.push(run);
    console.log(JSON.stringify({
      kind: "ordivon.game.station-zero-v3-placement-axis-progress",
      variantId: variant.variantId,
      profileId: profile.profileId,
      focus: `${run.focus.progress}/${run.focus.target}`,
      focusStatus: run.focus.status,
      rescueOutcome: run.rescueOutcome,
      vector: run.vector,
    }));
  }
}

const baselineByProfile = new Map(runs.filter((run) => run.variantId === "baseline").map((run) => [run.profile.profileId, run]));
const comparisons = VARIANTS.filter((variant) => variant.variantId !== "baseline").map((variant) => {
  const rows = runs.filter((run) => run.variantId === variant.variantId).map((run) => {
    const baseline = baselineByProfile.get(run.profile.profileId)!;
    return { profileId: run.profile.profileId, ...compare(baseline, run, variant.target!) };
  });
  const candidateChangedRate = rows.reduce((sum, row) => sum + row.candidateChanged, 0) / rows.reduce((sum, row) => sum + row.candidateComparisons, 0);
  const selectedChangedRate = rows.reduce((sum, row) => sum + row.selectedChanged, 0) / rows.reduce((sum, row) => sum + row.selectedComparisons, 0);
  const strategicConsequenceChangedProfiles = rows.filter((row) => row.strategicConsequenceChanged).length;
  const anyResolutionChangedProfiles = rows.filter((row) => row.anyResolutionChanged).length;
  const focusChangedProfiles = rows.filter((row) => JSON.stringify(row.baselineFocus) !== JSON.stringify(row.treatmentFocus)).length;
  const outcomeVectorChangedProfiles = rows.filter((row) => JSON.stringify(row.baselineVector) !== JSON.stringify(row.treatmentVector)).length;
  const objectiveRelevantChangedProfiles = rows.filter((row) => row.objectiveRelevantChanged).length;
  const admitted = candidateChangedRate >= 0.1 && selectedChangedRate >= 0.1 && strategicConsequenceChangedProfiles > 0 && objectiveRelevantChangedProfiles > 0;
  return {
    variantId: variant.variantId,
    description: variant.description,
    candidateChangedRate,
    selectedChangedRate,
    strategicConsequenceChangedProfiles,
    anyResolutionChangedProfiles,
    focusChangedProfiles,
    outcomeVectorChangedProfiles,
    objectiveRelevantChangedProfiles,
    admitted,
    rows,
  };
});

const axisAdmitted = comparisons.some((entry) => entry.admitted);
const summary = {
  schemaVersion: 1,
  kind: "ordivon.game.station-zero-v3-g5-placement-axis",
  hypothesis: "Objective-bearing placement is a production-worthy outer content axis only if changing civilian or Research Core location alters admitted choices, selected actions, and objective-relevant authoritative consequence without changing topology, rules, Objectives, or loadouts.",
  variants: VARIANTS.map(({ variantId, target, description }) => ({ variantId, target, description })),
  profiles: allProfiles.length,
  runs: runs.length,
  admissionRule: {
    candidateChangedRateAtLeast: 0.1,
    selectedChangedRateAtLeast: 0.1,
    strategicConsequenceChangedProfilesAtLeast: 1,
    objectiveRelevantChangedProfilesAtLeast: 1,
  },
  axisAdmitted,
  comparisons,
};
const outputDirectory = resolve("artifacts/evaluations");
mkdirSync(outputDirectory, { recursive: true });
const outputPath = resolve(outputDirectory, `station-zero-v3-g5-placement-axis-${Date.now()}.json`);
writeFileSync(outputPath, `${JSON.stringify({ ...summary, runs }, null, 2)}\n`);
console.log(JSON.stringify({ ...summary, outputPath }, null, 2));
