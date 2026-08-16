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

async function act(page: import("playwright").Page, actionId: string, expectedRevision: number): Promise<void> {
  await page.locator(`[data-case-action="${actionId}"]`).click();
  await page.waitForFunction((revision) => document.querySelector("[data-case-revision]")?.getAttribute("data-case-revision") === String(revision), expectedRevision);
}

process.env.TMPDIR = process.env.ORDIVON_BROWSER_TMPDIR ?? "/tmp";
const directory = mkdtempSync(join(tmpdir(), "ordivon-casefile-e2e-"));
const game = createGameServer({
  dbPath: join(directory, "v2.sqlite3"),
  v3DbPath: join(directory, "v3.sqlite3"),
  casefileDbPath: join(directory, "casefile.sqlite3"),
});
const base = await listen(game);
const executablePath = resolveChromiumExecutable(chromium.executablePath());
if (!executablePath) throw new Error("No Chromium executable is available for Casefile E2E");
const browser = await chromium.launch({ headless: true, executablePath });
const page = await browser.newPage({ viewport: { width: 1280, height: 960 } });
const errors: string[] = [];
page.on("pageerror", (error) => errors.push(`pageerror:${error.message}`));
page.on("console", (message) => { if (message.type() === "error") errors.push(`console:${message.text()}`); });

try {
  await page.goto(`${base}/casefile`, { waitUntil: "networkidle" });
  await page.getByRole("heading", { name: "Casefile" }).waitFor();
  assert.equal(await page.locator("[data-start]").count(), 3);
  await page.locator('[data-start="relay-sabotage"]').click();
  await page.getByRole("heading", { name: "The Silent Relay" }).waitFor();
  assert.match(await page.locator(".clock").textContent() ?? "", /8/);
  assert.equal(await page.locator("body").textContent().then((text) => text?.includes("Responsible:")), false);

  await act(page, "inspect:coolant-fiber", 1);
  await act(page, "question:sol", 2);
  assert.match(await page.locator("body").textContent() ?? "", /never entered the relay corridor/);
  assert.equal(await page.locator('[data-case-action="confront:sol:coolant-fiber"]').count(), 1);

  const url = page.url();
  await page.reload({ waitUntil: "networkidle" });
  assert.equal(page.url(), url);
  assert.match(await page.locator("body").textContent() ?? "", /Coolant glove fiber/);
  assert.match(await page.locator(".clock").textContent() ?? "", /6/);

  await act(page, "confront:sol:coolant-fiber", 3);
  assert.match(await page.locator("body").textContent() ?? "", /I did cross the corridor/);
  await act(page, "question:sol", 4);
  await act(page, "accuse:sol", 5);
  await page.getByTestId("casefile-terminal").waitFor();
  const terminal = await page.getByTestId("casefile-terminal").textContent() ?? "";
  assert.match(terminal, /Accusation confirmed/);
  assert.match(terminal, /Responsible:\s*Sol Renn/);
  assert.match(terminal, /disabled the relay/);
  assert.equal(await page.locator("[data-case-action]").count(), 0);

  await page.reload({ waitUntil: "networkidle" });
  await page.getByTestId("casefile-terminal").waitFor();
  assert.match(await page.getByTestId("casefile-terminal").textContent() ?? "", /Accusation confirmed/);

  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await mobile.goto(`${base}/casefile`, { waitUntil: "networkidle" });
  await mobile.locator('[data-start="missing-med-cache"]').click();
  await mobile.getByRole("heading", { name: "The Missing Cache" }).waitFor();
  const overflow = await mobile.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
  assert.equal(overflow, false);
  await mobile.close();

  assert.equal(errors.length, 0, errors.join("\n"));
  console.log(JSON.stringify({
    surface: "casefile-g6-candidate",
    scenarioCount: 3,
    recoveredAfterReload: true,
    terminalCorrect: true,
    mobileOverflow: false,
    browserErrors: errors,
  }, null, 2));
} finally {
  await browser.close();
  await game.close();
  rmSync(directory, { recursive: true, force: true });
}
