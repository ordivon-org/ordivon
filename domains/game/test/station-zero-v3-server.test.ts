import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { createGameServer } from "../src/server.ts";

async function listen(game: ReturnType<typeof createGameServer>): Promise<string> {
  await new Promise<void>((resolve) => game.server.listen(0, "127.0.0.1", resolve));
  const address = game.server.address();
  if (!address || typeof address === "string") throw new Error("server has no TCP address");
  return `http://127.0.0.1:${address.port}`;
}

async function json(response: Response): Promise<any> {
  const body = await response.json();
  assert.equal(response.ok, true, JSON.stringify(body));
  return body;
}

test("v3 preview API is isolated from the current executable and supports one explicit Turn commit", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-v3-server-"));
  const game = createGameServer({
    dbPath: join(directory, "current.sqlite3"),
    v3DbPath: join(directory, "v3.sqlite3"),
  });
  const base = await listen(game);
  const runId = "run:station-zero-v3:http";
  try {
    const previewHtml = await fetch(`${base}/v3`).then((response) => response.text());
    assert.match(previewHtml, /Station Zero v3/);
    const currentHtml = await fetch(`${base}/`).then((response) => response.text());
    assert.match(currentHtml, /ORDIVON GAME/);
    const rawSpatialLayout = await fetch(`${base}/assets/station-zero-v3/station-zero-layout.tmj`);
    assert.equal(rawSpatialLayout.status, 404, "full authored topology must never be served to the player browser");
    for (const sourceAsset of [
      "/assets/station-zero-v3/rescue-expression.aseprite",
      "/assets/station-zero-v3/rescue-expression.json",
      "/assets/station-zero-v3/expression-signals.svg",
      "/v3/assets/rescue-expression.aseprite",
      "/v3/assets/rescue-expression.json",
      "/v3/assets/expression-signals.svg",
    ]) {
      assert.equal((await fetch(`${base}${sourceAsset}`)).status, 404, `authoring source ${sourceAsset} must stay server-private`);
    }
    const sprite = await fetch(`${base}/v3/assets/rescue-expression.png`);
    assert.equal(sprite.status, 200);
    assert.equal(sprite.headers.get("content-type"), "image/png");
    for (const vectorAsset of ["system-signal.svg", "hazard-signal.svg"]) {
      const response = await fetch(`${base}/v3/assets/${vectorAsset}`);
      assert.equal(response.status, 200);
      assert.match(response.headers.get("content-type") ?? "", /^image\/svg\+xml/);
    }

    const catalog = await json(await fetch(`${base}/api/station-zero-v3/catalog`));
    assert.equal(catalog.kind, "ordivon.game.station-zero-v3-play-catalog");
    assert.equal(catalog.objectives.length, 3);

    const initialized = await json(await fetch(`${base}/api/station-zero-v3/runs`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ runId }),
    }));
    assert.equal(initialized.run.turn, 0);
    assert.equal(initialized.experience.preview, null);
    assert.equal(initialized.experience.canGeneratePreview, true);

    const currentRuns = await json(await fetch(`${base}/api/runs`));
    assert.equal(currentRuns.runs.some((run: any) => run.runId === runId), false);
    const v3Runs = await json(await fetch(`${base}/api/station-zero-v3/runs`));
    assert.equal(v3Runs.runs.some((run: any) => run.runId === runId), true);

    const saved = await json(await fetch(`${base}/api/station-zero-v3/order?runId=${encodeURIComponent(runId)}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        primaryObjectiveId: "recover-research-core",
        posture: "aggressive",
        formation: "cohesive",
        commanderDirectiveId: "scan-reactor",
        lootPolicy: "opportunistic",
      }),
    }));
    assert.equal(saved.view.experience.order.primaryObjectiveId, "recover-research-core");
    assert.equal(saved.view.experience.orderRevision, 2);

    const generated = await json(await fetch(`${base}/api/station-zero-v3/preview?runId=${encodeURIComponent(runId)}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: "{}",
    }));
    assert.equal(generated.view.experience.preview.actorIntents.length, 3);
    assert.deepEqual(generated.view.experience.preview.enemyPlansSealed.map((entry: any) => entry.factionId), ["pirate", "swarm"]);
    assert.equal(typeof generated.previewId, "string");
    assert.equal(typeof generated.previewDigest, "string");
    assert.equal("preview" in generated, false);
    assert.equal(JSON.stringify(generated).includes("pirate-captain-veyra"), false);
    assert.equal(JSON.stringify(generated).includes("swarm-stalker-kappa"), false);

    const beforeCommit = await json(await fetch(`${base}/api/station-zero-v3/state?runId=${encodeURIComponent(runId)}`));
    assert.equal(beforeCommit.run.turn, 0);
    assert.equal(game.v3Store.turnCount(runId), 0);

    const committed = await json(await fetch(`${base}/api/station-zero-v3/commit?runId=${encodeURIComponent(runId)}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ previewId: generated.previewId }),
    }));
    assert.equal(committed.worldRevision, 1);
    assert.equal(committed.view.run.turn, 1);
    assert.ok(committed.view.aftermath.visibleFacts.length > 0);
    assert.equal(game.v3Store.turnCount(runId), 1);

    const resumed = await json(await fetch(`${base}/api/station-zero-v3/resume?runId=${encodeURIComponent(runId)}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: "{}",
    }));
    assert.equal(resumed.run.turn, 1);
    assert.ok(resumed.experience.order);
  } finally {
    await game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("v3 HTTP rejects invalid strategic controls before changing the Order", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-v3-server-invalid-"));
  const game = createGameServer({ dbPath: ":memory:", v3DbPath: ":memory:" });
  const base = await listen(game);
  const runId = "run:station-zero-v3:http-invalid";
  try {
    await json(await fetch(`${base}/api/station-zero-v3/runs`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ runId }),
    }));
    const response = await fetch(`${base}/api/station-zero-v3/order?runId=${encodeURIComponent(runId)}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ posture: "omniscient" }),
    });
    const body = await response.json();
    assert.equal(response.status, 400);
    assert.equal(body.error, "invalid_request");
    const state = await json(await fetch(`${base}/api/station-zero-v3/state?runId=${encodeURIComponent(runId)}`));
    assert.equal(state.experience.order.posture, "balanced");
    assert.equal(state.experience.orderRevision, 1);
  } finally {
    await game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});
