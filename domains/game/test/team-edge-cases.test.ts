import assert from "node:assert/strict";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import type { PrimitiveWorldCommand, WorldFact } from "../src/model.ts";
import { ENGINEER_ID, MEDIC_ID, SECURITY_ID, initialTeamWorld } from "../src/scenario.ts";
import { GameStore } from "../src/storage.ts";
import { candidateAllowed, evaluateAuthority } from "../src/team/authority.ts";
import { compileTeamContext, factVisibleToActor } from "../src/team/context.ts";
import type { TeamActionCandidate } from "../src/team/model.ts";
import { nextObjectiveForRole, objectiveSatisfied, objectiveStatus, TEAM_OBJECTIVE_GRAPH } from "../src/team/objectives.ts";
import { actorTaskId, TeamStore, TeamStoreError } from "../src/team/store.ts";
import { listAvailableActions, materializeAction } from "../src/world.ts";

function setup(runId: string): { game: GameStore; team: TeamStore } {
  const game = new GameStore(":memory:");
  game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
  game.setActiveRun(runId);
  const team = new TeamStore(game);
  team.initialize(runId);
  return { game, team };
}

function decisionFor(command: PrimitiveWorldCommand, mode: "autonomous" | "supervised" | "locked", state = initialTeamWorld()) {
  const game = new GameStore(":memory:");
  game.createRun({ runId: "run:authority-edge", scenarioVersion: 2, rulesetVersion: 3 });
  game.setActiveRun("run:authority-edge");
  const team = new TeamStore(game);
  team.initialize();
  const profile = team.getProfile(ENGINEER_ID);
  const result = evaluateAuthority(game.activeRunId, profile, state.agents[ENGINEER_ID]!.capabilities,
    `action:${command.kind}`, `context:${command.kind}`, sha256(state), state, command, mode);
  game.close();
  return result;
}

test("ABAC attributes cover every primitive operation and environment band", () => {
  const base = { commandId: "authority-edge", actorId: ENGINEER_ID, expectedRevision: 0 };
  const commands: PrimitiveWorldCommand[] = [
    { ...base, kind: "move", targetRoomId: "power-junction" },
    { ...base, kind: "pickup_item", itemId: "spare-parts", quantity: 1 },
    { ...base, kind: "repair_system", targetSystemId: "cooling" },
    { ...base, kind: "repair_system", targetSystemId: "communications" },
    { ...base, kind: "set_power", targetSystemId: "cooling", enabled: true },
    { ...base, kind: "seal_hull", targetHazardId: "maintenance-breach" },
    { ...base, kind: "contain_hazard", targetHazardId: "maintenance-breach" },
    { ...base, kind: "stabilize_crew", targetCrewId: "crew-01" },
    { ...base, kind: "send_distress", targetSystemId: "communications" },
    { ...base, kind: "wait" },
  ];
  const domains = commands.map((command) => decisionFor(command, "autonomous").attributes.target.domain);
  assert.deepEqual(domains, ["room", "item", "system", "system", "system", "hazard", "hazard", "crew", "mission", "time"]);
  assert.equal(decisionFor(commands[2]!, "autonomous").attributes.target.criticality, "critical");
  assert.equal(decisionFor(commands[3]!, "autonomous").attributes.target.criticality, "important");
  assert.equal(decisionFor(commands[5]!, "autonomous").attributes.action.riskTags.includes("irreversible"), true);
  assert.equal(decisionFor(commands[6]!, "autonomous").attributes.action.riskTags.includes("alternative-objective"), true);
  assert.equal(decisionFor(commands[7]!, "autonomous").attributes.action.riskTags.includes("medical"), true);
  assert.equal(decisionFor(commands[8]!, "autonomous").attributes.action.riskTags.includes("external-signal"), true);

  const low = initialTeamWorld();
  low.resources.oxygen = 40;
  low.resources.reactorHeat = 80;
  low.systems.communications!.integrity = 1;
  low.systems.communications!.powered = true;
  const lowDecision = decisionFor(commands[0]!, "autonomous", low);
  assert.equal(lowDecision.attributes.environment.oxygenBand, "low");
  assert.equal(lowDecision.attributes.environment.reactorBand, "high");
  assert.equal(lowDecision.attributes.environment.communicationAvailable, true);

  const critical = initialTeamWorld();
  critical.resources.oxygen = 20;
  critical.resources.reactorHeat = 95;
  critical.mission.status = "failure";
  critical.mission.reason = "test";
  const criticalDecision = decisionFor(commands[0]!, "autonomous", critical);
  assert.equal(criticalDecision.attributes.environment.oxygenBand, "critical");
  assert.equal(criticalDecision.attributes.environment.reactorBand, "critical");
  assert.equal(criticalDecision.attributes.environment.missionPhase, "terminal");

  const autonomousShutdown = decisionFor({ ...base, kind: "set_power", targetSystemId: "life-support", enabled: false }, "autonomous");
  assert.equal(autonomousShutdown.outcome, "require-human");
  const lockedHazard = decisionFor({ ...base, kind: "contain_hazard", targetHazardId: "maintenance-breach" }, "locked");
  assert.equal(lockedHazard.outcome, "require-human");
});

