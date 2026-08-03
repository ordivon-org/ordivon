import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  StationZeroV3PlanningStore,
  StationZeroV3PlayService,
  StationZeroV3Store,
  applyStationZeroV3Turn,
  assertStationZeroV3AgentDecision,
  compileStationZeroV3AgentContext,
  createStationZeroV3Genesis,
  prepareStationZeroV3Commitment,
  type StationZeroActorIntent,
  type StationZeroFactionId,
  type StationZeroFactionTurnPlan,
  type StationZeroTurnBatch,
  type StationZeroV3PlanningHead,
  type StationZeroV3WorldState,
} from "../src/station-zero-v3/index.ts";

function fixture(name: string): {
  directory: string;
  path: string;
  runId: string;
  store: StationZeroV3Store;
  play: StationZeroV3PlayService;
} {
  const directory = mkdtempSync(join(tmpdir(), `ordivon-game-v3-p3-${name}-`));
  const path = join(directory, "station-zero-v3.sqlite3");
  const runId = `run:station-zero-v3:p3:${name}`;
  const store = new StationZeroV3Store(path);
  return { directory, path, runId, store, play: new StationZeroV3PlayService(store) };
}

const actorByFaction: Record<StationZeroFactionId, string> = {
  rescue: "engineer-imani",
  pirate: "pirate-captain-veyra",
  swarm: "hive-alpha",
};

function waitPlan(
  state: StationZeroV3WorldState,
  factionId: StationZeroFactionId,
  actorId = actorByFaction[factionId],
): StationZeroFactionTurnPlan {
  return {
    planId: `plan:test:${state.encounter.turn}:${factionId}`,
    factionId,
    expectedWorldRevision: state.revision,
    expectedTurn: state.encounter.turn,
    standingOrderRevision: state.encounter.activePlanRevision,
    commanderActions: [],
    actorIntents: [{
      intentId: `intent:test:${state.encounter.turn}:${actorId}:wait`,
      actorId,
      factionId,
      expectedWorldRevision: state.revision,
      expectedTurn: state.encounter.turn,
      kind: "wait",
    }],
    committedBy: `test:${factionId}`,
  };
}

function batch(
  state: StationZeroV3WorldState,
  plans: Partial<Record<StationZeroFactionId, StationZeroFactionTurnPlan>> = {},
): StationZeroTurnBatch {
  return {
    turnBatchId: `turn-batch:test:${state.revision}`,
    expectedWorldRevision: state.revision,
    expectedTurn: state.encounter.turn,
    factionPlans: [
      plans.rescue ?? waitPlan(state, "rescue"),
      plans.pirate ?? waitPlan(state, "pirate"),
      plans.swarm ?? waitPlan(state, "swarm"),
    ],
  };
}

function planningFor(state: StationZeroV3WorldState): StationZeroV3PlanningHead {
  const commitment = prepareStationZeroV3Commitment(state);
  return {
    schemaVersion: 1,
    kind: "ordivon.game.station-zero-v3-planning-head",
    planningId: `planning:test:${state.revision}`,
    runId: "run:test",
    worldRevision: state.revision,
    turn: state.encounter.turn,
    worldDigest: "test-world-digest",
    commitmentDigest: "test-commitment-digest",
    standingOrderRevision: state.encounter.activePlanRevision,
    planningRevision: 1,
    status: "open",
    submittedPlanDigests: {},
    turnBatchId: null,
    batchDigest: null,
    taskId: null,
    goalId: null,
    effectId: null,
    dispatchId: null,
    createdAt: "2026-08-03T00:00:00.000Z",
    updatedAt: "2026-08-03T00:00:00.000Z",
  };
  void commitment;
}

