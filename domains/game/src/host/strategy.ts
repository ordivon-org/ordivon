import type { WorldState } from "../model.ts";
import { ENGINEER_ID, isOperational } from "../scenario.ts";

export type GoalRequirementId =
  | "cooling_operational"
  | "breach_sealed"
  | "life_support_operational"
  | "life_support_powered"
  | "crew_stabilized"
  | "communications_operational"
  | "communications_powered"
  | "distress_sent"
  | "oxygen_safe"
  | "reactor_safe";

export type ThreatId =
  | "reactor_meltdown"
  | "station_asphyxiation"
  | "crew_lost"
  | "engineer_incapacitated"
  | "power_exhausted"
  | "mission_timeout";

export type ThreatSeverity = "critical" | "high" | "medium" | "low";

export interface GoalRequirementStatus {
  id: GoalRequirementId;
  label: string;
  category: "victory" | "distress_prerequisite";
  satisfied: boolean;
  dependencies: GoalRequirementId[];
}

export interface ThreatStatus {
  id: ThreatId;
  severity: ThreatSeverity;
  ticksToFailure: number;
  mitigationRequirements: GoalRequirementId[];
  detail: string;
}

export interface GoalStrategyAnalysis {
  requirements: GoalRequirementStatus[];
  satisfiedVictoryRequirements: number;
  totalVictoryRequirements: number;
  remainingVictoryRequirements: GoalRequirementId[];
  activeDistressPrerequisites: GoalRequirementId[];
  activeThreats: ThreatStatus[];
  optimisticMinimumPrimitiveStepsToVictory: number;
  turnsRemaining: number;
  optimisticStepSlack: number;
  lowerBoundTimeFeasible: boolean;
}

export type OperationStrategyClassification =
  | "projected_victory"
  | "immediate_failure"
  | "time_infeasible"
  | "goal_regression"
  | "safety_progress"
  | "goal_progress"
  | "neutral";

export type OperationSelectionClass = "preferred" | "viable" | "defer" | "blocked";

export interface OperationStrategyAnalysis {
  classification: OperationStrategyClassification;
  strategicScore: number;
  strategicRank: number;
  selectionClass: OperationSelectionClass;
  projectedVictory: boolean;
  lowerBoundTimeFeasible: boolean;
  remainingVictoryRequirements: GoalRequirementId[];
  activeDistressPrerequisites: GoalRequirementId[];
  optimisticMinimumPrimitiveStepsToVictory: number;
  optimisticStepSlack: number;
  newlySatisfied: GoalRequirementId[];
  regressed: GoalRequirementId[];
  threatsImproved: ThreatId[];
  threatsWorsened: ThreatId[];
  urgentMitigationsAdvanced: ThreatId[];
  urgentMitigationDepths: Partial<Record<ThreatId, number>>;
  controlAdvantages: string[];
  batteryConsumed: number;
  projectedPowerDraw: number;
  oneStepLookahead: {
    projectedVictoryOperationId: string | null;
    projectedVictoryLabel: string | null;
    preferredContinuationOperationId: string | null;
    preferredContinuationLabel: string | null;
  };
  summary: string;
}

const requirementDefinitions: Array<Omit<GoalRequirementStatus, "satisfied">> = [
  { id: "cooling_operational", label: "Reactor cooling is repaired", category: "victory", dependencies: [] },
  { id: "breach_sealed", label: "Maintenance hull breach is sealed", category: "victory", dependencies: [] },
  { id: "life_support_operational", label: "Life support is repaired", category: "victory", dependencies: [] },
  {
    id: "life_support_powered",
    label: "Life support remains powered",
    category: "victory",
    dependencies: ["life_support_operational"],
  },
  { id: "crew_stabilized", label: "Navigator Sato is stabilized", category: "victory", dependencies: [] },
  {
    id: "communications_operational",
    label: "Communications is repaired before distress transmission",
    category: "distress_prerequisite",
    dependencies: [],
  },
  {
    id: "communications_powered",
    label: "Communications is powered before distress transmission",
    category: "distress_prerequisite",
    dependencies: ["communications_operational"],
  },
  {
    id: "distress_sent",
    label: "Verified distress signal is transmitted",
    category: "victory",
    dependencies: ["communications_operational", "communications_powered"],
  },
  {
    id: "oxygen_safe",
    label: "Station oxygen is at least 35%",
    category: "victory",
    dependencies: ["breach_sealed", "life_support_operational", "life_support_powered"],
  },
  {
    id: "reactor_safe",
    label: "Reactor heat is at most 80%",
    category: "victory",
    dependencies: ["cooling_operational"],
  },
];

