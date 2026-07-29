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

test("Evidence Graph and Frames cover every verified Fixture revision without a second store", async () => {
  const { store, runId } = await finish("security-contain");
  try {
    const before = counts(store, runId);
    const graph = buildRunEvidenceGraph(store, runId);
    const summary = replaySummary(store, runId);
    assert.equal(summary.terminalRevision, 18);
    assert.equal(summary.frameCount, 19);
    assert.equal(summary.terminalStatus, "victory");
    assert.equal(summary.graphDigest, graph.graphDigest);
    assert.equal(summary.nodeCounts["world-state"], 19);
    assert.equal(summary.nodeCounts["world-event"], 18);
    assert.equal(summary.nodeCounts["team-round"], 18);
    assert.equal(summary.nodeCounts["team-context"], 54);
    assert.equal(summary.nodeCounts["team-proposal"], 54);
    assert.equal(summary.nodeCounts.effect, 18);
    assert.equal(summary.nodeCounts.dispatch, 18);
    assert.equal(summary.nodeCounts.observation, 18);
    assert.ok(graph.edges.every((edge) => !edge.required || (graph.nodes.some((node) => node.nodeId === edge.fromNodeId) && graph.nodes.some((node) => node.nodeId === edge.toNodeId))));

    for (let revision = 0; revision <= 18; revision += 1) {
      const frame = replayFrame(store, runId, revision, graph);
      const point = store.stateAtRevision(revision, runId);
      assert.equal(frame.revision, revision);
      assert.equal(frame.digest, point.digest);
      assert.deepEqual(frame.state, point.state);
      assert.equal(frame.verified, true);
      assert.ok(frame.byteLength <= MAX_REPLAY_FRAME_BYTES);
      if (revision === 0) {
        assert.equal(frame.worldEvent, null);
        assert.equal(frame.round, null);
      } else {
        assert.equal(frame.worldEvent?.nodeId, `world-event:${store.events(runId)[revision - 1]!.eventId}`);
        assert.equal(frame.round?.worldRevision, revision - 1);
        assert.equal(frame.observation?.worldAfterDigest, frame.digest);
      }
    }
    assert.deepEqual(counts(store, runId), before);
  } finally { store.close(); }
});

test("Replay Frame paging reaches a 22-revision history without gaps or duplicates", async () => {
  const { store, runId } = await finish("engineer-seal");
  try {
    const revisions: number[] = [];
    let next: number | null = 0;
    let digest: string | null = null;
    while (next !== null) {
      const page = replayFramesPage(store, runId, next, 5);
      digest ??= page.graphDigest;
      assert.equal(page.graphDigest, digest);
      revisions.push(...page.frames.map((frame) => frame.revision));
      next = page.nextFromRevision;
    }
    assert.deepEqual(revisions, Array.from({ length: 23 }, (_, revision) => revision));
    assert.equal(new Set(revisions).size, revisions.length);
    assert.throws(() => replayFramesPage(store, runId, -1, 5), /fromRevision/);
    assert.throws(() => replayFramesPage(store, runId, 0.5, 5), /fromRevision/);
    assert.throws(() => replayFramesPage(store, runId, 23, 5), /0 to 22/);
    assert.throws(() => replayFramesPage(store, runId, 0, 0), /frame limit/);
    assert.throws(() => replayFramesPage(store, runId, 0, 50.5), /frame limit/);
    assert.throws(() => replayFramesPage(store, runId, 0, 51), /frame limit/);
  } finally { store.close(); }
});

test("Graph identity ignores wall-clock metadata and construction order", async () => {
  const { store, runId } = await finish("security-contain");
  try {
    const first = buildRunEvidenceGraph(store, runId);
    const second = buildRunEvidenceGraph(store, runId);
    assert.deepEqual(second, first);
    store.db.prepare("UPDATE host_journal SET created_at = ? WHERE run_id = ?").run("2099-01-01T00:00:00.000Z", runId);
    const rows = store.db.prepare("SELECT round_id, value_json FROM team_rounds WHERE run_id = ?").all(runId) as unknown as Array<{ round_id: string; value_json: string }>;
    for (const row of rows) {
      const value = JSON.parse(row.value_json);
      value.createdAt = "2099-01-01T00:00:00.000Z";
      value.updatedAt = "2099-01-02T00:00:00.000Z";
      store.db.prepare("UPDATE team_rounds SET value_json = ? WHERE round_id = ?").run(JSON.stringify(value), row.round_id);
    }
    const after = buildRunEvidenceGraph(store, runId);
    assert.equal(after.graphDigest, first.graphDigest);
    assert.deepEqual(after.nodes, first.nodes);
    assert.deepEqual(after.edges, first.edges);
  } finally { store.close(); }
});

