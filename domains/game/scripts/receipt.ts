import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { communicationsFirstPolicy, recoveryPolicy, runPolicy } from "../src/policies.ts";
import { assertWorldInvariants, initialWorld } from "../src/scenario.ts";
import { GameStore } from "../src/storage.ts";
import { materializeAction } from "../src/world.ts";

const success = runPolicy(recoveryPolicy);
const failure = runPolicy(communicationsFirstPolicy);
assertWorldInvariants(success.state);
assertWorldInvariants(failure.state);

const directory = mkdtempSync(join(tmpdir(), "ordivon-game-m1-receipt-"));
const dbPath = join(directory, "world.sqlite3");
try {
  const store = new GameStore(dbPath);
  let state = store.loadState();
  let step = 0;
  const startedAt = performance.now();
  while (state.mission.status === "running") {
    const action = recoveryPolicy.choose(state);
    if (!action) throw new Error("recovery policy produced no action");
    const result = store.apply(materializeAction(action, `receipt:${step}:${action.actionId}`));
    if (result.result.status !== "accepted") throw new Error(result.result.reason);
    state = result.result.state;
    step += 1;
  }
  const executeMs = performance.now() - startedAt;
  store.close();

  const reopened = new GameStore(dbPath);
  const recovered = reopened.loadState();
  const recoveryStartedAt = performance.now();
  const recovery = reopened.recover();
  const recoveryMs = performance.now() - recoveryStartedAt;
  const replayStartedAt = performance.now();
  const replay = reopened.verifyReplay();
  const replayMs = performance.now() - replayStartedAt;
  const snapshotCount = reopened.snapshotCount();
  reopened.close();

  console.log(
    JSON.stringify(
      {
        node: process.version,
        platform: `${process.platform}/${process.arch}`,
        successfulPolicy: {
          status: success.state.mission.status,
          reason: success.state.mission.reason,
          turn: success.state.turn,
          digest: success.digest,
          batteryRemaining: success.state.resources.batteryCharge,
          oxygen: success.state.resources.oxygen,
          reactorHeat: success.state.resources.reactorHeat,
        },
        failingPolicy: {
          status: failure.state.mission.status,
          reason: failure.state.mission.reason,
          turn: failure.state.turn,
          digest: failure.digest,
        },
        persistedReplay: {
          recoveredDigest: recovery.digest,
          matchesPurePolicy: replay.digest === success.digest && recovery.digest === success.digest,
          recoveredStatus: recovered.mission.status,
          eventCount: replay.eventCount,
          snapshotCount,
          recoveryReplayedCommands: recovery.replayedCommandCount,
          verifyReplayedCommands: replay.replayedCommandCount,
          verified: replay.verified && recovery.verified,
          executeMs: Number(executeMs.toFixed(3)),
          recoveryMs: Number(recoveryMs.toFixed(3)),
          replayMs: Number(replayMs.toFixed(3)),
        },
      },
      null,
      2,
    ),
  );
} finally {
  rmSync(directory, { recursive: true, force: true });
}
