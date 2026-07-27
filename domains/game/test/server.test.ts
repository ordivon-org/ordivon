import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { createGameServer } from "../src/server.ts";

async function listen(game: ReturnType<typeof createGameServer>): Promise<string> {
  await new Promise<void>((resolve) => game.server.listen(0, "127.0.0.1", resolve));
  const address = game.server.address();
  if (!address || typeof address === "string") throw new Error("server did not expose a TCP address");
  return `http://127.0.0.1:${address.port}`;
}

test("web surface displays persisted state and accepts one action", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-server-test-"));
  const game = createGameServer({ dbPath: join(directory, "world.sqlite3") });

  try {
    const base = await listen(game);
    const page = await fetch(`${base}/`).then((response) => response.text());
    assert.match(page, /Station Zero/);

    const initial = await fetch(`${base}/api/state`).then((response) => response.json());
    assert.equal(initial.state.rooms["life-support"].powered, false);

    const suggestion = await fetch(`${base}/api/suggestion`).then((response) => response.json());
    assert.equal(suggestion.admitted.actionId, "restore-life-support-power");

    const actionResponse = await fetch(`${base}/api/actions`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        kind: "restore_power",
        commandId: "server-test-1",
        actorId: "engineer-01",
        targetId: "life-support",
        expectedRevision: 0,
      }),
    });
    assert.equal(actionResponse.status, 200);

    const terminal = await fetch(`${base}/api/state`).then((response) => response.json());
    assert.equal(terminal.state.rooms["life-support"].powered, true);
    assert.equal(terminal.eventCount, 1);

    const replay = await fetch(`${base}/api/replay`).then((response) => response.json());
    assert.equal(replay.verified, true);
    assert.equal(replay.digest, terminal.digest);
  } finally {
    await game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});
