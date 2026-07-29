import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import type { PrimitiveWorldCommand } from "../src/model.ts";
import { ProviderAdapterError } from "../src/providers/types.ts";
import { ENGINEER_ID, MEDIC_ID, SECURITY_ID } from "../src/scenario.ts";
import { GameStore } from "../src/storage.ts";
import { TeamHost, type TeamFaultPoint } from "../src/team/engine.ts";
import type { CompiledTeamContext, TeamProviderDecision } from "../src/team/model.ts";
import { FixtureTeamProvider, type TeamDecisionProvider } from "../src/team/providers.ts";
import { TeamStore } from "../src/team/store.ts";
import { listAvailableActions, materializeAction } from "../src/world.ts";

const TEAM_DIGEST = "a8ef1f491c35720ed02e66f004ccd7f3466f78991dcafecd442ceae66b09ceb7";
const TEAM_SEAL_DIGEST = "0913c9cacb05af3e1dc1bab3a43e3a3a36efd5277da127c18182d05166939bf4";

function fixture(runId = "run:team-engine"): { directory: string; path: string; game: GameStore } {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-team-engine-"));
  const path = join(directory, "world.sqlite3");
  const game = new GameStore(path);
  game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
  game.setActiveRun(runId);
  return { directory, path, game };
}

class CountingTeamProvider implements TeamDecisionProvider {
  readonly providerId = "counting-team-fixture-v1";
  readonly delegate: FixtureTeamProvider;
  calls = 0;
  constructor(options: ConstructorParameters<typeof FixtureTeamProvider>[0] = {}) {
    this.delegate = new FixtureTeamProvider(options);
  }
  async decide(context: CompiledTeamContext): Promise<TeamProviderDecision> {
    this.calls += 1;
    const decision = await this.delegate.decide(context);
    return { ...decision, providerId: this.providerId };
  }
  evidenceMetadata(): Record<string, unknown> { return { calls: this.calls }; }
}

class ActionProvider implements TeamDecisionProvider {
  readonly providerId: string;
  readonly choices: Record<string, string | null>;
  constructor(choices: Record<string, string | null>, providerId = "action-team-provider") {
    this.choices = choices;
    this.providerId = providerId;
  }
  async decide(context: CompiledTeamContext): Promise<TeamProviderDecision> {
    const desired = Object.hasOwn(this.choices, context.actorId) ? this.choices[context.actorId] : "wait";
    const candidate = desired === null || desired === undefined ? null : context.allowedActions.find((entry) => entry.actionId === desired) ?? null;
    return {
      providerId: this.providerId,
      contextId: context.contextId,
      selectedActionCandidateId: candidate?.actionCandidateId ?? null,
      confidence: candidate ? 0.9 : 0,
      rationale: candidate ? `Selected ${candidate.actionId}` : "Declined",
    };
  }
}

class MessageAwareContainmentProvider implements TeamDecisionProvider {
  readonly providerId = "message-aware-containment-v1";
  readonly delegate = new FixtureTeamProvider();

  async decide(context: CompiledTeamContext): Promise<TeamProviderDecision> {
    if (context.actorId !== SECURITY_ID) {
      const decision = await this.delegate.decide(context);
      return { ...decision, providerId: this.providerId };
    }
    const messageBlock = context.blocks.find((block) => block.kind === "message");
    const messages = Array.isArray(messageBlock?.payload) ? messageBlock.payload as Array<{ kind?: string; boundedSummary?: string }> : [];
    const containmentAssigned = messages.some((message) =>
      message.kind === "task-offer" && message.boundedSummary === "Security: contain the maintenance breach now.");
    if (containmentAssigned) {
      const decision = await this.delegate.decide(context);
      return { ...decision, providerId: this.providerId };
    }
    const wait = context.allowedActions.find((candidate) => candidate.actionId === "wait") ?? null;
    return {
      providerId: this.providerId,
      contextId: context.contextId,
      selectedActionCandidateId: wait?.actionCandidateId ?? null,
      confidence: wait ? 1 : 0,
      rationale: wait ? "No delivered containment assignment is visible." : "No admitted action is available.",
    };
  }
}

