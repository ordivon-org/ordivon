import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import test from "node:test";

import { AgentSessionStore } from "../src/agent/session-store.ts";
import { HostStore } from "../src/host/store.ts";
import { GameStore } from "../src/storage.ts";
import { TeamExecutionStore } from "../src/team/execution-store.ts";
import { TeamStore } from "../src/team/store.ts";

interface ChildResult {
  code: number | null;
  stdout: string;
  stderr: string;
}

function runChild(script: string, args: string[]): Promise<ChildResult> {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, ["--input-type=module", "-e", script, ...args], {
      cwd: process.cwd(),
      env: process.env,
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.once("error", reject);
    child.once("close", (code) => resolve({ code, stdout, stderr }));
  });
}

async function compete(script: string, args: string[], count = 4): Promise<void> {
  const results = await Promise.all(Array.from({ length: count }, () => runChild(script, args)));
  for (const result of results) {
    assert.equal(result.code, 0, result.stderr || result.stdout);
  }
}

test("independent processes converge on one Team initialization, Artifact, and Round", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-multiprocess-"));
  const databasePath = join(directory, "world.sqlite3");
  const runId = "run:multiprocess-idempotency";
  const storageUrl = pathToFileURL(join(process.cwd(), "src/storage.ts")).href;
  const teamStoreUrl = pathToFileURL(join(process.cwd(), "src/team/store.ts")).href;
  const executionStoreUrl = pathToFileURL(join(process.cwd(), "src/team/execution-store.ts")).href;
  const hostStoreUrl = pathToFileURL(join(process.cwd(), "src/host/store.ts")).href;
  const agentSessionStoreUrl = pathToFileURL(join(process.cwd(), "src/agent/session-store.ts")).href;
  const digestUrl = pathToFileURL(join(process.cwd(), "src/digest.ts")).href;

  try {
    const seed = new GameStore(databasePath);
    seed.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
    new TeamExecutionStore(new TeamStore(seed));
    new AgentSessionStore(new HostStore(seed.db));
    seed.close();

    const initializeScript = `
      import { GameStore } from ${JSON.stringify(storageUrl)};
      import { TeamStore } from ${JSON.stringify(teamStoreUrl)};
      const [databasePath, runId] = process.argv.slice(1);
      const game = new GameStore(databasePath);
      try {
        const projection = new TeamStore(game).initialize(runId);
        if (projection.tasks.length !== 4) throw new Error('unexpected task count');
      } finally { game.close(); }
    `;
    await compete(initializeScript, [databasePath, runId], 6);

    const agentInitializeScript = `
      import { GameStore } from ${JSON.stringify(storageUrl)};
      import { HostStore } from ${JSON.stringify(hostStoreUrl)};
      import { AgentSessionStore } from ${JSON.stringify(agentSessionStoreUrl)};
      const [databasePath, runId] = process.argv.slice(1);
      const game = new GameStore(databasePath);
      try {
        const session = new AgentSessionStore(new HostStore(game.db)).initialize(runId, ['fixture']);
        if (session.revision !== 1) throw new Error('unexpected Agent Session revision');
      } finally { game.close(); }
    `;
    await compete(agentInitializeScript, [databasePath, runId], 6);

    const artifactScript = `
      import { GameStore } from ${JSON.stringify(storageUrl)};
      import { HostStore } from ${JSON.stringify(hostStoreUrl)};
      const [databasePath] = process.argv.slice(1);
      const game = new GameStore(databasePath);
      try { new HostStore(game.db).putArtifact('audit-shared-artifact', { value: 1 }); }
      finally { game.close(); }
    `;
    await compete(artifactScript, [databasePath], 6);

    const roundScript = `
      import { GameStore } from ${JSON.stringify(storageUrl)};
      import { TeamStore } from ${JSON.stringify(teamStoreUrl)};
      import { TeamExecutionStore } from ${JSON.stringify(executionStoreUrl)};
      import { sha256 } from ${JSON.stringify(digestUrl)};
      const [databasePath, runId] = process.argv.slice(1);
      const game = new GameStore(databasePath);
      try {
        const state = game.loadState(runId);
        const worldDigest = sha256(state);
        const execution = new TeamExecutionStore(new TeamStore(game));
        execution.putRound({
          roundId: 'team-round:multiprocess-fixed', runId,
          worldRevision: state.revision, worldDigest,
          status: 'collecting', contextIds: [], resolvedActorIds: [], proposalIds: [],
          tickPlanId: null, effectId: null, dispatchId: null, observationId: null,
          blocker: null,
          createdAt: '2026-08-01T00:00:00.000Z',
          updatedAt: '2026-08-01T00:00:00.000Z',
        });
      } finally { game.close(); }
    `;
    await compete(roundScript, [databasePath, runId], 6);

    const game = new GameStore(databasePath);
    try {
      const team = new TeamStore(game);
      const execution = new TeamExecutionStore(team);
      team.verify(runId);
      execution.verify(runId);
      assert.equal(team.listProfiles(runId).length, 3);
      assert.equal(team.listTasks(runId).length, 4);
      assert.equal(execution.listRounds(runId).length, 1);
      const journal = team.host.listJournal(runId);
      assert.equal(journal.filter((event) => event.eventType === "team.configuration-created").length, 1);
      assert.equal(journal.filter((event) => event.eventType === "team.goal-created").length, 1);
      assert.equal(journal.filter((event) => event.eventType === "team.task-created").length, 4);
      assert.equal(journal.filter((event) => event.eventType === "team.round-created").length, 1);
      assert.equal(journal.filter((event) => event.eventType === "goal_created").length, 1);
      assert.equal(journal.filter((event) => event.eventType === "task_created").length, 1);
      assert.equal(
        Number((game.db.prepare("SELECT COUNT(*) AS count FROM game_agent_sessions WHERE run_id = ?").get(runId) as { count: number }).count),
        1,
      );
      const artifacts = game.db.prepare(
        "SELECT COUNT(*) AS count FROM host_artifacts WHERE kind = 'audit-shared-artifact'",
      ).get() as { count: number };
      assert.equal(Number(artifacts.count), 1);
    } finally {
      game.close();
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});