test("candidate authority helper admits permits and exact human grants only", () => {
  const candidate = { authorityOutcome: "permit" } as TeamActionCandidate;
  assert.equal(candidateAllowed(candidate, false), true);
  assert.equal(candidateAllowed({ ...candidate, authorityOutcome: "require-human" }, false), false);
  assert.equal(candidateAllowed({ ...candidate, authorityOutcome: "require-human" }, true), true);
  assert.equal(candidateAllowed({ ...candidate, authorityOutcome: "deny" }, true), false);
});

test("Objective predicates cover alternatives, powered dependencies, completion, and unknown IDs", () => {
  const state = initialTeamWorld();
  assert.equal(objectiveSatisfied(state, "cooling-operational"), false);
  state.systems.cooling!.integrity = 1;
  state.resources.reactorHeat = 20;
  assert.equal(objectiveSatisfied(state, "cooling-powered"), true);
  state.hazards["maintenance-breach"]!.contained = true;
  state.crew["crew-01"]!.stabilized = true;
  state.systems["life-support"]!.integrity = 1;
  state.systems["life-support"]!.powered = true;
  state.systems.communications!.integrity = 1;
  state.systems.communications!.powered = true;
  state.mission.distressSent = true;
  state.mission.status = "victory";
  state.mission.reason = "rescue_signal_verified";
  for (const node of TEAM_OBJECTIVE_GRAPH.nodes) {
    if (node.objectiveId === "breach-sealed") continue;
    assert.equal(objectiveSatisfied(state, node.objectiveId), true, node.objectiveId);
  }
  assert.equal(objectiveSatisfied(state, "breach-sealed"), false);
  state.hazards["maintenance-breach"]!.sealed = true;
  assert.equal(objectiveSatisfied(state, "breach-sealed"), true);
  assert.equal(objectiveStatus(state).every((status) => status.satisfied), true);
  assert.equal(nextObjectiveForRole(state, "engineer"), null);
  assert.equal(nextObjectiveForRole(state, "coordinator"), null);
  assert.throws(() => objectiveSatisfied(state, "unknown"), /unknown Objective/);
});

test("TeamStore exposes missing/corrupt identities and validates lease/message inputs", () => {
  const game = new GameStore(":memory:");
  game.createRun({ runId: "run:team-missing", scenarioVersion: 2, rulesetVersion: 3 });
  game.setActiveRun("run:team-missing");
  const team = new TeamStore(game);
  assert.throws(() => team.getGoal(), /not initialized/);
  team.initialize();
  assert.throws(() => team.getProfile("missing"), /unknown Team Profile/);
  assert.throws(() => team.getTask("task:missing"), /unknown Team Task/);
  assert.throws(() => team.acquireLease(actorTaskId(game.activeRunId, ENGINEER_ID), "", 0, 1), /valid lease/);
  assert.throws(() => team.acquireLease(actorTaskId(game.activeRunId, ENGINEER_ID), "owner", 0, 0), /valid lease/);
  assert.throws(() => team.sendMessage({ senderActorId: "missing", recipientActorIds: [MEDIC_ID], kind: "status-update", boundedSummary: "x", channel: "local" }), /actors must exist/);
  assert.throws(() => team.sendMessage({ senderActorId: ENGINEER_ID, recipientActorIds: [], kind: "status-update", boundedSummary: "x", channel: "local" }), /actors must exist/);
  assert.throws(() => team.sendMessage({ senderActorId: ENGINEER_ID, recipientActorIds: [MEDIC_ID], kind: "status-update", boundedSummary: "", channel: "local" }), /summary/);
  assert.throws(() => team.sendMessage({ senderActorId: ENGINEER_ID, recipientActorIds: [MEDIC_ID], kind: "status-update", boundedSummary: "x".repeat(513), channel: "local" }), /summary/);
  assert.throws(() => team.sendMessage({ senderActorId: ENGINEER_ID, recipientActorIds: [MEDIC_ID], kind: "status-update", boundedSummary: "x", channel: "local", ttlTicks: 0 }), /TTL/);

  game.db.prepare("UPDATE team_profiles SET value_json = ? WHERE run_id = ? AND actor_id = ?").run("{", game.activeRunId, MEDIC_ID);
  assert.throws(() => team.getProfile(MEDIC_ID), (error: unknown) => error instanceof TeamStoreError && error.code === "team_corrupt");
  game.close();
});

