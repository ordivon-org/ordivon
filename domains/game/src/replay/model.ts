import type { WorldState } from "../model.ts";

export interface PointInTimeReplayResult {
  runId: string;
  revision: number;
  state: WorldState;
  digest: string;
  snapshotRevision: number;
  replayedCommandCount: number;
  verified: true;
}
