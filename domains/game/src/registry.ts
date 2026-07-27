import type { ApplyResult, WorldCommand, WorldState } from "./model.ts";
import { initialWorld } from "./scenario.ts";
import { applyWorldCommand } from "./world.ts";

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

const rulesetV1: RulesetDefinition = {
  id: "station-zero-core",
  version: 1,
  apply: applyWorldCommand,
};

const scenarios = new Map([[`${scenarioV1.id}@${scenarioV1.version}`, scenarioV1]]);
const rulesets = new Map([[`${rulesetV1.id}@${rulesetV1.version}`, rulesetV1]]);

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