function requirementSatisfied(state: WorldState, id: GoalRequirementId): boolean {
  switch (id) {
    case "cooling_operational": return isOperational(state.systems.cooling?.integrity ?? 0);
    case "breach_sealed": return state.hazards["maintenance-breach"]?.sealed === true;
    case "life_support_operational": return isOperational(state.systems["life-support"]?.integrity ?? 0);
    case "life_support_powered": return state.systems["life-support"]?.powered === true;
    case "crew_stabilized": return state.crew["crew-01"]?.stabilized === true;
    case "communications_operational":
      return state.mission.distressSent || isOperational(state.systems.communications?.integrity ?? 0);
    case "communications_powered":
      return state.mission.distressSent || state.systems.communications?.powered === true;
    case "distress_sent": return state.mission.distressSent;
    case "oxygen_safe": return state.resources.oxygen >= 35;
    case "reactor_safe": return state.resources.reactorHeat <= 80;
  }
}

function severity(ticksToFailure: number): ThreatSeverity {
  if (ticksToFailure <= 3) return "critical";
  if (ticksToFailure <= 6) return "high";
  if (ticksToFailure <= 10) return "medium";
  return "low";
}

function finiteThreat(
  id: ThreatId,
  ticksToFailure: number,
  mitigationRequirements: GoalRequirementId[],
  detail: string,
): ThreatStatus | null {
  if (!Number.isFinite(ticksToFailure) || ticksToFailure < 0) return null;
  const ticks = Math.max(0, Math.ceil(ticksToFailure));
  return { id, severity: severity(ticks), ticksToFailure: ticks, mitigationRequirements, detail };
}

function currentOxygenDelta(state: WorldState): number {
  const breach = state.hazards["maintenance-breach"];
  const lifeSupport = state.systems["life-support"];
  return -2 + (breach?.sealed ? 0 : -2) +
    (lifeSupport?.powered && isOperational(lifeSupport.integrity) ? 5 : 0);
}

function currentHeatDelta(state: WorldState): number {
  const cooling = state.systems.cooling;
  return cooling?.powered && isOperational(cooling.integrity) ? -8 : 6;
}

function currentCrewDamage(state: WorldState): number {
  const crew = state.crew["crew-01"];
  if (!crew) return Number.POSITIVE_INFINITY;
  return (crew.stabilized ? 0 : 2) + (state.resources.oxygen < 25 ? 4 : 0);
}

function currentEngineerDamage(state: WorldState): number {
  const engineer = state.agents[ENGINEER_ID];
  if (!engineer) return Number.POSITIVE_INFINITY;
  let damage = state.resources.oxygen < 30 ? 8 : state.resources.oxygen < 45 ? 3 : 0;
  if (engineer.location === "reactor" && state.resources.reactorHeat > 85) damage += 5;
  return damage;
}

