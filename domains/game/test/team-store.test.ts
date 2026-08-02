import assert from "node:assert/strict";
import test from "node:test";

import type { PrimitiveWorldCommand } from "../src/model.ts";
import { ENGINEER_ID, MEDIC_ID, SECURITY_ID } from "../src/scenario.ts";
import { GameStore } from "../src/storage.ts";
import { actorTaskId, TeamStore, TeamStoreError } from "../src/team/store.ts";
import { listAvailableActions, materializeAction } from "../src/world.ts";

function setup(runId = "run:team-store"): { game: GameStore; team: TeamStore } {
  const game = new GameStore(":memory:");
  game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
  game.setActiveRun(runId);
  const team = new TeamStore(game);
  team.initialize(runId);
  return { game, team };
}

function action(game: GameStore, actorId: string, actionId: string, commandId: string): PrimitiveWorldCommand {
  const state = game.loadState();
  const candidate = listAvailableActions(state, actorId).find((entry) => entry.actionId === actionId);
  assert.ok(candidate, `${actorId} missing ${actionId}`);
  const command = materializeAction(candidate, commandId);
  if (command.kind === "team_tick") throw new Error("unexpected team command");
  return command;
}

test("TeamStore initializes one Goal, three Actor Tasks, and one Coordinator Task", () => {
  const { game, team } = setup();
  const projection = team.projection();
  assert.equal(projection.goal.status, "active");
  assert.equal(projection.profiles.length, 3);
  assert.deepEqual(projection.profiles.map((profile) => profile.actorId).sort(), [ENGINEER_ID, MEDIC_ID, SECURITY_ID]);
  assert.equal(projection.tasks.length, 4);
  assert.equal(projection.objectives.rootObjectiveId, "verified-rescue");
  assert.ok(projection.objectiveStatus.some((status) => status.objectiveId === "crew-stabilized" && !status.satisfied));
  team.verify();
  assert.equal(team.initialize().tasks.length, 4);
  game.close();
});

test("Task transitions use revision CAS and short exclusive leases", () => {
  const { game, team } = setup("run:team-lease");
  const taskId = actorTaskId(game.activeRunId, ENGINEER_ID);
  const lease = team.acquireLease(taskId, "host:a", 1_000, 500);
  assert.equal(lease.revision, 1);
  assert.throws(() => team.acquireLease(taskId, "host:b", 1_100, 500), (error: unknown) => error instanceof TeamStoreError && error.code === "team_lease_held");
  const renewed = team.acquireLease(taskId, "host:a", 1_200, 500);
  assert.equal(renewed.revision, 2);
  assert.throws(() => team.releaseLease(lease), /identity no longer matches/);
  team.releaseLease(renewed);
  const takeover = team.acquireLease(taskId, "host:b", 2_000, 500);
  team.releaseLease(takeover);

  const current = team.getTask(taskId);
  const waiting = team.setWait(taskId, { kind: "message", subjectId: "msg:1", reason: "awaiting evidence", sinceTick: 0 });
  assert.equal(waiting.state, "waiting");
  assert.equal(waiting.revision, current.revision + 1);
  const ready = team.setWait(taskId, null);
  assert.equal(ready.state, "ready");
  assert.throws(() => team.saveTask({ ...current, revision: current.revision + 1 }, "stale"), /revision/);
  game.close();
});

