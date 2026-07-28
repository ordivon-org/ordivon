import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { createGameServer } from "../src/server.ts";
import { MissionControlService } from "../src/mission-control/service.ts";
import { createMissionControlView, deriveInterventions, factSummary, missionControlEncodedSize } from "../src/mission-control/projection.ts";
import { GameStore } from "../src/storage.ts";
import { TeamExecutionStore } from "../src/team/execution-store.ts";
import type { ActionProposal } from "../src/team/model.ts";
import { FixtureTeamProvider } from "../src/team/providers.ts";
import { TeamStore } from "../src/team/store.ts";

function serviceFixture(runId: string) {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-m4-mission-control-"));
  const game = new GameStore(join(directory, "world.sqlite3"));
  const service = new MissionControlService(game, () => new FixtureTeamProvider());
  service.initialize({ runId, authorityPolicyMode: "autonomous", providers: { "engineer-01": "fixture", "medic-01": "fixture", "security-01": "fixture" } });
  return { directory, game, service };
}

async function listen(game: ReturnType<typeof createGameServer>): Promise<string> {
  await new Promise<void>((resolve) => game.server.listen(0, "127.0.0.1", resolve));
  const address = game.server.address();
  if (!address || typeof address === "string") throw new Error("server did not expose a TCP address");
  return `http://127.0.0.1:${address.port}`;
}

async function request(base: string, path: string, body?: unknown) {
  const response = await fetch(`${base}${path}`, body === undefined ? undefined : {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body),
  });
  return { status: response.status, body: await response.json() as any };
}

