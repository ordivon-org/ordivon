import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { AgentHost } from "../src/host/engine.ts";
import { RecoveryOperationProvider } from "../src/providers/fixture.ts";
import { GameStore } from "../src/storage.ts";
import { TeamHost } from "../src/team/engine.ts";
import { FixtureTeamProvider } from "../src/team/providers.ts";
import { validateHostWorkloadObject } from "../src/host-contract/validate.ts";
import type { VerificationReceipt } from "../src/host-contract/model.ts";

const WIRE_KINDS = new Set([
  "ordivon.host-task-descriptor",
  "ordivon.compiled-context-envelope",
  "ordivon.model-invocation-intent",
  "ordivon.model-decision",
  "ordivon.admitted-decision",
  "ordivon.dispatch-envelope",
  "ordivon.observation-envelope",
  "ordivon.verification-receipt",
  "ordivon.task-outcome",
]);

function count(entries: Array<{ contractKind: string }>, kind: string): number {
  return entries.filter((entry) => entry.contractKind === kind).length;
}

function validateWireEntries(entries: Array<{ contractKind: string; object: unknown }>): void {
  for (const entry of entries) {
    if (WIRE_KINDS.has(entry.contractKind)) validateHostWorkloadObject(entry.object);
  }
}

test("single-Actor execution writes one authoritative Host lifecycle per primitive World Effect", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-host-contract-single-"));
  const game = new GameStore(join(directory, "world.sqlite3"));
  try {
    const agent = new AgentHost(game, new RecoveryOperationProvider());
    const result = await agent.run(game.activeRunId, 256);
    assert.equal(result.projection.task.phase, "succeeded");
    assert.equal(result.worldDigest, "41d7bfd4c1b36f0a8e38533be7f7e9b48b1625608c76c5ced1ddd3d0952d02d2");

    agent.syncContract();
    const first = agent.contract.contracts.transcript(game.activeRunId);
    validateWireEntries(first);
    assert.equal(count(first, "ordivon.host-task-descriptor"), 25);
    assert.equal(count(first, "ordivon.compiled-context-envelope"), 0);
    assert.equal(count(first, "ordivon.model-invocation-intent"), 0);
    assert.equal(count(first, "ordivon.model-decision"), 0);
    assert.equal(count(first, "ordivon.admitted-decision"), 0);
    assert.equal(count(first, "ordivon.dispatch-envelope"), 25);
    assert.equal(count(first, "ordivon.observation-envelope"), 25);
    assert.equal(count(first, "ordivon.verification-receipt"), 25);
    assert.equal(count(first, "ordivon.task-outcome"), 25);
    assert.equal(game.db.prepare("SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?").get("host_tasks"), undefined);

    agent.syncContract();
    const second = agent.contract.contracts.transcript(game.activeRunId);
    assert.equal(second.length, first.length);
    assert.deepEqual(
      second.map((entry) => [entry.eventId, entry.contractDigest]),
      first.map((entry) => [entry.eventId, entry.contractDigest]),
    );
    assert.equal(game.verifyReplay().digest, result.worldDigest);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Team writes 18 authoritative joint Effect lifecycles with per-Actor results", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-host-contract-team-"));
  const runId = "run:host-contract-team";
  const game = new GameStore(join(directory, "world.sqlite3"));
  game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
  game.setActiveRun(runId);
  try {
    const team = new TeamHost(game, new FixtureTeamProvider());
    const result = await team.run(runId, 256);
    assert.equal(game.loadState(runId).mission.status, "victory");
    assert.equal(result.rounds.length, 18);
    assert.equal(result.worldDigest, "a8ef1f491c35720ed02e66f004ccd7f3466f78991dcafecd442ceae66b09ceb7");

    team.syncContract(runId);
    const first = team.contract.contracts.transcript(runId);
    validateWireEntries(first);
    assert.equal(count(first, "ordivon.host-task-descriptor"), 18);
    assert.equal(count(first, "ordivon.compiled-context-envelope"), 0);
    assert.equal(count(first, "ordivon.model-invocation-intent"), 0);
    assert.equal(count(first, "ordivon.model-decision"), 0);
    assert.equal(count(first, "ordivon.admitted-decision"), 0);
    assert.equal(count(first, "ordivon.goal-task-snapshot"), 0);
    assert.equal(count(first, "ordivon.game.team-tick-effect"), 0);
    assert.equal(count(first, "ordivon.dispatch-envelope"), 18);
    assert.equal(count(first, "ordivon.observation-envelope"), 18);
    assert.equal(count(first, "ordivon.verification-receipt"), 18);
    assert.equal(count(first, "ordivon.task-outcome"), 18);
    for (const table of ["team_goals", "team_tasks", "team_task_leases", "team_context_refs", "team_effects", "team_dispatches", "team_observations"]) {
      const row = game.db.prepare("SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?").get(table) as { name?: string } | undefined;
      assert.equal(row, undefined, table);
    }

    const verifications = first
      .filter((entry) => entry.contractKind === "ordivon.verification-receipt")
      .map((entry) => entry.object as unknown as VerificationReceipt);
    assert.equal(verifications.length, 18);
    assert.ok(verifications.every((receipt) => receipt.accepted));
    assert.ok(verifications.every((receipt) => receipt.resultItems.length === 3));
    assert.ok(verifications.every((receipt) => new Set(receipt.resultItems.map((item) => item.subjectRef)).size === 3));

    team.syncContract(runId);
    const second = team.contract.contracts.transcript(runId);
    assert.equal(second.length, first.length);
    assert.deepEqual(
      second.map((entry) => [entry.eventId, entry.contractDigest]),
      first.map((entry) => [entry.eventId, entry.contractDigest]),
    );
    assert.equal(game.verifyReplay(runId).digest, result.worldDigest);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});


