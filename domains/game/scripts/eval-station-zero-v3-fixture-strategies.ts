import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  StationZeroV3PlayService,
  StationZeroV3Store,
  type StationZeroV3CommanderOrder,
  type StationZeroV3CommanderOrderPatch,
  type StationZeroV3PlayView,
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
  order: StationZeroV3CommanderOrderPatch;
}

interface StrategyRun {
  profile: Omit<StrategyProfile, "order">;
  turns: number;
  rescueOutcome: StationZeroV3PlayView["outcomes"]["rescue"];
  pirateOutcome: StationZeroV3PlayView["outcomes"]["pirate"];
  swarmOutcome: StationZeroV3PlayView["outcomes"]["swarm"];
  terminalReason: string | null;
  requiredCompleted: number;
  requiredTotal: number;
  focus: {
    objectiveId: string;
    progress: number;
    target: number;
    status: string;
    firstProgressTurn: number | null;
    completedTurn: number | null;
  };
  milestones: {
    firstCivilianExtractedTurn: number | null;
    civilianExtractedFinal: number;
    firstCoreAcquiredTurn: number | null;
    coreExtractedTurn: number | null;
    hiveAlphaDeathTurn: number | null;
    specialistExtractedFinal: number;
    specialistDeadFinal: number;
    specialistIncapacitatedFinal: number;
  };
  rescueIntentStatuses: Record<string, number>;
  rescueIntentReasons: Record<string, number>;
  rescueSelectedActions: Record<string, number>;
  verified: boolean;
}

function profileId(objective: string, posture: string, formation: string): string {
  return `${objective}__${posture}__${formation}`;
}

function profiles(): StrategyProfile[] {
  return OBJECTIVES.flatMap((objective) => POSTURES.flatMap((posture) => FORMATIONS.map((formation) => ({
    profileId: profileId(objective, posture, formation),
    objective,
    posture,
    formation,
    order: {
      primaryObjectiveId: objective,
      posture,
      formation,
      retreatHealthThreshold: 0.3,
      lethalForce: "permitted",
      collateralPolicy: "forbidden",
      lootPolicy: "mission-only",
      protectedActorId: null,
      priorityTargetActorId: null,
    },
  }))));
}

function increment(target: Record<string, number>, key: string): void {
  target[key] = (target[key] ?? 0) + 1;
}

