import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { recoveryPolicy } from "../src/policies.ts";
import { UnsupportedVersionError } from "../src/registry.ts";
import { GameStore } from "../src/storage.ts";
import { materializeAction } from "../src/world.ts";

function withStore(run: (store: GameStore) => void): void {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-runs-"));
  try {
    const store = new GameStore(join(directory, "world.sqlite3"));
    try {
      run(store);
    } finally {
      store.close();
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

test("one database isolates multiple version-bound runs", () => {
  withStore((store) => {
    const second = store.createRun({ runId: "run:failure", seed: "station-zero-fixed-seed-02" });
    assert.equal(store.listRuns().length, 2);
    assert.equal(second.scenarioVersion, 1);
    assert.equal(second.rulesetVersion, 2);

    const firstState = store.loadState("run:default");
    const secondState = store.loadState("run:failure");
    const firstAction = recoveryPolicy.choose(firstState);
    const secondAction = recoveryPolicy.choose(secondState);
    assert.ok(firstAction);
    assert.ok(secondAction);

    const sharedCommandId = "shared-command-id";
    const first = store.apply(materializeAction(firstAction, sharedCommandId), "run:default");
    const secondResult = store.apply(materializeAction(secondAction, sharedCommandId), "run:failure");
    assert.equal(first.result.status, "accepted");
    assert.equal(secondResult.result.status, "accepted");
    assert.equal(store.eventCount("run:default"), 1);
    assert.equal(store.eventCount("run:failure"), 1);
    assert.equal(store.loadState("run:default").revision, 1);
    assert.equal(store.loadState("run:failure").revision, 1);
  });
});

test("unknown scenario and ruleset versions fail closed", () => {
  withStore((store) => {
    assert.throws(
      () => store.createRun({ scenarioVersion: 999 }),
      (error) => error instanceof UnsupportedVersionError && error.code === "unsupported_scenario_version",
    );
    assert.throws(
      () => store.createRun({ rulesetVersion: 999 }),
      (error) => error instanceof UnsupportedVersionError && error.code === "unknown_ruleset_version",
    );
  });
});
