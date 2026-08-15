import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { chromium } from "playwright";
import { resolveChromiumExecutable } from "./browser-equipment.ts";
import { createGameServer } from "../src/server.ts";


interface RetainedV3StateView {
  run: {
    scenarioCaseId: string;
    status: string;
    turn: number;
  };
  generatedFrom: { worldRevision: number };
  map: { zones: Array<{ zoneId: string; capacity: number }> };
  outcomes: { rescue: string; pirate: string; swarm: string };
}

function zoneCapacity(view: RetainedV3StateView, zoneId: string): number {
  const zone = view.map.zones.find((entry) => entry.zoneId === zoneId);
  assert.ok(zone, `missing Zone ${zoneId}`);
  return zone.capacity;
}

async function listen(game: ReturnType<typeof createGameServer>): Promise<string> {
  await new Promise<void>((resolve) => game.server.listen(0, "127.0.0.1", resolve));
  const address = game.server.address();
  if (!address || typeof address === "string") throw new Error("server has no TCP address");
  return `http://127.0.0.1:${address.port}`;
}

process.env.TMPDIR = process.env.ORDIVON_BROWSER_TMPDIR ?? "/tmp";
const directory = mkdtempSync(join(tmpdir(), "ordivon-game-v3-g5-e2e-"));
const game = createGameServer({ dbPath: join(directory, "v2.sqlite3"), v3DbPath: join(directory, "v3.sqlite3") });
const base = await listen(game);
const executablePath = resolveChromiumExecutable(chromium.executablePath());
if (!executablePath) throw new Error("No Chromium executable is available for Station Zero v3 G5 E2E");
const browser = await chromium.launch({ headless: true, executablePath });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
const browserErrors: string[] = [];
page.on("pageerror", (error) => browserErrors.push(`pageerror:${error.message}`));
page.on("console", (message) => { if (message.type() === "error") browserErrors.push(`console:${message.text()}`); });
const runId = "run:station-zero-v3:g5:junction-bottleneck";

try {
  await page.goto(`${base}/v3`, { waitUntil: "networkidle" });
  await page.getByTestId("scenario-case").selectOption("junction-bottleneck");
  await page.locator("#new-run-id").fill(runId);
  await page.getByTestId("start-run").click();
  await page.getByTestId("turn-number").waitFor();

  assert.match(await page.locator(".topbar .eyebrow").textContent() ?? "", /Junction Bottleneck/);
  const junction = page.locator('[data-zone-id="junction-cover"]');
  assert.equal(await junction.count(), 1);
  assert.match(await junction.textContent() ?? "", /Cap 1/);

  const opened = await page.evaluate(async (retainedRunId) => {
    const response = await fetch(`/api/station-zero-v3/state?runId=${encodeURIComponent(retainedRunId)}`);
    return response.json();
  }, runId) as RetainedV3StateView;
  assert.equal(opened.run.scenarioCaseId, "junction-bottleneck");
  assert.equal(zoneCapacity(opened, "junction-cover"), 1);

  let committedTurns = 0;
  while (await page.getByTestId("terminal-summary").count() === 0) {
    const before = Number(await page.getByTestId("turn-number").textContent());
    assert.ok(Number.isSafeInteger(before) && before < 20);
    if (await page.getByTestId("commit-turn").count() === 0) {
      await page.getByTestId("generate-preview").click();
      await page.getByTestId("commit-turn").waitFor();
    }
    await page.getByTestId("commit-turn").click();
    await page.waitForFunction((previousTurn) => {
      const terminal = document.querySelector('[data-testid="terminal-summary"]');
      const turn = Number(document.querySelector('[data-testid="turn-number"]')?.textContent ?? "-1");
      return Boolean(terminal) || turn > Number(previousTurn);
    }, before);
    committedTurns += 1;
  }

  assert.equal(committedTurns, 20);
  assert.equal(await page.getByTestId("turn-number").textContent(), "20");
  assert.equal(await page.getByTestId("operation-debrief").count(), 1);
  assert.equal(browserErrors.length, 0, browserErrors.join("\n"));

  const retained = await page.evaluate(async (retainedRunId) => {
    const response = await fetch(`/api/station-zero-v3/state?runId=${encodeURIComponent(retainedRunId)}`);
    return response.json();
  }, runId) as RetainedV3StateView;
  assert.equal(retained.run.scenarioCaseId, "junction-bottleneck");
  assert.equal(retained.run.status, "terminal");
  assert.equal(retained.run.turn, 20);
  assert.equal(retained.generatedFrom.worldRevision, 20);
  assert.equal(zoneCapacity(retained, "junction-cover"), 1);
  assert.equal(game.v3Store.getRun(runId).scenarioCaseId, "junction-bottleneck");
  assert.equal(game.v3Store.verify(runId).verified, true);
  assert.equal(game.v3Play.turns.recover(runId).world.turnCount, 20);

  await page.reload({ waitUntil: "networkidle" });
  await page.getByTestId("operation-debrief").waitFor();
  assert.match(await page.locator(".topbar .eyebrow").textContent() ?? "", /Junction Bottleneck/);
  assert.match(await page.locator('[data-zone-id="junction-cover"]').textContent() ?? "", /Cap 1/);
  assert.equal(browserErrors.length, 0, browserErrors.join("\n"));

  console.log(JSON.stringify({
    runId,
    scenarioCaseId: retained.run.scenarioCaseId,
    committedTurns,
    worldRevision: retained.generatedFrom.worldRevision,
    rescueOutcome: retained.outcomes.rescue,
    pirateOutcome: retained.outcomes.pirate,
    swarmOutcome: retained.outcomes.swarm,
    junctionCoverCapacity: zoneCapacity(retained, "junction-cover"),
    browserErrors,
  }, null, 2));
} finally {
  await browser.close();
  await game.close();
  rmSync(directory, { recursive: true, force: true });
}