test("fresh TeamHost rebuilds one contract transcript after World commit response loss", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-host-contract-recovery-"));
  const database = join(directory, "world.sqlite3");
  const runId = "run:host-contract-recovery";
  const game = new GameStore(database);
  game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
  game.setActiveRun(runId);
  let injected = false;
  try {
    const provider = new FixtureTeamProvider();
    const crashing = new TeamHost(game, provider, {
      faultInjector(point) {
        if (!injected && point === "after_world_apply") {
          injected = true;
          throw new Error("injected:after_world_apply");
        }
      },
    });
    for (let index = 0; index < 16 && !injected; index += 1) {
      try {
        await crashing.step(runId);
      } catch (error) {
        assert.match(String(error), /injected:after_world_apply/);
      }
    }
    assert.equal(injected, true);
    assert.equal(game.eventCount(runId), 1);
    game.close();

    const reopened = new GameStore(database, { activeRunId: runId });
    try {
      const fresh = new TeamHost(reopened, provider);
      const result = await fresh.run(runId, 256);
      assert.equal(result.worldDigest, "a8ef1f491c35720ed02e66f004ccd7f3466f78991dcafecd442ceae66b09ceb7");
      assert.equal(reopened.eventCount(runId), 18);
      fresh.syncContract(runId);
      const transcript = fresh.contract.contracts.transcript(runId);
      validateWireEntries(transcript);
      assert.equal(count(transcript, "ordivon.dispatch-envelope"), 18);
      assert.equal(count(transcript, "ordivon.observation-envelope"), 18);
      assert.equal(count(transcript, "ordivon.verification-receipt"), 18);
      assert.equal(new Set(
        transcript
          .filter((entry) => entry.contractKind === "ordivon.dispatch-envelope")
          .map((entry) => entry.contractDigest),
      ).size, 18);
      assert.equal(reopened.verifyReplay(runId).digest, result.worldDigest);
    } finally {
      reopened.close();
    }
  } finally {
    try { game.close(); } catch {}
    rmSync(directory, { recursive: true, force: true });
  }
});
