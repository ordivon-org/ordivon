import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import {
  canonicalizeStationZeroV3AgentActionBinding,
  StationZeroV3Store,
  StationZeroV3TurnService,
  stationZeroV3AgentActionBindingDigest,
  stationZeroV3AgentCandidates,
  type StationZeroV3AgentActionBinding,
} from "../src/station-zero-v3/index.ts";

function withStore(body: (store: StationZeroV3Store, dbPath: string) => void): void {
  const root = mkdtempSync(join(tmpdir(), "ordivon-game-agent-action-admission-"));
  const dbPath = join(root, "game.sqlite3");
  const store = new StationZeroV3Store(dbPath);
  try {
    body(store, dbPath);
  } finally {
    store.close();
    rmSync(root, { recursive: true, force: true });
  }
}

function binding(input: {
  runId: string;
  planningId: string;
  worldRevision: number;
  worldDigest: string;
  actorId: string;
  subjectRef: string;
  cognitionRef: string;
  intent: unknown;
}): { value: StationZeroV3AgentActionBinding; digest: `sha256:${string}` } {
  const sourceEvidence = {
    schemaVersion: 1,
    kind: "test-upstream-cognition-evidence",
    subjectRef: input.subjectRef,
    cognitionRef: input.cognitionRef,
  };
  const value: StationZeroV3AgentActionBinding = {
    schemaVersion: 1,
    kind: "ordivon.game.station-zero-v3-agent-action-binding",
    subjectRef: input.subjectRef,
    cognitionRef: input.cognitionRef,
    sourceAuthorityId: "caller:agent-action-test-owner",
    sourceEvidenceDigest: `sha256:${sha256(sourceEvidence)}`,
    runId: input.runId,
    planningId: input.planningId,
    worldRevision: input.worldRevision,
    worldDigest: input.worldDigest,
    actorId: input.actorId,
    intentDigest: `sha256:${sha256(input.intent)}`,
  };
  return { value, digest: stationZeroV3AgentActionBindingDigest(value) };
}

function submitThreePlans(
  store: StationZeroV3Store,
  runId: string,
  planningId: string,
  medicIntent: ReturnType<typeof stationZeroV3AgentCandidates>[number]["intent"],
): {
  turns: StationZeroV3TurnService;
  pirateIntent: ReturnType<typeof stationZeroV3AgentCandidates>[number]["intent"];
  swarmIntent: ReturnType<typeof stationZeroV3AgentCandidates>[number]["intent"];
} {
  const turns = new StationZeroV3TurnService(store);
  const planning = store.getPlanning(runId, planningId);
  const state = store.loadState(runId);
  const pirateIntent = stationZeroV3AgentCandidates(
    state,
    planning,
    "pirate-captain-veyra",
  ).find((candidate) => candidate.intent.kind === "wait")!.intent;
  const swarmIntent = stationZeroV3AgentCandidates(
    state,
    planning,
    "hive-alpha",
  ).find((candidate) => candidate.intent.kind === "wait")!.intent;

  for (const [factionId, actorIntent] of [
    ["rescue", medicIntent],
    ["pirate", pirateIntent],
    ["swarm", swarmIntent],
  ] as const) {
    turns.submitPlan(runId, planningId, {
      planId: `plan:agent-action-admission:${factionId}`,
      factionId,
      expectedWorldRevision: planning.worldRevision,
      expectedTurn: planning.turn,
      standingOrderRevision: planning.standingOrderRevision,
      commanderActions: [],
      actorIntents: [actorIntent],
      committedBy: `agent-action-admission:${factionId}`,
    });
  }
  return { turns, pirateIntent, swarmIntent };
}

test("Agent Action admission is optional until explicitly enabled", () => {
  withStore((store) => {
    const runId = "run:agent-action:optional";
    store.createRun({ runId, seed: "agent-action-optional" });
    const turns = new StationZeroV3TurnService(store);
    const planning = turns.openPlanning(runId);
    const state = store.loadState(runId);
    const medicIntent = stationZeroV3AgentCandidates(
      state,
      planning,
      "medic-reyes",
    ).find((candidate) => candidate.intent.kind === "wait")!.intent;
    submitThreePlans(store, runId, planning.planningId, medicIntent);
    const prepared = turns.prepare(runId, planning.planningId);
    assert.equal(prepared.prepared.planning.planningId, planning.planningId);
  });
});

test("Agent Action Binding rejects upstream-private fields", () => {
  const value = binding({
    runId: "run:contract",
    planningId: "planning:contract",
    worldRevision: 0,
    worldDigest: "world-digest",
    actorId: "medic-reyes",
    subjectRef: "subject:medic-reyes",
    cognitionRef: "cognition:medic-reyes:1",
    intent: { kind: "wait", actorId: "medic-reyes" },
  }).value;
  const leaked = { ...value, harnessRunId: "harness-private:must-not-enter-game" };
  assert.throws(
    () => canonicalizeStationZeroV3AgentActionBinding(leaked),
    /unexpected or missing fields/,
  );
});

