import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import { MissionControlService } from "../src/mission-control/service.ts";
import { recoveryPolicy } from "./support/world-policies.ts";
import { createGameServer } from "../src/server.ts";
import { GameStore, StorageError } from "../src/storage.ts";
import { FixtureTeamProvider } from "../src/team/providers.ts";
import { materializeAction } from "../src/world.ts";

async function finish(
  breachStrategy: "security-contain" | "engineer-seal",
): Promise<{ store: GameStore; service: MissionControlService; runId: string }> {
  const store = new GameStore(":memory:");
  const runId = `run:replay:${breachStrategy}`;
  const service = new MissionControlService(
    store,
    () => new FixtureTeamProvider({ breachStrategy }),
  );
  service.initialize({ runId, scenarioCaseId: "baseline" });
  for (let tick = 0; tick < 24 && service.state(runId).run.status === "running"; tick += 1) {
    const review = await service.advance(runId, "proposal-review");
    if (review.boundary === "terminal") break;
    await service.advance(runId, "tick-verified");
  }
  return { store, service, runId };
}

function retainedCounts(store: GameStore, runId: string): Record<string, number> {
  const runTables = [
    "commands",
    "events",
    "snapshots",
    "host_journal",
    "team_rounds",
    "team_round_contexts",
    "team_proposals",
    "team_authority_decisions",
    "team_tick_plans",
  ];
  const counts = Object.fromEntries(runTables.map((table) => {
    const row = store.db.prepare(`SELECT COUNT(*) AS count FROM ${table} WHERE run_id = ?`).get(runId) as { count: number };
    return [table, Number(row.count)];
  }));
  const artifacts = store.db.prepare("SELECT COUNT(*) AS count FROM host_artifacts").get() as { count: number };
  return { ...counts, host_artifacts: Number(artifacts.count) };
}

function expectedDigest(store: GameStore, runId: string, revision: number): string {
  if (revision === 0) return store.getRun(runId).genesisDigest;
  const row = store.db.prepare("SELECT after_digest FROM commands WHERE run_id = ? AND command_sequence = ?")
    .get(runId, revision - 1) as { after_digest: string } | undefined;
  if (!row) throw new Error(`missing retained digest for revision ${revision}`);
  return row.after_digest;
}

function applyOne(store: GameStore): void {
  const state = store.loadState();
  const action = recoveryPolicy.choose(state);
  assert.ok(action);
  const applied = store.apply(materializeAction(action, "replay-one"));
  assert.equal(applied.result.status, "accepted");
}

function expectCorrupt(run: () => unknown): void {
  assert.throws(run, (error) => error instanceof StorageError && error.code === "storage_corrupt");
}

async function listen(game: ReturnType<typeof createGameServer>): Promise<string> {
  await new Promise<void>((resolve) => game.server.listen(0, "127.0.0.1", resolve));
  const address = game.server.address();
  if (!address || typeof address === "string") throw new Error("server did not expose a TCP address");
  return `http://127.0.0.1:${address.port}`;
}

for (const [strategy, terminalRevision] of [["security-contain", 18]] as const) {
  test(`point-in-time replay verifies every ${strategy} revision from Genesis through terminal`, async () => {
    const { store, runId } = await finish(strategy);
    try {
      assert.equal(store.loadState(runId).revision, terminalRevision);
      const countsBefore = retainedCounts(store, runId);
      for (let revision = 0; revision <= terminalRevision; revision += 1) {
        const result = store.stateAtRevision(revision, runId);
        assert.equal(result.runId, runId);
        assert.equal(result.revision, revision);
        assert.equal(result.state.revision, revision);
        assert.equal(result.digest, sha256(result.state));
        assert.equal(result.digest, expectedDigest(store, runId, revision));
        assert.equal(result.replayedCommandCount, revision - result.snapshotRevision);
        assert.ok(result.snapshotRevision <= revision);
        assert.equal(result.verified, true);
      }
      const terminal = store.stateAtRevision(terminalRevision, runId);
      assert.equal(terminal.digest, store.verifyReplay(runId).digest);
      assert.deepEqual(retainedCounts(store, runId), countsBefore);
    } finally {
      store.close();
    }
  });
}

test("point-in-time revision validation is typed and bounded by retained World history", () => {
  const store = new GameStore(":memory:");
  try {
    assert.throws(() => store.stateAtRevision(-1), /non-negative integer/);
    assert.throws(() => store.stateAtRevision(0.5), /non-negative integer/);
    assert.throws(() => store.stateAtRevision(Number.NaN), /non-negative integer/);
    assert.throws(() => store.stateAtRevision(1), /integer from 0 to 0/);
    assert.throws(() => store.stateAtRevision(0, "run:missing"), /unknown run/);
    assert.throws(() => store.recover("run:missing"), /unknown run/);
    assert.throws(() => store.verifyReplay("run:missing"), /unknown run/);
  } finally {
    store.close();
  }
});