export function analyzeThreats(state: WorldState): ThreatStatus[] {
  if (state.mission.status !== "running") return [];
  const threats: ThreatStatus[] = [];
  const heatDelta = currentHeatDelta(state);
  if (heatDelta > 0) {
    const threat = finiteThreat(
      "reactor_meltdown",
      (100 - state.resources.reactorHeat) / heatDelta,
      ["cooling_operational", "reactor_safe"],
      `Reactor heat rises ${heatDelta} per Tick without powered cooling.`,
    );
    if (threat) threats.push(threat);
  }
  const oxygenDelta = currentOxygenDelta(state);
  if (oxygenDelta < 0) {
    const threat = finiteThreat(
      "station_asphyxiation",
      state.resources.oxygen / -oxygenDelta,
      ["breach_sealed", "life_support_operational", "life_support_powered", "oxygen_safe"],
      `Oxygen falls ${-oxygenDelta} per Tick under the current breach and life-support state.`,
    );
    if (threat) threats.push(threat);
  }
  const crew = state.crew["crew-01"];
  const crewDamage = currentCrewDamage(state);
  if (crew && crewDamage > 0 && Number.isFinite(crewDamage)) {
    const threat = finiteThreat(
      "crew_lost",
      crew.health / crewDamage,
      ["crew_stabilized", "oxygen_safe"],
      `Crew health falls ${crewDamage} per Tick under current conditions.`,
    );
    if (threat) threats.push(threat);
  }
  const engineer = state.agents[ENGINEER_ID];
  const engineerDamage = currentEngineerDamage(state);
  if (engineer && engineerDamage > 0 && Number.isFinite(engineerDamage)) {
    const threat = finiteThreat(
      "engineer_incapacitated",
      engineer.health / engineerDamage,
      ["oxygen_safe", "reactor_safe"],
      `Engineer health falls ${engineerDamage} per Tick at the current location and atmosphere.`,
    );
    if (threat) threats.push(threat);
  }
  const draw = Object.values(state.systems)
    .filter((system) => system.powered)
    .reduce((total, system) => total + system.powerDraw, 0);
  if (draw > 0) {
    const threat = finiteThreat(
      "power_exhausted",
      state.resources.batteryCharge / draw,
      ["distress_sent"],
      `Powered systems draw ${draw} battery units per Tick.`,
    );
    if (threat) threats.push(threat);
  }
  const timeout = finiteThreat(
    "mission_timeout",
    state.mission.turnLimit - state.turn,
    ["distress_sent"],
    `${state.mission.turnLimit - state.turn} Ticks remain before mission timeout.`,
  );
  if (timeout) threats.push(timeout);
  return threats.sort((left, right) =>
    left.ticksToFailure - right.ticksToFailure || left.id.localeCompare(right.id));
}

function optimisticMinimumSteps(state: WorldState): number {
  if (state.mission.status === "victory") return 0;
  if (state.mission.status === "failure") return Number.POSITIVE_INFINITY;
  const engineer = state.agents[ENGINEER_ID];
  if (!engineer) return Number.POSITIVE_INFINITY;
  let actions = 0;
  let sparePartsNeeded = 0;
  if (!isOperational(state.systems.cooling?.integrity ?? 0)) {
    actions += 1;
    sparePartsNeeded += state.systems.cooling?.repairParts ?? 0;
  }
  if (!isOperational(state.systems["life-support"]?.integrity ?? 0)) {
    actions += 1;
    sparePartsNeeded += state.systems["life-support"]?.repairParts ?? 0;
  }
  if (!state.systems["life-support"]?.powered) actions += 1;
  if (!state.hazards["maintenance-breach"]?.sealed) actions += 1;
  if (!state.crew["crew-01"]?.stabilized) actions += 1;
  if (!state.mission.distressSent) {
    if (!isOperational(state.systems.communications?.integrity ?? 0)) {
      actions += 1;
      sparePartsNeeded += state.systems.communications?.repairParts ?? 0;
    }
    if (!state.systems.communications?.powered) actions += 1;
    actions += 1;
  }
  if (sparePartsNeeded > engineer.inventory["spare-parts"]) actions += 1;
  if (!state.hazards["maintenance-breach"]?.sealed && engineer.inventory.sealant < 1) actions += 1;
  if (!state.crew["crew-01"]?.stabilized && engineer.inventory.medkit < 1) actions += 1;
  const cooling = state.systems.cooling;
  if (
    cooling &&
    !cooling.powered &&
    isOperational(cooling.integrity) &&
    state.resources.reactorHeat + 6 * actions >= 100
  ) actions += 1;

  let environmentTicks = 0;
  if (state.resources.oxygen < 35) {
    const delta = currentOxygenDelta(state);
    if (delta > 0) environmentTicks = Math.max(environmentTicks, Math.ceil((35 - state.resources.oxygen) / delta));
  }
  if (state.resources.reactorHeat > 80) {
    const delta = currentHeatDelta(state);
    if (delta < 0) environmentTicks = Math.max(environmentTicks, Math.ceil((state.resources.reactorHeat - 80) / -delta));
  }
  return Math.max(actions, environmentTicks);
}

