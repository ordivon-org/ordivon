import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  STATION_ZERO_V3_RESOURCE_EGRESS_KIND,
  StationZeroV3ResourceEgress,
  StationZeroV3ResourceEgressConflict,
  StationZeroV3ResourceEgressError,
  StationZeroV3Store,
  StationZeroV3TurnService,
  type StationZeroFactionId,
  type StationZeroFactionTurnPlan,
  type StationZeroV3PlanningHead,
  type StationZeroV3ResourceEgressRequest,
} from "../src/station-zero-v3/index.ts";
import { protocolDigest } from "../src/host-contract/canonical.ts";

const actorByFaction: Record<StationZeroFactionId, string> = {
  rescue: "medic-reyes",
  pirate: "pirate-captain-veyra",
  swarm: "hive-alpha",
};

function factionPlan(
  planning: StationZeroV3PlanningHead,
  factionId: StationZeroFactionId,
  extract = false,
): StationZeroFactionTurnPlan {
  const actorId = actorByFaction[factionId];
  return {
    planId: `plan:w2-p3:${planning.turn}:${factionId}`,
    factionId,
    expectedWorldRevision: planning.worldRevision,
    expectedTurn: planning.turn,
    standingOrderRevision: planning.standingOrderRevision,
    commanderActions: [],
    actorIntents: [extract
      ? {
          intentId: `intent:w2-p3:${planning.turn}:${actorId}:extract`,
          actorId,
          factionId,
          expectedWorldRevision: planning.worldRevision,
          expectedTurn: planning.turn,
          kind: "extract",
          extractionId: `extraction:w2-p3:${planning.turn}:${actorId}`,
        }
      : {
          intentId: `intent:w2-p3:${planning.turn}:${actorId}:wait`,
          actorId,
          factionId,
          expectedWorldRevision: planning.worldRevision,
          expectedTurn: planning.turn,
          kind: "wait",
        }],
    committedBy: factionId === "rescue" ? "player:w2-p3" : `agent:${factionId}`,
  };
}

function persistedExtraction(name: string) {
  const directory = mkdtempSync(join(tmpdir(), `ordivon-game-w2-egress-${name}-`));
  const path = join(directory, "station-zero-v3.sqlite3");
  const runId = `run:w2-p3:${name}`;
  const store = new StationZeroV3Store(path);
  store.createRun({ runId, seed: `w2-p3-${name}` });
  const service = new StationZeroV3TurnService(store);
  const planning = service.openPlanning(runId);
  service.submitPlan(runId, planning.planningId, factionPlan(planning, "rescue", true));
  service.submitPlan(runId, planning.planningId, factionPlan(planning, "pirate"));
  service.submitPlan(runId, planning.planningId, factionPlan(planning, "swarm"));
  service.execute(runId, planning.planningId);
  const turn = store.latestTurnReceipt(runId);
  assert.ok(turn);
  const fact = turn.record.resolution.facts.find((entry) =>
    entry.kind === "item_extracted" && entry.actorId === "medic-reyes" && entry.itemId === "medkit");
  assert.ok(fact && fact.kind === "item_extracted");
  const payload = {
    schemaVersion: 1,
    kind: "ordivon.w2.portable-resource",
    resourceType: "station-zero-v3-item",
    itemId: "medkit",
    category: "consumable",
  } as const;
  const request: StationZeroV3ResourceEgressRequest = {
    transferId: `transfer:w2-p3:${name}`,
    destinationWorldId: "security-world:w2-p3:B",
    resourceKind: STATION_ZERO_V3_RESOURCE_EGRESS_KIND,
    turnBatchId: turn.turnBatchId,
    factId: fact.factId,
    payload,
  };
  return { directory, path, runId, store, turn, fact, payload, request };
}

function cleanup(value: ReturnType<typeof persistedExtraction>): void {
  value.store.close();
  rmSync(value.directory, { recursive: true, force: true });
}

