import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { chromium } from "playwright";
import { resolveChromiumExecutable } from "./browser-equipment.ts";
import { createGameServer } from "../src/server.ts";

async function listen(game: ReturnType<typeof createGameServer>): Promise<string> {
  await new Promise<void>((resolve) => game.server.listen(0, "127.0.0.1", resolve));
  const address = game.server.address();
  if (!address || typeof address === "string") throw new Error("server has no TCP address");
  return `http://127.0.0.1:${address.port}`;
}

process.env.TMPDIR = process.env.ORDIVON_BROWSER_TMPDIR ?? "/tmp";
const directory = mkdtempSync(join(tmpdir(), "ordivon-game-g-series-lab-"));
const game = createGameServer({ dbPath: join(directory, "v2.sqlite3"), v3DbPath: join(directory, "v3.sqlite3") });
const base = await listen(game);
const executablePath = resolveChromiumExecutable(chromium.executablePath());
if (!executablePath) throw new Error("No Chromium executable is available for G-series Concept Lab E2E");
const browser = await chromium.launch({ headless: true, executablePath });
const page = await browser.newPage({ viewport: { width: 1280, height: 960 } });
const browserErrors: string[] = [];
page.on("pageerror", (error) => browserErrors.push(`pageerror:${error.message}`));
page.on("console", (message) => { if (message.type() === "error") browserErrors.push(`console:${message.text()}`); });

try {
  await page.goto(`${base}/lab`, { waitUntil: "networkidle" });
  await page.getByRole("heading", { name: "Concept Lab" }).waitFor();
  assert.match(await page.locator("body").textContent() ?? "", /Casefile/);
  assert.match(await page.locator("body").textContent() ?? "", /cheap playable falsifiers/i);

  // Casefile: the autonomy treatment must react to evidence while the cheap baseline stays fixed.
  await page.locator('[data-question="Sol"]').click();
  const firstAdaptive = await page.locator(".log article").first().textContent() ?? "";
  await page.locator('[data-trace="1"]').click();
  await page.locator('[data-question="Sol"]').click();
  const secondAdaptive = await page.locator(".log article").first().textContent() ?? "";
  assert.notEqual(secondAdaptive, firstAdaptive);
  assert.match(secondAdaptive, /passed the corridor/i);
  await page.locator('[data-accuse="Sol"]').click();
  assert.match(await page.locator(".finish").textContent() ?? "", /Correct\. Sol sabotaged the relay/);

  await page.locator('[data-mode="0"]').click();
  await page.locator('[data-question="Sol"]').click();
  await page.locator('[data-question="Sol"]').click();
  const baselineLog = await page.locator(".log").textContent() ?? "";
  const repeated = baselineLog.match(/I stayed in Galley all evening/g) ?? [];
  assert.equal(repeated.length, 2, "fixed testimony baseline should repeat the exact alibi");

  // Last Light: autonomous companion may refuse exploitative risk transfer; puppet baseline cannot.
  await page.locator('[data-concept="last-light"]').click();
  await page.locator('[data-mode="1"]').click();
  await page.locator('[data-companion="send"]').click();
  await page.locator('[data-companion="send"]').click();
  assert.match(await page.locator(".log").textContent() ?? "", /refuses to be used as expendable scouting/i);
  await page.locator('[data-mode="0"]').click();
  await page.locator('[data-companion="send"]').click();
  await page.locator('[data-companion="send"]').click();
  assert.doesNotMatch(await page.locator(".log").textContent() ?? "", /refuses/i);
  assert.match(await page.locator(".status-grid").textContent() ?? "", /4\/8/);

  // Echo Hunt: the adaptive hunter learns repeated decoy use; the fixed baseline does not.
  await page.locator('[data-concept="echo-hunt"]').click();
  await page.locator('[data-mode="1"]').click();
  await page.locator('[data-echo="decoy"]').click();
  await page.locator('[data-echo="decoy"]').click();
  assert.match(await page.locator(".sensor").textContent() ?? "", /do not turn toward it/i);
  await page.locator('[data-mode="0"]').click();
  await page.locator('[data-echo="decoy"]').click();
  await page.locator('[data-echo="decoy"]').click();
  assert.match(await page.locator(".sensor").textContent() ?? "", /movement veers away/i);

  // Lab must remain isolated from the Station Zero product paths.
  const v3 = await page.request.get(`${base}/v3`);
  assert.equal(v3.status(), 200);
  assert.equal(browserErrors.length, 0, browserErrors.join("\n"));

  console.log(JSON.stringify({
    surface: "g-series-concept-lab",
    treatments: {
      casefile: { adaptiveEvidenceReaction: true, fixedTestimonyRepeats: true },
      lastLight: { autonomousRefusal: true, puppetRefusal: false },
      echoHunt: { repeatedDecoyLearned: true, fixedDecoyResponse: true },
    },
    stationZeroIsolation: true,
    browserErrors,
  }, null, 2));
} finally {
  await browser.close();
  await game.close();
  rmSync(directory, { recursive: true, force: true });
}
