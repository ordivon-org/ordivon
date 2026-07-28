import type { ApplyResult, ApplyTickResult, TickBatch, WorldCommand, WorldState } from "./model.ts";
import { createScenarioCaseWorld, listScenarioCases } from "./scenario-cases.ts";
import { applyWorldCommand, applyWorldCommandV2, applyWorldCommandV3, applyWorldTick, applyWorldTickV2, applyWorldTickV3 } from "./world.ts";

export class UnsupportedVersionError extends Error {
  readonly code: "unsupported_scenario_version" | "unknown_ruleset_version";

  constructor(code: UnsupportedVersionError["code"], message: string) {
    super(message);
    this.name = "UnsupportedVersionError";
    this.code = code;
  }
}

export interface ScenarioCreateInput {
  caseId?: string;
  seed?: string;
}

export interface ScenarioDefinition {
  id: string;
  version: number;
  defaultCaseId: string;
  caseIds: string[];
  create(input?: ScenarioCreateInput | string): WorldState;
}

export interface RulesetDefinition {
  id: string;
  version: number;
  apply(state: WorldState, command: WorldCommand): ApplyResult;
  applyTick(state: WorldState, batch: TickBatch): ApplyTickResult;
}

function scenario(id: string, version: number, defaultCaseId: string): ScenarioDefinition {
  return {
    id,
    version,
    defaultCaseId,
    caseIds: listScenarioCases(id, version).map((definition) => definition.caseId),
    create(input = {}) {
      const normalized = typeof input === "string" ? { seed: input } : input;
      return createScenarioCaseWorld(id, version, normalized.caseId ?? defaultCaseId, normalized.seed).state;
    },
  };
}

const scenarioV1 = scenario("station-zero", 1, "legacy-fixed");
const scenarioV2 = scenario("station-zero", 2, "baseline");

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
  const definition = scenarios.get(`${id}@${version}`);
  if (!definition) {
    throw new UnsupportedVersionError(
      "unsupported_scenario_version",
      `unsupported scenario version: ${id}@${version}`,
    );
  }
  return definition;
}

export function resolveRuleset(id: string, version: number): RulesetDefinition {
  const definition = rulesets.get(`${id}@${version}`);
  if (!definition) {
    throw new UnsupportedVersionError(
      "unknown_ruleset_version",
      `unknown ruleset version: ${id}@${version}`,
    );
  }
  return definition;
}

export function listScenarioContracts(): Array<{ id: string; version: number }> {
  return [...scenarios.values()].map(({ id, version }) => ({ id, version }));
}

export function listRulesetContracts(): Array<{ id: string; version: number }> {
  return [...rulesets.values()].map(({ id, version }) => ({ id, version }));
}