export function analyzeGoalStrategy(state: WorldState): GoalStrategyAnalysis {
  const requirements = requirementDefinitions.map((requirement) => ({
    ...requirement,
    dependencies: [...requirement.dependencies],
    satisfied: requirementSatisfied(state, requirement.id),
  }));
  const victoryRequirements = requirements.filter((requirement) => requirement.category === "victory");
  const remainingVictoryRequirements = victoryRequirements
    .filter((requirement) => !requirement.satisfied)
    .map((requirement) => requirement.id);
  const activeDistressPrerequisites = requirements
    .filter((requirement) => requirement.category === "distress_prerequisite" && !requirement.satisfied)
    .map((requirement) => requirement.id);
  const turnsRemaining = Math.max(0, state.mission.turnLimit - state.turn);
  const optimisticMinimumPrimitiveStepsToVictory = optimisticMinimumSteps(state);
  const optimisticStepSlack = Number.isFinite(optimisticMinimumPrimitiveStepsToVictory)
    ? turnsRemaining - optimisticMinimumPrimitiveStepsToVictory
    : Number.NEGATIVE_INFINITY;
  return {
    requirements,
    satisfiedVictoryRequirements: victoryRequirements.length - remainingVictoryRequirements.length,
    totalVictoryRequirements: victoryRequirements.length,
    remainingVictoryRequirements,
    activeDistressPrerequisites,
    activeThreats: analyzeThreats(state),
    optimisticMinimumPrimitiveStepsToVictory,
    turnsRemaining,
    optimisticStepSlack,
    lowerBoundTimeFeasible: optimisticStepSlack >= 0,
  };
}

function mitigationDependencyDepth(
  satisfiedRequirement: GoalRequirementId,
  mitigationRequirement: GoalRequirementId,
  visited = new Set<GoalRequirementId>(),
): number | null {
  if (satisfiedRequirement === mitigationRequirement) return 0;
  if (visited.has(mitigationRequirement)) return null;
  visited.add(mitigationRequirement);
  const definition = requirementDefinitions.find((entry) => entry.id === mitigationRequirement);
  if (!definition) return null;
  const depths = definition.dependencies
    .map((dependency) => mitigationDependencyDepth(satisfiedRequirement, dependency, new Set(visited)))
    .filter((depth): depth is number => depth !== null);
  return depths.length === 0 ? null : Math.min(...depths) + 1;
}

function urgentMitigationDepths(
  before: GoalStrategyAnalysis,
  newlySatisfied: GoalRequirementId[],
): Partial<Record<ThreatId, number>> {
  const output: Partial<Record<ThreatId, number>> = {};
  for (const threat of before.activeThreats) {
    const depths = threat.mitigationRequirements.flatMap((mitigation) =>
      newlySatisfied
        .map((requirement) => mitigationDependencyDepth(requirement, mitigation))
        .filter((depth): depth is number => depth !== null));
    if (depths.length > 0) output[threat.id] = Math.min(...depths);
  }
  return output;
}

function requirementMap(analysis: GoalStrategyAnalysis): Map<GoalRequirementId, boolean> {
  return new Map(analysis.requirements.map((requirement) => [requirement.id, requirement.satisfied]));
}

function threatMap(analysis: GoalStrategyAnalysis): Map<ThreatId, number> {
  return new Map(analysis.activeThreats.map((threat) => [threat.id, threat.ticksToFailure]));
}

function threatChanges(before: GoalStrategyAnalysis, after: GoalStrategyAnalysis): {
  improved: ThreatId[];
  worsened: ThreatId[];
} {
  const beforeMap = threatMap(before);
  const afterMap = threatMap(after);
  const ids = new Set<ThreatId>([...beforeMap.keys(), ...afterMap.keys()]);
  const improved: ThreatId[] = [];
  const worsened: ThreatId[] = [];
  for (const id of ids) {
    const previous = beforeMap.get(id) ?? Number.POSITIVE_INFINITY;
    const next = afterMap.get(id) ?? Number.POSITIVE_INFINITY;
    if (next > previous) improved.push(id);
    else if (next < previous) worsened.push(id);
  }
  return { improved: improved.sort(), worsened: worsened.sort() };
}

