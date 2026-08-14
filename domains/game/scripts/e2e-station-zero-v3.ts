import assert from "node:assert/strict";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { chromium } from "playwright";

import { createGameServer } from "../src/server.ts";

function browserExecutable(): string | undefined {
  const candidates = [
    process.env.ORDIVON_CHROMIUM_EXECUTABLE,
    chromium.executablePath(),
    "/root/.cache/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell",
    "/root/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  ].filter((candidate): candidate is string => Boolean(candidate));
  return candidates.find((candidate) => existsSync(candidate));
}

async function listen(game: ReturnType<typeof createGameServer>): Promise<string> {
  await new Promise<void>((resolve) => game.server.listen(0, "127.0.0.1", resolve));
  const address = game.server.address();
  if (!address || typeof address === "string") throw new Error("server has no TCP address");
  return `http://127.0.0.1:${address.port}`;
}

process.env.TMPDIR = process.env.ORDIVON_BROWSER_TMPDIR ?? "/tmp";

const directory = mkdtempSync(join(tmpdir(), "ordivon-game-v3-e2e-"));
const game = createGameServer({
  dbPath: join(directory, "current.sqlite3"),
  v3DbPath: join(directory, "v3.sqlite3"),
});
const base = await listen(game);
const runId = "run:station-zero-v3:e2e";
const executablePath = browserExecutable();
if (!executablePath) throw new Error("No Chromium executable is available for Station Zero v3 E2E");
const browser = await chromium.launch({ headless: true, executablePath });
const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
const browserErrors: string[] = [];
page.on("pageerror", (error) => browserErrors.push(`pageerror:${error.message}`));
page.on("console", (message) => {
  if (message.type() === "error") browserErrors.push(`console:${message.text()}`);
});

try {
  await page.goto(`${base}/v3`, { waitUntil: "networkidle" });
  await page.getByTestId("start-run").waitFor();
  await page.locator("#new-run-id").fill(runId);
  await page.getByTestId("start-run").click();
  await page.getByTestId("turn-number").waitFor();
  assert.equal(await page.getByTestId("turn-number").textContent(), "0");

  await page.locator('[name="primaryObjectiveId"]').selectOption("recover-research-core");
  await page.locator('[name="posture"]').selectOption("aggressive");
  await page.locator('[name="formation"]').selectOption("cohesive");
  await page.locator('[name="lootPolicy"]').selectOption("opportunistic");
  await page.locator('[name="commanderDirectiveId"]').selectOption("scan-reactor");
  await page.getByTestId("generate-preview").click();
  await page.getByTestId("plan-preview").waitFor();
  assert.equal(await page.getByTestId("rescue-intent").count(), 3);
  assert.equal(await page.getByTestId("sealed-enemy-plan").count(), 2);
  const previewText = await page.getByTestId("plan-preview").textContent();
  assert.ok(previewText?.includes("Rescue plan preview"));
  assert.equal(previewText?.includes("Captain Veyra"), false);
  assert.equal(previewText?.includes("Hive Alpha"), false);

  await page.getByTestId("commit-turn").click();
  await page.waitForFunction(() => document.querySelector('[data-testid="turn-number"]')?.textContent === "1");
  await page.getByTestId("aftermath").waitFor();
  await page.getByTestId("temporal-expression-strip").waitFor();
  assert.ok(await page.getByTestId("temporal-expression").count() > 0);
  assert.ok(await page.locator(".temporal-map-event").count() > 0, "freshly committed visible spatial Facts should play once on the tactical map");
  assert.equal(await page.locator(".expression-strip.is-live").count(), 1);
  assert.equal(await page.locator(".aftermath details").evaluate((details) => details.hasAttribute("open")), false);
  const aftermathTop = await page.getByTestId("aftermath").evaluate((element) => element.getBoundingClientRect().top);
  assert.ok(Math.abs(aftermathTop) < 2, `fresh Turn evidence should be brought into view, got top=${aftermathTop}`);
  const turnOneBody = await page.locator("body").textContent() ?? "";
  assert.equal(turnOneBody.includes("Storage Floor"), false);
  assert.equal(turnOneBody.includes("Cargo Crates"), false);
  assert.ok(turnOneBody.includes("an uncharted sector"), "hidden movement origins should remain anonymous in the player recap");
  await page.waitForTimeout(2_000);
  const retainedOverlayOpacities = await page.locator(".temporal-map-event").evaluateAll((elements) =>
    elements.map((element) => Number(getComputedStyle(element).opacity)));
  assert.ok(retainedOverlayOpacities.every((opacity) => opacity <= 0.01), `temporal map playback must leave no state-like residue: ${retainedOverlayOpacities.join(",")}`);

  await page.reload({ waitUntil: "networkidle" });
  await page.getByTestId("turn-number").waitFor();
  assert.equal(await page.getByTestId("turn-number").textContent(), "1");
  await page.getByTestId("aftermath").waitFor();
  assert.equal(await page.getByTestId("temporal-expression-strip").count(), 1, "retained recap should survive reload");
  assert.equal(await page.locator(".expression-strip.is-live").count(), 0, "retained recap must not replay itself");
  assert.equal(await page.locator(".temporal-map-event").count(), 0, "map playback must be one-shot and absent on resume");
  assert.equal(await page.locator(".aftermath details").evaluate((details) => details.hasAttribute("open")), false);
  const resumedBody = await page.locator("body").textContent() ?? "";
  assert.equal(resumedBody.includes("Storage Floor"), false);
  assert.equal(resumedBody.includes("Cargo Crates"), false);

  let committedTurns = 1;
  while (await page.getByTestId("terminal-summary").count() === 0) {
    const before = Number(await page.getByTestId("turn-number").textContent());
    assert.ok(Number.isSafeInteger(before) && before < 14);
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

  assert.equal(await page.getByTestId("turn-number").textContent(), "14");
  assert.match(await page.getByTestId("terminal-summary").textContent() ?? "", /Rescue/);
  assert.match(await page.getByTestId("terminal-summary").textContent() ?? "", /Pirate/);
  assert.match(await page.getByTestId("terminal-summary").textContent() ?? "", /Swarm/);
  assert.equal(browserErrors.length, 0, browserErrors.join("\n"));

  const retained = await page.evaluate(async (retainedRunId) => {
    const response = await fetch(`/api/station-zero-v3/state?runId=${encodeURIComponent(retainedRunId)}`);
    return response.json();
  }, runId);
  assert.equal(retained.run.status, "terminal");
  assert.equal(retained.run.turn, 14);
  assert.equal(game.v3Store.turnCount(runId), 14);
  assert.equal(game.v3Play.turns.recover(runId).world.turnCount, 14);

  console.log(JSON.stringify({
    runId,
    committedTurns,
    worldRevision: retained.generatedFrom.worldRevision,
    rescueOutcome: retained.outcomes.rescue,
    pirateOutcome: retained.outcomes.pirate,
    swarmOutcome: retained.outcomes.swarm,
    visibleAftermathFacts: retained.aftermath.visibleFacts.length,
    browserErrors,
  }, null, 2));
} finally {
  await browser.close();
  await game.close();
  rmSync(directory, { recursive: true, force: true });
}
