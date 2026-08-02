import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { MissionControlService } from "../src/mission-control/service.ts";
import { assertEvidenceLinkIntegrity, buildRunEvidenceGraph, ReplayEvidenceError } from "../src/replay/evidence.ts";
import { MAX_REPLAY_FRAME_BYTES, replayFrame, replayFramesPage, replaySummary } from "../src/replay/frames.ts";
import { createGameServer } from "../src/server.ts";
import { GameStore } from "../src/storage.ts";
import { TeamHost } from "../src/team/engine.ts";
import { FixtureTeamProvider } from "../src/team/providers.ts";

async function finish(strategy: "security-contain" | "engineer-seal", store = new GameStore(":memory:")) {
  const runId = `run:replay-graph:${strategy}`;
  const service = new MissionControlService(store, () => new FixtureTeamProvider({ breachStrategy: strategy }));
  service.initialize({ runId, scenarioCaseId: "baseline" });
  for (let tick = 0; tick < 24 && service.state(runId).run.status === "running"; tick += 1) {
    const review = await service.advance(runId, "proposal-review");
    if (review.boundary === "terminal") break;
    await service.advance(runId, "tick-verified");
  }
  return { store, service, runId };
}

function counts(store: GameStore, runId: string): Record<string, number> {
  const tables = ["commands", "events", "snapshots", "host_journal", "team_rounds", "team_round_contexts", "team_proposals", "team_tick_plans", "team_messages", "team_authority_decisions", "team_authority_grants"];
  const output = Object.fromEntries(tables.map((table) => [table, Number((store.db.prepare(`SELECT COUNT(*) AS count FROM ${table} WHERE run_id = ?`).get(runId) as { count: number }).count)]));
  output.host_artifacts = Number((store.db.prepare("SELECT COUNT(*) AS count FROM host_artifacts").get() as { count: number }).count);
  return output;
}

async function listen(game: ReturnType<typeof createGameServer>): Promise<string> {
  await new Promise<void>((resolve) => game.server.listen(0, "127.0.0.1", resolve));
  const address = game.server.address();
  if (!address || typeof address === "string") throw new Error("server did not expose an address");
  return `http://127.0.0.1:${address.port}`;
}

test("world-only Runs retain exact bounded replay projections", () => {
  const store = new GameStore(":memory:");
  try {
    const graph = buildRunEvidenceGraph(store);
    const frame = replayFrame(store, store.activeRunId, 0, graph);
    assert.equal(graph.nodes.filter((node) => node.kind === "team-round").length, 0);
    assert.equal(frame.round, null);
    assert.equal(frame.digest, store.getRun().genesisDigest);
  } finally { store.close(); }
});

test("Message and player configuration evidence remain visible before the first World Tick", () => {
  const store = new GameStore(":memory:");
  const runId = "run:replay-graph:message-config";
  const service = new MissionControlService(store, () => new FixtureTeamProvider());
  try {
    service.initialize({ runId, scenarioCaseId: "baseline", authorityPolicyMode: "supervised" });
    service.command(runId, { action: "set-provider", actorId: "engineer-01", provider: "codex-hermes" });
    service.command(runId, {
      action: "send-message", senderActorId: "engineer-01", recipientActorIds: ["security-01"],
      kind: "help-request", boundedSummary: "Reserve the maintenance route.", channel: "station-radio", ttlTicks: 3,
    });
    const graph = buildRunEvidenceGraph(store, runId);
    const message = graph.nodes.find((node) => node.kind === "team-message");
    assert.ok(message);
    assert.equal(message.worldRevision, 0);
    assert.ok(graph.edges.some((edge) => edge.kind === "sent-by" && edge.toNodeId === message.nodeId));
    assert.ok(graph.edges.some((edge) => edge.kind === "addressed-to" && edge.fromNodeId === message.nodeId));
    const hostEvents = graph.nodes.filter((node) => node.kind === "host-event");
    assert.ok(hostEvents.some((node) => /configuration updated/.test(node.summary)));
    assert.ok(hostEvents.some((node) => /provider updated/.test(node.summary)));
    const frame = replayFrame(store, runId, 0, graph);
    assert.equal(frame.messages.length, 1);
    assert.ok(frame.playerInterventions.length >= 2);
  } finally { store.close(); }
});

test("fresh Replay reads a Dispatch-prepared Round before the World advances", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-replay-dispatch-"));
  const path = join(directory, "world.sqlite3");
  const runId = "run:replay-graph:dispatch-pending";
  let store = new GameStore(path);
  try {
    const service = new MissionControlService(store, () => new FixtureTeamProvider());
    service.initialize({ runId, scenarioCaseId: "baseline" });
    const host = new TeamHost(store, new FixtureTeamProvider());
    const statuses: string[] = [];
    for (let index = 0; index < 5; index += 1) statuses.push((await host.step(runId)).status);
    assert.deepEqual(statuses, ["initialized", "contexts_prepared", "proposals_recorded", "tick_plan_prepared", "dispatch_prepared"]);
    assert.equal(store.loadState(runId).revision, 0);
    store.close();

    store = new GameStore(path, { activeRunId: runId });
    const graph = buildRunEvidenceGraph(store, runId);
    assert.equal(graph.nodes.filter((node) => node.kind === "effect").length, 1);
    assert.equal(graph.nodes.filter((node) => node.kind === "dispatch").length, 1);
    assert.equal(graph.nodes.filter((node) => node.kind === "observation").length, 0);
    const frame = replayFrame(store, runId, 0, graph);
    assert.equal(frame.round?.status, "dispatched");
    assert.equal(frame.effect?.status, "dispatched");
    assert.equal(frame.dispatch?.status, "pending");
    assert.equal(frame.observation, null);
    assert.equal(frame.digest, store.getRun(runId).genesisDigest);
  } finally {
    try { store.close(); } catch {}
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Evidence link integrity rejects required dangling identities and permits optional references", () => {
  const nodes = [{ nodeId: "node:a" }, { nodeId: "node:b" }];
  assert.doesNotThrow(() => assertEvidenceLinkIntegrity(nodes, [
    { edgeId: "edge:required", kind: "records", fromNodeId: "node:a", toNodeId: "node:b", required: true },
    { edgeId: "edge:optional", kind: "references", fromNodeId: "node:a", toNodeId: "artifact:external", required: false },
  ]));
  assert.throws(
    () => assertEvidenceLinkIntegrity(nodes, [{ edgeId: "edge:missing", kind: "records", fromNodeId: "node:a", toNodeId: "node:missing", required: true }]),
    (error) => error instanceof ReplayEvidenceError && /dangling/.test(error.message),
  );
});

test("single Replay Frame revision validation rejects fractional, negative, and future revisions", () => {
  const store = new GameStore(":memory:");
  try {
    assert.throws(() => replayFrame(store, store.activeRunId, -1), /non-negative integer/);
    assert.throws(() => replayFrame(store, store.activeRunId, 0.5), /non-negative integer/);
    assert.throws(() => replayFrame(store, store.activeRunId, 1), /from 0 to 0/);
  } finally {
    store.close();
  }
});