test("Agent Contexts expose faction Knowledge and admitted Candidates, not hidden World truth", async () => {
  const { directory, runId, store, play } = fixture("limited-context");
  try {
    const view = play.initialize({ runId });
    const preview = (await play.generatePreview(runId)).preview;
    assert.equal(preview.agentDecisions.length, 5);
    assert.equal(preview.policyDecisions.length, 5);
    assert.equal(preview.contexts.length, 10);

    const engineer = preview.contexts.find((context) => context.actor.actorId === "engineer-imani");
    const captain = preview.contexts.find((context) => context.actor.actorId === "pirate-captain-veyra");
    assert.ok(engineer);
    assert.ok(captain);
    assert.equal(engineer.known.actors.some((actor) => actor.actorId === "pirate-captain-veyra"), false);
    assert.equal(engineer.known.actors.some((actor) => actor.actorId === "hive-alpha"), false);
    assert.equal(captain.playerOrder, null);
    assert.equal(engineer.playerOrder?.primaryObjectiveId, "rescue-two-civilians");
    assert.ok(engineer.candidates.length > 1);
    assert.equal(view.knownContacts.length, 0);

    const playerPreview = (await play.state(runId)).experience.preview;
    assert.ok(playerPreview);
    assert.deepEqual(playerPreview.enemyPlansSealed.map((entry) => entry.factionId), ["pirate", "swarm"]);
    assert.equal("factionPlans" in playerPreview, false);
    assert.equal(JSON.stringify(playerPreview).includes("pirate-captain-veyra"), false);
    assert.equal(JSON.stringify(playerPreview).includes("hive-alpha"), false);
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Agent Decisions cannot invent an action or enemy directive", () => {
  const state = createStationZeroV3Genesis();
  const planning = planningFor(state);
  const order = {
    schemaVersion: 1 as const,
    kind: "ordivon.game.station-zero-v3-commander-order" as const,
    runId: planning.runId,
    planningId: planning.planningId,
    expectedWorldRevision: 0,
    expectedTurn: 0,
    primaryObjectiveId: "rescue-two-civilians" as const,
    posture: "balanced" as const,
    formation: "split" as const,
    retreatHealthThreshold: 0.3,
    lethalForce: "permitted" as const,
    collateralPolicy: "forbidden" as const,
    lootPolicy: "mission-only" as const,
    protectedActorId: "medic-reyes",
    priorityTargetActorId: null,
    commanderDirectiveId: "scan-reactor" as const,
    issuedBy: "player:test",
  };
  const context = compileStationZeroV3AgentContext(state, planning, "engineer-imani", order);
  const valid = {
    schemaVersion: 1 as const,
    kind: "ordivon.game.station-zero-v3-agent-decision" as const,
    contextId: context.contextId,
    contextDigest: context.contextDigest,
    actorId: context.actor.actorId,
    factionId: context.factionId,
    candidateId: context.candidates[0]!.candidateId,
    directiveId: null,
    rationale: "Select one admitted action.",
    confidence: 0.7,
    providerId: "provider:test",
  };
  assert.doesNotThrow(() => assertStationZeroV3AgentDecision(context, valid));
  assert.throws(() => assertStationZeroV3AgentDecision(context, { ...valid, candidateId: "candidate:invented" }), /invented a Candidate/);
  assert.throws(() => assertStationZeroV3AgentDecision(context, { ...valid, directiveId: "steal-core" }), /directive does not match/);
});

test("Commander Order revisions invalidate prior previews and materially alter Rescue planning", async () => {
  const { directory, runId, store, play } = fixture("order-revision");
  try {
    play.initialize({ runId });
    const first = (await play.generatePreview(runId)).preview;
    const firstRescueDigest = JSON.stringify(first.factionPlans.rescue);
    const saved = play.saveOrder(runId, {
      primaryObjectiveId: "recover-research-core",
      posture: "aggressive",
      formation: "cohesive",
      lootPolicy: "opportunistic",
      commanderDirectiveId: "scan-reactor",
    });
    assert.equal(saved.view.experience.preview, null);
    assert.equal(saved.orderRevision, 2);

    const second = (await play.generatePreview(runId)).preview;
    assert.notEqual(second.previewId, first.previewId);
    assert.notEqual(JSON.stringify(second.factionPlans.rescue), firstRescueDigest);
    assert.equal(second.playerOrder.primaryObjectiveId, "recover-research-core");
    assert.equal(second.playerOrder.posture, "aggressive");
    assert.equal(second.factionPlans.pirate.planId, first.factionPlans.pirate.planId);
    assert.notEqual(second.previewDigest, first.previewDigest);
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Preview remains non-authoritative until explicit Commit, then binds all three exact Plans", async () => {
  const { directory, runId, store, play } = fixture("explicit-commit");
  try {
    play.initialize({ runId });
    const preview = (await play.generatePreview(runId)).preview;
    const planning = store.latestPlanning(runId)!;
    assert.deepEqual(planning.submittedPlanDigests, {});
    assert.equal(store.turnCount(runId), 0);

    const committed = await play.commitPreview(runId, preview.previewId);
    assert.equal(committed.turnSequence, 0);
    assert.equal(committed.worldRevision, 1);
    assert.equal(committed.hostState, "completed");
    assert.ok(committed.nextPlanningId);
    assert.equal(store.turnCount(runId), 1);
    const resolved = store.getPlanning(runId, planning.planningId);
    assert.deepEqual(Object.keys(resolved.submittedPlanDigests).sort(), ["pirate", "rescue", "swarm"]);
    assert.equal(new StationZeroV3PlanningStore(store).getHead(runId, planning.planningId).committedPreviewId, preview.previewId);
    assert.ok(committed.view.aftermath);
    assert.equal(committed.view.aftermath?.ownIntentResults.length, 3);
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("escorted civilians consume movement capacity, follow their specialist, and extract with them", () => {
  let state = prepareStationZeroV3Commitment(createStationZeroV3Genesis());
  state.actors["medic-reyes"]!.position.zoneId = "command-deck";
  state.actors["civilian-sato"]!.position.zoneId = "command-deck";
  state.actors["civilian-sato"]!.statusIds.push("escorted-by:medic-reyes");
  const move: StationZeroActorIntent = {
    intentId: "intent:test:medic:escort-airlock",
    actorId: "medic-reyes",
    factionId: "rescue",
    expectedWorldRevision: 0,
    expectedTurn: 0,
    kind: "move",
    targetZoneId: "rescue-airlock",
  };
  const rescue = waitPlan(state, "rescue", "medic-reyes");
  rescue.actorIntents = [move];
  let result = applyStationZeroV3Turn(state, batch(state, { rescue }));
  assert.equal(result.status, "accepted");
  if (result.status !== "accepted") return;
  assert.equal(result.state.actors["medic-reyes"]!.position.zoneId, "rescue-airlock");
  assert.equal(result.state.actors["civilian-sato"]!.position.zoneId, "rescue-airlock");
  assert.equal(result.resolution.facts.filter((fact) => fact.kind === "actor_moved").some((fact) => fact.actorId === "civilian-sato"), true);

  state = prepareStationZeroV3Commitment(result.state);
  const extract: StationZeroActorIntent = {
    intentId: "intent:test:medic:extract",
    actorId: "medic-reyes",
    factionId: "rescue",
    expectedWorldRevision: 1,
    expectedTurn: 1,
    kind: "extract",
    extractionId: "extraction:test:rescue",
  };
  const extractionPlan = waitPlan(state, "rescue", "medic-reyes");
  extractionPlan.actorIntents = [extract];
  result = applyStationZeroV3Turn(state, batch(state, { rescue: extractionPlan }));
  assert.equal(result.status, "accepted");
  if (result.status !== "accepted") return;
  assert.equal(result.state.actors["medic-reyes"]!.lifeState, "extracted");
  assert.equal(result.state.actors["civilian-sato"]!.lifeState, "extracted");
  assert.equal(result.state.factions.rescue.objectiveProgress["rescue-two-civilians"]!.progress, 1);
  assert.equal(result.state.factions.rescue.objectiveProgress["rescue-team-survives"]!.status, "completed");
});

test("P3 planning and selected Preview survive process restart", async () => {
  const { directory, path, runId, store, play } = fixture("restart");
  try {
    play.initialize({ runId });
    play.saveOrder(runId, { posture: "cautious", commanderDirectiveId: "scan-maintenance" });
    const preview = (await play.generatePreview(runId)).preview;
    store.close();

    const freshStore = new StationZeroV3Store(path);
    const freshPlay = new StationZeroV3PlayService(freshStore);
    try {
      const view = freshPlay.resume(runId);
      assert.equal(view.experience.order?.posture, "cautious");
      assert.equal(view.experience.preview?.previewId, preview.previewId);
      const committed = await freshPlay.commitPreview(runId, preview.previewId);
      assert.equal(committed.worldRevision, 1);
      assert.equal(freshStore.turnCount(runId), 1);
    } finally {
      freshStore.close();
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("deterministic policy units expand leader directives without full Agent calls", async () => {
  const { directory, runId, store, play } = fixture("policy-expansion");
  try {
    play.initialize({ runId });
    const preview = (await play.generatePreview(runId)).preview;
    assert.deepEqual(preview.agentDecisions.map((entry) => entry.actorId).sort(), [
      "engineer-imani", "hive-alpha", "medic-reyes", "pirate-captain-veyra", "security-chen",
    ]);
    assert.deepEqual(preview.policyDecisions.map((entry) => entry.actorId).sort(), [
      "pirate-hacker-nyx", "pirate-raider-holt", "swarm-drone-one", "swarm-drone-two", "swarm-stalker-kappa",
    ]);
    assert.ok(preview.policyDecisions.every((entry) => entry.leaderActorId === "pirate-captain-veyra" || entry.leaderActorId === "hive-alpha"));
    assert.ok(preview.policyDecisions.every((entry) => !entry.rationale.includes("provider")));
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("the bounded fixture planner can drive a complete 14-Turn encounter without admission or recovery failure", async () => {
  const { directory, runId, store, play } = fixture("full-encounter");
  try {
    let view = play.initialize({ runId });
    while (view.run.status === "running") {
      assert.ok(view.run.turn < view.run.turnLimit);
      const generated = await play.generatePreview(runId);
      assert.equal(generated.preview.factionPlans.rescue.actorIntents.length, view.ownActors.filter((actor) => actor.lifeState === "active").length);
      view = (await play.commitPreview(runId, generated.preview.previewId)).view;
    }
    assert.equal(view.run.turn, 14);
    assert.equal(view.run.status, "terminal");
    assert.equal(store.turnCount(runId), 14);
    assert.ok(["victory", "partial", "failure"].includes(view.outcomes.rescue));
    assert.equal(view.aftermath?.turnSequence, 13);
    assert.doesNotThrow(() => play.planning.verifyRun(runId));
    assert.equal(play.turns.recover(runId).world.turnCount, 14);
  } finally {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("P3 verification fails closed when Order or Preview evidence is changed", async () => {
  const orderFixture = fixture("tamper-order");
  try {
    orderFixture.play.initialize({ runId: orderFixture.runId });
    orderFixture.store.db.prepare(`UPDATE station_zero_v3_order_revisions SET order_json = '{}'
      WHERE run_id = ?`).run(orderFixture.runId);
    assert.throws(() => orderFixture.play.planning.verifyRun(orderFixture.runId), /Order row digest mismatch|Order digest differs/);
  } finally {
    orderFixture.store.close();
    rmSync(orderFixture.directory, { recursive: true, force: true });
  }

  const previewFixture = fixture("tamper-preview");
  try {
    previewFixture.play.initialize({ runId: previewFixture.runId });
    await previewFixture.play.generatePreview(previewFixture.runId);
    previewFixture.store.db.prepare(`UPDATE station_zero_v3_plan_previews SET preview_json = '{}'
      WHERE run_id = ?`).run(previewFixture.runId);
    assert.throws(() => previewFixture.play.planning.verifyRun(previewFixture.runId), /Plan Preview is inconsistent/);
  } finally {
    previewFixture.store.close();
    rmSync(previewFixture.directory, { recursive: true, force: true });
  }
});


test("the selected Preview remains resumable after partial Plan submission or P2 preparation", async () => {
  const partial = fixture("resume-partial-commit");
  try {
    partial.play.initialize({ runId: partial.runId });
    const preview = (await partial.play.generatePreview(partial.runId)).preview;
    const planning = partial.store.latestPlanning(partial.runId)!;
    partial.play.turns.submitPlan(partial.runId, planning.planningId, preview.factionPlans.rescue);

    const resumed = partial.play.resume(partial.runId);
    assert.equal(resumed.experience.canEditOrder, false);
    assert.equal(resumed.experience.canGeneratePreview, false);
    assert.equal(resumed.experience.canCommitPreview, true);
    const committed = await partial.play.commitPreview(partial.runId, preview.previewId);
    assert.equal(committed.worldRevision, 1);
    assert.equal(partial.store.turnCount(partial.runId), 1);
  } finally {
    partial.store.close();
    rmSync(partial.directory, { recursive: true, force: true });
  }

  const prepared = fixture("resume-prepared-commit");
  try {
    prepared.play.initialize({ runId: prepared.runId });
    const preview = (await prepared.play.generatePreview(prepared.runId)).preview;
    const planning = prepared.store.latestPlanning(prepared.runId)!;
    for (const factionId of ["rescue", "pirate", "swarm"] as const) {
      prepared.play.turns.submitPlan(prepared.runId, planning.planningId, preview.factionPlans[factionId]);
    }
    prepared.play.planning.markCommitted(prepared.runId, planning.planningId, preview.previewId);
    prepared.play.turns.prepare(prepared.runId, planning.planningId);
    assert.equal(prepared.store.getPlanning(prepared.runId, planning.planningId).status, "committed");

    const resumed = prepared.play.resume(prepared.runId);
    assert.equal(resumed.experience.canCommitPreview, true);
    const committed = await prepared.play.commitPreview(prepared.runId, preview.previewId);
    assert.equal(committed.worldRevision, 1);
    assert.equal(prepared.store.turnCount(prepared.runId), 1);
  } finally {
    prepared.store.close();
    rmSync(prepared.directory, { recursive: true, force: true });
  }
});