test("Mission Control exposes proposal review before mutation and commits at most one verified Tick", async () => {
  const { directory, game, service } = serviceFixture("run:m4-boundaries");
  try {
    const review = await service.advance("run:m4-boundaries", "proposal-review");
    assert.equal(review.boundary, "proposal-review");
    assert.equal(review.view.generatedFrom.worldRevision, 0);
    assert.equal(review.view.currentRound?.phase, "proposal-review");
    assert.equal(review.view.currentRound?.actors.length, 3);

    const committed = await service.advance("run:m4-boundaries", "tick-verified");
    assert.equal(committed.boundary, "tick-verified");
    assert.equal(committed.view.generatedFrom.worldRevision, 1);
    assert.equal(committed.view.currentRound?.phase, "verified");
    assert.ok(committed.view.timeline[0]?.facts.length);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Mission Control completes the Fixture mission with bounded pure state reads", async () => {
  const { directory, game, service } = serviceFixture("run:m4-complete");
  try {
    for (let tick = 0; tick < 24 && service.state("run:m4-complete").run.status === "running"; tick += 1) {
      const review = await service.advance("run:m4-complete", "proposal-review");
      assert.ok(["proposal-review", "terminal"].includes(review.boundary));
      if (review.boundary === "terminal") break;
      const committed = await service.advance("run:m4-complete", "tick-verified");
      assert.ok(["tick-verified", "terminal"].includes(committed.boundary));
    }
    const view = service.state("run:m4-complete");
    assert.equal(view.run.status, "victory");
    assert.equal(view.generatedFrom.worldRevision, 18);
    assert.ok(view.mission.score && view.mission.score > 1_000);
    assert.ok(view.actors.every((actor) => actor.evidence.some((entry) => entry.stage === "verified")));
    assert.ok(missionControlEncodedSize(view) <= 64 * 1024, missionControlEncodedSize(view).toString());

    const journalBefore = game.db.prepare("SELECT COUNT(*) AS count FROM host_journal WHERE run_id = ?").get("run:m4-complete") as { count: number };
    const first = createMissionControlView(game, "run:m4-complete");
    const second = createMissionControlView(game, "run:m4-complete");
    const journalAfter = game.db.prepare("SELECT COUNT(*) AS count FROM host_journal WHERE run_id = ?").get("run:m4-complete") as { count: number };
    assert.deepEqual(second, first);
    assert.equal(Number(journalAfter.count), Number(journalBefore.count));
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Mission Control configuration and pause/resume commands are durable", async () => {
  const { directory, game, service } = serviceFixture("run:m4-command");
  try {
    service.command("run:m4-command", { action: "pause", actorId: "medic-01" });
    service.command("run:m4-command", { action: "set-provider", actorId: "engineer-01", provider: "codex-hermes" });
    service.command("run:m4-command", { action: "set-authority-policy", policyMode: "locked" });
    const review = await service.advance("run:m4-command", "proposal-review");
    assert.equal(review.view.actors.find((actor) => actor.actorId === "medic-01")?.controlMode, "paused");
    assert.ok(!review.view.currentRound?.actors.some((actor) => actor.actorId === "medic-01"));
    assert.deepEqual(review.view.actors.find((actor) => actor.actorId === "engineer-01")?.providerOrder, ["codex-hermes"]);
    assert.equal(review.view.configuration?.authorityPolicyMode, "locked");

    service.command("run:m4-command", { action: "resume", actorId: "medic-01" });
    assert.equal(service.state("run:m4-command").actors.find((actor) => actor.actorId === "medic-01")?.controlMode, "active");
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("resource mismatch is visible before a Security spare-parts Proposal commits", async () => {
  const { directory, game, service } = serviceFixture("run:m4-resource-warning");
  try {
    await service.advance("run:m4-resource-warning", "proposal-review");
    const team = new TeamStore(game);
    const execution = new TeamExecutionStore(team);
    const projection = team.projection("run:m4-resource-warning", false);
    const round = execution.listRounds("run:m4-resource-warning")[0]!;
    const base = execution.listProposals(round.roundId)[0]!;
    const proposal: ActionProposal = {
      ...base,
      proposalId: "proposal:security-spare-parts",
      actorId: "security-01",
      actorTaskId: projection.tasks.find((task) => task.actorId === "security-01")!.taskId,
      command: { kind: "pickup_item", commandId: "command:security-spare-parts", actorId: "security-01", expectedRevision: 0, itemId: "spare-parts", quantity: 2 },
      status: "proposed",
      authorityOutcome: "permit",
    };
    const cards = deriveInterventions(game.loadState("run:m4-resource-warning"), projection, [proposal]);
    assert.equal(cards.find((card) => card.kind === "resource-mismatch")?.severity, "critical");
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Mission Control HTTP API initializes, advances, commands, paginates, and reads without writes", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-m4-http-"));
  const game = createGameServer({ dbPath: join(directory, "world.sqlite3"), teamProviderFactory: () => new FixtureTeamProvider() });
  try {
    const base = await listen(game);
    const initialized = await request(base, "/api/mission-control/initialize", { runId: "run:m4-http", authorityPolicyMode: "supervised", providers: { "engineer-01": "fixture", "medic-01": "fixture", "security-01": "fixture" } });
    assert.equal(initialized.status, 201);
    assert.equal(initialized.body.initialized, true);
    const journalBefore = Number((game.store.db.prepare("SELECT COUNT(*) AS count FROM host_journal WHERE run_id = ?").get("run:m4-http") as { count: number }).count);
    const state = await request(base, "/api/mission-control/state?runId=run:m4-http");
    const stateAgain = await request(base, "/api/mission-control/state?runId=run:m4-http");
    assert.deepEqual(stateAgain.body, state.body);
    const journalAfter = Number((game.store.db.prepare("SELECT COUNT(*) AS count FROM host_journal WHERE run_id = ?").get("run:m4-http") as { count: number }).count);
    assert.equal(journalAfter, journalBefore);

    const review = await request(base, "/api/mission-control/advance?runId=run:m4-http", { until: "proposal-review" });
    assert.equal(review.body.boundary, "proposal-review");
    const paused = await request(base, "/api/mission-control/command?runId=run:m4-http", { action: "pause", actorId: "medic-01" });
    assert.equal(paused.body.view.actors.find((actor: any) => actor.actorId === "medic-01").controlMode, "paused");
    const timeline = await request(base, "/api/mission-control/timeline?runId=run:m4-http&limit=5");
    assert.equal(timeline.status, 200);
    assert.ok(timeline.body.items.length <= 5);
  } finally {
    await game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});


test("Mission Control exposes setup state and rejects invalid initialization or advance inputs", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-m4-setup-"));
  const game = new GameStore(join(directory, "world.sqlite3"));
  const service = new MissionControlService(game, () => new FixtureTeamProvider());
  try {
    game.createRun({ runId: "run:m4-uninitialized", scenarioVersion: 2, rulesetVersion: 3 });
    const view = createMissionControlView(game, "run:m4-uninitialized");
    assert.equal(view.initialized, false);
    assert.equal(view.run.status, "setup");
    assert.deepEqual(view.actors, []);
    assert.equal(view.controls.canConfigure, true);
    await assert.rejects(() => service.advance("run:m4-uninitialized", "proposal-review"), /not initialized/);
    await assert.rejects(() => service.advance("run:m4-uninitialized", "proposal-review", 0), /maximumInternalSteps/);
    assert.throws(() => service.initialize({ runId: "" }), /runId/);
    assert.throws(() => service.initialize({ runId: "run:default" }), /Scenario v2/);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("supervised Mission Control explains, approves, and denies exact authority Proposals", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-m4-authority-"));
  const game = new GameStore(join(directory, "world.sqlite3"));
  const service = new MissionControlService(game, () => new FixtureTeamProvider());
  try {
    service.initialize({ runId: "run:m4-approve", authorityPolicyMode: "supervised" });
    let authority = null as Awaited<ReturnType<MissionControlService["advance"]>> | null;
    for (let tick = 0; tick < 10 && !authority; tick += 1) {
      const review = await service.advance("run:m4-approve", "proposal-review");
      assert.equal(review.boundary, "proposal-review");
      const result = await service.advance("run:m4-approve", "tick-verified");
      if (result.boundary === "authority") authority = result;
    }
    assert.ok(authority);
    const card = authority.view.inbox.find((entry) => entry.kind === "authority-request");
    assert.ok(card);
    assert.match(card.explanation, /authority|policy/i);
    assert.ok(card.consequence.length > 20);
    assert.ok(card.urgency.length > 5);
    const proposalId = card.commands.find((command) => command.action === "approve")?.proposalId;
    assert.ok(proposalId);
    assert.throws(() => service.command("run:m4-approve", { action: "approve", proposalId, expiresAtTick: -1 }), /expiresAtTick/);
    const grant = service.command("run:m4-approve", { action: "approve", proposalId, issuedBy: "player:test" }) as { proposalId: string };
    assert.equal(grant.proposalId, proposalId);
    const resumed = await service.advance("run:m4-approve", "tick-verified");
    assert.equal(resumed.boundary, "tick-verified");

    service.initialize({ runId: "run:m4-deny-service", authorityPolicyMode: "supervised" });
    let deniedBoundary = null as Awaited<ReturnType<MissionControlService["advance"]>> | null;
    for (let tick = 0; tick < 10 && !deniedBoundary; tick += 1) {
      await service.advance("run:m4-deny-service", "proposal-review");
      const result = await service.advance("run:m4-deny-service", "tick-verified");
      if (result.boundary === "authority") deniedBoundary = result;
    }
    assert.ok(deniedBoundary);
    const deniedId = deniedBoundary.view.inbox.find((entry) => entry.kind === "authority-request")?.commands.find((entry) => entry.action === "deny")?.proposalId;
    assert.ok(deniedId);
    const denied = service.command("run:m4-deny-service", { action: "deny", proposalId: deniedId }) as { status: string };
    assert.equal(denied.status, "rejected");
    const after = await service.advance("run:m4-deny-service", "tick-verified");
    const selected = after.view.currentRound?.selectedProposalIds ?? [];
    assert.ok(!selected.includes(deniedId));
    assert.throws(() => service.command("run:m4-deny-service", { action: "deny", proposalId: deniedId }), /not pending/);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Mission Control supports redirect, messaging, wait visibility, cancellation, and chained Providers", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-m4-commands-"));
  const game = new GameStore(join(directory, "world.sqlite3"));
  const requestedProviders: string[] = [];
  const service = new MissionControlService(game, (name) => {
    requestedProviders.push(name);
    return new FixtureTeamProvider();
  });
  try {
    service.initialize({ runId: "run:m4-command-matrix" });
    const team = new TeamStore(game);
    const engineer = team.listTasks("run:m4-command-matrix").find((task) => task.actorId === "engineer-01")!;
    team.transitionTask(engineer.taskId, { providerOrder: ["codex", "hermes"] }, "team.task-provider-updated");
    const redirected = service.command("run:m4-command-matrix", { action: "redirect-objective", actorId: "engineer-01", objectiveId: "communications-operational" }) as { activeObjectiveId: string };
    assert.equal(redirected.activeObjectiveId, "communications-operational");
    assert.throws(() => service.command("run:m4-command-matrix", { action: "redirect-objective", actorId: "medic-01", objectiveId: "communications-operational" }), /outside/);
    assert.throws(() => service.command("run:m4-command-matrix", { action: "redirect-objective", actorId: "engineer-01", objectiveId: "missing" }), /unknown Objective/);

    const message = service.command("run:m4-command-matrix", {
      action: "send-message", senderActorId: "engineer-01", recipientActorIds: ["security-01"],
      kind: "help-request", boundedSummary: "Reserve repair parts for Engineer.", channel: "station-radio", ttlTicks: 4,
    }) as { status: string };
    assert.equal(message.status, "pending");
    const pending = service.state("run:m4-command-matrix");
    assert.ok(pending.inbox.some((card) => card.kind === "message-pending"));

    service.command("run:m4-command-matrix", { action: "pause", actorId: "medic-01" });
    const paused = service.state("run:m4-command-matrix");
    assert.ok(paused.inbox.some((card) => card.kind === "task-wait" && card.actorIds.includes("medic-01")));
    service.command("run:m4-command-matrix", { action: "resume", actorId: "medic-01" });
    service.command("run:m4-command-matrix", { action: "cancel", actorId: "security-01" });
    assert.throws(() => service.command("run:m4-command-matrix", { action: "resume", actorId: "security-01" }), /Cancelled/);
    assert.throws(() => service.command("run:m4-command-matrix", { action: "pause", actorId: "missing" }), /matching Actor/);

    const limited = await service.advance("run:m4-command-matrix", "proposal-review", 1);
    assert.equal(limited.boundary, "step-limit");
    await service.advance("run:m4-command-matrix", "proposal-review");
    assert.ok(requestedProviders.includes("codex-hermes"));
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Mission Control derives redundancy, provider-wait, and mission-risk interventions", async () => {
  const { directory, game, service } = serviceFixture("run:m4-interventions");
  try {
    await service.advance("run:m4-interventions", "proposal-review");
    const team = new TeamStore(game);
    const execution = new TeamExecutionStore(team);
    const projection = team.projection("run:m4-interventions", false);
    const round = execution.listRounds("run:m4-interventions")[0]!;
    const proposals = execution.listProposals(round.roundId);
    const engineer = proposals.find((proposal) => proposal.actorId === "engineer-01")!;
    const security = proposals.find((proposal) => proposal.actorId === "security-01")!;
    const seal: ActionProposal = {
      ...engineer, proposalId: "proposal:seal", status: "proposed", authorityOutcome: "permit",
      command: { kind: "seal_hull", commandId: "command:seal", actorId: "engineer-01", expectedRevision: 0, targetHazardId: "maintenance-breach" },
    };
    const contain: ActionProposal = {
      ...security, proposalId: "proposal:contain", status: "proposed", authorityOutcome: "permit",
      command: { kind: "contain_hazard", commandId: "command:contain", actorId: "security-01", expectedRevision: 0, targetHazardId: "maintenance-breach" },
    };
    const state = game.loadState("run:m4-interventions");
    const risky = structuredClone(state);
    risky.resources.oxygen = 20;
    const cards = deriveInterventions(risky, projection, [seal, contain]);
    assert.ok(cards.some((card) => card.kind === "redundant-action"));
    assert.equal(cards.find((card) => card.kind === "mission-risk")?.severity, "critical");

    const medic = team.listTasks("run:m4-interventions").find((task) => task.actorId === "medic-01")!;
    team.transitionTask(medic.taskId, {
      state: "waiting",
      wait: { kind: "provider", subjectId: "context:test", reason: "Provider unavailable", sinceTick: 0 },
    }, "team.task-test-provider-wait");
    assert.ok(service.state("run:m4-interventions").inbox.some((card) => card.kind === "provider-failure"));
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Mission Control HTTP validates and routes the complete player command union", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-m4-http-commands-"));
  const game = createGameServer({ dbPath: join(directory, "world.sqlite3"), teamProviderFactory: () => new FixtureTeamProvider() });
  try {
    const base = await listen(game);
    await request(base, "/api/mission-control/initialize", { runId: "run:m4-http-commands", authorityPolicyMode: "autonomous" });
    for (const command of [
      { action: "set-provider", actorId: "engineer-01", provider: "fixture" },
      { action: "set-authority-policy", policyMode: "locked" },
      { action: "redirect-objective", actorId: "engineer-01", objectiveId: "communications-operational" },
      { action: "send-message", senderActorId: "engineer-01", recipientActorIds: ["medic-01"], kind: "status-update", boundedSummary: "Status shared locally.", channel: "local", ttlTicks: 3 },
      { action: "pause", actorId: "medic-01" },
      { action: "resume", actorId: "medic-01" },
      { action: "cancel", actorId: "security-01" },
    ]) {
      const response = await request(base, "/api/mission-control/command?runId=run:m4-http-commands", command);
      assert.equal(response.status, 200, JSON.stringify(command));
    }
    for (const [path, body] of [
      ["/api/mission-control/advance?runId=run:m4-http-commands", { until: "unknown" }],
      ["/api/mission-control/advance?runId=run:m4-http-commands", { until: "proposal-review", maximumInternalSteps: 0 }],
      ["/api/mission-control/command?runId=run:m4-http-commands", { action: "unknown" }],
      ["/api/mission-control/command?runId=run:m4-http-commands", { action: "set-provider", actorId: "engineer-01", provider: "unknown" }],
      ["/api/mission-control/command?runId=run:m4-http-commands", { action: "send-message", senderActorId: "engineer-01", recipientActorIds: [], kind: "unknown", boundedSummary: "x", channel: "local" }],
    ] as const) {
      const response = await request(base, path, body);
      assert.equal(response.status, 400, JSON.stringify(body));
    }
    assert.equal((await request(base, "/api/mission-control/timeline?runId=run:m4-http-commands&limit=0")).status, 400);
    assert.equal((await request(base, "/api/mission-control/timeline?runId=run:m4-http-commands&before=x")).status, 400);
  } finally {
    await game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});


test("Mission Control initializes existing Runs with explicit Providers and safely explains incomplete authority evidence", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-m4-provider-init-"));
  const game = new GameStore(join(directory, "world.sqlite3"));
  const requested: string[] = [];
  const service = new MissionControlService(game, (name) => {
    requested.push(name);
    return new FixtureTeamProvider();
  });
  try {
    game.createRun({ runId: "run:m4-existing", scenarioVersion: 2, rulesetVersion: 3 });
    const initialized = service.initialize({
      runId: "run:m4-existing",
      providers: { "engineer-01": "codex", "medic-01": "hermes", "security-01": "fixture" },
    });
    assert.deepEqual(initialized.actors.find((actor) => actor.actorId === "engineer-01")?.providerOrder, ["codex"]);
    assert.deepEqual(initialized.actors.find((actor) => actor.actorId === "medic-01")?.providerOrder, ["hermes"]);
    await service.advance("run:m4-existing", "proposal-review");
    assert.ok(requested.includes("codex"));
    assert.ok(requested.includes("hermes"));

    const team = new TeamStore(game);
    const execution = new TeamExecutionStore(team);
    const projection = team.projection("run:m4-existing", false);
    const round = execution.listRounds("run:m4-existing")[0]!;
    const base = execution.listProposals(round.roundId)[0]!;
    const missingDecision: ActionProposal = {
      ...base,
      proposalId: "proposal:missing-authority-evidence",
      authorityDecisionId: "authority:missing",
      authorityOutcome: "require-human",
      status: "proposed",
      command: { kind: "move", commandId: "command:move-warning", actorId: base.actorId, expectedRevision: 0, targetRoomId: "power-junction" },
    };
    const cards = deriveInterventions(game.loadState("run:m4-existing"), projection, [missingDecision]);
    const authority = cards.find((card) => card.kind === "authority-request");
    assert.equal(authority?.severity, "warning");
    assert.match(authority?.explanation ?? "", /explicit human authority/);
    assert.match(authority?.consequence ?? "", /room/);
    assert.throws(() => service.command("run:m4-existing", { action: "set-provider", actorId: "engineer-01", provider: "invalid" as any }), /unsupported/);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Mission Control warning bands, fact summaries, and terminal advance remain explicit", async () => {
  const { directory, game, service } = serviceFixture("run:m4-terminal-contract");
  try {
    const team = new TeamStore(game);
    const projection = team.projection("run:m4-terminal-contract", false);
    const warning = structuredClone(game.loadState("run:m4-terminal-contract"));
    warning.resources.oxygen = 30;
    assert.equal(deriveInterventions(warning, projection, []).find((card) => card.kind === "mission-risk")?.severity, "warning");
    assert.equal(deriveInterventions(game.loadState("run:m4-terminal-contract"), projection, []).some((card) => card.kind === "mission-risk"), false);
    assert.match(factSummary({ kind: "hull_breach_sealed", hazardId: "maintenance-breach" }), /sealed/);
    assert.match(factSummary({ kind: "mission_failed", reason: "mission_timeout" }), /failed/);
    assert.match(factSummary({ kind: "power_state_changed", systemId: "cooling", powered: false }), /disabled/);

    for (let tick = 0; tick < 24 && service.state("run:m4-terminal-contract").run.status === "running"; tick += 1) {
      await service.advance("run:m4-terminal-contract", "proposal-review");
      await service.advance("run:m4-terminal-contract", "tick-verified");
    }
    const terminal = await service.advance("run:m4-terminal-contract", "tick-verified");
    assert.equal(terminal.boundary, "terminal");
    assert.deepEqual(terminal.steps, []);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Mission Control review is idempotent and paused redirects, default messages, and provider-order fallback remain safe", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-m4-small-branches-"));
  const game = new GameStore(join(directory, "world.sqlite3"));
  const requested: string[] = [];
  const service = new MissionControlService(game, (name) => {
    requested.push(name);
    return new FixtureTeamProvider();
  });
  try {
    service.initialize({ runId: "run:m4-small-branches" });
    const team = new TeamStore(game);
    const engineer = team.listTasks("run:m4-small-branches").find((task) => task.actorId === "engineer-01")!;
    team.transitionTask(engineer.taskId, { providerOrder: ["fixture", "codex"] }, "team.task-provider-updated");

    service.command("run:m4-small-branches", { action: "pause", actorId: "engineer-01" });
    const redirected = service.command("run:m4-small-branches", {
      action: "redirect-objective", actorId: "engineer-01", objectiveId: "life-support-operational",
    }) as { state: string; control: { mode: string } };
    assert.equal(redirected.state, "waiting");
    assert.equal(redirected.control.mode, "paused");
    service.command("run:m4-small-branches", { action: "resume", actorId: "engineer-01" });

    const message = service.command("run:m4-small-branches", {
      action: "send-message", senderActorId: "engineer-01", recipientActorIds: ["medic-01"],
      kind: "status-update", boundedSummary: "Default TTL message.", channel: "local",
    }) as { expiryTick: number; createdTick: number };
    assert.equal(message.expiryTick - message.createdTick, 6);

    const first = await service.advance("run:m4-small-branches", "proposal-review");
    const repeated = await service.advance("run:m4-small-branches", "proposal-review");
    assert.equal(first.boundary, "proposal-review");
    assert.equal(repeated.boundary, "proposal-review");
    assert.deepEqual(repeated.steps, []);
    assert.ok(requested.includes("fixture"));
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});
