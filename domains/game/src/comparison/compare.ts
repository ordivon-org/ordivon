import { sha256 } from "../digest.ts";
import type { DeploymentManifest } from "../deployment/model.ts";
import { HostStore } from "../host/store.ts";
import { DeploymentStore } from "../deployment/store.ts";
import { scoreMission } from "../scoring.ts";
import type { GameStore } from "../storage.ts";
import { TEAM_OBJECTIVE_GRAPH, objectiveSatisfied } from "../team/objectives.ts";
import type { RunComparison, RunComparisonMetrics } from "./model.ts";

export class ComparisonError extends Error {
  readonly code = "comparison_incompatible";

  constructor(message: string) {
    super(message);
    this.name = "ComparisonError";
  }
}

export function comparisonCompatibility(
  left: DeploymentManifest,
  right: DeploymentManifest,
): { mode: "exact" | "descriptive-only"; reasons: string[] } {
  if (
    left.scenarioId !== right.scenarioId ||
    left.scenarioVersion !== right.scenarioVersion
  ) {
    throw new ComparisonError("Scenario contracts differ");
  }
  if (
    left.rulesetId !== right.rulesetId ||
    left.rulesetVersion !== right.rulesetVersion
  ) {
    throw new ComparisonError("Ruleset contracts differ");
  }
  if (left.evaluatedInputsDigest !== right.evaluatedInputsDigest) {
    throw new ComparisonError("Evaluated input contracts differ");
  }
  return left.scenarioCaseId === right.scenarioCaseId
    ? {
        mode: "exact",
        reasons: ["Scenario Case, ruleset, and evaluated inputs match."],
      }
    : {
        mode: "descriptive-only",
        reasons: ["Scenario Cases differ; output differences are descriptive only."],
      };
}

function metrics(store: GameStore, runId: string): RunComparisonMetrics {
  const terminal = store.loadState(runId);
  const states = Array.from(
    { length: terminal.revision + 1 },
    (_, revision) => store.stateAtRevision(revision, runId).state,
  );
  const objectiveCompletionOrder = TEAM_OBJECTIVE_GRAPH.nodes
    .flatMap((node) => {
      const revision = states.findIndex((state) =>
        objectiveSatisfied(state, node.objectiveId),
      );
      return revision < 0 ? [] : [{ id: node.objectiveId, revision }];
    })
    .sort((left, right) =>
      left.revision - right.revision || left.id.localeCompare(right.id),
    )
    .map((entry) => entry.id);
  const hostEventTypes = new HostStore(store.db).listEventTypes(runId);

  const terminalItemOwners: Record<string, string[]> = {};
  for (const itemId of Object.keys(terminal.resources.consumedItems).sort()) {
    terminalItemOwners[itemId] = Object.values(terminal.agents)
      .filter((actor) =>
        (actor.inventory[itemId as keyof typeof actor.inventory] ?? 0) > 0,
      )
      .map((actor) => actor.id)
      .sort();
  }

  return {
    runId,
    status: terminal.mission.status,
    reason: terminal.mission.reason,
    score: scoreMission(terminal).total,
    revisions: terminal.revision,
    minimumBattery: Math.min(...states.map((state) => state.resources.batteryCharge)),
    minimumOxygen: Math.min(...states.map((state) => state.resources.oxygen)),
    maximumReactorHeat: Math.max(...states.map((state) => state.resources.reactorHeat)),
    minimumActorHealth: Object.fromEntries(
      Object.keys(terminal.agents).sort().map((actorId) => [
        actorId,
        Math.min(...states.map((state) => state.agents[actorId]?.health ?? 0)),
      ]),
    ),
    minimumCrewHealth: Object.fromEntries(
      Object.keys(terminal.crew).sort().map((crewId) => [
        crewId,
        Math.min(...states.map((state) => state.crew[crewId]?.health ?? 0)),
      ]),
    ),
    objectiveCompletionOrder,
    playerInterventions: hostEventTypes.filter((eventType) =>
      /player|configuration-updated|task-provider-updated/.test(eventType),
    ).length,
    providerFailures: hostEventTypes.filter((eventType) =>
      /provider.*failed|provider-failed/.test(eventType),
    ).length,
    providerMetrics: {
      calls: null,
      inputTokens: null,
      outputTokens: null,
      costUsd: null,
    },
    terminalItemOwners,
  };
}

function inputDifferences(
  left: DeploymentManifest,
  right: DeploymentManifest,
): Array<{ field: string; left: unknown; right: unknown }> {
  const fields = [
    "scenarioCaseId",
    "coordinationProfileId",
    "authorityPolicyMode",
  ] as const;
  const output: Array<{ field: string; left: unknown; right: unknown }> = fields
    .filter((field) => JSON.stringify(left[field]) !== JSON.stringify(right[field]))
    .map((field) => ({ field, left: left[field], right: right[field] }));
  if (JSON.stringify(left.actors) !== JSON.stringify(right.actors)) {
    output.push({ field: "actors", left: left.actors, right: right.actors });
  }
  return output;
}

export function compareRuns(
  store: GameStore,
  leftRunId: string,
  rightRunId: string,
): RunComparison {
  if (leftRunId === rightRunId) {
    throw new TypeError("comparison requires two different Runs");
  }
  const deployments = new DeploymentStore(store);
  const leftManifest = deployments.get(leftRunId);
  const rightManifest = deployments.get(rightRunId);
  if (!leftManifest || !rightManifest) {
    throw new ComparisonError("Both Runs require retained Deployment Manifests");
  }

  const compatibility = comparisonCompatibility(leftManifest, rightManifest);
  const leftMetrics = metrics(store, leftRunId);
  const rightMetrics = metrics(store, rightRunId);
  const base = {
    schemaVersion: 1 as const,
    kind: "ordivon.game.run-comparison" as const,
    mode: compatibility.mode,
    compatibilityReasons: compatibility.reasons,
    left: { manifest: leftManifest, metrics: leftMetrics },
    right: { manifest: rightManifest, metrics: rightMetrics },
    inputDifferences: inputDifferences(leftManifest, rightManifest),
    metricDifferences: [
      { metric: "score", left: leftMetrics.score, right: rightMetrics.score },
      { metric: "revisions", left: leftMetrics.revisions, right: rightMetrics.revisions },
      {
        metric: "minimumBattery",
        left: leftMetrics.minimumBattery,
        right: rightMetrics.minimumBattery,
      },
      {
        metric: "minimumOxygen",
        left: leftMetrics.minimumOxygen,
        right: rightMetrics.minimumOxygen,
      },
      {
        metric: "maximumReactorHeat",
        left: leftMetrics.maximumReactorHeat,
        right: rightMetrics.maximumReactorHeat,
      },
      { metric: "status", left: leftMetrics.status, right: rightMetrics.status },
    ],
  };
  return { ...base, comparisonDigest: sha256(base) };
}
