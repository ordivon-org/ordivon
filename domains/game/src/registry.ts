import type { ApplyResult, ApplyTickResult, TickBatch, WorldCommand, WorldState } from "./model.ts";
import { createScenarioCaseWorld, listScenarioCases } from "./scenario-cases.ts";
import { applyWorldCommand, applyWorldTick } from "./world.ts";

export const SCENARIO_ID = "station-zero";
export const SCENARIO_VERSION = 2;
export const RULESET_ID = "station-zero-core";
export const RULESET_VERSION = 3;

export class UnsupportedVersionError extends Error {
  readonly code: "unsupported_scenario_version" | "unknown_ruleset_version";
  constructor(code: UnsupportedVersionError["code"], message: string) {
    super(message);
    this.name = "UnsupportedVersionError";
    this.code = code;
  }
}

export interface ScenarioCreateInput { caseId?: string; seed?: string; }
export interface ScenarioDefinition {
  id: string; version: number; defaultCaseId: string; caseIds: string[];
  create(input?: ScenarioCreateInput | string): WorldState;
}
export interface RulesetDefinition {
  id: string; version: number;
  apply(state: WorldState, command: WorldCommand): ApplyResult;
  applyTick(state: WorldState, batch: TickBatch): ApplyTickResult;
}

const scenario: ScenarioDefinition = {
  id: SCENARIO_ID,
  version: SCENARIO_VERSION,
  defaultCaseId: "baseline",
  caseIds: listScenarioCases().map((entry) => entry.caseId),
  create(input = {}) {
    const normalized = typeof input === "string" ? { seed: input } : input;
    return createScenarioCaseWorld(
      SCENARIO_ID, SCENARIO_VERSION, normalized.caseId ?? "baseline", normalized.seed,
    ).state;
  },
};

const ruleset: RulesetDefinition = {
  id: RULESET_ID, version: RULESET_VERSION, apply: applyWorldCommand, applyTick: applyWorldTick,
};

export function resolveScenario(id: string, version: number): ScenarioDefinition {
  if (id !== SCENARIO_ID || version !== SCENARIO_VERSION) {
    throw new UnsupportedVersionError("unsupported_scenario_version", `unsupported scenario version: ${id}@${version}`);
  }
  return scenario;
}

export function resolveRuleset(id: string, version: number): RulesetDefinition {
  if (id !== RULESET_ID || version !== RULESET_VERSION) {
    throw new UnsupportedVersionError("unknown_ruleset_version", `unknown ruleset version: ${id}@${version}`);
  }
  return ruleset;
}

export function listScenarioContracts(): Array<{ id: string; version: number }> {
  return [{ id: SCENARIO_ID, version: SCENARIO_VERSION }];
}
export function listRulesetContracts(): Array<{ id: string; version: number }> {
  return [{ id: RULESET_ID, version: RULESET_VERSION }];
}
