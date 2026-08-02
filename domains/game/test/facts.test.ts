import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import type { WorldCommand, WorldFact } from "../src/model.ts";
import { communicationsFirstPolicy, recoveryPolicy } from "./support/world-policies.ts";
import { resolveRuleset } from "../src/registry.ts";
import { initialTeamWorld } from "../src/scenario.ts";
import { GameStore } from "../src/storage.ts";
import { materializeAction } from "../src/world.ts";

function executePolicy(store: GameStore, runId: string, policy: typeof recoveryPolicy): void {
  let state = store.loadState(runId);
  let step = 0;
  while (state.mission.status === "running") {
    const action = policy.choose(state);
    assert.ok(action);
    const result = store.apply(materializeAction(action, `facts:${runId}:${step}:${action.actionId}`), runId);
    if (result.result.status !== "accepted") throw new Error(`${result.result.code}: ${result.result.reason}`);
    state = result.result.state;
    step += 1;
  }
}

test("failure and wait produce explicit facts", () => {
  const dir = mkdtempSync(join(tmpdir(), "ordivon-game-failure-facts-"));
  try {
    const store = new GameStore(join(dir, "world.sqlite3"));
    executePolicy(store, store.activeRunId, communicationsFirstPolicy);
    const facts = store.events().flatMap((event) => event.facts ?? []);
    assert.ok(facts.some((fact) => fact.kind === "agent_waited"));
    assert.ok(facts.some((fact) => fact.kind === "mission_failed" && fact.reason === "reactor_meltdown"));
    store.close();
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
