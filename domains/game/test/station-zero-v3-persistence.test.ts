import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  StationZeroV3Store,
  StationZeroV3TurnExecutor,
  StationZeroV3TurnService,
  createStationZeroV3MissionControlView,
  type StationZeroFactionId,
  type StationZeroFactionTurnPlan,
  type StationZeroV3PlanningHead,
  type StationZeroV3StorageFaultPoint,
} from "../src/station-zero-v3/index.ts";

const actorByFaction: Record<StationZeroFactionId, string> = {
  rescue: "engineer-imani",
  pirate: "pirate-captain-veyra",
  swarm: "hive-alpha",
};

function fixture(
  name: string,
  options: { faultInjector?: (point: StationZeroV3StorageFaultPoint) => void } = {},
): { directory: string; path: string; runId: string; store: StationZeroV3Store; service: StationZeroV3TurnService } {
  const directory = mkdtempSync(join(tmpdir(), `ordivon-game-v3-p2-${name}-`));
  const path = join(directory, "station-zero-v3.sqlite3");
  const runId = "run:station-zero-v3:p2";
  const store = new StationZeroV3Store(path, options);
  store.createRun({ runId });
  return { directory, path, runId, store, service: new StationZeroV3TurnService(store) };
}

function waitPlan(planning: StationZeroV3PlanningHead, factionId: StationZeroFactionId): StationZeroFactionTurnPlan {
  const actorId = actorByFaction[factionId];
  return {
    planId: `plan:${planning.turn}:${factionId}`,
    factionId,
    expectedWorldRevision: planning.worldRevision,
    expectedTurn: planning.turn,
    standingOrderRevision: planning.standingOrderRevision,
    commanderActions: [],
    actorIntents: [{
      intentId: `intent:${planning.turn}:${factionId}:${actorId}:wait`,
      actorId,
      factionId,
      expectedWorldRevision: planning.worldRevision,
      expectedTurn: planning.turn,
      kind: "wait",
    }],
    committedBy: factionId === "rescue" ? "player:mission-control" : `agent:${factionId}`,
  };
}

function submitAll(
  service: StationZeroV3TurnService,
  runId: string,
  planning: StationZeroV3PlanningHead,
  order: StationZeroFactionId[] = ["rescue", "pirate", "swarm"],
): void {
  for (const factionId of order) service.submitPlan(runId, planning.planningId, waitPlan(planning, factionId));
}

function tableCount(store: StationZeroV3Store, table: string, runId: string): number {
  const row = store.db.prepare(`SELECT COUNT(*) count FROM ${table} WHERE run_id = ?`).get(runId) as { count: number };
  return Number(row.count);
}

