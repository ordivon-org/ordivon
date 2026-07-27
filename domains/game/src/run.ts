import { randomUUID } from "node:crypto";

import type { MissionStatus, WorldState } from "./model.ts";

export const DEFAULT_RUN_ID = "run:default";
export const CURRENT_BUILD = "ordivon-game@0.1.0+m1.5";

export interface RunMetadata {
  runId: string;
  scenarioId: string;
  scenarioVersion: number;
  rulesetId: string;
  rulesetVersion: number;
  stateSchemaVersion: number;
  seed: string;
  status: MissionStatus;
  createdAt: string;
  createdWithBuild: string;
}

export interface CreateRunInput {
  runId?: string;
  scenarioId?: string;
  scenarioVersion?: number;
  rulesetId?: string;
  rulesetVersion?: number;
  seed?: string;
  createdWithBuild?: string;
  genesis?: WorldState;
}

export function newRunId(): string {
  return `run:${randomUUID()}`;
}
