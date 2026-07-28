import { randomUUID } from "node:crypto";

import type { MissionStatus, WorldState } from "./model.ts";
import { currentPackageIdentity } from "./release/inputs.ts";

export const DEFAULT_RUN_ID = "run:default";
export const CURRENT_BUILD = currentPackageIdentity();

export interface RunMetadata {
  runId: string;
  scenarioId: string;
  scenarioVersion: number;
  scenarioCaseId: string;
  rulesetId: string;
  rulesetVersion: number;
  stateSchemaVersion: number;
  seed: string;
  genesisDigest: string;
  evaluatedInputsDigest: string;
  status: MissionStatus;
  createdAt: string;
  createdWithBuild: string;
}

export interface CreateRunInput {
  runId?: string;
  scenarioId?: string;
  scenarioVersion?: number;
  scenarioCaseId?: string;
  rulesetId?: string;
  rulesetVersion?: number;
  seed?: string;
  evaluatedInputsDigest?: string;
  createdWithBuild?: string;
  genesis?: WorldState;
}

export function newRunId(): string {
  return `run:${randomUUID()}`;
}
