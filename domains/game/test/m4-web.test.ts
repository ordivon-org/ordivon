import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { createGameServer } from "../src/server.ts";
import { FixtureTeamProvider } from "../src/team/providers.ts";

async function listen(game: ReturnType<typeof createGameServer>): Promise<string> {
  await new Promise<void>((resolve) => game.server.listen(0, "127.0.0.1", resolve));
  const address = game.server.address();
  if (!address || typeof address === "string") throw new Error("server did not expose a TCP address");
  return `http://127.0.0.1:${address.port}`;
}

test("M4 main page is product-only while the historical engineering console remains available", async () => {
  const main = await readFile(new URL("../web/index.html", import.meta.url), "utf8");
  const debug = await readFile(new URL("../web/debug.html", import.meta.url), "utf8");
  assert.match(main, /Mission Control/);
  assert.doesNotMatch(main, /MANUAL COMMAND|PERSISTENT AGENT|Latest receipt|<pre/);
  assert.match(debug, /MANUAL COMMAND/);
  assert.match(debug, /PERSISTENT AGENT/);
  assert.match(debug, /debug\.js/);
  assert.match(debug, /debug\.css/);
});

test("server exposes the dependency-free M4 module graph and isolated debug surface", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-m4-static-"));
  const game = createGameServer({ dbPath: join(directory, "world.sqlite3"), teamProviderFactory: () => new FixtureTeamProvider() });
  try {
    const base = await listen(game);
    for (const path of [
      "/", "/styles.css", "/app.js", "/api.js", "/store.js", "/render-utils.js", "/render-map.js",
      "/render-actors.js", "/render-inbox.js", "/render-objectives.js", "/render-timeline.js", "/render-shell.js",
      "/debug.html", "/debug.css", "/debug.js",
    ]) {
      const response = await fetch(`${base}${path}`);
      assert.equal(response.status, 200, path);
      assert.ok(Number(response.headers.get("content-length")) > 0, path);
    }
    assert.match(await (await fetch(`${base}/`)).text(), /Mission Control/);
    assert.match(await (await fetch(`${base}/debug.html`)).text(), /MANUAL COMMAND/);
  } finally {
    await game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});
