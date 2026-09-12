import type { GameStore } from "../storage.ts";
import { diagnoseProjection } from "./diagnosis.ts";
import { replaySummaryFromGraph } from "./frames.ts";
import type { ReplayReport } from "./model.ts";
import { buildReplayProjection } from "./projection.ts";

export function buildReplayReport(
  store: GameStore,
  runId = store.activeRunId,
): ReplayReport {
  const projection = buildReplayProjection(store, runId);
  const terminal = projection.frames.at(-1)!.state;
  return {
    schemaVersion: 1,
    kind: "ordivon.game.replay-report",
    runId,
    summary: replaySummaryFromGraph(terminal, projection.graph),
    curves: projection.curves,
    keyTurns: projection.keyTurns,
    diagnosis: diagnoseProjection(store, projection),
  };
}
