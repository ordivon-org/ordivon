import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  FixtureStationZeroV3AgentProvider,
  StationZeroV3PlayService,
  StationZeroV3Store,
  type StationZeroV3CommanderDirectiveId,
  type StationZeroV3CommanderOrder,
  type StationZeroV3AgentContext,
  type StationZeroV3CommanderOrderPatch,
  type StationZeroV3PlanPreview,
  type StationZeroV3WorldState,
} from "../src/station-zero-v3/index.ts";

type PrimaryObjective = StationZeroV3CommanderOrder["primaryObjectiveId"];

type CandidateSelection = {
  actorId: string;
  label: string;
  kind: string;
  tags: string[];
};

const RESCUE_ACTORS = ["engineer-imani", "medic-reyes", "security-chen"] as const;

function baseOrder(objective: PrimaryObjective = "rescue-two-civilians"): StationZeroV3CommanderOrderPatch {
  return {
    primaryObjectiveId: objective,
    posture: "balanced",
    formation: "split",
    retreatHealthThreshold: 0.3,
    lethalForce: "permitted",
    collateralPolicy: "forbidden",
    lootPolicy: "mission-only",
    protectedActorId: null,
    priorityTargetActorId: null,
    commanderDirectiveId: "hold-command",
  };
}

function scanAvailable(state: StationZeroV3WorldState): boolean {
  const charges = state.factions.rescue.commanderAbilityCharges["orbital-scan"];
  return (charges === null || (charges !== undefined && charges > 0)) &&
    (state.factions.rescue.commanderAbilityCooldowns["orbital-scan"] ?? 0) === 0 &&
    state.factions.rescue.commandPoints >= 1;
}

function objectiveScan(state: StationZeroV3WorldState, objective: PrimaryObjective): StationZeroV3CommanderDirectiveId | null {
  if (!scanAvailable(state)) return null;
  if (objective === "rescue-two-civilians" && !state.factionKnowledge.rescue.discoveredZoneIds.includes("life-console")) return "scan-life-support";
  if (objective === "recover-research-core" && !state.factionKnowledge.rescue.discoveredZoneIds.includes("reactor-console")) return "scan-reactor";
  if (objective === "eliminate-hive-alpha" && !state.factionKnowledge.rescue.discoveredZoneIds.includes("maintenance-entry")) return "scan-maintenance";
  return null;
}

function exactOrder(state: StationZeroV3WorldState, objective: PrimaryObjective, extras: StationZeroV3CommanderOrderPatch = {}): StationZeroV3CommanderOrderPatch {
  const directive = objectiveScan(state, objective);
  return {
    ...baseOrder(objective),
    ...(directive ? { commanderDirectiveId: directive } : {}),
    ...extras,
  };
}

function selections(preview: StationZeroV3PlanPreview): CandidateSelection[] {
  return preview.agentDecisions
    .filter((decision) => decision.factionId === "rescue")
    .map((decision) => {
      const context = preview.contexts.find((entry) => entry.contextId === decision.contextId);
      const candidate = context?.candidates.find((entry) => entry.candidateId === decision.candidateId);
      if (!candidate) throw new Error(`Missing Rescue Candidate ${decision.candidateId}`);
      return {
        actorId: decision.actorId,
        label: candidate.label,
        kind: candidate.intent.kind,
        tags: [...candidate.tags].sort(),
      };
    })
    .sort((left, right) => left.actorId.localeCompare(right.actorId));
}

function selectionSignature(preview: StationZeroV3PlanPreview): string {
  return JSON.stringify(selections(preview).map((entry) => [entry.actorId, entry.label, entry.kind]));
}

function candidateSurfaceSignature(preview: StationZeroV3PlanPreview): string {
  return JSON.stringify(preview.contexts
    .filter((entry) => entry.factionId === "rescue")
    .map((context) => [context.actor.actorId, context.candidates.map((candidate) => [candidate.label, candidate.intent.kind, [...candidate.tags].sort()]).sort()])
    .sort());
}

function increment(target: Record<string, number>, key: string): void {
  target[key] = (target[key] ?? 0) + 1;
}

