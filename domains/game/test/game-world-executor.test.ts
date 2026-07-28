import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { GameWorldExecutor } from "../src/host-contract/game-world-executor.ts";
import { GameStore } from "../src/storage.ts";
import { listAvailableActions, materializeAction } from "../src/world.ts";

function fixture(): { directory: string; game: GameStore } {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-world-executor-"));
  return { directory, game: new GameStore(join(directory, "world.sqlite3")) };
}

test("GameWorldExecutor observes a committed command after response loss without redelivery", () => {
  const { directory, game } = fixture();
  try {
    const state = game.loadState();
    const wait = listAvailableActions(state, "engineer-01").find((action) => action.actionId === "wait");
    assert.ok(wait);
    const command = materializeAction(wait, "executor-response-loss");
    let injected = false;
    const crashing = new GameWorldExecutor(game, {
      faultInjector(point) {
        if (!injected && point === "after_world_commit") {
          injected = true;
          throw new Error("injected:response-loss");
        }
      },
    });
    assert.throws(() => crashing.deliverCommand(command), /injected:response-loss/);
    assert.equal(injected, true);
    assert.equal(game.eventCount(), 1);

    const fresh = new GameWorldExecutor(game);
    const observation = fresh.observeCommand(command);
    assert.ok(observation);
    assert.equal(observation.status, "succeeded");
    assert.equal(observation.commandId, command.commandId);
    assert.equal(observation.commandSequence, 0);
    assert.equal(observation.verificationSuccess, true);
    assert.equal(game.eventCount(), 1);

    const duplicate = fresh.deliverCommand(command);
    assert.equal(duplicate.idempotent, true);
    assert.equal(duplicate.worldEventId, observation.worldEventId);
    assert.equal(game.eventCount(), 1);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("GameWorldExecutor observe is a pure lookup for an absent command", () => {
  const { directory, game } = fixture();
  try {
    const state = game.loadState();
    const wait = listAvailableActions(state, "engineer-01").find((action) => action.actionId === "wait");
    assert.ok(wait);
    const command = materializeAction(wait, "executor-absent");
    const executor = new GameWorldExecutor(game);
    assert.equal(executor.observeCommand(command), null);
    assert.equal(game.eventCount(), 0);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});


test("GameWorldExecutor delivers, observes, and rejects Team Ticks without hidden retries", () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-world-executor-team-"));
  const runId = "run:executor-team";
  const game = new GameStore(join(directory, "world.sqlite3"));
  game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
  game.setActiveRun(runId);
  try {
    const executor = new GameWorldExecutor(game);
    const state = game.loadState(runId);
    const actors = ["engineer-01", "medic-01", "security-01"];
    const intents = actors.map((actorId, index) => {
      const wait = listAvailableActions(state, actorId).find((action) => action.actionId === "wait");
      assert.ok(wait);
      return { commandSequence: index, command: materializeAction(wait, `executor-team-wait:${actorId}`) };
    });
    const batch = { tickId: "executor-team:0", expectedWorldRevision: 0, intents };
    assert.equal(executor.observeTeamTick(batch, runId), null);
    const delivered = executor.deliverTeamTick(batch, runId);
    assert.equal(delivered.status, "succeeded");
    assert.equal(delivered.verificationSuccess, true);
    assert.equal(delivered.commandId, "team-tick:executor-team:0");
    assert.equal(game.eventCount(runId), 1);
    const observed = executor.observeTeamTick(batch, runId);
    assert.ok(observed);
    assert.equal(observed.worldEventId, delivered.worldEventId);
    assert.equal(executor.deliverTeamTick(batch, runId).idempotent, true);
    assert.equal(game.eventCount(runId), 1);

    const stale = { ...batch, tickId: "executor-team:stale" };
    const rejected = executor.deliverTeamTick(stale, runId);
    assert.equal(rejected.status, "rejected");
    assert.equal(rejected.rejectionCode, "stale_revision");
    assert.match(rejected.reason ?? "", /revision/i);
    assert.equal(rejected.worldEventId, null);
    assert.equal(game.eventCount(runId), 1);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("GameWorldExecutor returns typed rejection for a stale primitive Command", () => {
  const { directory, game } = fixture();
  try {
    const executor = new GameWorldExecutor(game);
    const state = game.loadState();
    const wait = listAvailableActions(state, "engineer-01").find((action) => action.actionId === "wait");
    assert.ok(wait);
    const command = materializeAction(wait, "executor-stale-command");
    game.apply(materializeAction(wait, "executor-advance"));
    const rejected = executor.deliverCommand(command);
    assert.equal(rejected.status, "rejected");
    assert.equal(rejected.rejectionCode, "stale_revision");
    assert.equal(rejected.verificationSuccess, false);
    assert.equal(rejected.worldAfterDigest, null);
    assert.equal(game.eventCount(), 1);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});
