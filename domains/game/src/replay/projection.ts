import type { JournalEvent } from "../model.ts";
import type { GameStore } from "../storage.ts";
import { replayCurvesFromFrames, replayKeyTurnsFromFrames } from "./analysis.ts";
import { buildRunEvidenceGraph } from "./evidence.ts";
import { buildReplayFrames } from "./frames.ts";
import type { PointInTimeReplayResult, ReplayProjection } from "./model.ts";
import { loadReplayTeamData } from "./team-data.ts";

function replayStates(
  store: GameStore,
  runId: string,
  terminalRevision: number,
): PointInTimeReplayResult[] {
  return Array.from(
    { length: terminalRevision + 1 },
    (_, revision) => store.stateAtRevision(revision, runId),
  );
}

export function buildReplayProjection(
  store: GameStore,
  runId = store.activeRunId,
): ReplayProjection {
  const terminal = store.loadState(runId);
  const replays = replayStates(store, runId, terminal.revision);
  const journal: JournalEvent[] = store.journalEvents(runId);
  const teamData = loadReplayTeamData(store, runId);
  const graph = buildRunEvidenceGraph(store, runId, {
    terminal,
    replays,
    journal,
    teamData,
  });
  const frames = buildReplayFrames(store, runId, graph, replays, journal, teamData);
  const curves = replayCurvesFromFrames(runId, graph, frames);
  const keyTurns = replayKeyTurnsFromFrames(runId, curves, frames);
  return {
    schemaVersion: 1,
    kind: "ordivon.game.replay-projection",
    runId,
    graph,
    frames,
    curves,
    keyTurns,
  };
}