test("real persisted item_extracted fact produces one Game-owned Resource Egress receipt", () => {
  const value = persistedExtraction("valid");
  try {
    const stateDigestBefore = value.turn.stateDigest;
    const egress = new StationZeroV3ResourceEgress(value.store);
    const receipt = egress.admit(value.runId, value.request);
    assert.equal(receipt.kind, "ordivon.world.resource-egress-receipt");
    assert.equal(receipt.transferId, value.request.transferId);
    assert.equal(receipt.sourceWorldId, value.runId);
    assert.equal(receipt.destinationWorldId, value.request.destinationWorldId);
    assert.equal(receipt.resourceKind, STATION_ZERO_V3_RESOURCE_EGRESS_KIND);
    assert.equal(receipt.payloadDigest, protocolDigest(value.payload));
    assert.equal(receipt.authority.mechanism, "station-zero-v3-retained-turn-replay.v1");
    assert.equal(receipt.authority.evidence.recordDigest, `sha256:${value.turn.recordDigest}`);
    assert.equal(receipt.authority.evidence.factId, value.fact.factId);
    assert.equal(receipt.authority.evidence.retainedReplayVerified, true);
    assert.equal(value.store.loadState(value.runId).revision, value.turn.state.revision);
    assert.equal(value.store.latestTurnReceipt(value.runId)?.stateDigest, stateDigestBefore);
    const count = value.store.db.prepare("SELECT COUNT(*) count FROM station_zero_v3_resource_egress WHERE run_id = ?")
      .get(value.runId) as { count: number };
    assert.equal(Number(count.count), 1);
  } finally {
    cleanup(value);
  }
});

test("exact Resource Egress retry is idempotent and survives store reopen", () => {
  const value = persistedExtraction("reopen");
  let receipt;
  try {
    const egress = new StationZeroV3ResourceEgress(value.store);
    receipt = egress.admit(value.runId, value.request);
    assert.deepEqual(egress.admit(value.runId, value.request), receipt);
    value.store.close();
    const freshStore = new StationZeroV3Store(value.path);
    try {
      const freshEgress = new StationZeroV3ResourceEgress(freshStore);
      assert.deepEqual(freshEgress.receipt(value.runId, value.request.transferId), receipt);
      assert.deepEqual(freshEgress.admit(value.runId, value.request), receipt);
      const count = freshStore.db.prepare("SELECT COUNT(*) count FROM station_zero_v3_resource_egress WHERE run_id = ?")
        .get(value.runId) as { count: number };
      assert.equal(Number(count.count), 1);
    } finally {
      freshStore.close();
    }
  } finally {
    rmSync(value.directory, { recursive: true, force: true });
  }
});

test("forged source Fact and wrong portable item are rejected before egress ledger mutation", () => {
  const value = persistedExtraction("reject");
  try {
    const egress = new StationZeroV3ResourceEgress(value.store);
    assert.throws(
      () => egress.admit(value.runId, { ...value.request, factId: "fact:forged:item_extracted" }),
      StationZeroV3ResourceEgressError,
    );
    assert.throws(
      () => egress.admit(value.runId, { ...value.request, payload: { ...value.payload, itemId: "spare-parts" } }),
      /Portable Resource itemId differs/i,
    );
    const count = value.store.db.prepare("SELECT COUNT(*) count FROM station_zero_v3_resource_egress WHERE run_id = ?")
      .get(value.runId) as { count: number };
    assert.equal(Number(count.count), 0);
  } finally {
    cleanup(value);
  }
});

test("one source occurrence cannot authorize two transfers or destinations", () => {
  const value = persistedExtraction("unique");
  try {
    const egress = new StationZeroV3ResourceEgress(value.store);
    const first = egress.admit(value.runId, value.request);
    assert.throws(
      () => egress.admit(value.runId, { ...value.request, transferId: "transfer:w2-p3:second" }),
      StationZeroV3ResourceEgressConflict,
    );
    assert.throws(
      () => egress.admit(value.runId, { ...value.request, destinationWorldId: "security-world:w2-p3:C" }),
      StationZeroV3ResourceEgressConflict,
    );
    assert.deepEqual(egress.receipt(value.runId, value.request.transferId), first);
  } finally {
    cleanup(value);
  }
});

test("same transfer identity cannot silently change portable payload", () => {
  const value = persistedExtraction("payload-conflict");
  try {
    const egress = new StationZeroV3ResourceEgress(value.store);
    egress.admit(value.runId, value.request);
    assert.throws(
      () => egress.admit(value.runId, {
        ...value.request,
        payload: { ...value.payload, category: "changed" },
      }),
      StationZeroV3ResourceEgressConflict,
    );
  } finally {
    cleanup(value);
  }
});
