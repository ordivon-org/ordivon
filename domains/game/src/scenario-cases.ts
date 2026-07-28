import { sha256 } from "./digest.ts";
import type { WorldState } from "./model.ts";
import { assertWorldInvariants, initialTeamWorld, initialWorld } from "./scenario.ts";

export interface ScenarioGenesisSpec {
  resources?: {
    batteryInitial?: number;
    oxygen?: number;
    reactorHeat?: number;
  };
  mission?: {
    turnLimit?: number;
  };
  crew?: Record<string, { health?: number }>;
  systems?: Record<string, { integrity?: number; powered?: boolean }>;
}

export interface ScenarioCaseDefinition {
  schemaVersion: 1;
  caseId: string;
  scenarioId: string;
  scenarioVersion: number;
  label: string;
  description: string;
  genesisSpec: ScenarioGenesisSpec;
  genesisSpecDigest: string;
}

interface ScenarioCaseInput extends Omit<ScenarioCaseDefinition, "schemaVersion" | "genesisSpecDigest"> {}

function boundedNumber(value: number, label: string, minimum: number, maximum: number): number {
  if (!Number.isFinite(value) || value < minimum || value > maximum) {
    throw new TypeError(`${label} must be between ${minimum} and ${maximum}`);
  }
  return value;
}

function boundedInteger(value: number, label: string, minimum: number, maximum: number): number {
  if (!Number.isSafeInteger(value) || value < minimum || value > maximum) {
    throw new TypeError(`${label} must be an integer between ${minimum} and ${maximum}`);
  }
  return value;
}

function defineCase(input: ScenarioCaseInput): ScenarioCaseDefinition {
  return {
    schemaVersion: 1,
    ...input,
    genesisSpecDigest: sha256({
      kind: "ordivon.game.scenario-genesis-spec",
      scenarioId: input.scenarioId,
      scenarioVersion: input.scenarioVersion,
      caseId: input.caseId,
      genesisSpec: input.genesisSpec,
    }),
  };
}

const CASES: ScenarioCaseDefinition[] = [
  defineCase({
    caseId: "legacy-fixed",
    scenarioId: "station-zero",
    scenarioVersion: 1,
    label: "Legacy fixed mission",
    description: "Frozen single-Engineer compatibility mission used by M1 and M2 evidence.",
    genesisSpec: {},
  }),
  defineCase({
    caseId: "baseline",
    scenarioId: "station-zero",
    scenarioVersion: 2,
    label: "Baseline emergency",
    description: "The verified three-specialist Station Zero baseline used by M3 and M4.",
    genesisSpec: {},
  }),
  defineCase({
    caseId: "power-constrained",
    scenarioId: "station-zero",
    scenarioVersion: 2,
    label: "Power constrained",
    description: "Starts with 50 battery energy. Security containment remains viable while the longer sealing route exhausts power.",
    genesisSpec: { resources: { batteryInitial: 50 } },
  }),
  defineCase({
    caseId: "oxygen-constrained",
    scenarioId: "station-zero",
    scenarioVersion: 2,
    label: "Oxygen constrained",
    description: "Starts at 62% oxygen. Delay and exposure become materially more dangerous without changing World rules.",
    genesisSpec: { resources: { oxygen: 62 } },
  }),
];

export function listScenarioCases(scenarioId = "station-zero", scenarioVersion = 2): ScenarioCaseDefinition[] {
  return CASES
    .filter((definition) => definition.scenarioId === scenarioId && definition.scenarioVersion === scenarioVersion)
    .map((definition) => structuredClone(definition));
}

export function resolveScenarioCase(
  scenarioId: string,
  scenarioVersion: number,
  caseId?: string,
): ScenarioCaseDefinition {
  const candidates = CASES.filter((definition) =>
    definition.scenarioId === scenarioId && definition.scenarioVersion === scenarioVersion);
  const selectedId = caseId ?? (scenarioVersion === 1 ? "legacy-fixed" : "baseline");
  const definition = candidates.find((candidate) => candidate.caseId === selectedId);
  if (!definition) {
    throw new TypeError(`unsupported Scenario Case: ${scenarioId}@${scenarioVersion}/${selectedId}`);
  }
  return structuredClone(definition);
}

export function applyScenarioGenesisSpec(base: WorldState, spec: ScenarioGenesisSpec): WorldState {
  const state = structuredClone(base);
  if (spec.resources?.batteryInitial !== undefined) {
    const battery = boundedInteger(spec.resources.batteryInitial, "batteryInitial", 1, 1_000);
    state.resources.batteryInitial = battery;
    state.resources.batteryCharge = battery;
    state.resources.energyConsumed = 0;
  }
  if (spec.resources?.oxygen !== undefined) {
    state.resources.oxygen = boundedNumber(spec.resources.oxygen, "oxygen", 0, 100);
  }
  if (spec.resources?.reactorHeat !== undefined) {
    state.resources.reactorHeat = boundedNumber(spec.resources.reactorHeat, "reactorHeat", 0, 100);
  }
  if (spec.mission?.turnLimit !== undefined) {
    state.mission.turnLimit = boundedInteger(spec.mission.turnLimit, "turnLimit", 1, 1_000);
  }
  for (const [crewId, patch] of Object.entries(spec.crew ?? {})) {
    const crew = state.crew[crewId];
    if (!crew) throw new TypeError(`unknown crew in Scenario Genesis Spec: ${crewId}`);
    if (patch.health !== undefined) crew.health = boundedNumber(patch.health, `${crewId}.health`, 0, 100);
  }
  for (const [systemId, patch] of Object.entries(spec.systems ?? {})) {
    const system = state.systems[systemId];
    if (!system) throw new TypeError(`unknown system in Scenario Genesis Spec: ${systemId}`);
    if (patch.integrity !== undefined) system.integrity = boundedNumber(patch.integrity, `${systemId}.integrity`, 0, 1);
    if (patch.powered !== undefined) system.powered = patch.powered;
  }
  assertWorldInvariants(state);
  return state;
}

export function createScenarioCaseWorld(
  scenarioId: string,
  scenarioVersion: number,
  caseId?: string,
  compatibilitySeed?: string,
): { definition: ScenarioCaseDefinition; state: WorldState; genesisDigest: string } {
  const definition = resolveScenarioCase(scenarioId, scenarioVersion, caseId);
  const base = scenarioVersion === 1 ? initialWorld() : initialTeamWorld();
  const state = applyScenarioGenesisSpec(base, definition.genesisSpec);
  if (compatibilitySeed) state.seed = compatibilitySeed;
  assertWorldInvariants(state);
  return { definition, state, genesisDigest: sha256(state) };
}
