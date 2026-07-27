import { resolve } from "node:path";

import { recoveryPolicy } from "../src/policies.ts";
import { GameStore } from "../src/storage.ts";
import { materializeAction } from "../src/world.ts";

const dbPath = resolve(process.cwd(), "data/station-zero.sqlite3");
const store = new GameStore(dbPath);
let state = store.loadState();
let step = store.eventCount();

while (state.mission.status === "running") {
  const action = recoveryPolicy.choose(state);
  if (!action) throw new Error("recovery policy produced no action");
  const result = store.apply(materializeAction(action, `demo:${step}:${action.actionId}`));
  if (result.result.status !== "accepted") {
    throw new Error(`${result.result.code}: ${result.result.reason}`);
  }
  state = result.result.state;
  step += 1;
}

const replay = store.replay();
store.close();
console.log(JSON.stringify({ dbPath, status: state.mission, turn: state.turn, digest: replay.digest, replay }, null, 2));
