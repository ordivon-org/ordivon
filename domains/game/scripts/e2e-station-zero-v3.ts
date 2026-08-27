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

const directory = mkdtempSync(join(tmpdir(), "ordivon-game-v3-e2e-"));
const game = createGameServer({
  researchSurfaces: true,
  dbPath: join(directory, "current.sqlite3"),
  v3DbPath: join(directory, "v3.sqlite3"),
});
const base = await listen(game);
const runId = "run:station-zero-v3:e2e";
const executablePath = resolveChromiumExecutable(chromium.executablePath());
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
  assert.match(await page.locator(".hero-grid").textContent() ?? "", /20turn limit/);
  const productionAssets = await page.evaluate(async () => {
    const paths = [
      "/v3/assets/rescue-specialists.png",
      "/v3/assets/audio/plan-ready.ogg",
      "/v3/assets/audio/commit.ogg",
      "/v3/assets/audio/aftermath.ogg",
    ];
    return Promise.all(paths.map(async (path) => {
      const response = await fetch(path);
      return { path, status: response.status, type: response.headers.get("content-type"), size: Number(response.headers.get("content-length") ?? 0) };
    }));
  });
  for (const asset of productionAssets) assert.equal(asset.status, 200, `missing G4 runtime asset ${asset.path}`);
  await page.locator("#new-run-id").fill(runId);
  await page.getByTestId("start-run").click();
  await page.getByTestId("turn-number").waitFor();
  assert.equal(await page.getByTestId("turn-number").textContent(), "0");
  assert.equal(await page.locator(".map-specialist").count(), 3, "each own specialist should have a distinct tactical atlas token");
  assert.equal(await page.locator(".card-portrait").count(), 3, "Specialist cards should consume the same authored atlas");
  assert.equal(await page.getByTestId("audio-toggle").textContent(), "Audio on");
  await page.getByTestId("audio-toggle").click();
  assert.equal(await page.getByTestId("audio-toggle").getAttribute("aria-pressed"), "true");
  assert.equal(await page.evaluate(() => localStorage.getItem("station-zero-v3-audio-muted")), "1");
  await page.getByTestId("audio-toggle").click();
  assert.equal(await page.getByTestId("audio-toggle").getAttribute("aria-pressed"), "false");
  assert.equal(await page.getByTestId("first-command").getAttribute("data-phase"), "order");
  assert.match(await page.getByTestId("first-command").textContent() ?? "", /Mission intent persists/);
  assert.match(await page.getByTestId("first-command").textContent() ?? "", /Remote capability is per-Turn/);

  assert.equal(await page.getByTestId("order-contingencies").evaluate((details) => details.hasAttribute("open")), false);
  assert.equal(await page.locator('[name="primaryObjectiveId"]').isVisible(), true);
  assert.equal(await page.locator('[name="posture"]').isVisible(), true);
  assert.equal(await page.locator('[name="formation"]').isVisible(), true);
  assert.equal(await page.locator('[name="commanderDirectiveId"]').isVisible(), true);
  assert.equal(await page.locator('[name="lootPolicy"]').isVisible(), false);

  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });
  mobile.on("pageerror", (error) => browserErrors.push(`mobile-pageerror:${error.message}`));
  mobile.on("console", (message) => { if (message.type() === "error") browserErrors.push(`mobile-console:${message.text()}`); });
  await mobile.goto(`${base}/v3`, { waitUntil: "networkidle" });
  await mobile.locator("#new-run-id").fill("run:station-zero-v3:g4-mobile");
  await mobile.getByTestId("start-run").click();
  await mobile.getByTestId("commander-order").waitFor();
  const mobileFlow = await mobile.evaluate(() => {
    const order = document.querySelector('[data-testid="commander-order"]')?.getBoundingClientRect();
    const map = document.querySelector('[data-testid="spatial-map"]')?.getBoundingClientRect();
    return {
      orderTop: order ? Math.round(order.top + scrollY) : null,
      mapTop: map ? Math.round(map.top + scrollY) : null,
      viewportHeight: innerHeight,
      specialistTokens: document.querySelectorAll('.map-specialist').length,
    };
  });
  assert.ok(mobileFlow.orderTop !== null && mobileFlow.orderTop < 900, `mobile Commander Order should begin before y=900, got ${mobileFlow.orderTop}`);
  assert.ok(mobileFlow.mapTop !== null && mobileFlow.orderTop < mobileFlow.mapTop, `mobile Command should precede full tactical map: ${JSON.stringify(mobileFlow)}`);
  assert.equal(mobileFlow.specialistTokens, 3);
  await mobile.close();

  await page.locator('[name="primaryObjectiveId"]').selectOption("recover-research-core");
  assert.match(await page.getByTestId("order-guidance").textContent() ?? "", /Optional side objective/);
  await page.locator('[name="posture"]').selectOption("aggressive");
  await page.locator('[name="formation"]').selectOption("cohesive");
  await page.locator('[name="commanderDirectiveId"]').selectOption("scan-reactor");
  assert.match(await page.getByTestId("order-guidance").textContent() ?? "", /next Planning Head/);
  await page.getByTestId("order-contingencies").locator("summary").click();
  assert.equal(await page.locator('[name="lootPolicy"]').count(), 0, "Product Value audit removed non-leveraged Loot policy from the player surface");
  assert.doesNotMatch(await page.getByTestId("order-contingencies").textContent() ?? "", /Loot policy/);
  await page.getByTestId("order-contingencies").locator("summary").click();

  let delayedPreview = false;
  await page.route("**/api/station-zero-v3/preview?**", async (route) => {
    if (!delayedPreview) { delayedPreview = true; await new Promise((resolve) => setTimeout(resolve, 450)); }
    await route.continue();
  });
  await page.getByTestId("generate-preview").click();
  await page.getByTestId("deliberation-state").waitFor();
  assert.equal(await page.getByTestId("busy").getAttribute("data-busy-kind"), "deliberation");
  assert.match(await page.getByTestId("deliberation-state").textContent() ?? "", /World paused at Turn 0/);
  assert.match(await page.getByTestId("deliberation-state").textContent() ?? "", /Enemy plans sealed/);
  assert.equal(await page.getByTestId("turn-number").textContent(), "0", "Preview waiting must not advance the World");
  await page.waitForTimeout(180);
  const deliberationElapsed = Number.parseFloat((await page.locator('[data-busy-elapsed]').textContent() ?? "0").replace("s", ""));
  assert.ok(deliberationElapsed >= 0.1, `deliberation elapsed time must be client-observed, got ${deliberationElapsed}`);
  await page.getByTestId("plan-preview").waitFor();
  await page.unroute("**/api/station-zero-v3/preview?**");
  assert.equal(await page.getByTestId("first-command").count(), 0, "first-command orientation should disappear once a real plan exists");
  assert.equal(await page.getByTestId("rescue-intent").count(), 3);
  assert.equal(await page.getByTestId("sealed-enemy-plan").count(), 2);
  const retainedAfterGenerate = await page.evaluate(async (retainedRunId) => {
    const response = await fetch(`/api/station-zero-v3/state?runId=${encodeURIComponent(retainedRunId)}`);
    return response.json();
  }, runId);
  assert.equal(retainedAfterGenerate.experience.order.primaryObjectiveId, "recover-research-core");
  assert.equal(retainedAfterGenerate.experience.order.posture, "aggressive");
  assert.equal(retainedAfterGenerate.experience.order.formation, "cohesive");
  assert.equal(retainedAfterGenerate.experience.order.lootPolicy, "mission-only");
  assert.equal(retainedAfterGenerate.experience.order.commanderDirectiveId, "scan-reactor");
  const previewText = await page.getByTestId("plan-preview").textContent();
  assert.ok(previewText?.includes("Rescue plan preview"));
  assert.ok(previewText?.includes("recover-research-core"));
  assert.equal(previewText?.includes("Captain Veyra"), false);
  assert.equal(previewText?.includes("Hive Alpha"), false);
  assert.equal(await page.getByTestId("plan-impact").count(), 1);
  assert.match(await page.getByTestId("plan-impact").textContent() ?? "", /Not an outcome forecast/);
  assert.equal(await page.locator('.plan-impact-row').count(), 3);
  assert.equal(await page.locator('[data-objective-id="rescue-two-civilians"]').getAttribute('data-impact'), "none");
  assert.equal(await page.locator('[data-objective-id="rescue-team-survives"]').getAttribute('data-impact'), "none");
  const selectedCoreImpact = page.locator('[data-objective-id="recover-research-core"]');
  assert.equal(await selectedCoreImpact.getAttribute('data-impact'), "none");
  assert.match(await selectedCoreImpact.textContent() ?? "", /Optional · Priority/);

  await page.locator('[name="posture"]').selectOption("cautious");
  assert.equal(await page.getByTestId("commit-turn").isDisabled(), true, "local Order edits must invalidate the visible Preview before Commit");
  assert.equal(await page.locator("[data-order-dirty-notice]").isVisible(), true);
  assert.equal((await page.getByTestId("generate-preview").textContent())?.trim(), "Regenerate team plan");
  await page.locator('[name="posture"]').selectOption("aggressive");
  assert.equal(await page.getByTestId("commit-turn").isDisabled(), false, "returning to the exact preview-bound Order should restore Commit");
  assert.equal(await page.locator("[data-order-dirty-notice]").isVisible(), false);

  await page.getByTestId("commit-turn").click();
  await page.waitForFunction(() => document.querySelector('[data-testid="turn-number"]')?.textContent === "1");
  await page.getByTestId("aftermath").waitFor();
  assert.equal(await page.locator('[name="primaryObjectiveId"]').inputValue(), "recover-research-core");
  assert.equal(await page.locator('[name="posture"]').inputValue(), "aggressive");
  assert.equal(await page.locator('[name="formation"]').inputValue(), "cohesive");
  assert.equal(await page.locator('[name="lootPolicy"]').count(), 0);
  assert.equal(await page.locator('[name="commanderDirectiveId"]').inputValue(), "reroute-cooling", "Turn-local Remote capability should be recalculated from the new World state");
  const coolingEvidence = page.locator('[data-testid="system-evidence"] [data-system-id="cooling"]');
  assert.equal(await coolingEvidence.count(), 1, "Reactor observation must expose bounded Cooling condition on the next Planning Head");
  assert.match(await coolingEvidence.textContent() ?? "", /58% integrity · unpowered/);
  assert.match(await coolingEvidence.textContent() ?? "", /Last confirmed Turn 0/);
  await page.locator('[name="commanderDirectiveId"]').selectOption("reroute-cooling");
  assert.match(await page.getByTestId("order-guidance").textContent() ?? "", /last observed 1 Turn ago/);
  assert.match(await page.getByTestId("order-guidance").textContent() ?? "", /Power alone will not reduce heat until a local repair raises integrity to 60%/);
  assert.equal((await page.locator('.revision').textContent())?.trim(), "Revision 1");
  await page.getByTestId("temporal-expression-strip").waitFor();
  assert.equal(await page.getByTestId("plan-review").count(), 1);
  assert.equal(await page.getByTestId("plan-review-front").count(), 3);
  assert.equal(await page.locator('[data-testid="plan-review-front"][data-objective-id="recover-research-core"]').getAttribute("data-planned-impact"), "none");
  assert.equal(await page.getByTestId("intent-review").count(), 3);
  assert.match(await page.getByTestId("aftermath").textContent() ?? "", /Planned: Overwatch Command Deck/);
  assert.match(await page.getByTestId("aftermath").textContent() ?? "", /no hostile movement triggered/);
  assert.ok(await page.getByTestId("temporal-expression").count() > 0);
  assert.ok(await page.locator(".temporal-map-event").count() > 0, "freshly committed visible spatial Facts should play once on the tactical map");
  assert.equal(await page.locator(".expression-strip.is-live").count(), 1);
  assert.equal(await page.locator(".aftermath details").evaluate((details) => details.hasAttribute("open")), false);
  const aftermathTop = await page.getByTestId("aftermath").evaluate((element) => element.getBoundingClientRect().top);
  assert.ok(Math.abs(aftermathTop) < 2, `fresh Turn evidence should be brought into view, got top=${aftermathTop}`);
  const turnOneBody = await page.locator("body").textContent() ?? "";
  assert.equal(turnOneBody.includes("Storage Floor"), false);
  assert.equal(turnOneBody.includes("Cargo Crates"), false);
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

  assert.equal(await page.getByTestId("turn-number").textContent(), "20");
  assert.match(await page.getByTestId("terminal-summary").textContent() ?? "", /Rescue/);
  assert.match(await page.getByTestId("terminal-summary").textContent() ?? "", /Pirate/);
  assert.match(await page.getByTestId("terminal-summary").textContent() ?? "", /Swarm/);
  assert.equal(await page.getByTestId("operation-debrief").count(), 1);
  const debriefText = (await page.getByTestId("operation-debrief").textContent() ?? "").replace(/\s+/g, " " ).trim();
  assert.match(debriefText, /Turn limit reached/);
  assert.ok(debriefText.includes("0 / 2 required fronts completed"));
  assert.match(debriefText, /Recover the Research Core/);
  assert.equal(await page.getByTestId("debrief-focus").count(), 1);
  assert.ok((await page.locator('[data-testid="debrief-focus"][data-objective-id="recover-research-core"]').textContent() ?? "").includes("20 / 20 Turns"));
  assert.equal(await page.locator('[data-testid="debrief-focus"][data-objective-id="rescue-two-civilians"]').count(), 0);
  assert.match(debriefText, /No verified progress/);
  assert.equal(debriefText.includes("Eliminate the Hive Alpha"), false);
  assert.equal(await page.getByTestId("commander-order").count(), 0);
  assert.equal(await page.getByTestId("plan-preview").count(), 0);
  assert.equal(await page.getByTestId("commit-turn").count(), 0);
  await page.reload({ waitUntil: "networkidle" });
  await page.getByTestId("operation-debrief").waitFor();
  const reloadedDebriefText = (await page.getByTestId("operation-debrief").textContent() ?? "").replace(/\s+/g, " " ).trim();
  assert.equal(reloadedDebriefText, debriefText, "terminal debrief should reconstruct identically after reload");
  assert.equal(await page.getByTestId("commander-order").count(), 0);
  assert.equal(browserErrors.length, 0, browserErrors.join("\n"));

  const retained = await page.evaluate(async (retainedRunId) => {
    const response = await fetch(`/api/station-zero-v3/state?runId=${encodeURIComponent(retainedRunId)}`);
    return response.json();
  }, runId);
  assert.equal(retained.run.status, "terminal");
  assert.equal(retained.run.turn, 20);
  assert.equal(game.v3Store!.turnCount(runId), 20);
  assert.equal(game.v3Play!.turns.recover(runId).world.turnCount, 20);

  console.log(JSON.stringify({
    runId,
    committedTurns,
    worldRevision: retained.generatedFrom.worldRevision,
    rescueOutcome: retained.outcomes.rescue,
    pirateOutcome: retained.outcomes.pirate,
    swarmOutcome: retained.outcomes.swarm,
    visibleAftermathFacts: retained.aftermath.visibleFacts.length,
    g4: { mobileFlow, productionAssets, delayedPreview, specialistAtlasTokens: 3 },
    browserErrors,
  }, null, 2));
} finally {
  await browser.close();
  await game.close();
  rmSync(directory, { recursive: true, force: true });
}
