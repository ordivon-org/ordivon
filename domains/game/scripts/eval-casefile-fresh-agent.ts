import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { chromium, type Page } from "playwright";
import { resolveChromiumExecutable } from "./browser-equipment.ts";
import { createResearchPreviewServer } from "../experiments/research-preview/server.ts";
import { loadExternalJsonModel, type ExternalJsonModelCallEvidence } from "./external-json-model.ts";

interface Decision { actionIndex: number; interpretation: string; expectation: string; confidence: number }
interface Reflection { understanding: string; confusion: string; evidenceUsed: string; replayDesire: number; replayReason: string }

const model = await loadExternalJsonModel();

let callCount = 0;
let promptTokens = 0;
let completionTokens = 0;
const latencies: number[] = [];
const callEvidence: ExternalJsonModelCallEvidence[] = [];

async function callJson(system: string, payload: unknown): Promise<Record<string, unknown>> {
  const result = await model.json(system, payload);
  if (!result.value || typeof result.value !== "object" || Array.isArray(result.value)) throw new TypeError("external model output must be one object");
  callCount += 1;
  if (result.evidence) {
    callEvidence.push({ ...result.evidence });
    promptTokens += Number(result.evidence.inputTokens ?? 0);
    completionTokens += Number(result.evidence.outputTokens ?? 0);
    if (typeof result.evidence.latencyMs === "number") latencies.push(result.evidence.latencyMs);
  }
  return result.value;
}

const PLAYER_SYSTEM = `You are a fresh player in a short detective game you have never seen before.
You receive only the current player-visible page state and numbered legal actions.
Goal: investigate efficiently and make the best-supported accusation before investigation moves run out.
Do not assume hidden truth, developer intent, or undocumented rules. Learn from testimony, traces, contradictions, and the remaining move budget.
Return JSON only with exactly actionIndex, interpretation, expectation, confidence. actionIndex must be a legal index; confidence is 0..1. Keep text concise and do not reveal chain-of-thought.`;

const REFLECTION_SYSTEM = `You just finished one short detective-game case from player-visible information only.
Report your own fresh-player understanding. Do not infer hidden implementation or developer intent. Do not reveal chain-of-thought.
Return JSON only with exactly understanding, confusion, evidenceUsed, replayDesire, replayReason. replayDesire is 0..1; strings under 240 characters.`;

function text(value: unknown, label: string): string {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} must be non-empty`);
  return value.trim().slice(0, 240);
}

async function visibleState(page: Page): Promise<string> {
  return await page.evaluate(() => {
    const shell = document.querySelector(".shell");
    if (!shell) throw new Error("missing Casefile shell");
    const clone = shell.cloneNode(true) as HTMLElement;
    clone.querySelectorAll("button").forEach((button) => button.remove());
    return clone.innerText.replace(/\s+/g, " ").trim().slice(0, 12_000);
  });
}

async function actions(page: Page): Promise<string[]> {
  return await page.locator("[data-case-action]").evaluateAll((buttons) => buttons.map((button) => (button.textContent ?? "").replace(/\s+/g, " ").trim()));
}

async function choose(page: Page, scenarioId: string, step: number): Promise<Decision> {
  const state = await visibleState(page);
  const legal = await actions(page);
  assert.ok(legal.length > 0, `${scenarioId}: no legal actions before terminal`);
  const output = await callJson(PLAYER_SYSTEM, { scenarioId, step, visibleState: state, legalActions: legal.map((label, actionIndex) => ({ actionIndex, label })) });
  if (!Number.isSafeInteger(output.actionIndex) || (output.actionIndex as number) < 0 || (output.actionIndex as number) >= legal.length) throw new TypeError("illegal model actionIndex");
  if (typeof output.confidence !== "number" || output.confidence < 0 || output.confidence > 1) throw new TypeError("invalid model confidence");
  return { actionIndex: output.actionIndex as number, interpretation: text(output.interpretation, "interpretation"), expectation: text(output.expectation, "expectation"), confidence: output.confidence };
}

async function reflect(transcript: unknown, terminal: string): Promise<Reflection> {
  const output = await callJson(REFLECTION_SYSTEM, { transcript, terminal });
  if (typeof output.replayDesire !== "number" || output.replayDesire < 0 || output.replayDesire > 1) throw new TypeError("invalid replayDesire");
  return { understanding: text(output.understanding, "understanding"), confusion: text(output.confusion, "confusion"), evidenceUsed: text(output.evidenceUsed, "evidenceUsed"), replayDesire: output.replayDesire, replayReason: text(output.replayReason, "replayReason") };
}

process.env.TMPDIR = process.env.ORDIVON_BROWSER_TMPDIR ?? "/tmp";
const directory = mkdtempSync(join(tmpdir(), "casefile-fresh-agent-"));
const game = createResearchPreviewServer({ researchSurfaces: true, dbPath: join(directory, "v2.sqlite3"), v3DbPath: join(directory, "v3.sqlite3"), casefileDbPath: join(directory, "casefile.sqlite3") });
await new Promise<void>((resolve) => game.server.listen(0, "127.0.0.1", resolve));
const address = game.server.address();
if (!address || typeof address === "string") throw new Error("server has no TCP address");
const base = `http://127.0.0.1:${address.port}`;
const executablePath = resolveChromiumExecutable(chromium.executablePath());
if (!executablePath) throw new Error("No Chromium executable available");
const browser = await chromium.launch({ headless: true, executablePath });

