import type { DeploymentManifest } from "../deployment/model.ts";

export type ComparisonMode = "exact" | "descriptive-only";

export interface RunComparisonMetrics {
  runId: string;
  status: string;
  reason: string | null;
  score: number;
  revisions: number;
  minimumBattery: number;
  minimumOxygen: number;
  maximumReactorHeat: number;
  minimumActorHealth: Record<string, number>;
  minimumCrewHealth: Record<string, number>;
  objectiveCompletionOrder: string[];
  playerInterventions: number;
  providerFailures: number;
  providerMetrics: {
    calls: number | null;
    inputTokens: number | null;
    outputTokens: number | null;
    costUsd: number | null;
  };
  terminalItemOwners: Record<string, string[]>;
}

export interface RunComparison {
  schemaVersion: 1;
  kind: "ordivon.game.run-comparison";
  mode: ComparisonMode;
  compatibilityReasons: string[];
  left: { manifest: DeploymentManifest; metrics: RunComparisonMetrics };
  right: { manifest: DeploymentManifest; metrics: RunComparisonMetrics };
  inputDifferences: Array<{ field: string; left: unknown; right: unknown }>;
  metricDifferences: Array<{
    metric: string;
    left: number | string | null;
    right: number | string | null;
  }>;
  comparisonDigest: string;
}