test("Messages support partial delivery and unchanged pending refresh", () => {
  const { game, team } = setup("run:team-partial-message");
  const state = game.loadState();
  const medicMove = listAvailableActions(state, MEDIC_ID).find((entry) => entry.actionId === "move:power-junction");
  assert.ok(medicMove);
  const move = materializeAction(medicMove, "partial-medic-move");
  game.applyTeamTick({ tickId: "partial-separate", expectedWorldRevision: 0, intents: [{ commandSequence: 0, command: move }] });
  const message = team.sendMessage({
    senderActorId: ENGINEER_ID,
    recipientActorIds: [MEDIC_ID, SECURITY_ID, SECURITY_ID],
    kind: "help-request",
    boundedSummary: "One recipient is local and one is remote.",
    channel: "local",
    ttlTicks: 4,
  });
  assert.equal(message.status, "pending");
  assert.deepEqual(message.deliveredActorIds, [SECURITY_ID]);
  assert.deepEqual(message.pendingActorIds, [MEDIC_ID]);
  const unchanged = team.refreshMessages().find((entry) => entry.messageId === message.messageId);
  assert.equal(unchanged?.status, "pending");
  game.close();
});

test("Authority persistence rejects identity drift and handles existing, missing, and expired Grants", () => {
  const { game, team } = setup("run:team-authority-edge");
  const state = game.loadState();
  const profile = team.getProfile(ENGINEER_ID);
  const move = materializeAction(listAvailableActions(state, ENGINEER_ID).find((entry) => entry.actionId === "move:power-junction")!, "authority-edge-move");
  if (move.kind === "team_tick") throw new Error("unexpected team action");
  const decision = evaluateAuthority(game.activeRunId, profile, state.agents[ENGINEER_ID]!.capabilities,
    "action:edge", "context:edge", sha256(state), state, move, "autonomous");
  team.putAuthorityDecision(decision);
  assert.throws(() => team.putAuthorityDecision({ ...decision, reason: "different" }), /identity differs/);

  const input = {
    actorId: ENGINEER_ID, proposalId: "proposal:edge", actionCandidateId: "action:edge",
    contextDigest: "context:edge", worldDigest: sha256(state), policyRevision: 1,
    operationKind: move.kind, targetId: "power-junction", expiresAtTick: 0, issuedBy: "player:edge",
  } as const;
  const grant = team.issueGrant(input);
  assert.equal(team.issueGrant(input).grantId, grant.grantId);
  assert.throws(() => team.consumeGrant("authority-grant:missing", input.proposalId, input.contextDigest, input.worldDigest, 0), /unknown Authority Grant/);
  assert.throws(() => team.consumeGrant(grant.grantId, input.proposalId, input.contextDigest, input.worldDigest, 1), /consumed or expired/);
  game.close();
});

test("terminal synchronization fails all Tasks once and is idempotent", () => {
  const { game, team } = setup("run:team-terminal-failure");
  let sequence = 0;
  while (game.loadState().mission.status === "running" && sequence < 24) {
    const state = game.loadState();
    const command: PrimitiveWorldCommand = {
      kind: "wait", commandId: `terminal-wait:${sequence}`, actorId: ENGINEER_ID, expectedRevision: state.revision,
    };
    game.applyTeamTick({ tickId: `terminal-tick:${sequence}`, expectedWorldRevision: state.revision, intents: [{ commandSequence: sequence, command }] });
    sequence += 1;
  }
  assert.equal(game.loadState().mission.status, "failure");
  const first = team.synchronizeTerminal();
  assert.equal(first.goal.status, "failed");
  assert.equal(first.tasks.every((task) => task.state === "failed"), true);
  const revision = first.goal.revision;
  const second = team.synchronizeTerminal();
  assert.equal(second.goal.revision, revision);
  team.verify();
  game.close();
});