function driveToHazardChoice(game: GameStore): void {
  const command = (actorId: string, actionId: string, commandId: string): PrimitiveWorldCommand => {
    const state = game.loadState();
    const action = listAvailableActions(state, actorId).find((entry) => entry.actionId === actionId);
    assert.ok(action, `${actorId} missing ${actionId}`);
    const result = materializeAction(action, commandId);
    if (result.kind === "team_tick") throw new Error("unexpected team command");
    return result;
  };
  const apply = (tickId: string, commands: PrimitiveWorldCommand[]): void => {
    const state = game.loadState();
    const result = game.applyTeamTick({
      tickId,
      expectedWorldRevision: state.revision,
      intents: commands.map((entry, index) => ({ commandSequence: state.revision * 3 + index, command: entry })),
    });
    assert.equal(result.result.status, "accepted");
  };
  apply("setup:0", [
    command(ENGINEER_ID, "move:power-junction", "setup:e0"),
    command(MEDIC_ID, "move:power-junction", "setup:m0"),
    command(SECURITY_ID, "move:power-junction", "setup:s0"),
  ]);
  apply("setup:1", [
    command(ENGINEER_ID, "move:storage", "setup:e1"),
    command(MEDIC_ID, "wait", "setup:m1"),
    command(SECURITY_ID, "move:storage", "setup:s1"),
  ]);
  apply("setup:2", [
    command(ENGINEER_ID, "pickup:sealant:1", "setup:e2"),
    command(MEDIC_ID, "wait", "setup:m2"),
    command(SECURITY_ID, "move:maintenance", "setup:s2"),
  ]);
  apply("setup:3", [
    command(ENGINEER_ID, "move:maintenance", "setup:e3"),
    command(MEDIC_ID, "wait", "setup:m3"),
    command(SECURITY_ID, "wait", "setup:s3"),
  ]);
}

