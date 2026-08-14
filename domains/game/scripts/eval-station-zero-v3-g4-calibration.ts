import { execFileSync } from "node:child_process";
import { existsSync, mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { chromium, type Browser, type Page } from "playwright";

import { createGameServer } from "../src/server.ts";

type Severity = "critical" | "major" | "minor";
interface Finding { id: string; severity: Severity; passed: boolean; evidence: unknown; }

const findings: Finding[] = [];
function finding(id: string, severity: Severity, passed: boolean, evidence: unknown): void {
  findings.push({ id, severity, passed, evidence });
}

function chromiumExecutable(): string {
  const candidates = [
    process.env.ORDIVON_CHROMIUM_EXECUTABLE,
    chromium.executablePath(),
    "/root/.cache/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell",
    "/root/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
  ].filter((entry): entry is string => Boolean(entry));
  const selected = candidates.find((entry) => existsSync(entry));
  if (!selected) throw new Error("No Chromium executable available for G4 calibration");
  return selected;
}

async function startRun(page: Page, base: string, runId: string): Promise<void> {
  await page.goto(`${base}/v3`, { waitUntil: "networkidle" });
  await page.locator("#new-run-id").fill(runId);
  await page.getByTestId("start-run").click();
  await page.getByTestId("turn-number").waitFor();
}

function silhouetteMetrics(): { opaque: Record<string, number>; pairwiseDifference: Record<string, number>; minimumDifference: number } {
  const temp = mkdtempSync(join(tmpdir(), "station-zero-g4-silhouette-"));
  try {
    const atlas = resolve("web-v3/assets/rescue-specialists.png");
    const frames = { engineer: 0, medic: 24, security: 48 } as const;
    const opaque: Record<string, number> = {};
    for (const [name, x] of Object.entries(frames)) {
      const output = join(temp, `${name}.png`);
      execFileSync("/usr/bin/convert", [atlas, "-crop", `24x24+${x}+0`, "+repage", "-alpha", "extract", output], { stdio: "ignore" });
      const raw = execFileSync("/usr/bin/convert", [output, "-threshold", "1", "-format", "%[fx:mean*576]", "info:"], { encoding: "utf8" });
      opaque[name] = Math.round(Number(raw.trim()));
    }
    const pairs = [["engineer", "medic"], ["engineer", "security"], ["medic", "security"]] as const;
    const pairwiseDifference: Record<string, number> = {};
    for (const [left, right] of pairs) {
      try {
        execFileSync("/usr/bin/compare", ["-metric", "AE", join(temp, `${left}.png`), join(temp, `${right}.png`), "null:"], { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
        pairwiseDifference[`${left}-${right}`] = 0;
      } catch (error: any) {
        const text = String(error?.stderr ?? "").trim();
        const match = text.match(/^(\d+)/);
        if (!match) throw error;
        pairwiseDifference[`${left}-${right}`] = Number(match[1]);
      }
    }
    return { opaque, pairwiseDifference, minimumDifference: Math.min(...Object.values(pairwiseDifference)) };
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
}

async function geometryAndMedia(browser: Browser, base: string): Promise<void> {
  const desktop = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
  await startRun(desktop, base, "run:g4-calibration:desktop");
  const d = await desktop.evaluate(() => {
    const rect = (selector: string) => {
      const element = document.querySelector(selector);
      if (!element) return null;
      const r = element.getBoundingClientRect();
      return { top: Math.round(r.top + scrollY), bottom: Math.round(r.bottom + scrollY), width: Math.round(r.width), height: Math.round(r.height) };
    };
    return { order: rect('[data-testid="commander-order"]'), map: rect('[data-testid="spatial-map"]'), overflowX: document.documentElement.scrollWidth > innerWidth };
  });
  finding("desktop-no-horizontal-overflow", "major", !d.overflowX, d);
  finding("desktop-command-near-first-viewport", "minor", Boolean(d.order && d.order.top < 1150), d);
  await desktop.close();

  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await startRun(mobile, base, "run:g4-calibration:mobile");
  const m = await mobile.evaluate(() => {
    const rect = (selector: string) => {
      const element = document.querySelector(selector);
      if (!element) return null;
      const r = element.getBoundingClientRect();
      return { top: Math.round(r.top + scrollY), bottom: Math.round(r.bottom + scrollY) };
    };
    return {
      order: rect('[data-testid="commander-order"]'),
      map: rect('[data-testid="spatial-map"]'),
      overflowX: document.documentElement.scrollWidth > innerWidth,
      domOrder: [...document.querySelectorAll('.mission > *')].map((element) => element.className),
    };
  });
  finding("mobile-command-before-map", "critical", Boolean(m.order && m.map && m.order.top < m.map.top), m);
  finding("mobile-command-first-viewport", "major", Boolean(m.order && m.order.top < 900), m);
  finding("mobile-no-horizontal-overflow", "major", !m.overflowX, m);
  finding("mobile-dom-reading-order", "critical", m.domOrder.indexOf("planning-grid") < m.domOrder.indexOf("situation-grid"), m.domOrder);

  await mobile.evaluate(() => document.body.focus());
  const tabSequence: Array<{ insideOrder: boolean; insideMap: boolean; action: string | null; name: string | null; top: number | null }> = [];
  for (let index = 0; index < 9; index += 1) {
    await mobile.keyboard.press("Tab");
    tabSequence.push(await mobile.evaluate(() => {
      const element = document.activeElement as HTMLElement | null;
      const r = element?.getBoundingClientRect();
      return {
        insideOrder: Boolean(element && document.querySelector('[data-testid="commander-order"]')?.contains(element)),
        insideMap: Boolean(element && document.querySelector('[data-testid="spatial-map"]')?.contains(element)),
        action: element?.dataset.action ?? null,
        name: element?.getAttribute("name") ?? null,
        top: r ? Math.round(r.top + scrollY) : null,
      };
    }));
  }
  const firstMap = tabSequence.findIndex((entry) => entry.insideMap);
  const firstOrder = tabSequence.findIndex((entry) => entry.insideOrder);
  finding("mobile-tab-order-follows-command-before-map", "critical", firstOrder >= 0 && firstMap > firstOrder, tabSequence);
  await mobile.close();

  const mediaFail = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await mediaFail.route("**/v3/assets/rescue-specialists.png", (route) => route.abort());
  await mediaFail.route("**/v3/assets/audio/**", (route) => route.abort());
  await startRun(mediaFail, base, "run:g4-calibration:media-failure");
  const fallback = await mediaFail.evaluate(() => ({
    tokens: [...document.querySelectorAll('.specialist-token')].map((element) => ({ text: element.textContent?.trim(), label: element.getAttribute("aria-label") })),
    names: [...document.querySelectorAll('.actor-card h3')].map((element) => element.textContent?.trim()),
  }));
  finding("media-failure-keeps-specialist-identity", "critical", fallback.tokens.length === 6 && fallback.tokens.every((entry) => entry.text && entry.label) && fallback.names.length === 3, fallback);
  await mediaFail.close();

  const reduced = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: "reduce" });
  await startRun(reduced, base, "run:g4-calibration:reduced-motion");
  const reducedState = await reduced.evaluate(() => ({
    prefers: matchMedia("(prefers-reduced-motion: reduce)").matches,
    tokenAnimation: getComputedStyle(document.querySelector('.specialist-token')!).animationName,
  }));
  finding("reduced-motion-static-specialist-state", "major", reducedState.prefers && reducedState.tokenAnimation === "none", reducedState);
  await reduced.close();
}

async function repeatedTurnCalibration(browser: Browser, base: string): Promise<void> {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  let previewRequests = 0;
  let commitRequests = 0;
  await page.route("**/api/station-zero-v3/preview?**", async (route) => { previewRequests += 1; await new Promise((resolve) => setTimeout(resolve, 300)); await route.continue(); });
  await page.route("**/api/station-zero-v3/commit?**", async (route) => { commitRequests += 1; await new Promise((resolve) => setTimeout(resolve, 300)); await route.continue(); });
  await startRun(page, base, "run:g4-calibration:repeated");

  const appLive = await page.locator("#app").getAttribute("aria-live");
  const announcer = await page.locator("#status-announcer").evaluate((element) => ({ role: element.getAttribute("role"), live: element.getAttribute("aria-live"), atomic: element.getAttribute("aria-atomic") }));
  finding("dedicated-status-announcer", "critical", appLive === null && announcer.role === "status" && announcer.live === "polite" && announcer.atomic === "true", { appLive, announcer });

  const rounds: unknown[] = [];
  for (let turn = 0; turn < 3; turn += 1) {
    const before = await page.getByTestId("turn-number").textContent();
    await page.getByTestId("generate-preview").click();
    await page.getByTestId("busy").waitFor();
    await page.waitForTimeout(70);
    const deliberation = await page.evaluate(() => ({
      turn: document.querySelector('[data-testid="turn-number"]')?.textContent,
      inert: document.querySelector('.mission')?.hasAttribute("inert"),
      ariaBusy: document.querySelector('.mission')?.getAttribute("aria-busy"),
      status: document.querySelector('#status-announcer')?.textContent,
      kind: document.querySelector('[data-testid="busy"]')?.getAttribute("data-busy-kind"),
    }));
    await page.keyboard.press("Tab");
    const focusUnderMission = await page.evaluate(() => Boolean(document.querySelector('.mission')?.contains(document.activeElement)));
    await page.getByTestId("plan-preview").waitFor();
    await page.waitForTimeout(20);
    const preview = await page.evaluate(() => ({
      status: document.querySelector('#status-announcer')?.textContent,
      intents: document.querySelectorAll('[data-testid="rescue-intent"]').length,
      sealed: document.querySelectorAll('[data-testid="sealed-enemy-plan"]').length,
      impactIds: [...document.querySelectorAll('[data-testid="plan-impact"] [data-objective-id]')].map((element) => element.getAttribute("data-objective-id")),
      actions: [...document.querySelectorAll('[data-testid="rescue-intent"]')].map((element) => ({
        actor: element.querySelector("h3")?.textContent?.trim(),
        action: [...element.children].find((child) => child.tagName === "STRONG")?.textContent?.trim(),
      })),
    }));
    await page.getByTestId("commit-turn").click();
    await page.getByTestId("busy").waitFor();
    await page.waitForTimeout(70);
    const resolving = await page.evaluate(() => ({
      turn: document.querySelector('[data-testid="turn-number"]')?.textContent,
      inert: document.querySelector('.mission')?.hasAttribute("inert"),
      status: document.querySelector('#status-announcer')?.textContent,
      kind: document.querySelector('[data-testid="busy"]')?.getAttribute("data-busy-kind"),
    }));
    await page.waitForFunction((expected) => document.querySelector('[data-testid="turn-number"]')?.textContent === String(expected), turn + 1);
    await page.getByTestId("aftermath").waitFor();
    await page.waitForTimeout(20);
    const aftermath = await page.evaluate(() => ({
      status: document.querySelector('#status-announcer')?.textContent,
      reviewIds: [...document.querySelectorAll('[data-testid="plan-review-front"]')].map((element) => element.getAttribute("data-objective-id")),
      actions: [...document.querySelectorAll('[data-testid="intent-review"]')].map((element) => ({
        actor: element.querySelector("strong")?.textContent?.trim(),
        planned: element.querySelector("small")?.textContent?.replace(/^Planned:\s*/, "").trim(),
      })),
    }));
    const exactActions = preview.actions.every((planned) => aftermath.actions.some((result) => result.actor === planned.actor && result.planned === planned.action));
    const exactFronts = [...preview.impactIds].sort().join("|") === [...aftermath.reviewIds].sort().join("|");
    rounds.push({ turn, before, deliberation, focusUnderMission, preview, resolving, aftermath, exactActions, exactFronts });
    finding(`turn-${turn + 1}-deliberation-frozen`, "critical", deliberation.turn === before && Boolean(deliberation.inert) && deliberation.ariaBusy === "true" && deliberation.kind === "deliberation" && !focusUnderMission, deliberation);
    finding(`turn-${turn + 1}-preview-legible`, "critical", preview.intents === 3 && preview.sealed === 2 && /Plan ready/.test(preview.status ?? ""), preview);
    finding(`turn-${turn + 1}-resolution-frozen`, "critical", resolving.turn === before && Boolean(resolving.inert) && resolving.kind === "resolution" && /Resolving/.test(resolving.status ?? ""), resolving);
    finding(`turn-${turn + 1}-plan-consequence-continuity`, "critical", exactActions && exactFronts && /resolved/.test(aftermath.status ?? ""), { preview, aftermath });
  }
  finding("repeated-deliberation-request-count", "major", previewRequests === 3 && commitRequests === 3, { previewRequests, commitRequests, rounds });

  const contrastSamples = await page.evaluate(() => {
    function parse(value: string): [number, number, number, number] {
      const match = value.match(/rgba?\((\d+(?:\.\d+)?)\D+(\d+(?:\.\d+)?)\D+(\d+(?:\.\d+)?)(?:\D+(\d*\.?\d+))?/);
      return match ? [Number(match[1]), Number(match[2]), Number(match[3]), match[4] === undefined ? 1 : Number(match[4])] : [0, 0, 0, 0];
    }
    function over(top: [number, number, number, number], bottom: [number, number, number, number]): [number, number, number, number] {
      const alpha = top[3] + bottom[3] * (1 - top[3]);
      if (!alpha) return [0, 0, 0, 0];
      return [
        (top[0] * top[3] + bottom[0] * bottom[3] * (1 - top[3])) / alpha,
        (top[1] * top[3] + bottom[1] * bottom[3] * (1 - top[3])) / alpha,
        (top[2] * top[3] + bottom[2] * bottom[3] * (1 - top[3])) / alpha,
        alpha,
      ];
    }
    function background(element: Element): [number, number, number, number] {
      const layers: [number, number, number, number][] = [];
      for (let node: Element | null = element; node; node = node.parentElement) layers.push(parse(getComputedStyle(node).backgroundColor));
      let composite: [number, number, number, number] = [0, 0, 0, 0];
      for (const layer of layers.reverse()) composite = over(layer, composite);
      return composite;
    }
    function luminance(color: [number, number, number, number]): number {
      const convert = (channel: number) => { const value = channel / 255; return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4; };
      return convert(color[0]) * 0.2126 + convert(color[1]) * 0.7152 + convert(color[2]) * 0.0722;
    }
    function ratio(left: [number, number, number, number], right: [number, number, number, number]): number {
      const a = luminance(left); const b = luminance(right); return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    }
    return [".actor-card small", ".eyebrow", ".audio-toggle", ".order-guidance p", ".turn span"].map((selector) => {
      const element = document.querySelector(selector);
      if (!element) return null;
      return { selector, ratio: ratio(parse(getComputedStyle(element).color), background(element)), fontSize: getComputedStyle(element).fontSize };
    }).filter(Boolean);
  });
  const minimumContrast = Math.min(...contrastSamples.map((entry: any) => entry.ratio));
  finding("key-text-contrast-proxy", "major", minimumContrast >= 4.5, { minimumContrast, contrastSamples });
  await page.close();
}

const tempDirectory = mkdtempSync(join(tmpdir(), "station-zero-g4-calibration-server-"));
const server = createGameServer({ dbPath: join(tempDirectory, "v2.sqlite3"), v3DbPath: join(tempDirectory, "v3.sqlite3") });
await new Promise<void>((resolvePromise) => server.server.listen(0, "127.0.0.1", () => resolvePromise()));
const address = server.server.address();
if (!address || typeof address === "string") throw new Error("G4 calibration server did not expose a TCP address");
const base = `http://127.0.0.1:${address.port}`;
const browser = await chromium.launch({ headless: true, executablePath: chromiumExecutable() });
try {
  const silhouettes = silhouetteMetrics();
  finding("specialist-silhouette-discriminability", "major", silhouettes.minimumDifference >= 40, silhouettes);
  await geometryAndMedia(browser, base);
  await repeatedTurnCalibration(browser, base);
} finally {
  await browser.close();
  await server.close();
  rmSync(tempDirectory, { recursive: true, force: true });
}

const summary = {
  total: findings.length,
  passed: findings.filter((entry) => entry.passed).length,
  failed: findings.filter((entry) => !entry.passed).length,
  criticalFailed: findings.filter((entry) => !entry.passed && entry.severity === "critical").length,
  majorFailed: findings.filter((entry) => !entry.passed && entry.severity === "major").length,
};
const report = { schemaVersion: 1, kind: "ordivon.game.station-zero-v3-g4-calibration", summary, findings };
const outputDirectory = resolve(process.env.ORDIVON_EVAL_ARTIFACT_DIR ?? "artifacts/evaluations");
mkdirSync(outputDirectory, { recursive: true });
const outputPath = resolve(outputDirectory, `station-zero-v3-g4-calibration-${Date.now()}.json`);
writeFileSync(outputPath, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify({ ...report, outputPath }, null, 2));
if (summary.failed > 0) process.exitCode = 1;