test("Agent Action admission is exact, action-scoped, cognition-bound, and restart-verifiable", () => {
  withStore((store, dbPath) => {
    const runId = "run:agent-action:test";
    store.createRun({ runId, seed: "agent-action-test" });
    const turns = new StationZeroV3TurnService(store);
    const planning = turns.openPlanning(runId);
    const state = store.loadState(runId);
    const medicMoves = stationZeroV3AgentCandidates(
      state,
      planning,
      "medic-reyes",
    ).filter((candidate) => candidate.intent.kind === "move");
    assert.ok(medicMoves.length >= 2);
    const cognitionA = medicMoves[0]!;
    const cognitionB = medicMoves[1]!;

    store.enableAgentActionAdmission(runId, planning.planningId);
    const submitted = submitThreePlans(
      store,
      runId,
      planning.planningId,
      cognitionA.intent,
    );

    assert.throws(
      () => turns.prepare(runId, planning.planningId),
      /lacks exact Agent Action admission/,
    );

    const shared = {
      runId,
      planningId: planning.planningId,
      worldRevision: planning.worldRevision,
      worldDigest: planning.worldDigest,
      actorId: "medic-reyes",
      subjectRef: "continuity-subject:medic-reyes",
    };
    const bindingA = binding({
      ...shared,
      cognitionRef: "cognition:medic-reyes:a",
      intent: cognitionA.intent,
    });
    const wrongAction = binding({
      ...shared,
      cognitionRef: "cognition:medic-reyes:b",
      intent: cognitionB.intent,
    });

    assert.throws(
      () => store.admitAgentActionBinding({
        runId,
        planningId: planning.planningId,
        actorId: "medic-reyes",
        binding: wrongAction.value,
        bindingDigest: wrongAction.digest,
      }),
      /does not authorize this exact Actor Intent/,
    );

    const laundering = structuredClone(bindingA.value);
    laundering.subjectRef = "continuity-subject:mallory";
    assert.throws(
      () => store.admitAgentActionBinding({
        runId,
        planningId: planning.planningId,
        actorId: "medic-reyes",
        binding: laundering,
        bindingDigest: bindingA.digest,
      }),
      /does not authorize this exact Actor Intent/,
    );

    const medicAdmission = store.admitAgentActionBinding({
      runId,
      planningId: planning.planningId,
      actorId: "medic-reyes",
      binding: bindingA.value,
      bindingDigest: bindingA.digest,
    });
    assert.equal(medicAdmission.subjectRef, shared.subjectRef);
    assert.equal(medicAdmission.cognitionRef, bindingA.value.cognitionRef);
    assert.equal(medicAdmission.bindingDigest, bindingA.digest);

    const cognitionSwap = binding({
      ...shared,
      cognitionRef: "cognition:medic-reyes:alternate-same-action",
      intent: cognitionA.intent,
    });
    assert.throws(
      () => store.admitAgentActionBinding({
        runId,
        planningId: planning.planningId,
        actorId: "medic-reyes",
        binding: cognitionSwap.value,
        bindingDigest: cognitionSwap.digest,
      }),
      /already admitted under another Subject, Cognition, evidence, or Plan/,
    );

    for (const [actorId, intent] of [
      ["pirate-captain-veyra", submitted.pirateIntent],
      ["hive-alpha", submitted.swarmIntent],
    ] as const) {
      const value = binding({
        runId,
        planningId: planning.planningId,
        worldRevision: planning.worldRevision,
        worldDigest: planning.worldDigest,
        actorId,
        subjectRef: `continuity-subject:${actorId}`,
        cognitionRef: `cognition:${actorId}:current`,
        intent,
      });
      store.admitAgentActionBinding({
        runId,
        planningId: planning.planningId,
        actorId,
        binding: value.value,
        bindingDigest: value.digest,
      });
    }

    const executed = turns.execute(runId, planning.planningId);
    assert.equal(executed.host.state, "completed");
    const receipt = store.latestTurnReceipt(runId)!;
    assert.equal(
      receipt.record.resolution.intentResolutions.find(
        (resolution) => resolution.actorId === "medic-reyes",
      )?.status,
      "executed",
    );
    assert.ok(
      receipt.record.resolution.facts.some(
        (fact) => fact.kind === "actor_moved" && fact.actorId === "medic-reyes",
      ),
    );

    const retained = store.db.prepare(
      `SELECT cognition_ref, binding_json FROM station_zero_v3_agent_action_admissions
       WHERE run_id = ? AND planning_id = ? AND actor_id = ?`,
    ).get(runId, planning.planningId, "medic-reyes") as {
      cognition_ref: string;
      binding_json: string;
    };
    assert.equal(retained.cognition_ref, bindingA.value.cognitionRef);
    const retainedBinding = JSON.parse(retained.binding_json) as Record<string, unknown>;
    assert.equal(retainedBinding.kind, "ordivon.game.station-zero-v3-agent-action-binding");
    assert.equal(retainedBinding.cognitionRef, bindingA.value.cognitionRef);
    assert.equal("harnessRunId" in retainedBinding, false);

    const reopened = new StationZeroV3Store(dbPath);
    try {
      assert.equal(reopened.verify(runId).verified, true);
    } finally {
      reopened.close();
    }

    store.db.prepare(
      `UPDATE station_zero_v3_agent_action_admissions
       SET cognition_ref = ? WHERE run_id = ? AND planning_id = ? AND actor_id = ?`,
    ).run("cognition:tampered", runId, planning.planningId, "medic-reyes");
    const tampered = new StationZeroV3Store(dbPath);
    try {
      assert.throws(
        () => tampered.verify(runId),
        /Agent Action Binding drifted for Actor medic-reyes/,
      );
    } finally {
      tampered.close();
    }
  });
});