function currentFocus(play: StationZeroV3PlayService, runId: string, objective: PrimaryObjective): { progress: number; target: number; status: string } {
  const view = play.state(runId);
  const row = view.objectives.find((entry) => entry.objectiveId === objective);
  if (!row) throw new Error(`Missing objective ${objective}`);
  return { progress: row.progress, target: row.target, status: row.status };
}

async function controlLeverageAudit() {
  const store = new StationZeroV3Store(":memory:");
  const play = new StationZeroV3PlayService(store);
  const runId = "run:product-value:control-leverage";
  let view = play.initialize({ runId, seed: "product-value:control-leverage" });

  const stats: Record<string, {
    probes: number;
    changedSelection: number;
    changedCandidateSurface: number;
    changedCommanderAction: number;
    sampleEffects: Array<{ turn: number; variant: string; baseline: CandidateSelection[]; counterfactual: CandidateSelection[] }>;
    skipped: number;
  }> = {};
  const ensure = (id: string) => stats[id] ??= { probes: 0, changedSelection: 0, changedCandidateSurface: 0, changedCommanderAction: 0, sampleEffects: [], skipped: 0 };

  try {
    while (view.run.status === "running") {
      const state = store.loadState(runId);
      const baselinePatch = exactOrder(state, "rescue-two-civilians", { retreatHealthThreshold: 0.300001 + view.run.turn * 0.000001 });
      play.saveOrder(runId, baselinePatch);
      const baseline = (await play.generatePreview(runId)).preview;
      const baselineSelection = selectionSignature(baseline);
      const baselineSurface = candidateSurfaceSignature(baseline);
      const baselineCommander = baseline.commanderAction?.commanderAbilityId ?? null;

      const knownHostile = Object.values(state.factionKnowledge.rescue.knownActors)
        .find((known) => state.actors[known.actorId]?.factionId !== "rescue" && known.observedLifeState === "active")?.actorId ?? null;
      const aliveProtected = RESCUE_ACTORS.find((actorId) => state.actors[actorId]?.lifeState === "active" && actorId !== "security-chen") ?? null;
      const directiveCandidate = (["scan-reactor", "scan-maintenance", "scan-life-support", "reroute-cooling"] as StationZeroV3CommanderDirectiveId[])
        .find((directive) => directive !== baselinePatch.commanderDirectiveId) ?? null;

      const variants: Array<{ control: string; variant: string; patch: StationZeroV3CommanderOrderPatch | null }> = [
        { control: "primaryObjective", variant: "recover-research-core", patch: { primaryObjectiveId: "recover-research-core" } },
        { control: "primaryObjective", variant: "eliminate-hive-alpha", patch: { primaryObjectiveId: "eliminate-hive-alpha" } },
        { control: "posture", variant: "cautious", patch: { posture: "cautious" } },
        { control: "posture", variant: "aggressive", patch: { posture: "aggressive" } },
        { control: "formation", variant: "cohesive", patch: { formation: "cohesive" } },
        { control: "retreatHealthThreshold", variant: "0.85", patch: { retreatHealthThreshold: 0.85 } },
        { control: "lethalForce", variant: "forbidden", patch: { lethalForce: "forbidden" } },
        { control: "lethalForce", variant: "preferred", patch: { lethalForce: "preferred" } },
        { control: "collateralPolicy", variant: "permitted", patch: { collateralPolicy: "permitted" } },
        { control: "lootPolicy", variant: "ignore", patch: { lootPolicy: "ignore" } },
        { control: "lootPolicy", variant: "opportunistic", patch: { lootPolicy: "opportunistic" } },
        { control: "protectedActorId", variant: aliveProtected ?? "unavailable", patch: aliveProtected ? { protectedActorId: aliveProtected } : null },
        { control: "priorityTargetActorId", variant: knownHostile ?? "unavailable", patch: knownHostile ? { priorityTargetActorId: knownHostile } : null },
        { control: "commanderDirectiveId", variant: directiveCandidate ?? "unavailable", patch: directiveCandidate ? { commanderDirectiveId: directiveCandidate } : null },
      ];

      for (const variant of variants) {
        const stat = ensure(variant.control);
        if (!variant.patch) { stat.skipped += 1; continue; }
        try {
          play.saveOrder(runId, { ...baselinePatch, ...variant.patch });
          const counterfactual = (await play.generatePreview(runId)).preview;
          stat.probes += 1;
          const selectionChanged = selectionSignature(counterfactual) !== baselineSelection;
          const surfaceChanged = candidateSurfaceSignature(counterfactual) !== baselineSurface;
          const commanderChanged = (counterfactual.commanderAction?.commanderAbilityId ?? null) !== baselineCommander;
          if (selectionChanged) stat.changedSelection += 1;
          if (surfaceChanged) stat.changedCandidateSurface += 1;
          if (commanderChanged) stat.changedCommanderAction += 1;
          if ((selectionChanged || surfaceChanged || commanderChanged) && stat.sampleEffects.length < 3) {
            stat.sampleEffects.push({ turn: view.run.turn, variant: variant.variant, baseline: selections(baseline), counterfactual: selections(counterfactual) });
          }
        } catch {
          stat.skipped += 1;
        }
      }

      const restoredPatch = { ...baselinePatch, retreatHealthThreshold: 0.300002 + view.run.turn * 0.000001 };
      play.saveOrder(runId, restoredPatch);
      const restored = await play.generatePreview(runId);
      if (selectionSignature(restored.preview) !== baselineSelection || candidateSurfaceSignature(restored.preview) !== baselineSurface) {
        throw new Error(`Semantically neutral baseline restore changed Turn ${view.run.turn} planning surface`);
      }
      view = (await play.commitPreview(runId, restored.preview.previewId)).view;
    }

    const controls = Object.fromEntries(Object.entries(stats).map(([control, stat]) => [control, {
      ...stat,
      selectionLeverageRate: stat.probes ? stat.changedSelection / stat.probes : null,
      anyLeverageRate: stat.probes ? (stat.changedSelection + stat.changedCandidateSurface + stat.changedCommanderAction > 0 ? 1 : 0) : null,
      classification: stat.probes === 0
        ? "UNTESTED"
        : stat.changedSelection + stat.changedCandidateSurface + stat.changedCommanderAction === 0
          ? "NO_OBSERVED_LEVERAGE"
          : stat.changedSelection === 0 && stat.changedCommanderAction > 0
            ? "DIRECT_COMMAND_ONLY"
            : stat.changedSelection / stat.probes < 0.15
              ? "NARROW_LEVERAGE"
              : "OBSERVED_LEVERAGE",
    }]));
    return { turns: view.run.turn, controls };
  } finally {
    store.close();
  }
}