test("Context validates default and invalid budgets and rejects unknown actor state", () => {
  const { game, team } = setup("run:team-context-edge");
  const task = team.getTask(actorTaskId(game.activeRunId, ENGINEER_ID));
  const profile = team.getProfile(ENGINEER_ID);
  const input = { store: game, runId: game.activeRunId, task, profile, goal: team.getGoal(), messages: [], policyMode: "autonomous" as const };
  assert.equal(compileTeamContext(input).manifest.tokenBudget, 4_000);
  assert.throws(() => compileTeamContext({ ...input, tokenBudget: 255 }), /at least 256/);
  assert.throws(() => compileTeamContext({ ...input, tokenBudget: 300.5 }), /at least 256/);
  assert.throws(() => compileTeamContext({ ...input, profile: { ...profile, actorId: "missing" }, task: { ...task, actorId: "missing" } }), /unknown team actor/);
  game.close();
});


test("Fact visibility is actor-local for actions and objects while telemetry remains public", () => {
  const state = initialTeamWorld();
  state.agents[ENGINEER_ID]!.location = "reactor";
  state.agents[MEDIC_ID]!.location = "medical-bay";
  state.agents[SECURITY_ID]!.location = "maintenance";
  const localFacts: Array<[WorldFact, string, boolean]> = [
    [{ kind: "agent_moved", actorId: ENGINEER_ID, fromRoomId: "power-junction", toRoomId: "reactor" }, ENGINEER_ID, true],
    [{ kind: "agent_moved", actorId: MEDIC_ID, fromRoomId: "power-junction", toRoomId: "medical-bay" }, ENGINEER_ID, false],
    [{ kind: "agent_waited", actorId: ENGINEER_ID }, ENGINEER_ID, true],
    [{ kind: "item_picked_up", actorId: MEDIC_ID, roomId: "medical-bay", itemId: "medkit", quantity: 1 }, ENGINEER_ID, false],
    [{ kind: "item_consumed", actorId: ENGINEER_ID, itemId: "spare-parts", quantity: 1, purpose: "repair:cooling" }, ENGINEER_ID, true],
    [{ kind: "health_changed", subjectType: "agent", subjectId: ENGINEER_ID, before: 100, after: 90, causes: ["reactor_heat_exposure"] }, ENGINEER_ID, true],
    [{ kind: "health_changed", subjectType: "agent", subjectId: MEDIC_ID, before: 100, after: 90, causes: ["low_oxygen"] }, ENGINEER_ID, false],
    [{ kind: "health_changed", subjectType: "crew", subjectId: "crew-01", before: 50, after: 49, causes: ["untreated_injury"] }, ENGINEER_ID, true],
    [{ kind: "system_repaired", systemId: "cooling", beforeIntegrity: 0.2, afterIntegrity: 1 }, ENGINEER_ID, true],
    [{ kind: "power_state_changed", systemId: "communications", powered: true }, ENGINEER_ID, false],
    [{ kind: "hull_breach_sealed", hazardId: "maintenance-breach" }, SECURITY_ID, true],
    [{ kind: "hull_breach_sealed", hazardId: "maintenance-breach" }, ENGINEER_ID, false],
    [{ kind: "hazard_contained", hazardId: "maintenance-breach", actorId: SECURITY_ID }, SECURITY_ID, true],
    [{ kind: "hazard_contained", hazardId: "maintenance-breach", actorId: ENGINEER_ID }, ENGINEER_ID, true],
    [{ kind: "crew_stabilized", crewId: "crew-01", health: 62 }, MEDIC_ID, true],
    [{ kind: "crew_stabilized", crewId: "crew-01", health: 62 }, ENGINEER_ID, false],
  ];
  for (const [fact, actorId, expected] of localFacts) {
    assert.equal(factVisibleToActor(fact, state, actorId), expected, `${fact.kind}:${actorId}`);
  }
  const publicFacts: WorldFact[] = [
    { kind: "distress_signal_sent", systemId: "communications" },
    { kind: "battery_consumed", amount: 2, poweredSystems: ["cooling"] },
    { kind: "oxygen_changed", before: 75, after: 74, causes: ["baseline_consumption"] },
    { kind: "reactor_heat_changed", before: 40, after: 46, causes: ["cooling_unavailable"] },
    { kind: "mission_succeeded", reason: "rescue_signal_verified" },
    { kind: "mission_failed", reason: "reactor_meltdown" },
  ];
  for (const fact of publicFacts) assert.equal(factVisibleToActor(fact, state, ENGINEER_ID), true, fact.kind);
  assert.equal(factVisibleToActor(publicFacts[0]!, state, "missing"), false);
});
