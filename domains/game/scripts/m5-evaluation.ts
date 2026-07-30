import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { compareRuns } from "../src/comparison/compare.ts";
import { MissionControlService, type MissionProviderFactory } from "../src/mission-control/service.ts";
import type { M5Evaluation, M5EvaluationRun } from "../src/release/artifact.ts";
import { createEvaluatedInputManifest } from "../src/release/inputs.ts";
import { buildReplayReport } from "../src/replay/report.ts";
import { listRulesetContracts, listScenarioContracts } from "../src/registry.ts";
import { scoreMission } from "../src/scoring.ts";
import { GameStore } from "../src/storage.ts";
import { FixtureTeamProvider } from "../src/team/providers.ts";

const factory: MissionProviderFactory = (_name, options) =>
  new FixtureTeamProvider({
    breachStrategy: options?.coordinationProfileId === "engineer-seal"
      ? "engineer-seal"
      : "security-contain",
  });

async function finish(service: MissionControlService, runId: string): Promise<void> {
  for (let round = 0; round < 30 && service.state(runId).run.status === "running"; round += 1) {
    const review = await service.advance(runId, "proposal-review");
    if (review.boundary === "terminal") break;
    await service.advance(runId, "tick-verified");
  }
  if (service.state(runId).run.status === "running") {
    throw new Error(`M5 evaluation exceeded 30 Rounds: ${runId}`);
  }
}

function evaluationRun(
  store: GameStore,
  runId: string,
  coordinationProfileId: string,
): M5EvaluationRun {
  const report = buildReplayReport(store, runId);
  const classCounts = Object.fromEntries(
    ["VERIFIED_DIRECT", "VERIFIED_CONTRIBUTOR", "COUNTERFACTUAL_SENSITIVE", "CONTEXT_ONLY"]
      .map((evidenceClass) => [
        evidenceClass,
        report.diagnosis.claims.filter((claim) => claim.evidenceClass === evidenceClass).length,
      ]),
  );
  return {
    runId,
    coordinationProfileId,
    status: report.diagnosis.terminal.status,
    reason: report.diagnosis.terminal.reason,
    revision: report.diagnosis.terminal.revision,
    score: scoreMission(store.loadState(runId)).total,
    graphDigest: report.summary.graphDigest,
    curvesDigest: report.curves.curvesDigest,
    diagnosisDigest: report.diagnosis.diagnosisDigest,
    frameCount: report.summary.frameCount,
    keyTurnCount: report.keyTurns.length,
    evidenceClassCounts: classCounts,
  };
}

export async function createM5Evaluation(input: {
  sourceCommit: string;
  sourceTree: string;
  evaluatedInputsDigest: string;
}): Promise<M5Evaluation> {
  const store = new GameStore(":memory:");
  const service = new MissionControlService(store, factory);
  const shortRunId = "run:m5-release:specialist-containment";
  const longRunId = "run:m5-release:engineer-seal";
  try {
    service.initialize({
      runId: shortRunId,
      scenarioCaseId: "power-constrained",
      coordinationProfileId: "specialist-containment",
    });
    service.initialize({
      runId: longRunId,
      scenarioCaseId: "power-constrained",
      coordinationProfileId: "engineer-seal",
    });
    await finish(service, shortRunId);
    await finish(service, longRunId);
    const comparison = compareRuns(store, shortRunId, longRunId);
    const left = evaluationRun(store, shortRunId, "specialist-containment");
    const right = evaluationRun(store, longRunId, "engineer-seal");
    return {
      schemaVersion: 1,
      kind: "ordivon.game.m5-evaluation",
      sourceCommit: input.sourceCommit,
      sourceTree: input.sourceTree,
      evaluatedInputsDigest: input.evaluatedInputsDigest,
      runs: { specialistContainment: left, engineerSeal: right },
      comparison: {
        mode: "exact",
        comparisonDigest: comparison.comparisonDigest,
        inputDifferenceFields: comparison.inputDifferences.map((difference) => difference.field),
        statusChanged: left.status !== right.status,
        scoreDelta: left.score - right.score,
        minimumBatteryDelta:
          comparison.left.metrics.minimumBattery - comparison.right.metrics.minimumBattery,
      },
      browserJourney: {
        command: "pnpm e2e",
        expectedFirstOutcome: "victory",
        expectedSecondOutcome: "power_exhausted",
        replayRevision: 5,
        diagnosisEvidenceClass: "VERIFIED_DIRECT",
        comparisonMode: "exact",
        reloadRecoveryRequired: true,
      },
      conclusions: {
        deterministicFixtureReleasePathPassed:
          left.status === "victory" && right.reason === "power_exhausted",
        replayDiagnosisPassed:
          left.frameCount > 1 && (left.evidenceClassCounts.VERIFIED_DIRECT ?? 0) > 0,
        coordinationOnlyOutcomeDifferencePassed:
          comparison.mode === "exact" &&
          comparison.inputDifferences.length === 1 &&
          comparison.inputDifferences[0]?.field === "coordinationProfileId",
        runtimeDependenciesAdded: false,
        liveProvidersReleaseBlocking: false,
      },
    };
  } finally {
    store.close();
  }
}

function git(argument: string): string {
  return execFileSync("git", ["rev-parse", argument], { encoding: "utf8" }).trim();
}

async function main(): Promise<void> {
  const sourceCommit = git("HEAD^{commit}");
  const sourceTree = git("HEAD^{tree}");
  const inputs = createEvaluatedInputManifest({
    scenarioContracts: listScenarioContracts(),
    rulesetContracts: listRulesetContracts(),
    sourceCommit,
    sourceTree,
  });
  const evaluation = await createM5Evaluation({
    sourceCommit,
    sourceTree,
    evaluatedInputsDigest: inputs.evaluatedInputsDigest,
  });
  const text = JSON.stringify(evaluation, null, 2) + "\n";
  const outputIndex = process.argv.indexOf("--out");
  if (outputIndex >= 0) {
    const path = process.argv[outputIndex + 1];
    if (!path?.trim()) throw new TypeError("--out requires a file path");
    writeFileSync(resolve(path), text);
  }
  process.stdout.write(text);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main();
}