function knowledgeSnapshot(state: StationZeroV3WorldState) {
  const knowledge = state.factionKnowledge.rescue;
  return {
    discoveredZones: [...knowledge.discoveredZoneIds].sort(),
    knownActors: Object.values(knowledge.knownActors).map((actor) => `${actor.actorId}:${actor.confidence}:${actor.lastKnownZoneId}`).sort(),
    knownSystems: [...knowledge.knownSystemIds].sort(),
    knownHazards: [...knowledge.knownHazardIds].sort(),
    reports: [...knowledge.reportIds].sort(),
  };
}

async function informationBranch(objective: PrimaryObjective, directive: StationZeroV3CommanderDirectiveId, useScan: boolean) {
  const store = new StationZeroV3Store(":memory:");
  const play = new StationZeroV3PlayService(store);
  const runId = `run:product-value:information:${objective}:${useScan ? "scan" : "hold"}`;
  let view = play.initialize({ runId, seed: `product-value:information:${objective}` });
  const selectedByTurn: CandidateSelection[][] = [];
  let firstPostScanSurface = "";
  let immediateKnowledge: ReturnType<typeof knowledgeSnapshot> | null = null;
  try {
    for (let step = 0; step < 5 && view.run.status === "running"; step += 1) {
      const patch = {
        ...baseOrder(objective),
        commanderDirectiveId: step === 0 && useScan ? directive : "hold-command",
      } as StationZeroV3CommanderOrderPatch;
      play.saveOrder(runId, patch);
      const generated = await play.generatePreview(runId);
      selectedByTurn.push(selections(generated.preview));
      view = (await play.commitPreview(runId, generated.preview.previewId)).view;
      if (step === 0) immediateKnowledge = knowledgeSnapshot(store.loadState(runId));
      if (step === 0 && view.run.status === "running") {
        play.saveOrder(runId, { ...baseOrder(objective), commanderDirectiveId: "hold-command" });
        firstPostScanSurface = candidateSurfaceSignature((await play.generatePreview(runId)).preview);
      }
    }
    const state = store.loadState(runId);
    const finalKnowledge = knowledgeSnapshot(state);
    return {
      turns: view.run.turn,
      ...finalKnowledge,
      immediateKnowledge,
      firstPostScanSurface,
      selectedByTurn,
      focus: currentFocus(play, runId, objective),
      rescueOutcome: view.outcomes.rescue,
    };
  } finally {
    store.close();
  }
}

