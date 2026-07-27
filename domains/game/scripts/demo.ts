import { resolve } from "node:path";

import { sha256 } from "../src/digest.ts";
import { GameStore } from "../src/storage.ts";

const dbPath = resolve(process.cwd(), "data/station-zero.sqlite3");
const store = new GameStore(dbPath);
const before = store.loadState();
const applied = store.apply({
  kind: "restore_power",
  commandId: "m0-demo-restore-power",
  actorId: "engineer-01",
  targetId: "life-support",
  expectedRevision: 0,
});
store.close();

const recoveredStore = new GameStore(dbPath);
const recovered = recoveredStore.loadState();
const replay = recoveredStore.replay();
recoveredStore.close();

console.log(
  JSON.stringify(
    {
      dbPath,
      beforeDigest: sha256(before),
      applyStatus: applied.result.status,
      idempotent: applied.idempotent,
      recoveredDigest: sha256(recovered),
      replay,
    },
    null,
    2,
  ),
);