async function evaluate(profile: StrategyProfile): Promise<StrategyRun> {
  const store = new StationZeroV3Store(":memory:");
  const play = new StationZeroV3PlayService(store);
  const runId = `run:fixture-viability:${profile.profileId}`;
  let view = play.initialize({ runId, seed: `fixture-viability:${profile.profileId}` });
  const rescueIntentStatuses: Record<string, number> = {};
  const rescueIntentReasons: Record<string, number> = {};
  const rescueSelectedActions: Record<string, number> = {};
  let firstCivilianExtractedTurn: number | null = null;
  let firstCoreAcquiredTurn: number | null = null;
  let coreExtractedTurn: number | null = null;
  let hiveAlphaDeathTurn: number | null = null;

  try {
    while (view.run.status === "running") {
      const beforeOrder = store.loadState(runId);
      const scanCharges = beforeOrder.factions.rescue.commanderAbilityCharges["orbital-scan"];
      const scanAvailable =
        (scanCharges === null || (scanCharges !== undefined && scanCharges > 0)) &&
        (beforeOrder.factions.rescue.commanderAbilityCooldowns["orbital-scan"] ?? 0) === 0 &&
        beforeOrder.factions.rescue.commandPoints >= 1;
      const objectiveScanDirective =
        profile.objective === "rescue-two-civilians" && !beforeOrder.factionKnowledge.rescue.discoveredZoneIds.includes("life-console")
          ? "scan-life-support"
          : profile.objective === "recover-research-core" && !beforeOrder.factionKnowledge.rescue.discoveredZoneIds.includes("reactor-console")
            ? "scan-reactor"
            : profile.objective === "eliminate-hive-alpha" && !beforeOrder.factionKnowledge.rescue.discoveredZoneIds.includes("maintenance-entry")
              ? "scan-maintenance"
              : null;
      play.saveOrder(runId, {
        ...profile.order,
        ...(scanAvailable && objectiveScanDirective ? { commanderDirectiveId: objectiveScanDirective } : {}),
      });
      const generated = await play.generatePreview(runId);
      for (const decision of generated.preview.agentDecisions.filter((entry) => entry.factionId === "rescue")) {
        const context = generated.preview.contexts.find((entry) => entry.contextId === decision.contextId);
        const candidate = context?.candidates.find((entry) => entry.candidateId === decision.candidateId);
        increment(rescueSelectedActions, candidate?.label ?? decision.candidateId);
      }
      view = (await play.commitPreview(runId, generated.preview.previewId)).view;
      const receipt = store.latestTurnReceipt(runId);
      if (!receipt) throw new Error(`missing Turn receipt after committed Turn ${view.run.turn}`);
      const state = receipt.state;
      const turn = receipt.turnSequence + 1;

      const rescueActorIds = new Set(Object.values(state.actors).filter((actor) => actor.factionId === "rescue").map((actor) => actor.actorId));
      for (const resolution of receipt.record.resolution.intentResolutions) {
        if (!rescueActorIds.has(resolution.actorId)) continue;
        increment(rescueIntentStatuses, resolution.status);
        increment(rescueIntentReasons, resolution.reason);
      }

      const extractedCivilians = Object.values(state.actors).filter((actor) => actor.kind === "civilian" && actor.lifeState === "extracted").length;
      if (extractedCivilians > 0 && firstCivilianExtractedTurn === null) firstCivilianExtractedTurn = turn;
      const rescueHasCore = Object.values(state.actors).some((actor) => actor.factionId === "rescue" && actor.inventoryItemIds.includes("research-core"));
      if (rescueHasCore && firstCoreAcquiredTurn === null) firstCoreAcquiredTurn = turn;
      const coreExtracted = Object.values(state.actors).some((actor) => actor.factionId === "rescue" && actor.lifeState === "extracted" && actor.inventoryItemIds.includes("research-core"));
      if (coreExtracted && coreExtractedTurn === null) coreExtractedTurn = turn;
      if (state.actors["hive-alpha"]?.lifeState === "dead" && hiveAlphaDeathTurn === null) hiveAlphaDeathTurn = turn;
    }

    play.planning.verifyRun(runId);
    play.turns.recover(runId);
    view = play.state(runId);
    const finalState = store.loadState(runId);
    const focus = view.debrief?.objectives.find((objective) => objective.objectiveId === profile.objective);
    if (!view.debrief || !focus) throw new Error(`terminal Run lacks debrief/focus for ${profile.profileId}`);
    const specialists = Object.values(finalState.actors).filter((actor) => actor.factionId === "rescue");
    const civilians = Object.values(finalState.actors).filter((actor) => actor.kind === "civilian");

    return {
      profile: {
        profileId: profile.profileId,
        objective: profile.objective,
        posture: profile.posture,
        formation: profile.formation,
      },
      turns: view.run.turn,
      rescueOutcome: view.outcomes.rescue,
      pirateOutcome: view.outcomes.pirate,
      swarmOutcome: view.outcomes.swarm,
      terminalReason: view.outcomes.reason,
      requiredCompleted: view.debrief.requiredCompleted,
      requiredTotal: view.debrief.requiredTotal,
      focus: {
        objectiveId: focus.objectiveId,
        progress: focus.finalProgress,
        target: focus.target,
        status: focus.finalStatus,
        firstProgressTurn: focus.firstProgressTurn,
        completedTurn: focus.completedTurn,
      },
      milestones: {
        firstCivilianExtractedTurn,
        civilianExtractedFinal: civilians.filter((actor) => actor.lifeState === "extracted").length,
        firstCoreAcquiredTurn,
        coreExtractedTurn,
        hiveAlphaDeathTurn,
        specialistExtractedFinal: specialists.filter((actor) => actor.lifeState === "extracted").length,
        specialistDeadFinal: specialists.filter((actor) => actor.lifeState === "dead").length,
        specialistIncapacitatedFinal: specialists.filter((actor) => actor.lifeState === "incapacitated").length,
      },
      rescueIntentStatuses,
      rescueIntentReasons,
      rescueSelectedActions,
      verified: true,
    };
  } finally {
    store.close();
  }
}

interface RescueValueVector {
  civilians: number;
  core: number;
  hive: number;
  specialistsExtracted: number;
  specialistsDead: number;
  specialistsIncapacitated: number;
}

function valueVector(run: StrategyRun): RescueValueVector {
  return {
    civilians: run.milestones.civilianExtractedFinal,
    core: run.milestones.coreExtractedTurn === null ? 0 : 1,
    hive: run.milestones.hiveAlphaDeathTurn === null ? 0 : 1,
    specialistsExtracted: run.milestones.specialistExtractedFinal,
    specialistsDead: run.milestones.specialistDeadFinal,
    specialistsIncapacitated: run.milestones.specialistIncapacitatedFinal,
  };
}

function dominates(left: StrategyRun, right: StrategyRun): boolean {
  const a = valueVector(left);
  const b = valueVector(right);
  const weak =
    a.civilians >= b.civilians &&
    a.core >= b.core &&
    a.hive >= b.hive &&
    a.specialistsExtracted >= b.specialistsExtracted &&
    a.specialistsDead <= b.specialistsDead &&
    a.specialistsIncapacitated <= b.specialistsIncapacitated;
  const strict =
    a.civilians > b.civilians ||
    a.core > b.core ||
    a.hive > b.hive ||
    a.specialistsExtracted > b.specialistsExtracted ||
    a.specialistsDead < b.specialistsDead ||
    a.specialistsIncapacitated < b.specialistsIncapacitated;
  return weak && strict;
}