async function informationAudit() {
  const cases: Array<{ objective: PrimaryObjective; directive: StationZeroV3CommanderDirectiveId }> = [
    { objective: "rescue-two-civilians", directive: "scan-life-support" },
    { objective: "recover-research-core", directive: "scan-reactor" },
    { objective: "eliminate-hive-alpha", directive: "scan-maintenance" },
  ];
  const results = [];
  for (const entry of cases) {
    const scanned = await informationBranch(entry.objective, entry.directive, true);
    const held = await informationBranch(entry.objective, entry.directive, false);
    if (!scanned.immediateKnowledge || !held.immediateKnowledge) throw new Error(`Missing immediate Knowledge snapshot for ${entry.objective}`);
    const immediateGainedZones = scanned.immediateKnowledge.discoveredZones.filter((value) => !held.immediateKnowledge!.discoveredZones.includes(value));
    const immediateGainedActors = scanned.immediateKnowledge.knownActors.filter((value) => !held.immediateKnowledge!.knownActors.includes(value));
    const immediateGainedSystems = scanned.immediateKnowledge.knownSystems.filter((value) => !held.immediateKnowledge!.knownSystems.includes(value));
    const immediateGainedHazards = scanned.immediateKnowledge.knownHazards.filter((value) => !held.immediateKnowledge!.knownHazards.includes(value));
    const gainedZonesAtTurnFive = scanned.discoveredZones.filter((value) => !held.discoveredZones.includes(value));
    const firstTurnSelectionChanged = JSON.stringify(scanned.selectedByTurn[1] ?? []) !== JSON.stringify(held.selectedByTurn[1] ?? []);
    const immediateGainCount = immediateGainedZones.length + immediateGainedActors.length + immediateGainedSystems.length + immediateGainedHazards.length;
    results.push({
      objective: entry.objective,
      directive: entry.directive,
      immediateGainedZones,
      immediateGainedActors,
      immediateGainedSystems,
      immediateGainedHazards,
      gainedZonesAtTurnFive,
      candidateSurfaceChangedAfterScan: scanned.firstPostScanSurface !== held.firstPostScanSurface,
      firstTurnSelectionChanged,
      scannedFocus: scanned.focus,
      heldFocus: held.focus,
      focusDelta: scanned.focus.progress - held.focus.progress,
      scanned,
      held,
      classification: immediateGainCount === 0
        ? "NO_IMMEDIATE_INFORMATION_GAIN"
        : scanned.firstPostScanSurface === held.firstPostScanSurface && !firstTurnSelectionChanged && scanned.focus.progress === held.focus.progress
          ? "INFORMATION_WITHOUT_OBSERVED_COMMAND_EFFECT"
          : "INFORMATION_CHANGES_COMMAND_SURFACE",
    });
  }
  return { cases: results };
}

async function decideWithOrder(context: StationZeroV3AgentContext, patch: StationZeroV3CommanderOrderPatch) {
  if (!context.playerOrder) throw new Error(`Rescue context lacks player order: ${context.contextId}`);
  const cloned = structuredClone(context);
  cloned.playerOrder = { ...cloned.playerOrder!, ...patch };
  return new FixtureStationZeroV3AgentProvider().decide(cloned);
}