test("P2 persists one Planning Head, exactly one Plan per Faction, and one canonical Turn Batch", () => {
  const { directory, runId, store, service } = fixture("planning");
  try {
    const planning = service.openPlanning(runId);
    assert.equal(planning.status, "open");
    assert.equal(planning.worldRevision, 0);
    assert.equal(planning.planningRevision, 1);
    assert.deepEqual(service.openPlanning(runId), planning);

    const rescue = waitPlan(planning, "rescue");
    const first = service.submitPlan(runId, planning.planningId, rescue);
    const duplicate = service.submitPlan(runId, planning.planningId, rescue);
    assert.equal(first.idempotent, false);
    assert.equal(duplicate.idempotent, true);
    assert.equal(first.planDigest, duplicate.planDigest);

    const conflicting = structuredClone(rescue);
    conflicting.committedBy = "player:conflicting";
    assert.throws(() => service.submitPlan(runId, planning.planningId, conflicting), /already bound to another Plan/);

    service.submitPlan(runId, planning.planningId, waitPlan(planning, "swarm"));
    service.submitPlan(runId, planning.planningId, waitPlan(planning, "pirate"));
    const prepared = service.prepare(runId, planning.planningId);
    assert.equal(prepared.prepared.planning.status, "committed");
    assert.deepEqual(prepared.prepared.batch.factionPlans.map((plan) => plan.factionId), ["rescue", "pirate", "swarm"]);
    assert.equal(prepared.prepared.batch.turnBatchId, `turn-batch:station-zero-v3:${runId}:r0`);
    assert.equal(prepared.host.state, "reconciling");
    assert.equal(prepared.host.revision, 2);
    assert.equal(tableCount(store, "station_zero_v3_faction_plans", runId), 3);
    assert.equal(tableCount(store, "station_zero_v3_turn_batches", runId), 1);
    assert.equal(service.prepare(runId, planning.planningId).prepared.batchDigest, prepared.prepared.batchDigest);
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("P2 executes one durable Turn and completes the existing Embedded Host lifecycle", () => {
  const { directory, runId, store, service } = fixture("execute");
  try {
    const planning = service.openPlanning(runId);
    submitAll(service, runId, planning);
    const result = service.execute(runId, planning.planningId);

    assert.equal(result.observation.status, "succeeded");
    assert.equal(result.observation.idempotent, false);
    assert.equal(result.host.state, "completed");
    assert.equal(result.host.revision, 5);
    assert.equal(store.loadState(runId).revision, 1);
    assert.equal(store.loadState(runId).encounter.turn, 1);
    assert.equal(store.getPlanning(runId, planning.planningId).status, "resolved");
    assert.equal(tableCount(store, "station_zero_v3_world_events", runId), 1);
    assert.equal(tableCount(store, "station_zero_v3_turn_records", runId), 1);
    assert.equal(store.hostSequence(runId), 4);
    assert.equal(service.authority.contracts.transcript(runId).length, 5);

    const receipt = store.latestTurnReceipt(runId);
    assert.ok(receipt);
    assert.equal(receipt.event.turnRecordDigest, receipt.recordDigest);
    assert.equal(receipt.event.worldDigestAfter, receipt.stateDigest);
    assert.equal(receipt.record.resolution.intentResolutions.length, 3);
    assert.ok(receipt.record.resolution.intentResolutions.every((entry) => entry.verificationPassed));

    const duplicate = service.execute(runId, planning.planningId);
    assert.equal(duplicate.observation.idempotent, true);
    assert.equal(duplicate.host.state, "completed");
    assert.equal(tableCount(store, "station_zero_v3_world_events", runId), 1);
    assert.equal(service.authority.contracts.transcript(runId).length, 5);
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("response loss after World commit is recovered by observing the original Turn identity", () => {
  const { directory, path, runId, store, service } = fixture("response-loss");
  try {
    const planning = service.openPlanning(runId);
    submitAll(service, runId, planning);
    const prepared = service.prepare(runId, planning.planningId).prepared;
    const crashingExecutor = new StationZeroV3TurnExecutor(store, {
      faultInjector(point) {
        if (point === "after_world_commit") throw new Error("injected:response-loss");
      },
    });
    assert.throws(() => crashingExecutor.deliver(prepared), /injected:response-loss/);
    assert.equal(tableCount(store, "station_zero_v3_world_events", runId), 1);
    assert.equal(service.authority.projection(runId, prepared.taskId).state, "reconciling");
    store.close();

    const freshStore = new StationZeroV3Store(path);
    const freshService = new StationZeroV3TurnService(freshStore);
    try {
      const observed = freshService.observe(runId, planning.planningId);
      assert.ok(observed);
      assert.equal(observed.idempotent, true);
      assert.equal(observed.turnBatchId, prepared.batch.turnBatchId);
      const recovered = freshService.recover(runId);
      assert.equal(recovered.world.turnCount, 1);
      assert.equal(recovered.host?.state, "completed");
      assert.equal(freshStore.turnCount(runId), 1);
      assert.equal(freshService.authority.contracts.transcript(runId).length, 5);
      assert.equal(freshService.execute(runId, planning.planningId).observation.idempotent, true);
      assert.equal(freshStore.turnCount(runId), 1);
    } finally {
      freshStore.close();
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("pre-commit fault points roll back Event, Record, World Head, and Planning resolution together", () => {
  for (const faultPoint of ["after_event_insert", "after_record_insert", "after_head_update"] as const) {
    let active = false;
    const fixtureState = fixture(`rollback-${faultPoint}`, {
      faultInjector(point) {
        if (active && point === faultPoint) throw new Error(`injected:${faultPoint}`);
      },
    });
    const { directory, runId, store, service } = fixtureState;
    try {
      const planning = service.openPlanning(runId);
      submitAll(service, runId, planning);
      const prepared = service.prepare(runId, planning.planningId).prepared;
      active = true;
      assert.throws(() => store.applyPreparedTurn(runId, planning.planningId), new RegExp(`injected:${faultPoint}`));
      active = false;

      assert.equal(tableCount(store, "station_zero_v3_world_events", runId), 0);
      assert.equal(tableCount(store, "station_zero_v3_turn_records", runId), 0);
      assert.equal(store.loadState(runId).revision, 0);
      assert.equal(store.getPlanning(runId, planning.planningId).status, "committed");
      assert.equal(store.turnReceiptByBatch(runId, prepared.batch.turnBatchId), null);
      assert.equal(store.recover(runId).turnCount, 0);
    } finally {
      store.close();
      rmSync(directory, { recursive: true, force: true });
    }
  }
});

test("an after-commit storage fault leaves one observable Turn and never permits redelivery", () => {
  let active = false;
  const { directory, path, runId, store, service } = fixture("after-commit", {
    faultInjector(point) {
      if (active && point === "after_commit") throw new Error("injected:after-commit");
    },
  });
  try {
    const planning = service.openPlanning(runId);
    submitAll(service, runId, planning);
    const prepared = service.prepare(runId, planning.planningId).prepared;
    active = true;
    assert.throws(() => store.applyPreparedTurn(runId, planning.planningId), /injected:after-commit/);
    active = false;
    assert.equal(tableCount(store, "station_zero_v3_world_events", runId), 1);
    assert.equal(store.loadState(runId).revision, 1);
    store.close();

    const freshStore = new StationZeroV3Store(path);
    try {
      const freshService = new StationZeroV3TurnService(freshStore);
      const observed = freshService.observe(runId, planning.planningId);
      assert.ok(observed);
      assert.equal(observed.turnBatchId, prepared.batch.turnBatchId);
      assert.equal(freshStore.applyPreparedTurn(runId, planning.planningId).idempotent, true);
      assert.equal(freshStore.turnCount(runId), 1);
    } finally {
      freshStore.close();
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Recovery rebuilds a missing World Head but rejects a divergent or tampered authority stream", () => {
  const { directory, path, runId, store, service } = fixture("recovery");
  try {
    const planning = service.openPlanning(runId);
    submitAll(service, runId, planning);
    service.execute(runId, planning.planningId);
    const expectedDigest = store.loadWorldHead(runId).stateDigest;
    store.db.prepare("DELETE FROM station_zero_v3_world_heads WHERE run_id = ?").run(runId);
    const rebuilt = store.recover(runId);
    assert.equal(rebuilt.headRebuilt, true);
    assert.equal(rebuilt.stateDigest, expectedDigest);
    assert.equal(store.loadWorldHead(runId).stateDigest, expectedDigest);
    store.close();

    const divergent = new StationZeroV3Store(path);
    try {
      divergent.db.prepare("UPDATE station_zero_v3_world_heads SET state_digest = ? WHERE run_id = ?")
        .run("0".repeat(64), runId);
      assert.throws(() => divergent.recover(runId), /World Head metadata or digest differs/);
      divergent.db.prepare("UPDATE station_zero_v3_world_heads SET state_digest = ? WHERE run_id = ?")
        .run(expectedDigest, runId);
      divergent.db.prepare("UPDATE station_zero_v3_turn_records SET record_json = '{}' WHERE run_id = ?")
        .run(runId);
      assert.throws(() => divergent.recover(runId), /row digest mismatch/);
    } finally {
      divergent.close();
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("canonical persistence is independent from Faction submission order", () => {
  const left = fixture("canonical-left");
  const right = fixture("canonical-right");
  try {
    const leftPlanning = left.service.openPlanning(left.runId);
    const rightPlanning = right.service.openPlanning(right.runId);
    submitAll(left.service, left.runId, leftPlanning, ["rescue", "pirate", "swarm"]);
    submitAll(right.service, right.runId, rightPlanning, ["swarm", "rescue", "pirate"]);

    const leftPrepared = left.service.prepare(left.runId, leftPlanning.planningId).prepared;
    const rightPrepared = right.service.prepare(right.runId, rightPlanning.planningId).prepared;
    assert.equal(leftPrepared.batchDigest, rightPrepared.batchDigest);
    assert.deepEqual(leftPrepared.batch, rightPrepared.batch);

    const leftReceipt = left.store.applyPreparedTurn(left.runId, leftPlanning.planningId);
    const rightReceipt = right.store.applyPreparedTurn(right.runId, rightPlanning.planningId);
    assert.equal(leftReceipt.eventDigest, rightReceipt.eventDigest);
    assert.equal(leftReceipt.recordDigest, rightReceipt.recordDigest);
    assert.equal(leftReceipt.stateDigest, rightReceipt.stateDigest);
  } finally {
    left.store.close();
    right.store.close();
    rmSync(left.directory, { recursive: true, force: true });
    rmSync(right.directory, { recursive: true, force: true });
  }
});

test("Mission Control projection exposes player Knowledge rather than hidden World truth", () => {
  const { directory, runId, store, service } = fixture("projection");
  try {
    let view = createStationZeroV3MissionControlView(store, service, runId);
    assert.equal(view.run.playerFactionId, "rescue");
    assert.deepEqual(view.knownContacts, []);
    assert.deepEqual(view.ownActors.map((actor) => actor.actorId), ["engineer-imani", "medic-reyes", "security-chen"]);
    assert.equal(view.planning.planningId, null);
    assert.equal(view.generatedFrom.hostSequence, -1);

    const planning = service.openPlanning(runId);
    submitAll(service, runId, planning);
    service.prepare(runId, planning.planningId);
    view = createStationZeroV3MissionControlView(store, service, runId);
    assert.equal(view.planning.status, "committed");
    assert.equal(view.planning.canExecute, true);
    assert.equal(view.hostExecution?.state, "reconciling");
    assert.equal(view.knownContacts.some((contact) => contact.actorId === "pirate-captain-veyra"), false);
    assert.equal(view.knownContacts.some((contact) => contact.actorId === "hive-alpha"), false);

    service.execute(runId, planning.planningId);
    view = createStationZeroV3MissionControlView(store, service, runId);
    assert.equal(view.generatedFrom.worldRevision, 1);
    assert.equal(view.hostExecution?.state, "completed");
    assert.equal(view.latestTurn?.turnSequence, 0);
    assert.ok(view.latestTurn?.visibleFactIds.length);
    assert.equal(view.latestTurn?.visibleFactIds.some((factId) => !factId.startsWith("fact:")), false);
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Turn Batch admission rejects duplicate Intent identities across Factions before persistence", () => {
  const { directory, runId, store, service } = fixture("duplicate-intents");
  try {
    const planning = service.openPlanning(runId);
    const rescue = waitPlan(planning, "rescue");
    const pirate = waitPlan(planning, "pirate");
    pirate.actorIntents[0]!.intentId = rescue.actorIntents[0]!.intentId;
    service.submitPlan(runId, planning.planningId, rescue);
    service.submitPlan(runId, planning.planningId, pirate);
    service.submitPlan(runId, planning.planningId, waitPlan(planning, "swarm"));
    assert.throws(() => service.prepare(runId, planning.planningId), /duplicates Intent identities across Factions/);
    assert.equal(tableCount(store, "station_zero_v3_turn_batches", runId), 0);
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});


test("a committed Planning Head survives restart before Host preparation and keeps the same identities", () => {
  const { directory, path, runId, store, service } = fixture("planning-restart");
  try {
    const planning = service.openPlanning(runId);
    submitAll(service, runId, planning);
    const committed = store.commitPlanning(runId, planning.planningId);
    assert.equal(store.hostSequence(runId), -1);
    store.close();

    const freshStore = new StationZeroV3Store(path);
    const freshService = new StationZeroV3TurnService(freshStore);
    try {
      const prepared = freshService.prepare(runId, planning.planningId);
      assert.equal(prepared.prepared.taskId, committed.taskId);
      assert.equal(prepared.prepared.dispatchId, committed.dispatchId);
      assert.equal(prepared.prepared.batchDigest, committed.batchDigest);
      assert.equal(prepared.host.state, "reconciling");
      assert.equal(freshStore.hostSequence(runId), 1);
      const executed = freshService.execute(runId, planning.planningId);
      assert.equal(executed.host.state, "completed");
      assert.equal(freshStore.turnCount(runId), 1);
    } finally {
      freshStore.close();
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("multiple durable Turns recover through aligned World and Host histories", () => {
  const { directory, path, runId, store, service } = fixture("multi-turn");
  try {
    const firstPlanning = service.openPlanning(runId);
    submitAll(service, runId, firstPlanning);
    const first = service.execute(runId, firstPlanning.planningId);
    assert.equal(first.host.state, "completed");

    const secondPlanning = service.openPlanning(runId);
    assert.equal(secondPlanning.worldRevision, 1);
    assert.equal(secondPlanning.turn, 1);
    assert.equal(secondPlanning.standingOrderRevision, 1);
    submitAll(service, runId, secondPlanning, ["pirate", "swarm", "rescue"]);
    const second = service.execute(runId, secondPlanning.planningId);
    assert.equal(second.host.state, "completed");
    assert.equal(store.loadState(runId).revision, 2);
    assert.equal(store.turnCount(runId), 2);
    assert.equal(service.authority.contracts.transcript(runId).length, 10);
    assert.equal(store.hostSequence(runId), 9);
    store.close();

    const freshStore = new StationZeroV3Store(path);
    const freshService = new StationZeroV3TurnService(freshStore);
    try {
      const recovered = freshService.recover(runId);
      assert.equal(recovered.world.turnCount, 2);
      assert.equal(recovered.world.state.revision, 2);
      assert.equal(recovered.world.state.encounter.turn, 2);
      assert.equal(recovered.host?.state, "completed");
      assert.equal(freshService.authority.listDispatches(runId).length, 2);
      assert.equal(freshService.authority.listObservations(runId).length, 2);
      assert.equal(freshStore.latestTurnReceipt(runId)?.turnSequence, 1);
    } finally {
      freshStore.close();
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});


test("a prepared Turn without a World result blocks the next Planning Head", () => {
  const { directory, runId, store, service } = fixture("planning-gate-prepared");
  try {
    const planning = service.openPlanning(runId);
    submitAll(service, runId, planning);
    const prepared = service.prepare(runId, planning.planningId).prepared;
    assert.equal(store.getPlanning(runId, planning.planningId).status, "committed");
    assert.equal(store.turnReceiptByBatch(runId, prepared.batch.turnBatchId), null);
    assert.throws(() => service.openPlanning(runId), /prepared but has no authoritative World result/);
    assert.equal(store.listPlanning(runId).length, 1);
    assert.equal(store.loadState(runId).revision, 0);
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("a response-lost World result is reconciled under the original Dispatch before the next Planning opens", () => {
  const { directory, runId, store, service } = fixture("planning-gate-reconcile");
  try {
    const planning = service.openPlanning(runId);
    submitAll(service, runId, planning);
    const prepared = service.prepare(runId, planning.planningId).prepared;
    const crashing = new StationZeroV3TurnExecutor(store, {
      faultInjector(point) {
        if (point === "after_world_commit") throw new Error("injected:response-loss-before-next-planning");
      },
    });
    assert.throws(() => crashing.deliver(prepared), /response-loss-before-next-planning/);
    assert.equal(service.authority.projection(runId, prepared.taskId).state, "reconciling");

    const next = service.openPlanning(runId);
    assert.equal(service.authority.projection(runId, prepared.taskId).state, "completed");
    assert.equal(next.worldRevision, 1);
    assert.equal(next.turn, 1);
    assert.equal(next.planningId, `planning:station-zero-v3:${runId}:r1`);
    assert.equal(store.listPlanning(runId).length, 2);
    assert.equal(store.turnCount(runId), 1);
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Recovery rejects tampered canonical Batch and Planning evidence", () => {
  const batchFixture = fixture("tamper-batch");
  try {
    const planning = batchFixture.service.openPlanning(batchFixture.runId);
    submitAll(batchFixture.service, batchFixture.runId, planning);
    batchFixture.service.execute(batchFixture.runId, planning.planningId);
    batchFixture.store.db.prepare(`UPDATE station_zero_v3_turn_batches
      SET batch_json = '{}' WHERE run_id = ? AND planning_id = ?`)
      .run(batchFixture.runId, planning.planningId);
    assert.throws(() => batchFixture.store.recover(batchFixture.runId), /Turn Batch differs from Planning Head/);
  } finally {
    batchFixture.store.close();
    rmSync(batchFixture.directory, { recursive: true, force: true });
  }

  const planningFixture = fixture("tamper-planning");
  try {
    const planning = planningFixture.service.openPlanning(planningFixture.runId);
    submitAll(planningFixture.service, planningFixture.runId, planning);
    planningFixture.service.execute(planningFixture.runId, planning.planningId);
    planningFixture.store.db.prepare(`UPDATE station_zero_v3_planning_heads
      SET head_json = '{}' WHERE run_id = ? AND planning_id = ?`)
      .run(planningFixture.runId, planning.planningId);
    assert.throws(() => planningFixture.store.recover(planningFixture.runId), /Planning Head is inconsistent/);
  } finally {
    planningFixture.store.close();
    rmSync(planningFixture.directory, { recursive: true, force: true });
  }
});


test("Recovery rejects tampered retained Faction Plans independently from the canonical Batch", () => {
  const { directory, runId, store, service } = fixture("tamper-faction-plan");
  try {
    const planning = service.openPlanning(runId);
    submitAll(service, runId, planning);
    service.execute(runId, planning.planningId);
    store.db.prepare(`UPDATE station_zero_v3_faction_plans
      SET plan_json = '{}' WHERE run_id = ? AND planning_id = ? AND faction_id = 'pirate'`)
      .run(runId, planning.planningId);
    assert.throws(() => store.recover(runId), /Faction Plan digest differs from Planning Head/);
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});