test("local Messages deliver by co-location, wait across separation, and later converge", () => {
  const { game, team } = setup("run:team-messages");
  const immediate = team.sendMessage({
    senderActorId: ENGINEER_ID,
    recipientActorIds: [MEDIC_ID],
    kind: "status-update",
    boundedSummary: "Both specialists are in Command Center.",
    channel: "local",
  });
  assert.equal(immediate.status, "delivered");
  assert.deepEqual(immediate.deliveredActorIds, [MEDIC_ID]);
  assert.equal(team.sendMessage({
    senderActorId: ENGINEER_ID,
    recipientActorIds: [MEDIC_ID],
    kind: "status-update",
    boundedSummary: "Both specialists are in Command Center.",
    channel: "local",
  }).messageId, immediate.messageId);

  const medicMove = action(game, MEDIC_ID, "move:power-junction", "message-medic-move");
  const first = game.applyTeamTick({ tickId: "message-separate", expectedWorldRevision: 0, intents: [{ commandSequence: 0, command: medicMove }] });
  assert.equal(first.result.status, "accepted");
  const pending = team.sendMessage({
    senderActorId: ENGINEER_ID,
    recipientActorIds: [MEDIC_ID],
    kind: "help-request",
    boundedSummary: "Meet at the power junction.",
    channel: "local",
    ttlTicks: 3,
  });
  assert.equal(pending.status, "pending");

  const engineerMove = action(game, ENGINEER_ID, "move:power-junction", "message-engineer-move");
  const second = game.applyTeamTick({ tickId: "message-rejoin", expectedWorldRevision: 1, intents: [{ commandSequence: 1, command: engineerMove }] });
  assert.equal(second.result.status, "accepted");
  const journalBeforeProjection = team.host.listJournal(game.activeRunId).length;
  assert.equal(
    team.projection().messages.find((message) => message.messageId === pending.messageId)?.status,
    "pending",
  );
  assert.equal(team.host.listJournal(game.activeRunId).length, journalBeforeProjection);
  const delivered = team.refreshMessages().find((message) => message.messageId === pending.messageId);
  assert.equal(delivered?.status, "delivered");
  assert.deepEqual(delivered?.pendingActorIds, []);
  game.close();
});

test("radio Messages remain pending while communications are unavailable and expire deterministically", () => {
  const { game, team } = setup("run:team-radio");
  const message = team.sendMessage({
    senderActorId: ENGINEER_ID,
    recipientActorIds: [SECURITY_ID],
    kind: "task-offer",
    boundedSummary: "Contain the breach when the radio returns.",
    channel: "station-radio",
    ttlTicks: 1,
  });
  assert.equal(message.status, "pending");
  const wait = action(game, ENGINEER_ID, "wait", "radio-wait");
  game.applyTeamTick({ tickId: "radio-expire", expectedWorldRevision: 0, intents: [{ commandSequence: 0, command: wait }] });
  const expired = team.refreshMessages().find((entry) => entry.messageId === message.messageId);
  assert.equal(expired?.status, "expired");
  game.close();
});

test("Team Goal reads fail closed when the retained Objective Graph Artifact is missing", () => {
  const { game, team } = setup("run:team-objective-artifact");
  try {
    const row = game.db.prepare(
      "SELECT digest FROM host_artifacts WHERE kind = 'team-objective-graph'",
    ).get() as { digest: string } | undefined;
    assert.ok(row);
    game.db.prepare("DELETE FROM host_artifacts WHERE digest = ?").run(row.digest);
    assert.throws(
      () => team.getGoal(game.activeRunId),
      (error: unknown) => error instanceof TeamStoreError && error.code === "team_corrupt" && /Objective Graph Artifact/.test(error.message),
    );
    assert.equal(
      Number((game.db.prepare(
        "SELECT COUNT(*) AS count FROM host_artifacts WHERE kind = 'team-objective-graph'",
      ).get() as { count: number }).count),
      0,
      "a read must not silently recreate missing objective evidence",
    );
  } finally {
    game.close();
  }
});

test("terminal Team Messages remain immutable across repeated refresh", () => {
  const { game, team } = setup("run:team-message-terminal");
  try {
    const delivered = team.sendMessage({
      senderActorId: ENGINEER_ID,
      recipientActorIds: [MEDIC_ID],
      kind: "status-update",
      boundedSummary: "This message is already delivered.",
      channel: "local",
    });
    assert.equal(delivered.status, "delivered");
    const before = team.host.listJournal(game.activeRunId).length;
    assert.deepEqual(
      team.refreshMessages().find((message) => message.messageId === delivered.messageId),
      delivered,
    );
    assert.equal(team.host.listJournal(game.activeRunId).length, before);
  } finally {
    game.close();
  }
});