async function targetedControlOpportunityAudit() {
  const opportunities = {
    retreatHealthThreshold: { opportunities: 0, changed: 0, examples: [] as unknown[] },
    lootPolicy: { opportunities: 0, changed: 0, examples: [] as unknown[] },
    priorityTargetActorId: { opportunities: 0, changed: 0, examples: [] as unknown[] },
  };
  const profiles: Array<{ id: string; objective: PrimaryObjective; extras: StationZeroV3CommanderOrderPatch }> = [
    { id: "rescue", objective: "rescue-two-civilians", extras: { posture: "cautious", formation: "cohesive" } },
    { id: "core", objective: "recover-research-core", extras: { posture: "cautious", formation: "split" } },
    { id: "hive", objective: "eliminate-hive-alpha", extras: { posture: "balanced", formation: "split" } },
  ];
  for (const profile of profiles) {
    const store = new StationZeroV3Store(":memory:");
    const play = new StationZeroV3PlayService(store);
    const runId = `run:product-value:targeted-control:${profile.id}`;
    let view = play.initialize({ runId, seed: `product-value:targeted-control:${profile.id}` });
    try {
      while (view.run.status === "running") {
        const state = store.loadState(runId);
        play.saveOrder(runId, exactOrder(state, profile.objective, profile.extras));
        const generated = await play.generatePreview(runId);
        for (const context of generated.preview.contexts.filter((entry) => entry.factionId === "rescue")) {
          const baseline = generated.preview.agentDecisions.find((entry) => entry.contextId === context.contextId);
          if (!baseline) continue;
          const extract = context.candidates.find((candidate) => candidate.intent.kind === "extract");
          const healthRatio = context.actor.maximumHealth > 0 ? context.actor.health / context.actor.maximumHealth : 1;
          if (extract && healthRatio <= 0.85 && healthRatio > 0.05) {
            const stat = opportunities.retreatHealthThreshold; stat.opportunities += 1;
            const low = await decideWithOrder(context, { retreatHealthThreshold: 0.05 });
            const high = await decideWithOrder(context, { retreatHealthThreshold: 0.85 });
            if (low.candidateId !== high.candidateId) stat.changed += 1;
            if (stat.examples.length < 4) stat.examples.push({ profile: profile.id, turn: view.run.turn, actorId: context.actor.actorId, healthRatio, low: context.candidates.find((c) => c.candidateId === low.candidateId)?.label, high: context.candidates.find((c) => c.candidateId === high.candidateId)?.label });
          }
          const optionalPickup = context.candidates.find((candidate) => candidate.intent.kind === "pickup" && !candidate.tags.includes("objective:recover-research-core"));
          if (optionalPickup) {
            const stat = opportunities.lootPolicy; stat.opportunities += 1;
            const ignore = await decideWithOrder(context, { lootPolicy: "ignore" });
            const opportunistic = await decideWithOrder(context, { lootPolicy: "opportunistic" });
            if (ignore.candidateId !== opportunistic.candidateId) stat.changed += 1;
            if (stat.examples.length < 4) stat.examples.push({ profile: profile.id, turn: view.run.turn, actorId: context.actor.actorId, pickup: optionalPickup.label, ignore: context.candidates.find((c) => c.candidateId === ignore.candidateId)?.label, opportunistic: context.candidates.find((c) => c.candidateId === opportunistic.candidateId)?.label });
          }
          const attackTargets = [...new Set(context.candidates.filter((candidate) => candidate.intent.kind === "attack").map((candidate) => candidate.intent.kind === "attack" ? candidate.intent.targetActorId : null).filter((value): value is string => Boolean(value)))];
          if (attackTargets.length >= 2) {
            const stat = opportunities.priorityTargetActorId; stat.opportunities += 1;
            const first = await decideWithOrder(context, { priorityTargetActorId: attackTargets[0]! });
            const second = await decideWithOrder(context, { priorityTargetActorId: attackTargets[1]! });
            if (first.candidateId !== second.candidateId) stat.changed += 1;
            if (stat.examples.length < 4) stat.examples.push({ profile: profile.id, turn: view.run.turn, actorId: context.actor.actorId, targets: attackTargets.slice(0, 2), first: context.candidates.find((c) => c.candidateId === first.candidateId)?.label, second: context.candidates.find((c) => c.candidateId === second.candidateId)?.label });
          }
        }
        view = (await play.commitPreview(runId, generated.preview.previewId)).view;
      }
    } finally { store.close(); }
  }
  return {
    ...opportunities,
    classifications: Object.fromEntries(Object.entries(opportunities).map(([control, stat]) => [control, stat.opportunities === 0 ? "NO_RELEVANT_STATE" : stat.changed === 0 ? "RELEVANT_STATE_NO_LEVERAGE" : "OBSERVED_CONTEXTUAL_LEVERAGE"])),
  };
}