const results: unknown[] = [];
try {
  for (const scenarioId of ["relay-sabotage", "missing-med-cache", "false-pressure-alarm"]) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 960 } });
    try {
      await page.goto(`${base}/casefile`, { waitUntil: "networkidle" });
      await page.locator(`[data-start="${scenarioId}"]`).click();
      await page.locator("[data-case-revision=\"0\"]").waitFor();
      const transcript: Array<{ step: number; state: string; legal: string[]; chosen: string; interpretation: string; expectation: string; confidence: number }> = [];
      for (let step = 1; step <= 9; step += 1) {
        if (await page.locator("[data-testid=\"casefile-terminal\"]").count()) break;
        const state = await visibleState(page);
        const legal = await actions(page);
        const decision = await choose(page, scenarioId, step);
        const chosen = legal[decision.actionIndex]!;
        transcript.push({ step, state, legal, chosen, interpretation: decision.interpretation, expectation: decision.expectation, confidence: decision.confidence });
        const currentRevision = Number(await page.locator("[data-case-revision]").getAttribute("data-case-revision"));
        await page.locator("[data-case-action]").nth(decision.actionIndex).click();
        await page.waitForFunction((revision) => {
          const current = document.querySelector("[data-case-revision]")?.getAttribute("data-case-revision");
          return current !== null && Number(current) > Number(revision);
        }, currentRevision);
      }
      const terminalLocator = page.locator("[data-testid=\"casefile-terminal\"]");
      const terminal = await terminalLocator.count() ? (await terminalLocator.textContent() ?? "").replace(/\s+/g, " ").trim() : "No terminal outcome within nine decisions.";
      const reflection = await reflect(transcript.map(({ step, chosen, interpretation, expectation }) => ({ step, chosen, interpretation, expectation })), terminal);
      results.push({ scenarioId, terminal, solved: /Accusation confirmed/.test(terminal), steps: transcript.map(({ step, chosen, confidence }) => ({ step, chosen, confidence })), reflection });
    } finally { await page.close(); }
  }

  console.log(JSON.stringify({
    kind: "ordivon.game.casefile-g6-fresh-agent-play",
    evidenceBoundary: "fresh-agent independent comprehension/play evidence; not human fun, attachment, retention, or market evidence",
    provider: { providerId: model.providerId },
    results,
    calls: { count: callCount, promptTokens, completionTokens, latencyMs: latencies, evidence: callEvidence },
  }, null, 2));
} finally {
  await browser.close();
  await game.close();
  rmSync(directory, { recursive: true, force: true });
}
