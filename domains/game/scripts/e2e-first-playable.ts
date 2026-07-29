import assert from "node:assert/strict";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { chromium } from "playwright";

import type { DeploymentProviderOptions } from "../src/deployment/model.ts";
import { createGameServer, type TeamProviderFactory } from "../src/server.ts";
import { FixtureTeamProvider } from "../src/team/providers.ts";

const fixtureFactory: TeamProviderFactory = (_name, options?: DeploymentProviderOptions) =>
  new FixtureTeamProvider({
    breachStrategy: options?.coordinationProfileId === "engineer-seal"
      ? "engineer-seal"
      : "security-contain",
  });

function browserExecutable(): string | undefined {
  const candidates = [
    process.env.ORDIVON_CHROMIUM_EXECUTABLE,
    chromium.executablePath(),
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  ].filter((candidate): candidate is string => Boolean(candidate));
  return candidates.find((candidate) => existsSync(candidate));
}

async function waitIdle(page: import("playwright").Page): Promise<void> {
  await page.waitForFunction(() => !document.querySelector(".busy-overlay"));
}

async function clickAndWait(
  page: import("playwright").Page,
  name: string | RegExp,
): Promise<void> {
  await page.getByRole("button", { name }).click();
  await waitIdle(page);
}

async function finishMission(page: import("playwright").Page): Promise<void> {
  for (let index = 0; index < 30; index += 1) {
    if (await page.locator(".terminal-panel").count()) return;
    const prepare = page.getByRole("button", { name: "Prepare proposals" });
    await prepare.waitFor({ state: "visible" });
    if (await prepare.isEnabled()) await clickAndWait(page, "Prepare proposals");
    if (await page.locator(".terminal-panel").count()) return;
    const commit = page.getByRole("button", { name: "Commit one verified Tick" });
    await commit.waitFor({ state: "visible" });
    if (await commit.isEnabled()) await clickAndWait(page, "Commit one verified Tick");
  }
  throw new Error("Mission did not reach a terminal state within 30 Rounds");
}

process.env.TMPDIR = process.env.ORDIVON_BROWSER_TMPDIR ?? "/tmp";

const directory = mkdtempSync(join(tmpdir(), "ordivon-first-playable-e2e-"));
const game = createGameServer({
  dbPath: join(directory, "station-zero.sqlite3"),
  teamProviderFactory: fixtureFactory,
});
let browser: import("playwright").Browser | null = null;
try {
  await new Promise<void>((resolve) => game.server.listen(0, "127.0.0.1", resolve));
  const address = game.server.address();
  if (!address || typeof address === "string") throw new Error("Game server has no TCP address");
  const base = `http://127.0.0.1:${address.port}`;
  const executablePath = browserExecutable();
  if (!executablePath) throw new Error("No Chromium-compatible executable is available");
  browser = await chromium.launch({ headless: true, executablePath });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const browserErrors: string[] = [];
  page.on("pageerror", (error) => browserErrors.push(error.message));

  await page.goto(base, { waitUntil: "networkidle" });
  await page.getByRole("heading", { name: "Direct an imperfect autonomous team." }).waitFor();
  await page.selectOption('select[name="scenarioCaseId"]', "power-constrained");
  await page.selectOption('select[name="coordinationProfileId"]', "specialist-containment");
  await clickAndWait(page, "Start verified mission");
  await page.getByRole("heading", { name: "Station Zero", level: 1 }).waitFor();

  await page.getByRole("button", { name: "Pause" }).first().click();
  await waitIdle(page);
  await page.getByRole("button", { name: "Resume" }).first().click();
  await waitIdle(page);
  await finishMission(page);
  await page.getByRole("heading", { name: "Rescue signal verified" }).waitFor();
  const firstRunUrl = new URL(page.url());
  const firstRunId = firstRunUrl.searchParams.get("runId");
  assert.ok(firstRunId);

  await clickAndWait(page, "Open verified Replay");
  await page.locator("[data-replay-revision]").waitFor();
  const slider = page.locator("[data-replay-revision]");
  await slider.fill("5");
  await waitIdle(page);
  await page.getByRole("heading", { name: "Revision 5", level: 1, exact: true }).waitFor();
  assert.match(page.url(), /view=replay/);
  assert.match(page.url(), /revision=5/);

  await clickAndWait(page, "Diagnosis");
  await page.getByRole("heading", { name: "Why the mission succeeded" }).waitFor();
  assert.ok(await page.locator(".diagnosis-claim.verified-direct").count());

  await clickAndWait(page, "Mission");
  await clickAndWait(page, "Deploy again from this Run");
  await page.getByRole("heading", { name: "Change one verified deployment input." }).waitFor();
  await page.selectOption('select[name="coordinationProfileId"]', "engineer-seal");
  await clickAndWait(page, "Start comparison Run");
  await finishMission(page);
  await page.getByRole("heading", { name: "Mission failed" }).waitFor();
  assert.match(await page.locator(".terminal-panel").innerText(), /power_exhausted/);
  const secondRunUrl = new URL(page.url());
  const secondRunId = secondRunUrl.searchParams.get("runId");
  assert.ok(secondRunId && secondRunId !== firstRunId);
  assert.equal(secondRunUrl.searchParams.get("compareRunId"), firstRunId);

  await clickAndWait(page, "Compare with base Run");
  await page.getByRole("heading", { name: "Exact compatible comparison" }).waitFor();
  const comparisonText = await page.locator(".comparison-grid").innerText();
  assert.match(comparisonText, /Victory/i);
  assert.match(comparisonText, /Failure/i);
  assert.match(await page.locator(".comparison-differences").innerText(), /Coordination profile/i);

  await page.reload({ waitUntil: "networkidle" });
  await page.getByRole("heading", { name: "Exact compatible comparison" }).waitFor();
  assert.equal(new URL(page.url()).searchParams.get("runId"), secondRunId);
  assert.deepEqual(browserErrors, []);

  console.log(JSON.stringify({
    schemaVersion: 1,
    kind: "ordivon.game.first-playable-browser-receipt",
    browser: await browser.version(),
    firstRunId,
    secondRunId,
    firstOutcome: "victory",
    secondOutcome: "power_exhausted",
    replayRevision: 5,
    diagnosis: "verified-direct",
    comparison: "exact",
    reloadRecovered: true,
  }, null, 2));
} finally {
  await browser?.close();
  await game.close();
  rmSync(directory, { recursive: true, force: true });
}