async function pressureRun(profileId: string, objective: PrimaryObjective, orderExtras: StationZeroV3CommanderOrderPatch) {
  const store = new StationZeroV3Store(":memory:");
  const play = new StationZeroV3PlayService(store);
  const runId = `run:product-value:pressure:${profileId}`;
  let view = play.initialize({ runId, seed: `product-value:pressure:${profileId}` });
  const turns: any[] = [];
  const selectedActions: Record<string, number> = {};
  try {
    while (view.run.status === "running") {
      const before = store.loadState(runId);
      const patch = exactOrder(before, objective, orderExtras);
      play.saveOrder(runId, patch);
      const generated = await play.generatePreview(runId);
      const selected = selections(generated.preview);
      for (const entry of selected) increment(selectedActions, `${entry.actorId}:${entry.label}`);
      view = (await play.commitPreview(runId, generated.preview.previewId)).view;
      const receipt = store.latestTurnReceipt(runId);
      if (!receipt) throw new Error(`Missing pressure receipt ${profileId}`);
      const after = receipt.state;
      const environmentFacts = receipt.record.resolution.facts.filter((fact) => fact.kind === "environment_changed");
      const pressureHealthFacts = receipt.record.resolution.facts.filter((fact) => fact.kind === "actor_health_changed" && fact.causes.some((cause) => cause === "low_oxygen" || cause === "reactor_heat"));
      turns.push({
        turn: view.run.turn,
        before: { ...before.environment },
        after: { ...after.environment },
        environmentFacts,
        pressureHealthFacts,
        selected,
        heatPlanningPressure: before.environment.reactorHeat >= 72,
        oxygenPlanningPressure: before.environment.oxygen <= 55,
        heatDamagePressure: after.environment.reactorHeat > 85,
        oxygenDamagePressure: after.environment.oxygen < 35,
      });
    }
    const resource = (key: keyof StationZeroV3WorldState["environment"]) => {
      const values = turns.flatMap((turn) => [turn.before[key], turn.after[key]]).filter((value): value is number => typeof value === "number");
      return { min: Math.min(...values), max: Math.max(...values), changedTurns: turns.filter((turn) => turn.before[key] !== turn.after[key]).length };
    };
    return {
      profileId,
      objective,
      outcome: view.outcomes.rescue,
      focus: currentFocus(play, runId, objective),
      resources: {
        oxygen: resource("oxygen"),
        reactorHeat: resource("reactorHeat"),
        alertLevel: resource("alertLevel"),
        biomass: resource("biomass"),
        batteryCharge: resource("batteryCharge"),
      },
      heatPlanningPressureTurns: turns.filter((turn) => turn.heatPlanningPressure).length,
      oxygenPlanningPressureTurns: turns.filter((turn) => turn.oxygenPlanningPressure).length,
      pressureDamageTurns: turns.filter((turn) => turn.pressureHealthFacts.length > 0).length,
      selectedActions,
      turns,
    };
  } finally {
    store.close();
  }
}

async function pressureAudit() {
  const runs = [
    await pressureRun("rescue-cautious-cohesive", "rescue-two-civilians", { posture: "cautious", formation: "cohesive" }),
    await pressureRun("core-cautious-split", "recover-research-core", { posture: "cautious", formation: "split" }),
    await pressureRun("hive-balanced-split", "eliminate-hive-alpha", { posture: "balanced", formation: "split" }),
  ];
  const thresholdRuns = runs.filter((run) => run.heatPlanningPressureTurns > 0 || run.oxygenPlanningPressureTurns > 0).length;
  const damageRuns = runs.filter((run) => run.pressureDamageTurns > 0).length;
  return {
    runs,
    thresholdRuns,
    damageRuns,
    classification: thresholdRuns === 0
      ? "PRESSURE_METERS_MOVE_BUT_PLANNING_THRESHOLDS_NOT_REACHED"
      : damageRuns === thresholdRuns
        ? "PRESSURE_REACHES_PLANNING_AND_DAMAGE_THRESHOLDS"
        : "PRESSURE_REACHES_PLANNING_THRESHOLDS_BEFORE_DAMAGE_IN_SOME_RUNS",
  };
}

