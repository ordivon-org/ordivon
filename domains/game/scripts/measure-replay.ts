import { performance } from "node:perf_hooks";
import { buildReplayReport } from "../src/replay/report.ts";
import { GameStore } from "../src/storage.ts";
import { TeamHost } from "../src/team/engine.ts";
import { FixtureTeamProvider } from "../src/team/providers.ts";

const runId = "run:measure:replay";
const store = new GameStore(":memory:");
try {
  store.createRun({
    runId,
    scenarioVersion: 2,
    scenarioCaseId: "baseline",
    rulesetVersion: 3,
  });
  await new TeamHost(store, new FixtureTeamProvider()).run(runId, 512);
  buildReplayReport(store, runId);
  const samples: number[] = [];
  for (let index = 0; index < 5; index += 1) {
    const startedAt = performance.now();
    buildReplayReport(store, runId);
    samples.push(performance.now() - startedAt);
  }
  samples.sort((left, right) => left - right);
  const medianMs = samples[2]!;
  const productTargetMs = 1500;
  const thresholdMs = Number(
    process.env.ORDIVON_REPLAY_REPORT_P50_MAX_MS ?? productTargetMs,
  );
  if (!Number.isFinite(thresholdMs) || thresholdMs <= 0) {
    throw new TypeError("ORDIVON_REPLAY_REPORT_P50_MAX_MS must be a positive number");
  }
  const result = {
    schemaVersion: 1,
    kind: "ordivon.game.replay-performance",
    revision: store.loadState(runId).revision,
    samplesMs: samples.map((value) => Number(value.toFixed(3))),
    medianMs: Number(medianMs.toFixed(3)),
    productTargetMs,
    productTargetPassed: medianMs <= productTargetMs,
    thresholdMs,
    runnerAllowanceMs: Math.max(0, thresholdMs - productTargetMs),
    passed: medianMs <= thresholdMs,
  };
  console.log(JSON.stringify(result, null, 2));
  if (!result.passed) process.exitCode = 1;
} finally {
  store.close();
}