function vectorSignature(vector: RescueValueVector): string {
  return JSON.stringify(vector);
}

function classification(run: StrategyRun): string {
  const focusComplete = run.focus.status === "completed";
  if (focusComplete && run.rescueOutcome === "victory") return "focus+victory";
  if (focusComplete && run.rescueOutcome === "partial") return "focus+partial";
  if (focusComplete) return `focus+${run.rescueOutcome}`;
  if (run.rescueOutcome === "victory") return "victory-without-focus";
  if (run.rescueOutcome === "partial") return "partial-without-focus";
  return "focus-failed";
}

const evaluated: StrategyRun[] = [];
for (const profile of profiles()) {
  const run = await evaluate(profile);
  evaluated.push(run);
  console.log(JSON.stringify({
    kind: "ordivon.game.station-zero-v3-fixture-viability-progress",
    profileId: profile.profileId,
    classification: classification(run),
    focus: `${run.focus.progress}/${run.focus.target}`,
    required: `${run.requiredCompleted}/${run.requiredTotal}`,
    rescueOutcome: run.rescueOutcome,
    terminalReason: run.terminalReason,
  }));
}

const byObjective = Object.fromEntries(OBJECTIVES.map((objective) => {
  const runs = evaluated.filter((run) => run.profile.objective === objective);
  return [objective, {
    profiles: runs.length,
    focusCompleted: runs.filter((run) => run.focus.status === "completed").length,
    rescueVictory: runs.filter((run) => run.rescueOutcome === "victory").length,
    rescuePartial: runs.filter((run) => run.rescueOutcome === "partial").length,
    rescueFailure: runs.filter((run) => run.rescueOutcome === "failure").length,
    classifications: Object.fromEntries([...new Set(runs.map(classification))].sort().map((value) => [value, runs.filter((run) => classification(run) === value).length])),
    best: runs
      .toSorted((left, right) =>
        Number(right.focus.status === "completed") - Number(left.focus.status === "completed") ||
        right.requiredCompleted - left.requiredCompleted ||
        right.milestones.specialistExtractedFinal - left.milestones.specialistExtractedFinal ||
        left.milestones.specialistDeadFinal - right.milestones.specialistDeadFinal ||
        left.profile.profileId.localeCompare(right.profile.profileId))
      .slice(0, 3)
      .map((run) => ({ profileId: run.profile.profileId, classification: classification(run), required: `${run.requiredCompleted}/${run.requiredTotal}`, focus: `${run.focus.progress}/${run.focus.target}` })),
  }];
}));

const paretoRuns = evaluated.filter((candidate) =>
  !evaluated.some((other) => other !== candidate && dominates(other, candidate)));
const uniquePareto = new Map<string, StrategyRun[]>();
for (const run of paretoRuns) {
  const signature = vectorSignature(valueVector(run));
  const group = uniquePareto.get(signature) ?? [];
  group.push(run);
  uniquePareto.set(signature, group);
}

const summary = {
  schemaVersion: 1,
  kind: "ordivon.game.station-zero-v3-fixture-strategic-viability",
  matrix: {
    objectives: OBJECTIVES,
    postures: POSTURES,
    formations: FORMATIONS,
    profiles: evaluated.length,
    deterministicReplicasPerProfile: 1,
  },
  baselinePolicies: {
    retreatHealthThreshold: 0.3,
    lethalForce: "permitted",
    collateralPolicy: "forbidden",
    lootPolicy: "mission-only",
    protectedActorId: null,
    priorityTargetActorId: null,
    objectiveDiscoveryPolicy: {
      "rescue-two-civilians": "Use the legal scan-life-support Commander directive until Life Support Console is known.",
      "recover-research-core": "Use the legal scan-reactor Commander directive until Reactor Console is known.",
      "eliminate-hive-alpha": "Use the legal scan-maintenance Commander directive until Maintenance Entry is known; never infer hidden Hive position.",
    },
  },
  byObjective,
  pareto: {
    profileCount: paretoRuns.length,
    uniqueOutcomeSignatures: uniquePareto.size,
    signatures: [...uniquePareto.entries()].map(([signature, runs]) => ({
      signature,
      vector: valueVector(runs[0]!),
      profiles: runs.map((run) => run.profile.profileId).sort(),
    })),
  },
  runs: evaluated,
};

const outputDirectory = resolve(process.env.ORDIVON_EVAL_ARTIFACT_DIR ?? "artifacts/evaluations");
mkdirSync(outputDirectory, { recursive: true });
const outputPath = resolve(outputDirectory, `station-zero-v3-fixture-viability-${Date.now()}.json`);
writeFileSync(outputPath, `${JSON.stringify(summary, null, 2)}\n`);
console.log(JSON.stringify({ kind: "ordivon.game.station-zero-v3-fixture-viability-summary", outputPath, byObjective, pareto: summary.pareto }, null, 2));
