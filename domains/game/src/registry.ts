import type { ApplyResult, ApplyTickResult, TickBatch, WorldCommand, WorldState } from "./model.ts";
import { initialTeamWorld, initialWorld } from "./scenario.ts";
import { applyWorldCommand, applyWorldCommandV2, applyWorldCommandV3, applyWorldTick, applyWorldTickV2, applyWorldTickV3 } from "./world.ts";

export class UnsupportedVersionError extends Error {
  readonly code: "unsupported_scenario_version" | "unknown_ruleset_version";

  constructor(code: UnsupportedVersionError["code"], message: string) {
    super(message);
    this.name = "UnsupportedVersionError";
    this.code = code;
  }
}

export interface ScenarioDefinition {
  id: string;
  version: number;
  create(seed?: string): WorldState;
}

export interface RulesetDefinition {
  id: string;
  version: number;
  apply(state: WorldState, command: WorldCommand): ApplyResult;
  applyTick(state: WorldState, batch: TickBatch): ApplyTickResult;
}

const scenarioV1: ScenarioDefinition = {
  id: "station-zero",
  version: 1,
  create(seed) {
    const state = initialWorld();
    if (seed) state.seed = seed;
    return state;
  },
};

const scenarioV2: ScenarioDefinition = {
  id: "station-zero",
  version: 2,
  create(seed) {
    const state = initialTeamWorld();
    if (seed) state.seed = seed;
    return state;
  },
};

const rulesetV1: RulesetDefinition = {
  id: "station-zero-core",
  version: 1,
  apply: applyWorldCommand,
  applyTick: applyWorldTick,
};


const rulesetV2: RulesetDefinition = {
  id: "station-zero-core",
  version: 2,
  apply: applyWorldCommandV2,
  applyTick: applyWorldTickV2,
};

const rulesetV3: RulesetDefinition = {
  id: "station-zero-core",
  version: 3,
  apply: applyWorldCommandV3,
  applyTick: applyWorldTickV3,
};

const scenarios = new Map([
  [`${scenarioV1.id}@${scenarioV1.version}`, scenarioV1],
  [`${scenarioV2.id}@${scenarioV2.version}`, scenarioV2],
]);
const rulesets = new Map([
  [`${rulesetV1.id}@${rulesetV1.version}`, rulesetV1],
  [`${rulesetV2.id}@${rulesetV2.version}`, rulesetV2],
  [`${rulesetV3.id}@${rulesetV3.version}`, rulesetV3],
]);

export function resolveScenario(id: string, version: number): ScenarioDefinition {
  const scenario = scenarios.get(`${id}@${version}`);
  if (!scenario) {
    throw new UnsupportedVersionError(
      "unsupported_scenario_version",
      `unsupported scenario version: ${id}@${version}`,
    );
  }
  return scenario;
}

export function resolveRuleset(id: string, version: number): RulesetDefinition {
  const ruleset = rulesets.get(`${id}@${version}`);
  if (!ruleset) {
    throw new UnsupportedVersionError(
      "unknown_ruleset_version",
      `unknown ruleset version: ${id}@${version}`,
    );
  }
  return ruleset;
}
