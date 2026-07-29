import assert from "node:assert/strict";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import { ENGINEER_ID, MEDIC_ID, SECURITY_ID, initialWorld } from "../src/scenario.ts";
import { GameStore } from "../src/storage.ts";
import { evaluateAuthority } from "../src/team/authority.ts";
import { actorCanClaimMissionItem, compileTeamContext } from "../src/team/context.ts";
import { actorTaskId, TeamStore } from "../src/team/store.ts";
import { listAvailableActions, materializeAction } from "../src/world.ts";

function setup(runId = "run:team-context"): { game: GameStore; team: TeamStore } {
  const game = new GameStore(":memory:");
  game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
  game.setActiveRun(runId);
  const team = new TeamStore(game);
  team.initialize(runId);
  return { game, team };
}

function contextFor(team: TeamStore, actorId: string, policyMode: "autonomous" | "supervised" | "locked" = "autonomous", tokenBudget = 4_000) {
  return compileTeamContext({
    store: team.game,
    runId: team.game.activeRunId,
    task: team.getTask(actorTaskId(team.game.activeRunId, actorId)),
    profile: team.getProfile(actorId),
    goal: team.getGoal(),
    messages: team.listMessages(),
    policyMode,
    tokenBudget,
  });
}

test("Actor Contexts are deterministic, bounded, and materially role-local", () => {
  const { game, team } = setup();
  const engineer = contextFor(team, ENGINEER_ID);
  const engineerAgain = contextFor(team, ENGINEER_ID);
  const medic = contextFor(team, MEDIC_ID);
  const security = contextFor(team, SECURITY_ID);
  assert.deepEqual(engineer, engineerAgain);
  assert.notEqual(engineer.contextId, medic.contextId);
  assert.notEqual(medic.contextId, security.contextId);
  assert.ok(engineer.allowedActions.every((candidate) => candidate.actorId === ENGINEER_ID));
  assert.ok(medic.allowedActions.every((candidate) => candidate.actorId === MEDIC_ID));
  assert.ok(security.allowedActions.every((candidate) => candidate.actorId === SECURITY_ID));
  assert.ok(engineer.allowedActions.length <= 8);
  assert.ok(engineer.manifest.estimatedTokens <= engineer.manifest.tokenBudget);
  assert.equal(engineer.worldDigest, sha256(game.loadState()));

  const engineerObjectives = engineer.blocks.find((block) => block.kind === "objective")?.payload;
  const medicObjectives = medic.blocks.find((block) => block.kind === "objective")?.payload;
  assert.notDeepEqual(engineerObjectives, medicObjectives);
  game.close();
});

test("Actor local Context does not expose remote room objects", () => {
  const { game, team } = setup("run:team-local-knowledge");
  const state = game.loadState();
  const engineerMove = listAvailableActions(state, ENGINEER_ID).find((entry) => entry.actionId === "move:power-junction");
  const medicMove = listAvailableActions(state, MEDIC_ID).find((entry) => entry.actionId === "move:power-junction");
  const securityMove = listAvailableActions(state, SECURITY_ID).find((entry) => entry.actionId === "move:power-junction");
  assert.ok(engineerMove && medicMove && securityMove);
  const commands = [engineerMove, medicMove, securityMove].map((entry, index) => materializeAction(entry, `local-step-${index}`));
  game.applyTeamTick({
    tickId: "local-step",
    expectedWorldRevision: 0,
    intents: commands.map((command, index) => ({ commandSequence: index, command })),
  });
  const context = contextFor(team, ENGINEER_ID);
  const local = context.blocks.find((block) => block.kind === "local")?.payload as { systems?: unknown[]; hazards?: unknown[]; crew?: unknown[] };
  assert.deepEqual(local.systems, []);
  assert.deepEqual(local.hazards, []);
  assert.deepEqual(local.crew, []);
  const serialized = JSON.stringify(local);
  assert.ok(!serialized.includes("maintenance-breach"));
  assert.ok(!serialized.includes("crew-01"));
  game.close();
});

