import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { createGameServer, type TeamProviderName } from "../src/server.ts";
import type { CompiledTeamContext, TeamProviderDecision } from "../src/team/model.ts";
import { FixtureTeamProvider, type TeamDecisionProvider } from "../src/team/providers.ts";

async function listen(game: ReturnType<typeof createGameServer>): Promise<string> {
  await new Promise<void>((resolve) => game.server.listen(0, "127.0.0.1", resolve));
  const address = game.server.address();
  if (!address || typeof address === "string") throw new Error("server did not expose a TCP address");
  return `http://127.0.0.1:${address.port}`;
}

async function json(base: string, path: string, options?: RequestInit): Promise<{ status: number; body: any }> {
  const response = await fetch(`${base}${path}`, options);
  return { status: response.status, body: await response.json() };
}

function post(base: string, path: string, body: unknown): Promise<{ status: number; body: any }> {
  return json(base, path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

class NamedTeamProvider implements TeamDecisionProvider {
  readonly providerId: string;
  readonly delegate = new FixtureTeamProvider();
  calls = 0;

  constructor(name: TeamProviderName) {
    this.providerId = `test-team-provider:${name}`;
  }

  async decide(context: CompiledTeamContext): Promise<TeamProviderDecision> {
    this.calls += 1;
    const decision = await this.delegate.decide(context);
    return { ...decision, providerId: this.providerId };
  }

  evidenceMetadata(): Record<string, unknown> { return { calls: this.calls, providerId: this.providerId }; }
}

test("Team HTTP API initializes, switches Providers, and completes the 18-round mission", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-team-server-"));
  const providers: NamedTeamProvider[] = [];
  const game = createGameServer({
    dbPath: join(directory, "world.sqlite3"),
    teamProviderFactory(name) {
      const provider = new NamedTeamProvider(name);
      providers.push(provider);
      return provider;
    },
  });
  try {
    const base = await listen(game);

    const html = await fetch(`${base}/`).then((response) => response.text());
    const script = await fetch(`${base}/app.js`).then((response) => response.text());
    const debugHtml = await fetch(`${base}/debug.html`).then((response) => response.text());
    const debugScript = await fetch(`${base}/debug.js`).then((response) => response.text());
    assert.match(html, /Mission Control/);
    assert.match(script, /advanceMission|mission-control/);
    assert.match(debugHtml, /Station Zero Specialists/);
    assert.match(debugHtml, /team-provider/);
    assert.match(debugScript, /\/api\/team\/state/);
    assert.match(debugScript, /approve-proposal/);

    const created = await post(base, "/api/runs", { runId: "run:http-team", scenarioVersion: 2, rulesetVersion: 3 });
    assert.equal(created.status, 201);

    const before = await json(base, "/api/team/state?runId=run:http-team&provider=fixture");
    assert.equal(before.status, 200);
    assert.equal(before.body.initialized, false);

    const initialized = await post(base, "/api/team/initialize?runId=run:http-team", { provider: "codex", policyMode: "autonomous" });
    assert.equal(initialized.status, 201);
    assert.equal(initialized.body.provider, "codex");
    assert.equal(initialized.body.projection.tasks.length, 4);

    const first = await post(base, "/api/team/step?runId=run:http-team", { provider: "codex", policyMode: "autonomous" });
    assert.equal(first.status, 200);
    assert.equal(first.body.receipt.status, "initialized");
    const second = await post(base, "/api/team/step?runId=run:http-team", { provider: "hermes", policyMode: "autonomous" });
    assert.equal(second.body.receipt.status, "contexts_prepared");
    const third = await post(base, "/api/team/step?runId=run:http-team", { provider: "codex-hermes", policyMode: "autonomous" });
    assert.equal(third.body.receipt.status, "proposals_recorded");
    assert.ok(third.body.team.proposals.every((proposal: { providerId: string }) => proposal.providerId === "test-team-provider:codex-hermes"));

    const completed = await post(base, "/api/team/run?runId=run:http-team", { provider: "hermes-codex", policyMode: "autonomous", maximumSteps: 512 });
    assert.equal(completed.status, 200);
    assert.equal(completed.body.world.state.mission.status, "victory");
    assert.equal(completed.body.world.state.revision, 18);
    assert.equal(completed.body.world.digest, "a8ef1f491c35720ed02e66f004ccd7f3466f78991dcafecd442ceae66b09ceb7");
    assert.equal(completed.body.receipt.rounds.length, 18);
    assert.ok(completed.body.receipt.rounds.every((round: { status: string }) => round.status === "completed"));
    assert.equal(completed.body.team.projection.goal.status, "succeeded");
    assert.ok(completed.body.team.projection.tasks.every((task: { state: string }) => task.state === "completed"));

    const journalBefore = Number(game.store.db.prepare("SELECT COUNT(*) AS count FROM host_journal WHERE run_id = ?").get("run:http-team")!.count);
    const state = await json(base, "/api/team/state?runId=run:http-team&provider=fixture&policyMode=autonomous");
    const stateAgain = await json(base, "/api/team/state?runId=run:http-team&provider=fixture&policyMode=autonomous");
    assert.equal(state.body.initialized, true);
    assert.equal(state.body.rounds.length, 18);
    assert.equal(stateAgain.body.timeline.length, state.body.timeline.length);
    const journalAfter = Number(game.store.db.prepare("SELECT COUNT(*) AS count FROM host_journal WHERE run_id = ?").get("run:http-team")!.count);
    assert.equal(journalAfter, journalBefore);
    assert.ok(providers.some((provider) => provider.providerId === "test-team-provider:codex-hermes" && provider.calls === 3));
  } finally {
    await game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("supervised Team API stops for authority, consumes one approval, and resumes", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-team-server-authority-"));
  const game = createGameServer({
    dbPath: join(directory, "world.sqlite3"),
    teamProviderFactory: (name) => new NamedTeamProvider(name),
  });
  try {
    const base = await listen(game);
    await post(base, "/api/runs", { runId: "run:http-team-authority", scenarioVersion: 2, rulesetVersion: 3 });
    await post(base, "/api/team/initialize?runId=run:http-team-authority", { provider: "fixture", policyMode: "supervised" });
    const blocked = await post(base, "/api/team/run?runId=run:http-team-authority", { provider: "fixture", policyMode: "supervised", maximumSteps: 128 });
    assert.equal(blocked.status, 200);
    assert.equal(blocked.body.receipt.steps.at(-1).status, "authority_required");
    assert.equal(blocked.body.world.state.revision, 4);
    const pending = blocked.body.team.proposals.find((proposal: { authorityOutcome: string; status: string }) => proposal.authorityOutcome === "require-human" && proposal.status === "proposed");
    assert.ok(pending);

    const approved = await post(base, "/api/team/input?runId=run:http-team-authority", {
      provider: "fixture", policyMode: "supervised", action: "approve", proposalId: pending.proposalId, issuedBy: "player:test",
    });
    assert.equal(approved.status, 200);
    assert.equal(approved.body.result.proposalId, pending.proposalId);
    assert.equal(approved.body.result.consumedAtTick, null);

    const resumed = await post(base, "/api/team/run?runId=run:http-team-authority", { provider: "fixture", policyMode: "supervised", maximumSteps: 4 });
    assert.equal(resumed.status, 200);
    assert.equal(resumed.body.world.state.revision, 5);
    const grant = resumed.body.team.projection.authorityGrants.find((entry: { proposalId: string }) => entry.proposalId === pending.proposalId);
    assert.equal(grant.consumedAtTick, 4);
  } finally {
    await game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Team input supports Messages, objective redirect, pause, cancel, and denial", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-team-server-input-"));
  const game = createGameServer({
    dbPath: join(directory, "world.sqlite3"),
    teamProviderFactory: (name) => new NamedTeamProvider(name),
  });
  try {
    const base = await listen(game);
    await post(base, "/api/runs", { runId: "run:http-team-input", scenarioVersion: 2, rulesetVersion: 3 });
    await post(base, "/api/team/initialize?runId=run:http-team-input", { provider: "fixture", policyMode: "autonomous" });

    const message = await post(base, "/api/team/input?runId=run:http-team-input", {
      provider: "fixture", action: "send-message", senderActorId: "engineer-01", recipientActorIds: ["medic-01"],
      kind: "status-update", boundedSummary: "Command Center status is shared.", channel: "local", ttlTicks: 3,
    });
    assert.equal(message.status, 200);
    assert.equal(message.body.result.status, "delivered");

    const redirected = await post(base, "/api/team/input?runId=run:http-team-input", {
      provider: "fixture", action: "redirect-objective", actorId: "engineer-01", objectiveId: "communications-operational",
    });
    assert.equal(redirected.status, 200);
    assert.equal(redirected.body.result.activeObjectiveId, "communications-operational");

    const paused = await post(base, "/api/team/input?runId=run:http-team-input", { provider: "fixture", action: "pause", actorId: "medic-01" });
    assert.equal(paused.status, 200);
    assert.equal(paused.body.result[0].state, "waiting");
    const cancelled = await post(base, "/api/team/input?runId=run:http-team-input", { provider: "fixture", action: "cancel", actorId: "security-01" });
    assert.equal(cancelled.status, 200);
    assert.equal(cancelled.body.result[0].state, "cancelled");

    const secondRun = await post(base, "/api/runs", { runId: "run:http-team-deny", scenarioVersion: 2, rulesetVersion: 3 });
    assert.equal(secondRun.status, 201);
    await post(base, "/api/team/initialize?runId=run:http-team-deny", { provider: "fixture", policyMode: "supervised" });
    const blocked = await post(base, "/api/team/run?runId=run:http-team-deny", { provider: "fixture", policyMode: "supervised", maximumSteps: 128 });
    const proposal = blocked.body.team.proposals.find((entry: { authorityOutcome: string; status: string }) => entry.authorityOutcome === "require-human" && entry.status === "proposed");
    assert.ok(proposal);
    const denied = await post(base, "/api/team/input?runId=run:http-team-deny", { provider: "fixture", policyMode: "supervised", action: "deny", proposalId: proposal.proposalId });
    assert.equal(denied.status, 200);
    assert.equal(denied.body.result.status, "rejected");
    assert.equal(denied.body.result.rejectionReason, "player_denied");
  } finally {
    await game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Team API validates versions, providers, policies, budgets, and input unions", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-team-server-errors-"));
  const game = createGameServer({
    dbPath: join(directory, "world.sqlite3"),
    teamProviderFactory: (name) => new NamedTeamProvider(name),
  });
  try {
    const base = await listen(game);
    const legacy = await post(base, "/api/team/initialize", { provider: "fixture" });
    assert.equal(legacy.status, 409);
    await post(base, "/api/runs", { runId: "run:http-team-errors", scenarioVersion: 2, rulesetVersion: 3 });

    for (const [path, body] of [
      ["/api/team/initialize?runId=run:http-team-errors", { provider: "unknown" }],
      ["/api/team/initialize?runId=run:http-team-errors", { provider: "fixture", policyMode: "unknown" }],
      ["/api/team/step?runId=run:http-team-errors", []],
      ["/api/team/run?runId=run:http-team-errors", { provider: "fixture", maximumSteps: 0 }],
      ["/api/team/run?runId=run:http-team-errors", { provider: "fixture", maximumSteps: 1025 }],
      ["/api/team/run?runId=run:http-team-errors", { provider: "fixture", maximumSteps: 1.5 }],
    ] as const) {
      const response = await post(base, path, body);
      assert.equal(response.status, 400, path);
    }

    await post(base, "/api/team/initialize?runId=run:http-team-errors", { provider: "fixture" });
    for (const body of [
      { provider: "fixture", action: "unknown" },
      { provider: "fixture", action: "send-message", senderActorId: "engineer-01", recipientActorIds: ["medic-01"], kind: "unknown", boundedSummary: "x", channel: "local" },
      { provider: "fixture", action: "send-message", senderActorId: "engineer-01", recipientActorIds: ["medic-01"], kind: "status-update", boundedSummary: "x", channel: "unknown" },
      { provider: "fixture", action: "redirect-objective", actorId: "medic-01", objectiveId: "communications-operational" },
      { provider: "fixture", action: "redirect-objective", actorId: "medic-01", objectiveId: "missing" },
      { provider: "fixture", action: "pause", actorId: "missing" },
      { provider: "fixture", action: "approve", proposalId: "missing" },
      { provider: "fixture", action: "deny", proposalId: "missing" },
    ]) {
      const response = await post(base, "/api/team/input?runId=run:http-team-errors", body);
      assert.ok([400, 409, 500].includes(response.status), JSON.stringify(body));
    }
  } finally {
    await game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});