function strategicScore(
  before: GoalStrategyAnalysis,
  after: GoalStrategyAnalysis,
  projectedStatus: WorldState["mission"]["status"],
  newlySatisfied: GoalRequirementId[],
  regressed: GoalRequirementId[],
  improvedThreats: ThreatId[],
  worsenedThreats: ThreatId[],
  mitigationDepths: Partial<Record<ThreatId, number>>,
  controlAdvantages: string[],
  primitiveSteps: number,
): number {
  if (projectedStatus === "victory") return -1_000_000;
  if (projectedStatus === "failure") return 1_000_000;
  let score = 0;
  score += after.remainingVictoryRequirements.length * 10_000;
  score += after.activeDistressPrerequisites.length * 4_000;
  score += Math.max(0, after.optimisticMinimumPrimitiveStepsToVictory) * 100;
  score += primitiveSteps * 10;
  score += regressed.length * 20_000;
  score -= newlySatisfied.length * 5_000;
  for (const threatId of improvedThreats) {
    const threat = before.activeThreats.find((candidate) => candidate.id === threatId);
    score -= Math.max(1, 14 - (threat?.ticksToFailure ?? 14)) * 1_500;
  }
  for (const threatId of worsenedThreats) {
    const threat = after.activeThreats.find((candidate) => candidate.id === threatId);
    score += Math.max(1, 14 - (threat?.ticksToFailure ?? 14)) * 2_000;
  }
  for (const [threatId, depth] of Object.entries(mitigationDepths) as Array<[ThreatId, number]>) {
    const threat = before.activeThreats.find((candidate) => candidate.id === threatId);
    if (threat) {
      const dependencyWeight = 1 / (depth + 1);
      score -= Math.max(1, 16 - threat.ticksToFailure) * 4_000 * dependencyWeight;
    }
  }
  score -= controlAdvantages.length * 35_000;
  if (
    newlySatisfied.length === 0 &&
    improvedThreats.length === 0 &&
    Object.keys(mitigationDepths).length === 0 &&
    controlAdvantages.length === 0
  ) {
    score += 15_000;
  }
  if (!after.lowerBoundTimeFeasible) score += 500_000;
  const mostUrgent = after.activeThreats[0];
  if (mostUrgent) score += Math.max(0, 12 - mostUrgent.ticksToFailure) * 1_000;
  if (after.remainingVictoryRequirements.length > before.remainingVictoryRequirements.length) score += 10_000;
  return score;
}