test("TeamHost completes 18 atomic rounds with three persistent specialists", async () => {
  const { directory, game } = fixture();
  try {
    const provider = new CountingTeamProvider();
    const host = new TeamHost(game, provider);
    const result = await host.run(game.activeRunId, 256);
    const state = game.loadState();
    assert.equal(state.mission.status, "victory");
    assert.equal(state.revision, 18);
    assert.equal(state.turn, 18);
    assert.equal(provider.calls, 54);
    assert.equal(result.rounds.length, 18);
    assert.ok(result.rounds.every((round) => round.status === "completed"));
    assert.equal(game.eventCount(), 18);
    assert.equal(sha256(state), TEAM_DIGEST);
    assert.equal(game.verifyReplay().digest, TEAM_DIGEST);
    assert.equal(result.projection.goal.status, "succeeded");
    assert.ok(result.projection.tasks.every((task) => task.state === "completed"));
    const proposalCount = Number(game.db.prepare("SELECT COUNT(*) AS count FROM team_proposals").get()!.count);
    const observationCount = host.execution.authority.listObservations(game.activeRunId).length;
    assert.equal(proposalCount, 54);
    assert.equal(observationCount, 18);
    host.team.verify();
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});



test("Engineer sealing is a distinct verified 22-Round victory path", async () => {
  const { directory, game } = fixture("run:team-engineer-seal");
  try {
    const provider = new CountingTeamProvider({ breachStrategy: "engineer-seal" });
    const host = new TeamHost(game, provider);
    const result = await host.run(game.activeRunId, 320);
    const state = game.loadState();
    assert.equal(state.mission.status, "victory");
    assert.equal(state.revision, 22);
    assert.equal(result.rounds.length, 22);
    assert.ok(result.rounds.every((round) => round.status === "completed"));
    assert.equal(state.hazards["maintenance-breach"]?.sealed, true);
    assert.equal(state.hazards["maintenance-breach"]?.contained, false);
    assert.equal(state.resources.batteryCharge, 0);
    assert.equal(sha256(state), TEAM_SEAL_DIGEST);
    assert.equal(game.verifyReplay().digest, TEAM_SEAL_DIGEST);
    assert.equal(provider.calls, 66);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("communication reachability changes the deterministic Team outcome", async () => {
  const execute = async (channel: "local" | "station-radio") => {
    const runId = `run:team-communication:${channel}`;
    const { directory, game } = fixture(runId);
    const host = new TeamHost(game, new MessageAwareContainmentProvider());
    host.initialize(runId);
    const message = host.team.sendMessage({
      senderActorId: ENGINEER_ID,
      recipientActorIds: [SECURITY_ID],
      kind: "task-offer",
      boundedSummary: "Security: contain the maintenance breach now.",
      channel,
      ttlTicks: 22,
    }, runId);
    const initialStatus = message.status;
    const result = await host.run(runId, 320);
    const terminal = game.loadState(runId);
    const retained = host.team.listMessages(runId).find((entry) => entry.messageId === message.messageId);
    const output = { directory, game, terminal, result, initialStatus, retained };
    return output;
  };

  const local = await execute("local");
  const radio = await execute("station-radio");
  try {
    assert.equal(local.initialStatus, "delivered");
    assert.equal(local.terminal.mission.status, "victory");
    assert.equal(local.terminal.hazards["maintenance-breach"]?.contained, true);
    assert.equal(local.result.rounds.every((round) => round.status === "completed"), true);

    assert.equal(radio.initialStatus, "pending");
    assert.equal(radio.terminal.mission.status, "failure");
    assert.equal(radio.terminal.mission.reason, "power_exhausted");
    assert.equal(radio.terminal.hazards["maintenance-breach"]?.contained, false);
    assert.equal(radio.retained?.status, "delivered");
    assert.equal(radio.result.rounds.every((round) => round.status === "completed"), true);
  } finally {
    local.game.close();
    radio.game.close();
    rmSync(local.directory, { recursive: true, force: true });
    rmSync(radio.directory, { recursive: true, force: true });
  }
});

const faultPoints: TeamFaultPoint[] = [
  "after_context_persisted",
  "after_provider_call",
  "after_proposal_persisted",
  "after_tick_plan_persisted",
  "after_dispatch_prepared",
  "after_world_apply",
  "after_observation_persisted",
  "before_task_advance",
];

test("every TeamHost interruption boundary converges without duplicate World Ticks", async () => {
  for (const point of faultPoints) {
    const runId = `run:team-fault:${point}`;
    const { directory, path, game } = fixture(runId);
    const provider = new CountingTeamProvider();
    let injected = false;
    try {
      const crashing = new TeamHost(game, provider, {
        faultInjector(current) {
          if (!injected && current === point) {
            injected = true;
            throw new Error(`injected:${point}`);
          }
        },
      });
      for (let index = 0; index < 16 && !injected; index += 1) {
        try { await crashing.step(runId); }
        catch (error) { assert.match(String(error), new RegExp(`injected:${point}`)); }
      }
      assert.equal(injected, true, point);
      game.close();

      const reopened = new GameStore(path, { activeRunId: runId });
      try {
        const fresh = new TeamHost(reopened, provider);
        const result = await fresh.run(runId, 256);
        assert.equal(reopened.loadState(runId).mission.status, "victory", point);
        assert.equal(reopened.eventCount(runId), 18, point);
        assert.equal(sha256(reopened.loadState(runId)), TEAM_DIGEST, point);
        assert.equal(result.rounds.length, 18, point);
        assert.ok(result.rounds.every((round) => round.status === "completed"), point);
        assert.equal(fresh.execution.authority.listDispatches(runId).length, 18, point);
        assert.equal(fresh.execution.authority.listObservations(runId).length, 18, point);
        fresh.team.verify(runId);
      } finally {
        reopened.close();
      }
    } finally {
      try { game.close(); } catch {}
      rmSync(directory, { recursive: true, force: true });
    }
  }
});

test("one failed specialist does not block unrelated Actor progress", async () => {
  const { directory, game } = fixture("run:team-provider-failure");
  try {
    const provider = new CountingTeamProvider({ failActors: [SECURITY_ID] });
    const host = new TeamHost(game, provider);
    const result = await host.run(game.activeRunId, 15);
    assert.ok(game.loadState().revision >= 2);
    const securityTask = result.projection.tasks.find((task) => task.actorId === SECURITY_ID);
    assert.equal(securityTask?.state, "waiting");
    assert.equal(securityTask?.wait?.kind, "provider");
    const latest = [...result.rounds].reverse().find((round) => host.execution.listProposals(round.roundId).length > 0);
    assert.ok(latest);
    const proposals = host.execution.listProposals(latest.roundId);
    assert.ok(proposals.some((proposal) => proposal.actorId === ENGINEER_ID));
    assert.ok(proposals.some((proposal) => proposal.actorId === MEDIC_ID));
    assert.ok(!proposals.some((proposal) => proposal.actorId === SECURITY_ID));
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("conflicting seal and containment Proposals select one legal hazard action deterministically", async () => {
  const { directory, game } = fixture("run:team-conflict");
  try {
    driveToHazardChoice(game);
    const provider = new ActionProvider({
      [ENGINEER_ID]: "seal:maintenance-breach",
      [MEDIC_ID]: "wait",
      [SECURITY_ID]: "contain:maintenance-breach",
    });
    const host = new TeamHost(game, provider);
    const result = await host.run(game.activeRunId, 7);
    assert.equal(game.loadState().revision, 5);
    const round = result.rounds.at(-1);
    assert.equal(round?.status, "completed");
    const proposals = host.execution.listProposals(round!.roundId);
    const hazard = proposals.filter((proposal) => ["seal_hull", "contain_hazard"].includes(proposal.command.kind));
    assert.equal(hazard.length, 2);
    assert.equal(hazard.filter((proposal) => proposal.status === "verified").length, 1);
    assert.equal(hazard.filter((proposal) => proposal.status === "rejected").length, 1);
    const event = game.events().at(-1);
    assert.equal(event?.intentReceipts?.length, 2);
    assert.equal(event?.intentReceipts?.filter((receipt) => ["seal_hull", "contain_hazard"].includes(receipt.commandKind)).length, 1);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("supervised high-risk Proposals wait for an exact single-use Grant", async () => {
  const { directory, game } = fixture("run:team-authority-engine");
  try {
    driveToHazardChoice(game);
    const provider = new ActionProvider({
      [ENGINEER_ID]: "seal:maintenance-breach",
      [MEDIC_ID]: null,
      [SECURITY_ID]: "contain:maintenance-breach",
    });
    const host = new TeamHost(game, provider, { policyMode: "supervised" });
    const blocked = await host.run(game.activeRunId, 8);
    assert.equal(blocked.steps.at(-1)?.status, "authority_required");
    assert.equal(game.loadState().revision, 4);
    const round = blocked.rounds.at(-1)!;
    const proposal = host.execution.listProposals(round.roundId).find((entry) => entry.actorId === SECURITY_ID)!;
    assert.equal(proposal.authorityOutcome, "require-human");
    const grant = host.team.issueGrant({
      actorId: proposal.actorId,
      proposalId: proposal.proposalId,
      actionCandidateId: proposal.actionCandidateId,
      contextDigest: proposal.contextId,
      worldDigest: proposal.worldDigest,
      policyRevision: 1,
      operationKind: proposal.command.kind,
      targetId: "maintenance-breach",
      expiresAtTick: 5,
      issuedBy: "player:test",
    });
    const resumed = await host.run(game.activeRunId, 4);
    assert.equal(game.loadState().revision, 5);
    assert.equal(resumed.rounds.at(-1)?.status, "completed");
    assert.equal(host.team.listAuthorityGrants().find((entry) => entry.grantId === grant.grantId)?.consumedAtTick, 4);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("world drift during concurrent cognition supersedes all stale Team Decisions", async () => {
  const { directory, game } = fixture("run:team-cognition-drift");
  try {
    let mutated = false;
    const drifting: TeamDecisionProvider = {
      providerId: "drifting-team-provider",
      async decide(context) {
        if (!mutated) {
          mutated = true;
          const state = game.loadState();
          const wait = listAvailableActions(state, ENGINEER_ID).find((entry) => entry.actionId === "wait")!;
          const command = materializeAction(wait, "team-provider-drift");
          game.applyTeamTick({ tickId: "provider-drift", expectedWorldRevision: state.revision, intents: [{ commandSequence: 0, command }] });
        }
        const candidate = context.allowedActions[0] ?? null;
        return { providerId: "drifting-team-provider", contextId: context.contextId, selectedActionCandidateId: candidate?.actionCandidateId ?? null, confidence: 1, rationale: "stale on purpose" };
      },
    };
    const host = new TeamHost(game, drifting);
    assert.equal((await host.step()).status, "initialized");
    assert.equal((await host.step()).status, "contexts_prepared");
    assert.equal((await host.step()).status, "proposals_recorded");
    const blocked = await host.step();
    assert.equal(blocked.status, "blocked");
    assert.equal(game.eventCount(), 1);
    assert.equal(Number(game.db.prepare("SELECT COUNT(*) AS count FROM team_proposals").get()!.count), 0);
    assert.ok(host.team.listTasks().filter((task) => task.actorId).every((task) => task.wait?.kind === "replan"));
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("TeamHost validates the run step budget and technical Provider failure shape", async () => {
  const { directory, game } = fixture("run:team-budget-provider");
  try {
    const failed: TeamDecisionProvider = {
      providerId: "failed-team-provider",
      async decide() { throw new ProviderAdapterError("unavailable", "offline"); },
    };
    const host = new TeamHost(game, failed);
    await assert.rejects(() => host.run(game.activeRunId, 0), /maximumSteps/);
    const result = await host.run(game.activeRunId, 4);
    assert.equal(result.steps.length, 4);
    assert.equal(result.steps.at(-1)?.status, "blocked");
    assert.equal(game.eventCount(), 0);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("player Task redirect supersedes a prepared Context before Provider admission", async () => {
  const { directory, game } = fixture("run:team-task-redirect");
  try {
    const provider = new ActionProvider({
      [ENGINEER_ID]: "move:power-junction",
      [MEDIC_ID]: "move:power-junction",
      [SECURITY_ID]: "move:power-junction",
    });
    const host = new TeamHost(game, provider);
    assert.equal((await host.step()).status, "initialized");
    assert.equal((await host.step()).status, "contexts_prepared");
    const engineerTask = host.team.listTasks().find((task) => task.actorId === ENGINEER_ID)!;
    host.team.transitionTask(engineerTask.taskId, {
      state: "ready",
      activeObjectiveId: "communications-operational",
      preparedContextDigest: null,
      admittedProposalId: null,
      wait: null,
    }, "team.task-test-redirected", { objectiveId: "communications-operational" });
    assert.equal((await host.step()).status, "proposals_recorded");
    const round = host.execution.listRounds(game.activeRunId)[0]!;
    const proposals = host.execution.listProposals(round.roundId);
    assert.ok(!proposals.some((proposal) => proposal.actorId === ENGINEER_ID));
    assert.ok(proposals.some((proposal) => proposal.actorId === MEDIC_ID));
    assert.ok(proposals.some((proposal) => proposal.actorId === SECURITY_ID));
    const redirected = host.team.getTask(engineerTask.taskId);
    assert.equal(redirected.wait?.kind, "replan");
    assert.match(redirected.wait?.reason ?? "", /Task changed after Context preparation/);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});