test("Snapshot identity, presence, and Command anchoring fail closed", () => {
  for (const mutation of ["missing", "digest", "revision", "invariant", "sequence", "anchor"] as const) {
    const store = new GameStore(":memory:", { snapshotInterval: 1 });
    try {
      applyOne(store);
      if (mutation === "missing") {
        store.db.prepare("DELETE FROM snapshots").run();
      } else if (mutation === "digest") {
        store.db.prepare("UPDATE snapshots SET digest = ? WHERE revision = 1").run("tampered");
      } else if (mutation === "revision") {
        const row = store.db.prepare("SELECT state_json FROM snapshots WHERE revision = 1").get() as { state_json: string };
        const state = JSON.parse(row.state_json) as { revision: number };
        state.revision = 0;
        store.db.prepare("UPDATE snapshots SET state_json = ?, digest = ? WHERE revision = 1")
          .run(JSON.stringify(state), sha256(state));
      } else if (mutation === "invariant") {
        const row = store.db.prepare("SELECT state_json FROM snapshots WHERE revision = 1").get() as { state_json: string };
        const state = JSON.parse(row.state_json) as { resources: { oxygen: number } };
        state.resources.oxygen = 101;
        store.db.prepare("UPDATE snapshots SET state_json = ?, digest = ? WHERE revision = 1")
          .run(JSON.stringify(state), sha256(state));
      } else if (mutation === "sequence") {
        store.db.prepare("UPDATE snapshots SET command_sequence = -1 WHERE revision = 1").run();
      } else {
        const row = store.db.prepare("SELECT digest FROM snapshots WHERE revision = 1").get() as { digest: string };
        store.db.prepare("UPDATE commands SET after_digest = ? WHERE command_sequence = 0").run(`${row.digest}:other`);
      }
      expectCorrupt(() => store.stateAtRevision(1));
    } finally {
      store.close();
    }
  }
});

test("validly rehashed malformed Command and Event records still fail closed", () => {
  for (const table of ["commands", "events"] as const) {
    const store = new GameStore(":memory:", { snapshotInterval: 1 });
    try {
      applyOne(store);
      if (table === "commands") {
        const row = store.db.prepare("SELECT * FROM commands WHERE command_sequence = 0").get() as {
          command_sequence: number;
          command_id: string;
          before_digest: string;
          after_digest: string;
          previous_digest: string | null;
        };
        const commandJson = "{";
        const digest = sha256({
          kind: "command",
          runId: store.activeRunId,
          sequence: row.command_sequence,
          commandId: row.command_id,
          commandJson,
          beforeDigest: row.before_digest,
          afterDigest: row.after_digest,
          previousDigest: row.previous_digest ?? "",
        });
        store.db.prepare("UPDATE commands SET command_json = ?, record_digest = ? WHERE command_sequence = 0")
          .run(commandJson, digest);
      } else {
        const row = store.db.prepare("SELECT * FROM events WHERE event_sequence = 0").get() as {
          event_sequence: number;
          command_id: string;
          before_digest: string;
          after_digest: string;
          previous_digest: string | null;
        };
        const eventJson = "{";
        const digest = sha256({
          kind: "event",
          runId: store.activeRunId,
          sequence: row.event_sequence,
          commandId: row.command_id,
          eventJson,
          beforeDigest: row.before_digest,
          afterDigest: row.after_digest,
          previousDigest: row.previous_digest ?? "",
        });
        store.db.prepare("UPDATE events SET event_json = ?, record_digest = ? WHERE event_sequence = 0")
          .run(eventJson, digest);
      }
      expectCorrupt(() => store.stateAtRevision(1));
    } finally {
      store.close();
    }
  }
});

test("validly rehashed sequence gaps and cross-stream digest mismatches fail closed", () => {
  for (const mutation of ["sequence-gap", "cross-stream"] as const) {
    const store = new GameStore(":memory:", { snapshotInterval: 1 });
    try {
      applyOne(store);
      if (mutation === "sequence-gap") {
        const command = store.db.prepare("SELECT * FROM commands WHERE command_sequence = 0").get() as {
          command_id: string;
          command_json: string;
          before_digest: string;
          after_digest: string;
        };
        const event = store.db.prepare("SELECT * FROM events WHERE event_sequence = 0").get() as {
          command_id: string;
          event_json: string;
          before_digest: string;
          after_digest: string;
        };
        store.db.prepare("UPDATE commands SET command_sequence = 2, record_digest = ? WHERE command_sequence = 0").run(sha256({
          kind: "command", runId: store.activeRunId, sequence: 2, commandId: command.command_id,
          commandJson: command.command_json, beforeDigest: command.before_digest, afterDigest: command.after_digest,
          previousDigest: "",
        }));
        store.db.prepare("UPDATE events SET event_sequence = 2, record_digest = ? WHERE event_sequence = 0").run(sha256({
          kind: "event", runId: store.activeRunId, sequence: 2, commandId: event.command_id,
          eventJson: event.event_json, beforeDigest: event.before_digest, afterDigest: event.after_digest,
          previousDigest: "",
        }));
      } else {
        const row = store.db.prepare("SELECT * FROM events WHERE event_sequence = 0").get() as {
          event_sequence: number;
          command_id: string;
          event_json: string;
          before_digest: string;
          after_digest: string;
          previous_digest: string | null;
        };
        const afterDigest = `${row.after_digest}:different`;
        const digest = sha256({
          kind: "event", runId: store.activeRunId, sequence: row.event_sequence, commandId: row.command_id,
          eventJson: row.event_json, beforeDigest: row.before_digest, afterDigest,
          previousDigest: row.previous_digest ?? "",
        });
        store.db.prepare("UPDATE events SET after_digest = ?, record_digest = ? WHERE event_sequence = 0")
          .run(afterDigest, digest);
      }
      expectCorrupt(() => store.stateAtRevision(1));
    } finally {
      store.close();
    }
  }
});