test("player interventions appear in the exact revision Frame", async () => {
  const store = new GameStore(":memory:");
  const runId = "run:replay-graph:player";
  const service = new MissionControlService(store, () => new FixtureTeamProvider());
  try {
    service.initialize({ runId, scenarioCaseId: "baseline" });
    service.command(runId, { action: "pause", actorId: "medic-01" });
    const frame = replayFrame(store, runId, 0);
    assert.ok(frame.playerInterventions.some((entry) => /player paused/.test(entry.summary)));
    assert.ok(frame.evidenceNodeIds.includes(`world-state:${runId}:0`));
  } finally { store.close(); }
});

test("dangling required Proposal identities fail closed", async () => {
  const { store, runId } = await finish("security-contain");
  try {
    const row = store.db.prepare("SELECT proposal_id, value_json FROM team_proposals WHERE run_id = ? LIMIT 1").get(runId) as { proposal_id: string; value_json: string };
    const proposal = JSON.parse(row.value_json);
    proposal.contextId = "context:missing";
    store.db.prepare("UPDATE team_proposals SET value_json = ? WHERE proposal_id = ?").run(JSON.stringify(proposal), row.proposal_id);
    assert.throws(() => buildRunEvidenceGraph(store, runId), (error) => error instanceof ReplayEvidenceError && /missing Context/.test(error.message));
  } finally { store.close(); }
});

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

test("Replay summary, frame, and paged-frame HTTP APIs are read-only and typed", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-replay-graph-http-"));
  const game = createGameServer({ dbPath: join(directory, "world.sqlite3"), teamProviderFactory: () => new FixtureTeamProvider() });
  try {
    const runId = "run:replay-graph:http";
    const service = new MissionControlService(game.store, () => new FixtureTeamProvider());
    service.initialize({ runId, scenarioCaseId: "baseline" });
    for (let tick = 0; tick < 24 && service.state(runId).run.status === "running"; tick += 1) {
      await service.advance(runId, "proposal-review");
      await service.advance(runId, "tick-verified");
    }
    const base = await listen(game);
    const before = counts(game.store, runId);
    const summaryResponse = await fetch(`${base}/api/replay/summary?runId=${runId}`);
    assert.equal(summaryResponse.status, 200);
    const summary = await summaryResponse.json() as any;
    assert.equal(summary.frameCount, 19);
    const pageResponse = await fetch(`${base}/api/replay/frames?runId=${runId}&fromRevision=0&limit=4`);
    assert.equal(pageResponse.status, 200);
    const page = await pageResponse.json() as any;
    assert.deepEqual(page.frames.map((frame: any) => frame.revision), [0, 1, 2, 3]);
    assert.equal(page.nextFromRevision, 4);
    const frameResponse = await fetch(`${base}/api/replay/frame?runId=${runId}&revision=18`);
    assert.equal(frameResponse.status, 200);
    const frame = await frameResponse.json() as any;
    assert.equal(frame.state.mission.status, "victory");
    assert.equal(frame.digest, summary.terminalDigest);
    assert.equal((await fetch(`${base}/api/replay/frame?runId=${runId}`)).status, 400);
    assert.equal((await fetch(`${base}/api/replay/frames?runId=${runId}&limit=0`)).status, 400);
    assert.deepEqual(counts(game.store, runId), before);
  } finally {
    await game.close();
    rmSync(directory, { recursive: true, force: true });
  }
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

test("supervised authority Grant is linked before and after exact consumption", async () => {
  const store = new GameStore(":memory:");
  const runId = "run:replay-graph:grant";
  const service = new MissionControlService(store, () => new FixtureTeamProvider());
  try {
    service.initialize({ runId, scenarioCaseId: "baseline", authorityPolicyMode: "supervised" });
    let authorityProposalId: string | null = null;
    for (let tick = 0; tick < 12 && authorityProposalId === null; tick += 1) {
      await service.advance(runId, "proposal-review");
      const result = await service.advance(runId, "tick-verified");
      if (result.boundary === "authority") {
        authorityProposalId = result.view.inbox.find((card) => card.kind === "authority-request")?.commands.find((command) => command.action === "approve")?.proposalId ?? null;
      }
    }
    assert.ok(authorityProposalId);
    const issued = service.command(runId, { action: "approve", proposalId: authorityProposalId, issuedBy: "player:replay-test" }) as { grantId: string };
    const issuedGraph = buildRunEvidenceGraph(store, runId);
    const issuedNode = issuedGraph.nodes.find((node) => node.nodeId === `authority-grant:${issued.grantId}`);
    assert.ok(issuedNode);
    assert.match(issuedNode.summary, /issued/);
    assert.ok(issuedGraph.edges.some((edge) => edge.kind === "granted-for" && edge.fromNodeId === issuedNode.nodeId));
    await service.advance(runId, "tick-verified");
    const consumedGraph = buildRunEvidenceGraph(store, runId);
    assert.match(consumedGraph.nodes.find((node) => node.nodeId === issuedNode.nodeId)?.summary ?? "", /consumed/);
  } finally { store.close(); }
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
