import { writeSync } from "node:fs";
import { WebStore } from "../../src/store.ts";
import { commit } from "./effect-recovery.ts";

const [path, phase] = process.argv.slice(2);
if (path === undefined || (phase !== "before-commit" && phase !== "after-commit")) throw new Error("invalid fixture input");
const store = new WebStore(path);
const grant = store.getAgentGrant("grant:recovery");
const nativeExec = store.db.exec.bind(store.db);
Object.defineProperty(store.db, "exec", { value: (sql: string) => {
  if (sql === "COMMIT") {
    if (phase === "after-commit") nativeExec(sql);
    writeSync(1, "reached:" + phase + "\n");
    // The disposable child alone is terminated; no close or finally runs.
    process.kill(process.pid, "SIGKILL");
    throw new Error("unreachable");
  }
  nativeExec(sql);
}});
commit(store, grant, phase);
throw new Error("fixture failed to terminate");
