import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { HostStore, HostStoreError } from "../src/host/store.ts";
import { newAttemptId, type AgentAttempt } from "../src/host/model.ts";
import { GameStore } from "../src/storage.ts";

function withStores(run: (game: GameStore, host: HostStore) => void): void {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-host-store-"));
  try {
    const game = new GameStore(join(directory, "world.sqlite3"));
    try { run(game, new HostStore(game.db)); }
    finally { game.close(); }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

test("Host initialization is durable and idempotent", () => {
  withStores((game, host) => {
    const first = host.initializeRun(game.getRun(), game.loadState(), ["codex", "hermes"]);
    const second = host.initializeRun(game.getRun(), game.loadState(), ["fixture"]);
    assert.deepEqual(second, first);
    assert.equal(first.goal.status, "active");
    assert.equal(first.task.phase, "ready");
    assert.deepEqual(first.task.providerOrder, ["codex", "hermes"]);
    assert.deepEqual(host.listJournal(game.activeRunId).map((event) => event.eventType), [
      "goal_created", "task_created",
    ]);
    host.verifyJournal(game.activeRunId);
  });
});

test("Host projections isolate Runs and reuse no cognitive identity", () => {
  withStores((game, host) => {
    const secondRun = game.createRun({ runId: "run:second" });
    const first = host.initializeRun(game.getRun("run:default"), game.loadState("run:default"), ["codex"]);
    const second = host.initializeRun(secondRun, game.loadState("run:second"), ["hermes"]);
    assert.notEqual(first.goal.goalId, second.goal.goalId);
    assert.notEqual(first.task.taskId, second.task.taskId);
    assert.deepEqual(host.getTask("run:default").providerOrder, ["codex"]);
    assert.deepEqual(host.getTask("run:second").providerOrder, ["hermes"]);
    assert.equal(host.listJournal("run:default").length, 2);
    assert.equal(host.listJournal("run:second").length, 2);
  });
});

test("Host Artifacts are content addressed and detect mutation", () => {
  withStores((game, host) => {
    host.initializeRun(game.getRun(), game.loadState());
    const first = host.putArtifact("agent-context", { revision: 0, allowed: ["repair:cooling"] });
    const duplicate = host.putArtifact("agent-context", { allowed: ["repair:cooling"], revision: 0 });
    assert.equal(duplicate.digest, first.digest);
    assert.deepEqual(host.getArtifact(first.digest).content, first.content);
    game.db.prepare("UPDATE host_artifacts SET content_json = ? WHERE digest = ?")
      .run('{"revision":1}', first.digest);
    assert.throws(
      () => host.getArtifact(first.digest),
      (error) => error instanceof HostStoreError && error.code === "host_corrupt",
    );
  });
});

test("Attempts survive a fresh HostStore process", () => {
  withStores((game, host) => {
    const projection = host.initializeRun(game.getRun(), game.loadState());
    const now = new Date().toISOString();
    const attempt: AgentAttempt = {
      attemptId: newAttemptId(game.activeRunId),
      taskId: projection.task.taskId,
      runId: game.activeRunId,
      attemptNumber: 1,
      revision: 1,
      status: "context_pending",
      providerId: null,
      contextDigest: null,
      decisionDigest: null,
      operationCandidateId: null,
      skillStepIndex: 0,
      skillStepCount: 0,
      blocker: null,
      createdAt: now,
      updatedAt: now,
    };
    host.createAttempt(attempt);
    const fresh = new HostStore(game.db);
    assert.deepEqual(fresh.getAttempt(attempt.attemptId), attempt);
    assert.equal(fresh.listAttempts(game.activeRunId).length, 1);
    fresh.verifyJournal(game.activeRunId);
  });
});

test("Host Journal rejects tampering and conflicting Event identity", () => {
  withStores((game, host) => {
    host.initializeRun(game.getRun(), game.loadState());
    host.appendEvent(game.activeRunId, "test_event", "host-event:test", { value: 1 });
    assert.throws(
      () => host.appendEvent(game.activeRunId, "test_event", "host-event:test", { value: 2 }),
      (error) => error instanceof HostStoreError && error.code === "host_constraint",
    );
    game.db.prepare("UPDATE host_journal SET payload_json = ? WHERE event_id = ?")
      .run('{"value":9}', "host-event:test");
    assert.throws(
      () => host.verifyJournal(game.activeRunId),
      (error) => error instanceof HostStoreError && error.code === "host_corrupt",
    );
  });
});

test("terminal mappings and terminal Host initialization are explicit", () => {
  withStores((game, host) => {
    const victory = structuredClone(game.loadState());
    victory.mission.status = "victory";
    victory.mission.reason = "rescue_signal_verified";
    const projection = host.initializeRun(game.getRun(), victory);
    assert.equal(projection.goal.status, "succeeded");
    assert.equal(projection.task.phase, "succeeded");
  });
  withStores((game, host) => {
    const failure = structuredClone(game.loadState());
    failure.mission.status = "failure";
    failure.mission.reason = "reactor_meltdown";
    const projection = host.initializeRun(game.getRun(), failure);
    assert.equal(projection.goal.status, "failed");
    assert.equal(projection.task.phase, "failed");
  });
});

test("Goal, Task, and Attempt projection revisions persist with journal evidence", () => {
  withStores((game, host) => {
    const projection = host.initializeRun(game.getRun(), game.loadState());
    const now = new Date().toISOString();
    const goal = { ...projection.goal, revision: 2, updatedAt: now };
    host.saveGoal(goal, "goal_reviewed", "host-event:goal-reviewed", { revision: 2 });
    const task = { ...projection.task, phase: "active" as const, revision: 2, updatedAt: now };
    host.saveTask(task, "task_activated", "host-event:task-active", { revision: 2 });
    const attempt: AgentAttempt = {
      attemptId: newAttemptId(game.activeRunId), taskId: task.taskId, runId: game.activeRunId,
      attemptNumber: 1, revision: 1, status: "context_pending", providerId: null,
      contextDigest: null, decisionDigest: null, operationCandidateId: null,
      skillStepIndex: 0, skillStepCount: 0, blocker: null, createdAt: now, updatedAt: now,
    };
    host.createAttempt(attempt);
    const updated = { ...attempt, revision: 2, status: "provider_pending" as const, updatedAt: new Date().toISOString() };
    host.saveAttempt(updated, "provider_invocation_started", "host-event:provider-start", { provider: "codex" });
    assert.equal(host.getGoal(game.activeRunId).revision, 2);
    assert.equal(host.getTask(game.activeRunId).phase, "active");
    assert.equal(host.getAttempt(attempt.attemptId).status, "provider_pending");
    assert.deepEqual(host.listJournal(game.activeRunId).map((event) => event.eventType), [
      "goal_created", "task_created", "goal_reviewed", "task_activated",
      "attempt_created", "provider_invocation_started",
    ]);
    host.verifyJournal(game.activeRunId);
  });
});

test("Host error and idempotency branches fail closed", () => {
  withStores((game, host) => {
    assert.throws(() => host.getGoal(game.activeRunId), /not initialized/);
    assert.throws(() => host.getTask(game.activeRunId), /not initialized/);
    assert.throws(() => host.getAttempt("attempt:missing"), /unknown Host Attempt/);
    assert.throws(() => host.getArtifact("missing"), /unknown Host Artifact/);
    assert.throws(() => host.putArtifact(" ", {}), /artifact kind/);
    assert.throws(() => host.appendEvent("run:missing", "test", "event", {}), /unknown run/);

    host.initializeRun(game.getRun(), game.loadState());
    const artifact = host.putArtifact("context", { value: 1 });
    game.db.prepare("UPDATE host_artifacts SET kind = ? WHERE digest = ?").run("tampered", artifact.digest);
    assert.throws(
      () => host.putArtifact("context", { value: 1 }),
      (error) => error instanceof HostStoreError && error.code === "host_corrupt",
    );

    const first = host.appendEvent(game.activeRunId, "test", "host-event:idempotent", { value: 1 });
    const duplicate = host.appendEvent(game.activeRunId, "test", "host-event:idempotent", { value: 1 });
    assert.equal(duplicate.recordDigest, first.recordDigest);
  });
});

test("Host Journal detects missing and relinked records", () => {
  withStores((game, host) => {
    host.initializeRun(game.getRun(), game.loadState());
    game.db.prepare("DELETE FROM host_journal WHERE sequence = 0").run();
    assert.throws(
      () => host.verifyJournal(game.activeRunId),
      (error) => error instanceof HostStoreError && error.code === "host_corrupt",
    );
  });
  withStores((game, host) => {
    host.initializeRun(game.getRun(), game.loadState());
    game.db.prepare("UPDATE host_journal SET previous_digest = ? WHERE sequence = 1").run("wrong");
    assert.throws(
      () => host.verifyJournal(game.activeRunId),
      (error) => error instanceof HostStoreError && error.code === "host_corrupt",
    );
  });
});
