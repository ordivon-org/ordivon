import assert from "node:assert/strict";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { chromium } from "playwright";

import type { DeploymentProviderOptions } from "../src/deployment/model.ts";
import { createGameServer } from "../src/server.ts";
import type { MissionProviderFactory } from "../src/mission-control/service.ts";
import { FixtureTeamProvider } from "../src/team/providers.ts";

const fixtureFactory: MissionProviderFactory = (_name, options?: DeploymentProviderOptions) =>
  new FixtureTeamProvider({
    breachStrategy: options?.coordinationProfileId === "engineer-seal"
      ? "engineer-seal"
      : "security-contain",
  });

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

async function waitIdle(page: import("playwright").Page): Promise<void> {
  await page.waitForFunction(() => !document.querySelector(".busy-overlay"));
}

async function clickAndWait(page: import("playwright").Page, name: string | RegExp): Promise<void> {
  await page.getByRole("button", { name }).click();
  await waitIdle(page);
}

async function finishMission(page: import("playwright").Page): Promise<{ runActions: number; approvals: number }> {
  let runActions = 0;
  let approvals = 0;
  for (let index = 0; index < 40; index += 1) {
    if (await page.locator(".terminal-panel").count()) return { runActions, approvals };
    const authorize = page.getByRole("button", { name: "Authorize" });
    if (await authorize.count()) {
      await authorize.first().click();
      approvals += 1;
      await waitIdle(page);
      continue;
    }
    const run = page.getByRole("button", { name: "Run until intervention" });
    await run.waitFor({ state: "visible" });
    if (!await run.isEnabled()) {
      const text = await page.locator(".mission-shell").innerText();
      throw new Error(`Mission stopped without an actionable intervention:\n${text}`);
    }
    await run.click();
    runActions += 1;
    await waitIdle(page);
  }
  throw new Error("Mission did not reach a terminal state within 40 player decisions");
}

process.env.TMPDIR = process.env.ORDIVON_BROWSER_TMPDIR ?? "/tmp";

const directory = mkdtempSync(join(tmpdir(), "ordivon-first-playable-e2e-"));
const game = createGameServer({
  dbPath: join(directory, "station-zero.sqlite3"),
  providerFactory: fixtureFactory,
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
  await page.getByRole("heading", { name: "Command the emergency, not every Tick." }).waitFor();
  await page.selectOption('select[name="scenarioCaseId"]', "power-constrained");
  await page.selectOption('select[name="doctrineId"]', "critical-approval");
  await clickAndWait(page, "Begin emergency response");
  await page.getByRole("heading", { name: "Station Zero", level: 1 }).waitFor();
  await page.getByRole("heading", { name: "What needs command attention" }).waitFor();
  assert.equal(await page.getByRole("button", { name: "Prepare proposals" }).count(), 0);
  assert.equal(await page.getByRole("button", { name: "Commit one verified Tick" }).count(), 0);

  await page.getByText("Issue a direct command").first().click();
  await page.getByRole("button", { name: "Pause" }).first().click();
  await waitIdle(page);
  await page.getByRole("button", { name: "Resume" }).first().click();
  await waitIdle(page);

  const firstInteraction = await finishMission(page);
  await page.getByRole("heading", { name: "Rescue signal verified" }).waitFor();
  assert.ok(firstInteraction.runActions < 18, JSON.stringify(firstInteraction));
  assert.ok(firstInteraction.approvals > 0, JSON.stringify(firstInteraction));
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
  await page.getByRole("heading", { name: "Change the command doctrine. Compare the consequence." }).waitFor();
  await page.getByText("Provider and coordination configuration").click();
  await page.selectOption('select[name="coordinationProfileId"]', "engineer-seal");
  await clickAndWait(page, "Start comparison mission");
  const secondInteraction = await finishMission(page);
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
    schemaVersion: 2,
    kind: "ordivon.game.first-playable-browser-receipt",
    browser: await browser.version(),
    firstRunId,
    secondRunId,
    firstOutcome: "victory",
    secondOutcome: "power_exhausted",
    firstInteraction,
    secondInteraction,
    replayRevision: 5,
    diagnosis: "verified-direct",
    comparison: "exact",
    reloadRecovered: true,
    productLoop: "intervention-driven",
  }, null, 2));
} finally {
  await browser?.close();
  await game.close();
  rmSync(directory, { recursive: true, force: true });
}