async function specialistIdentityAudit() {
  const store = new StationZeroV3Store(":memory:");
  const play = new StationZeroV3PlayService(store);
  const runId = "run:product-value:specialist-identity";
  let view = play.initialize({ runId, seed: "product-value:specialist-identity" });
  const actors: Record<string, {
    roleId: string;
    selectedKinds: Record<string, number>;
    selectedTags: Record<string, number>;
    selectedLabels: Record<string, number>;
    candidateTags: Record<string, number>;
    uniqueAbilitySelections: Record<string, number>;
    responsibilityTurns: number;
  }> = {};
  try {
    while (view.run.status === "running") {
      const state = store.loadState(runId);
      play.saveOrder(runId, exactOrder(state, "rescue-two-civilians", { posture: "balanced", formation: "cohesive" }));
      const generated = await play.generatePreview(runId);
      for (const context of generated.preview.contexts.filter((entry) => entry.factionId === "rescue")) {
        const row = actors[context.actor.actorId] ??= {
          roleId: context.actor.roleId,
          selectedKinds: {}, selectedTags: {}, selectedLabels: {}, candidateTags: {}, uniqueAbilitySelections: {}, responsibilityTurns: 0,
        };
        if (context.responsibility) row.responsibilityTurns += 1;
        for (const candidate of context.candidates) for (const tag of candidate.tags) increment(row.candidateTags, tag);
        const decision = generated.preview.agentDecisions.find((entry) => entry.actorId === context.actor.actorId);
        const candidate = context.candidates.find((entry) => entry.candidateId === decision?.candidateId);
        if (!candidate) continue;
        increment(row.selectedKinds, candidate.intent.kind);
        increment(row.selectedLabels, candidate.label);
        for (const tag of candidate.tags) increment(row.selectedTags, tag);
        if (candidate.intent.kind === "use_ability") increment(row.uniqueAbilitySelections, candidate.intent.abilityId);
      }
      view = (await play.commitPreview(runId, generated.preview.previewId)).view;
    }

    const actorIds = Object.keys(actors).sort();
    const pairwise = [];
    for (let leftIndex = 0; leftIndex < actorIds.length; leftIndex += 1) {
      for (let rightIndex = leftIndex + 1; rightIndex < actorIds.length; rightIndex += 1) {
        const left = actors[actorIds[leftIndex]!]!;
        const right = actors[actorIds[rightIndex]!]!;
        const leftTags = new Set(Object.keys(left.selectedTags).filter((tag) => left.selectedTags[tag]! > 0));
        const rightTags = new Set(Object.keys(right.selectedTags).filter((tag) => right.selectedTags[tag]! > 0));
        const intersection = [...leftTags].filter((tag) => rightTags.has(tag)).length;
        const union = new Set([...leftTags, ...rightTags]).size;
        pairwise.push({
          left: actorIds[leftIndex], right: actorIds[rightIndex],
          selectedTagJaccard: union ? intersection / union : 1,
          leftUniqueTags: [...leftTags].filter((tag) => !rightTags.has(tag)).sort(),
          rightUniqueTags: [...rightTags].filter((tag) => !leftTags.has(tag)).sort(),
        });
      }
    }
    const roleSpecificSignals = Object.fromEntries(Object.entries(actors).map(([actorId, row]) => [actorId, {
      roleId: row.roleId,
      selectedRoleAbilityIds: Object.keys(row.uniqueAbilitySelections).sort(),
      responsibilityTurns: row.responsibilityTurns,
      selectedKinds: row.selectedKinds,
      topSelectedLabels: Object.entries(row.selectedLabels).sort((a, b) => b[1] - a[1]).slice(0, 8),
      roleSemanticTags: Object.keys(row.selectedTags).filter((tag) => ["medical", "engineering", "combat", "guard", "repair", "stabilize"].some((needle) => tag.includes(needle))).sort(),
    }]));
    const maxJaccard = Math.max(...pairwise.map((entry) => entry.selectedTagJaccard));
    return {
      turns: view.run.turn,
      actors,
      pairwise,
      roleSpecificSignals,
      maxSelectedTagJaccard: maxJaccard,
      classification: maxJaccard >= 0.9 ? "BEHAVIORALLY_CONVERGENT" : maxJaccard >= 0.7 ? "SOME_ROLE_DIFFERENTIATION" : "DISTINCT_BEHAVIORAL_SIGNATURES",
    };
  } finally {
    store.close();
  }
}

