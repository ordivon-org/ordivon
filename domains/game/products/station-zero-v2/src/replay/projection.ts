import type { JournalEvent } from "../model.ts";
import type { GameStore } from "../storage.ts";
import { replayCurvesFromFrames, replayKeyTurnsFromFrames } from "./analysis.ts";
import { buildRunEvidenceGraph } from "./evidence.ts";
import { buildReplayFrames } from "./frames.ts";
import type { ReplayProjection } from "./model.ts";
import { loadReplayTeamData } from "./team-data.ts";

export function buildReplayProjection(
  store: GameStore,
  runId = store.activeRunId,
): ReplayProjection {
  const replays = store.statesAtEveryRevision(runId);
  const terminal = replays.at(-1)!.state;
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