export function analyzeOperationStrategy(
  beforeState: WorldState,
  afterState: WorldState,
  primitiveSteps: number,
): OperationStrategyAnalysis {
  const before = analyzeGoalStrategy(beforeState);
  const after = analyzeGoalStrategy(afterState);
  const beforeRequirements = requirementMap(before);
  const afterRequirements = requirementMap(after);
  const newlySatisfied: GoalRequirementId[] = [];
  const regressed: GoalRequirementId[] = [];
  const persistentRequirements = new Set<GoalRequirementId>([
    "cooling_operational",
    "breach_sealed",
    "life_support_operational",
    "life_support_powered",
    "crew_stabilized",
    "communications_operational",
    "communications_powered",
    "distress_sent",
  ]);
  for (const [id, satisfiedBefore] of beforeRequirements) {
    const satisfiedAfter = afterRequirements.get(id) ?? false;
    if (!satisfiedBefore && satisfiedAfter) newlySatisfied.push(id);
    if (persistentRequirements.has(id) && satisfiedBefore && !satisfiedAfter) regressed.push(id);
  }
  const changes = threatChanges(before, after);
  const mitigationDepths = urgentMitigationDepths(before, newlySatisfied);
  const urgentMitigationsAdvanced = (Object.keys(mitigationDepths) as ThreatId[]).sort();
  const controlAdvantages: string[] = [];
  const beforeCooling = beforeState.systems.cooling;
  const afterCooling = afterState.systems.cooling;
  const urgentNonPowerThreat = after.activeThreats.some((threat) =>
    threat.id !== "power_exhausted" &&
    threat.id !== "mission_timeout" &&
    (threat.severity === "critical" || threat.severity === "high"));
  if (
    beforeCooling?.powered &&
    afterCooling &&
    !afterCooling.powered &&
    isOperational(afterCooling.integrity) &&
    !urgentNonPowerThreat &&
    after.requirements.find((requirement) => requirement.id === "oxygen_safe")?.satisfied === true &&
    Number.isFinite(after.optimisticMinimumPrimitiveStepsToVictory) &&
    afterState.resources.reactorHeat + 6 * after.optimisticMinimumPrimitiveStepsToVictory <= 80
  ) {
    controlAdvantages.push("cooling_shutdown_preserves_battery_through_optimistic_goal_horizon");
  }
  const beforeCommunications = beforeState.systems.communications;
  const afterCommunications = afterState.systems.communications;
  if (
    beforeCommunications?.powered &&
    afterCommunications &&
    !afterCommunications.powered &&
    afterState.mission.distressSent
  ) {
    controlAdvantages.push("communications_shutdown_after_distress_preserves_battery");
  }
  const projectedVictory = afterState.mission.status === "victory";
  let classification: OperationStrategyClassification;
  if (projectedVictory) classification = "projected_victory";
  else if (afterState.mission.status === "failure") classification = "immediate_failure";
  else if (!after.lowerBoundTimeFeasible) classification = "time_infeasible";
  else if (regressed.length > 0) classification = "goal_regression";
  else if (changes.improved.length > 0 || controlAdvantages.length > 0) classification = "safety_progress";
  else if (newlySatisfied.length > 0) classification = "goal_progress";
  else classification = "neutral";

  const score = strategicScore(
    before,
    after,
    afterState.mission.status,
    newlySatisfied,
    regressed,
    changes.improved,
    changes.worsened,
    mitigationDepths,
    controlAdvantages,
    primitiveSteps,
  );
  const summary = projectedVictory
    ? "This Operation reaches verified victory if its deterministic Skill completes."
    : classification === "immediate_failure"
      ? `This Operation reaches terminal failure: ${afterState.mission.reason ?? "unknown"}.`
      : classification === "time_infeasible"
        ? "Even the optimistic action lower bound exceeds the remaining mission Ticks after this Operation."
        : regressed.length > 0
          ? `This Operation regresses satisfied requirements: ${regressed.join(", ")}.`
          : controlAdvantages.length > 0
            ? `This Operation provides safe control: ${controlAdvantages.join(", ")}.`
            : newlySatisfied.length > 0
              ? `This Operation satisfies: ${newlySatisfied.join(", ")}.`
              : changes.improved.length > 0
                ? `This Operation improves threat horizons: ${changes.improved.join(", ")}.`
                : "This Operation makes no explicit Goal progress under the current dependency model.";
  return {
    classification,
    strategicScore: score,
    strategicRank: 0,
    selectionClass: "viable",
    projectedVictory,
    lowerBoundTimeFeasible: after.lowerBoundTimeFeasible,
    remainingVictoryRequirements: [...after.remainingVictoryRequirements],
    activeDistressPrerequisites: [...after.activeDistressPrerequisites],
    optimisticMinimumPrimitiveStepsToVictory: after.optimisticMinimumPrimitiveStepsToVictory,
    optimisticStepSlack: after.optimisticStepSlack,
    newlySatisfied: newlySatisfied.sort(),
    regressed: regressed.sort(),
    threatsImproved: changes.improved,
    threatsWorsened: changes.worsened,
    urgentMitigationsAdvanced,
    urgentMitigationDepths: mitigationDepths,
    controlAdvantages,
    batteryConsumed: beforeState.resources.batteryCharge - afterState.resources.batteryCharge,
    projectedPowerDraw: Object.values(afterState.systems)
      .filter((system) => system.powered)
      .reduce((total, system) => total + system.powerDraw, 0),
    oneStepLookahead: {
      projectedVictoryOperationId: null,
      projectedVictoryLabel: null,
      preferredContinuationOperationId: null,
      preferredContinuationLabel: null,
    },
    summary,
  };
}