const controlLeverage = await controlLeverageAudit();
console.log(JSON.stringify({ kind: "ordivon.game.station-zero-v3-product-value-progress", lane: "control-leverage", controls: Object.fromEntries(Object.entries(controlLeverage.controls).map(([key, value]) => [key, { classification: value.classification, probes: value.probes, changedSelection: value.changedSelection, changedCommanderAction: value.changedCommanderAction }])) }, null, 2));
const information = await informationAudit();
console.log(JSON.stringify({ kind: "ordivon.game.station-zero-v3-product-value-progress", lane: "information", cases: information.cases.map((entry) => ({ objective: entry.objective, classification: entry.classification, immediateGainedZones: entry.immediateGainedZones.length, firstTurnSelectionChanged: entry.firstTurnSelectionChanged, focusDelta: entry.focusDelta })) }, null, 2));
const targetedControls = await targetedControlOpportunityAudit();
console.log(JSON.stringify({ kind: "ordivon.game.station-zero-v3-product-value-progress", lane: "targeted-controls", classifications: targetedControls.classifications, details: targetedControls }, null, 2));
const pressure = await pressureAudit();
console.log(JSON.stringify({ kind: "ordivon.game.station-zero-v3-product-value-progress", lane: "pressure", classification: pressure.classification, runs: pressure.runs.map((run) => ({ profileId: run.profileId, heatPlanningPressureTurns: run.heatPlanningPressureTurns, oxygenPlanningPressureTurns: run.oxygenPlanningPressureTurns, pressureDamageTurns: run.pressureDamageTurns, resources: run.resources })) }, null, 2));
const specialistIdentity = await specialistIdentityAudit();
console.log(JSON.stringify({ kind: "ordivon.game.station-zero-v3-product-value-progress", lane: "specialist-identity", classification: specialistIdentity.classification, maxSelectedTagJaccard: specialistIdentity.maxSelectedTagJaccard, roleSpecificSignals: specialistIdentity.roleSpecificSignals }, null, 2));

const report = {
  schemaVersion: 1,
  kind: "ordivon.game.station-zero-v3-product-value-evaluation",
  method: {
    controlLeverage: "same-world-revision counterfactual Preview perturbation; baseline restored before Commit",
    information: "same-seed paired Runs differing only by first-Turn objective-relevant scan vs hold command",
    pressure: "three representative full 20-Turn deterministic strategy Runs",
    specialistIdentity: "full deterministic Rescue Run comparing selected/candidate semantic distributions by specialist",
  },
  controlLeverage,
  targetedControls,
  information,
  pressure,
  specialistIdentity,
};
const outputDirectory = resolve(process.env.ORDIVON_EVAL_ARTIFACT_DIR ?? "artifacts/evaluations");
mkdirSync(outputDirectory, { recursive: true });
const outputPath = resolve(outputDirectory, `station-zero-v3-product-value-${Date.now()}.json`);
writeFileSync(outputPath, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify({ kind: "ordivon.game.station-zero-v3-product-value-summary", outputPath, controlLeverage: Object.fromEntries(Object.entries(controlLeverage.controls).map(([key, value]) => [key, value.classification])), targetedControls: targetedControls.classifications, information: information.cases.map((entry) => ({ objective: entry.objective, classification: entry.classification, focusDelta: entry.focusDelta })), pressure: pressure.classification, specialistIdentity: specialistIdentity.classification }, null, 2));
