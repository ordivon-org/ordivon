import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import type { WorldCommand, WorldFact } from "../src/model.ts";
import { communicationsFirstPolicy, recoveryPolicy } from "../src/policies.ts";
import { resolveRuleset } from "../src/registry.ts";
import { initialWorld } from "../src/scenario.ts";
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

test("ruleset v2 preserves v1 state digests while enriching events", () => {
  const commands = readFileSync("fixtures/m1-v1/success.commands.jsonl", "utf8")
    .trim().split("\n").map((line) => JSON.parse(line) as WorldCommand);
  const v1 = resolveRuleset("station-zero-core", 1);
  const v2 = resolveRuleset("station-zero-core", 2);
  let stateV1 = initialWorld();
  let stateV2 = initialWorld();
  for (const command of commands) {
    const resultV1 = v1.apply(stateV1, command);
    const resultV2 = v2.apply(stateV2, command);
    assert.equal(resultV1.status, "accepted");
    assert.equal(resultV2.status, "accepted");
    if (resultV1.status !== "accepted" || resultV2.status !== "accepted") throw new Error("ruleset rejected fixture");
    assert.equal(resultV1.event.facts, undefined);
    assert.ok(resultV2.event.facts && resultV2.event.facts.length > 0);
    assert.equal(resultV2.event.verification?.success, true);
    stateV1 = resultV1.state;
    stateV2 = resultV2.state;
    assert.equal(sha256(stateV1), sha256(stateV2));
  }
});

test("a successful v2 Run emits action, environment, verification, and terminal facts", () => {
  const dir = mkdtempSync(join(tmpdir(), "ordivon-game-facts-"));
  try {
    const store = new GameStore(join(dir, "world.sqlite3"));
    assert.equal(store.getRun().rulesetVersion, 2);
    executePolicy(store, store.activeRunId, recoveryPolicy);
    const events = store.events();
    const facts = events.flatMap((event) => event.facts ?? []);
    const kinds = new Set(facts.map((fact) => fact.kind));
    for (const expected of [
      "agent_moved", "item_picked_up", "item_consumed", "system_repaired",
      "power_state_changed", "hull_breach_sealed", "crew_stabilized",
      "distress_signal_sent", "battery_consumed", "oxygen_changed",
      "reactor_heat_changed", "health_changed", "mission_succeeded",
    ] satisfies WorldFact["kind"][]) {
      assert.ok(kinds.has(expected), `missing fact kind: ${expected}`);
    }
    assert.ok(events.every((event) => event.verification?.success));
    assert.ok(events.every((event) => event.verification?.checks.every((check) => check.passed)));
    const repair = events.find((event) => event.commandKind === "repair_system");
    assert.ok(repair?.facts?.some((fact) => fact.kind === "system_repaired"));
    assert.ok(repair?.changes.some((change) => change.path.includes("systems") && change.path.endsWith("integrity")));
    store.close();
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

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