test("Context compiler selects optional blocks under budget and fails when required state cannot fit", () => {
  const { game, team } = setup("run:team-budget");
  team.sendMessage({
    senderActorId: ENGINEER_ID,
    recipientActorIds: [MEDIC_ID],
    kind: "fact-share",
    boundedSummary: "Cooling damage is visible on the public alarm panel.",
    channel: "local",
  });
  const full = contextFor(team, MEDIC_ID, "autonomous", 4_000);
  const reduced = contextFor(team, MEDIC_ID, "autonomous", 1_200);
  assert.ok(full.manifest.selectedBlockIds.length >= reduced.manifest.selectedBlockIds.length);
  assert.ok(reduced.manifest.omittedBlockIds.length >= 1);
  assert.throws(() => contextFor(team, MEDIC_ID, "autonomous", 256), /exceeds token budget/);
  game.close();
});

test("ABAC separates routine permit, supervised approval, and critical shutdown", () => {
  const { game, team } = setup("run:team-authority");
  const state = game.loadState();
  const worldDigest = sha256(state);
  const engineer = team.getProfile(ENGINEER_ID);
  const actor = state.agents[ENGINEER_ID];
  assert.ok(actor);
  const moveAction = listAvailableActions(state, ENGINEER_ID).find((entry) => entry.actionId === "move:power-junction");
  assert.ok(moveAction);
  const move = materializeAction(moveAction, "authority-move");
  if (move.kind === "team_tick") throw new Error("unexpected team action");
  const routine = evaluateAuthority(game.activeRunId, engineer, actor.capabilities, "action:routine", "context:routine", worldDigest, state, move, "autonomous");
  assert.equal(routine.outcome, "permit");

  const supervised = evaluateAuthority(game.activeRunId, engineer, actor.capabilities, "action:power", "context:power", worldDigest, state, {
    kind: "set_power", commandId: "authority-power", actorId: ENGINEER_ID, expectedRevision: 0, targetSystemId: "cooling", enabled: true,
  }, "supervised");
  assert.equal(supervised.outcome, "require-human");

  const shutdown = evaluateAuthority(game.activeRunId, engineer, actor.capabilities, "action:shutdown", "context:shutdown", worldDigest, state, {
    kind: "set_power", commandId: "authority-shutdown", actorId: ENGINEER_ID, expectedRevision: 0, targetSystemId: "life-support", enabled: false,
  }, "locked");
  assert.equal(shutdown.outcome, "deny");
  assert.equal(shutdown.attributes.target.criticality, "critical");
  game.close();
});

test("Authority Decisions are idempotent and Grants are exact, expiring, and single-use", () => {
  const { game, team } = setup("run:team-grant");
  const context = contextFor(team, SECURITY_ID, "supervised");
  const candidate = context.allowedActions.find((entry) => entry.actionId === "move:power-junction");
  assert.ok(candidate);
  const state = game.loadState();
  const decision = evaluateAuthority(game.activeRunId, team.getProfile(SECURITY_ID), state.agents[SECURITY_ID]!.capabilities,
    candidate.actionCandidateId, context.contextId, context.worldDigest, state, candidate.command, "supervised");
  assert.equal(team.putAuthorityDecision(decision).decisionId, decision.decisionId);
  assert.equal(team.putAuthorityDecision(decision).decisionId, decision.decisionId);

  const grant = team.issueGrant({
    actorId: SECURITY_ID,
    proposalId: "proposal:security:1",
    actionCandidateId: candidate.actionCandidateId,
    contextDigest: context.contextId,
    worldDigest: context.worldDigest,
    policyRevision: 1,
    operationKind: candidate.command.kind,
    targetId: candidate.actionId,
    expiresAtTick: 2,
    issuedBy: "player:local",
  });
  const consumed = team.consumeGrant(grant.grantId, grant.proposalId, context.contextId, context.worldDigest, 1);
  assert.equal(consumed.consumedAtTick, 1);
  assert.throws(() => team.consumeGrant(grant.grantId, grant.proposalId, context.contextId, context.worldDigest, 1), /consumed or expired/);
  assert.throws(() => team.consumeGrant(grant.grantId, "proposal:other", context.contextId, context.worldDigest, 1), /binding differs/);
  game.close();
});


test("expired delivered Messages remain historical and leave current Context", () => {
  const { game, team } = setup("run:team-expired-context");
  const task = team.getTask(actorTaskId(game.activeRunId, ENGINEER_ID));
  const context = compileTeamContext({
    store: game,
    runId: game.activeRunId,
    task,
    profile: team.getProfile(ENGINEER_ID),
    goal: team.getGoal(),
    messages: [{
      messageId: "team-message:expired",
      runId: game.activeRunId,
      senderActorId: MEDIC_ID,
      recipientActorIds: [ENGINEER_ID],
      kind: "status-update",
      referencedFactIds: [],
      referencedArtifactDigests: [],
      boundedSummary: "This message has expired.",
      channel: "local",
      createdTick: 0,
      expiryTick: 1,
      deliveredActorIds: [ENGINEER_ID],
      pendingActorIds: [],
      status: "expired",
      createdAt: "1970-01-01T00:00:00.000Z",
      updatedAt: "1970-01-01T00:00:01.000Z",
    }],
    policyMode: "autonomous",
  });
  const messages = context.blocks.find((block) => block.kind === "message")?.payload;
  assert.deepEqual(messages, []);
  game.close();
});


test("Team Context prevents mission-critical items from being stranded on incapable Actors", () => {
  const { game, team } = setup("run:team-critical-item-claim");
  const apply = (tickId: string, actionIds: Record<string, string>): void => {
    const state = game.loadState();
    const commands = [ENGINEER_ID, MEDIC_ID, SECURITY_ID].map((actorId, index) => {
      const action = listAvailableActions(state, actorId).find((entry) => entry.actionId === actionIds[actorId]);
      assert.ok(action, `${actorId} missing ${actionIds[actorId]}`);
      const command = materializeAction(action, `${tickId}:${index}`);
      if (command.kind === "team_tick") throw new Error("unexpected team action");
      return { commandSequence: state.revision * 3 + index, command };
    });
    const result = game.applyTeamTick({ tickId, expectedWorldRevision: state.revision, intents: commands });
    assert.equal(result.result.status, "accepted");
  };

  apply("critical-items:0", {
    [ENGINEER_ID]: "move:power-junction",
    [MEDIC_ID]: "move:power-junction",
    [SECURITY_ID]: "move:power-junction",
  });
  apply("critical-items:1", {
    [ENGINEER_ID]: "move:storage",
    [MEDIC_ID]: "move:medical-bay",
    [SECURITY_ID]: "move:storage",
  });

  const engineer = contextFor(team, ENGINEER_ID);
  const medic = contextFor(team, MEDIC_ID);
  const security = contextFor(team, SECURITY_ID);
  const actionIds = (context: ReturnType<typeof contextFor>) => context.allowedActions.map((entry) => entry.actionId);

  assert.ok(actionIds(engineer).includes("pickup:sealant:1"));
  assert.ok(actionIds(engineer).includes("pickup:spare-parts:2"));
  assert.ok(actionIds(medic).includes("pickup:medkit:1"));
  assert.ok(!actionIds(security).includes("pickup:sealant:1"));
  assert.ok(!actionIds(security).includes("pickup:spare-parts:2"));

  const primitiveSecurityActions = listAvailableActions(game.loadState(), SECURITY_ID).map((entry) => entry.actionId);
  assert.ok(primitiveSecurityActions.includes("pickup:sealant:1"));
  assert.ok(primitiveSecurityActions.includes("pickup:spare-parts:2"));
  game.close();
});


test("mission-item claim policy fails closed for missing Actors and leaves non-mission items general", () => {
  const state = initialWorld();
  assert.equal(actorCanClaimMissionItem(state, "missing-actor", "sealant"), false);
  assert.equal(actorCanClaimMissionItem(state, ENGINEER_ID, "sealant"), true);
  assert.equal(actorCanClaimMissionItem(state, SECURITY_ID, "sealant"), false);
  assert.equal(actorCanClaimMissionItem(state, SECURITY_ID, "unknown-item" as never), true);
});
