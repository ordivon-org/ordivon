import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { chromium, type Page } from "playwright";
import { resolveChromiumExecutable } from "../../../tools/browser-equipment.ts";
import { createResearchPreviewServer } from "../../research-preview/server.ts";
import { loadExternalJsonModel } from "../../../tools/external-json-model.ts";

interface PlayerDecision {
  actionIndex: number;
  interpretation: string;
  expectation: string;
  confidence: number;
}

interface ExitReflection {
  understanding: string;
  confusion: string;
  replayDesire: number;
  replayReason: string;
  emotionalSignal: string;
}

interface CallEvidence {
  concept: string;
  treatment: "autonomy" | "baseline";
  stage: "decision" | "reflection";
  step: number;
  routeId: string | null;
  modelId: string | null;
  latencyMs: number;
  promptTokens: number;
  completionTokens: number;
}

interface SessionEvidence {
  concept: string;
  treatment: "autonomy" | "baseline";
  steps: Array<{
    step: number;
    visibleState: string;
    actions: string[];
    decision: PlayerDecision;
  }>;
  terminal: string;
  reflection: ExitReflection;
}

const PLAYER_SYSTEM = `You are a fresh player testing an unfamiliar small game prototype.
You receive ONLY player-visible state and a numbered list of currently legal actions.
Do not assume hidden rules, developer intent, architecture, or secret state.
Try to achieve the visible game goal while learning from consequences.
Choose exactly one legal action index.
Do not reveal chain-of-thought. Give only short player-facing interpretation and expectation.
Return JSON only with exactly: actionIndex, interpretation, expectation, confidence.
confidence must be 0..1.`;

const REFLECTION_SYSTEM = `You just played one unfamiliar small game session from player-visible information only.
Assess your own experience as a fresh player. Do not infer hidden implementation or developer intent.
Do not reveal chain-of-thought.
Return JSON only with exactly: understanding, confusion, replayDesire, replayReason, emotionalSignal.
replayDesire must be 0..1. Keep each string under 220 characters.`;

const model = await loadExternalJsonModel();

const calls: CallEvidence[] = [];

function parseObject(text: string): Record<string, unknown> {
  const value = JSON.parse(text);
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new TypeError("model output must be one object");
  return value as Record<string, unknown>;
}

async function modelJson(
  concept: string,
  treatment: "autonomy" | "baseline",
  stage: "decision" | "reflection",
  step: number,
  system: string,
  payload: unknown,
): Promise<Record<string, unknown>> {
  const result = await model.json(system, payload);
  if (result.evidence) {
    calls.push({
      concept,
      treatment,
      stage,
      step,
      routeId: result.evidence.routeId ?? null,
      modelId: result.evidence.modelId ?? null,
      latencyMs: Number(result.evidence.latencyMs ?? 0),
      promptTokens: Number(result.evidence.inputTokens ?? 0),
      completionTokens: Number(result.evidence.outputTokens ?? 0),
    });
  }
  return result.value;
}

function shortText(value: unknown, label: string): string {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} must be non-empty text`);
  return value.trim().slice(0, 220);
}

async function decide(
  concept: string,
  treatment: "autonomy" | "baseline",
  step: number,
  visibleState: string,
  actions: string[],
): Promise<PlayerDecision> {
  const output = await modelJson(concept, treatment, "decision", step, PLAYER_SYSTEM, {
    visibleState,
    legalActions: actions.map((label, actionIndex) => ({ actionIndex, label })),
  });
  const actionIndex = output.actionIndex;
  if (!Number.isSafeInteger(actionIndex) || (actionIndex as number) < 0 || (actionIndex as number) >= actions.length) {
    throw new TypeError(`model selected illegal actionIndex ${String(actionIndex)} for ${actions.length} actions`);
  }
  const confidence = output.confidence;
  if (typeof confidence !== "number" || !Number.isFinite(confidence) || confidence < 0 || confidence > 1) {
    throw new TypeError("confidence must be 0..1");
  }
  return {
    actionIndex: actionIndex as number,
    interpretation: shortText(output.interpretation, "interpretation"),
    expectation: shortText(output.expectation, "expectation"),
    confidence,
  };
}

async function reflect(
  concept: string,
  treatment: "autonomy" | "baseline",
  step: number,
  transcript: SessionEvidence["steps"],
  terminal: string,
): Promise<ExitReflection> {
  const output = await modelJson(concept, treatment, "reflection", step, REFLECTION_SYSTEM, {
    session: transcript.map((entry) => ({
      step: entry.step,
      visibleState: entry.visibleState,
      chosenAction: entry.actions[entry.decision.actionIndex],
      expectation: entry.decision.expectation,
    })),
    terminal,
  });
  const replayDesire = output.replayDesire;
  if (typeof replayDesire !== "number" || !Number.isFinite(replayDesire) || replayDesire < 0 || replayDesire > 1) {
    throw new TypeError("replayDesire must be 0..1");
  }
  return {
    understanding: shortText(output.understanding, "understanding"),
    confusion: shortText(output.confusion, "confusion"),
    replayDesire,
    replayReason: shortText(output.replayReason, "replayReason"),
    emotionalSignal: shortText(output.emotionalSignal, "emotionalSignal"),
  };
}

async function visibleSnapshot(page: Page, concept: string): Promise<string> {
  return await page.evaluate((conceptId) => {
    const left = document.querySelector("section.game-grid > .panel:first-child");
    const log = document.querySelector("section.game-grid > .panel:nth-child(2) .log");
    if (!left) throw new Error("missing game panel");
    const clone = left.cloneNode(true) as HTMLElement;
    clone.querySelectorAll("button,.prototype-note,.eyebrow").forEach((node) => node.remove());
    // Treatment labels are evaluation controls, not intended player knowledge.
    clone.querySelectorAll(".metric").forEach((metric) => {
      const label = metric.querySelector("span")?.textContent?.trim().toLowerCase();
      if (label === "mode" || label === "hunter") metric.remove();
    });
    if (conceptId === "last-light") {
      clone.querySelectorAll("p").forEach((paragraph) => {
        if (paragraph.textContent?.includes("autonomy mode")) paragraph.textContent = paragraph.textContent.split("You can ask")[0]?.trim() ?? "";
      });
    }
    const normalize = (text: string) => text.replace(/\s+/g, " ").trim();
    const leftText = normalize(clone.innerText);
    const logText = normalize((log as HTMLElement | null)?.innerText ?? "");
    return `${leftText}\nRECENT CONSEQUENCES: ${logText}`.slice(0, 8_000);
  }, concept);
}

async function legalActions(page: Page): Promise<string[]> {
  return await page.locator("section.game-grid > .panel:first-child button:not([disabled])").evaluateAll((buttons) =>
    buttons.map((button) => (button.textContent ?? "").replace(/\s+/g, " ").trim()).filter(Boolean),
  );
}

async function terminalText(page: Page): Promise<string | null> {
  const finish = page.locator(".finish");
  if (await finish.count() === 0) return null;
  return (await finish.textContent() ?? "").replace(/\s+/g, " ").replace(/New seed/g, "").trim();
}

async function playSession(
  page: Page,
  concept: string,
  treatment: "autonomy" | "baseline",
): Promise<SessionEvidence> {
  await page.goto(`${base}/lab`, { waitUntil: "networkidle" });
  if (concept !== "casefile") await page.locator(`[data-concept="${concept}"]`).click();
  if (treatment === "baseline") await page.locator('[data-mode="0"]').click();
  else await page.locator('[data-mode="1"]').click();

  const steps: SessionEvidence["steps"] = [];
  for (let step = 1; step <= 10; step += 1) {
    const terminal = await terminalText(page);
    if (terminal) {
      const reflection = await reflect(concept, treatment, step, steps, terminal);
      return { concept, treatment, steps, terminal, reflection };
    }
    const state = await visibleSnapshot(page, concept);
    const actions = await legalActions(page);
    assert.ok(actions.length > 0, `${concept}/${treatment} has no legal action before terminal`);
    const decision = await decide(concept, treatment, step, state, actions);
    steps.push({ step, visibleState: state, actions, decision });
    await page.locator("section.game-grid > .panel:first-child button:not([disabled])").nth(decision.actionIndex).click();
  }
  const terminal = await terminalText(page) ?? "Session exceeded the 10-step evaluation budget without a terminal outcome.";
  const reflection = await reflect(concept, treatment, 11, steps, terminal);
  return { concept, treatment, steps, terminal, reflection };
}

if (process.env.ORDIVON_BROWSER_TMPDIR) process.env.TMPDIR = process.env.ORDIVON_BROWSER_TMPDIR;
const directory = mkdtempSync(join(tmpdir(), "ordivon-game-core-fresh-agent-"));
const game = createResearchPreviewServer({ researchSurfaces: true, dbPath: join(directory, "v2.sqlite3"), v3DbPath: join(directory, "v3.sqlite3") });
await new Promise<void>((resolve) => game.server.listen(0, "127.0.0.1", resolve));
const address = game.server.address();
if (!address || typeof address === "string") throw new Error("server has no TCP address");
const base = `http://127.0.0.1:${address.port}`;
const executablePath = resolveChromiumExecutable(chromium.executablePath());
if (!executablePath) throw new Error("No Chromium executable available");
const browser = await chromium.launch({ headless: true, executablePath });

const sessions: SessionEvidence[] = [];
try {
  const requestedConcepts = (process.env.GAME_CORE_CONCEPTS ?? "casefile,last-light,echo-hunt").split(",").map((value) => value.trim()).filter(Boolean);
  const requestedTreatments = (process.env.GAME_CORE_TREATMENTS ?? "autonomy,baseline").split(",").map((value) => value.trim()).filter(Boolean);
  for (const concept of ["casefile", "last-light", "echo-hunt"] as const) {
    if (!requestedConcepts.includes(concept)) continue;
    for (const treatment of ["autonomy", "baseline"] as const) {
      if (!requestedTreatments.includes(treatment)) continue;
      const page = await browser.newPage({ viewport: { width: 1280, height: 960 } });
      try {
        sessions.push(await playSession(page, concept, treatment));
      } finally {
        await page.close();
      }
    }
  }

  const summary = sessions.map((session) => ({
    concept: session.concept,
    treatment: session.treatment,
    stepCount: session.steps.length,
    terminal: session.terminal,
    replayDesire: session.reflection.replayDesire,
    understanding: session.reflection.understanding,
    confusion: session.reflection.confusion,
    replayReason: session.reflection.replayReason,
    emotionalSignal: session.reflection.emotionalSignal,
    decisions: session.steps.map((step) => ({
      step: step.step,
      chosenAction: step.actions[step.decision.actionIndex],
      interpretation: step.decision.interpretation,
      expectation: step.decision.expectation,
      confidence: step.decision.confidence,
    })),
  }));

  console.log(JSON.stringify({
    kind: "ordivon.game.core-research-fresh-agent-blind-play",
    evidenceBoundary: "fresh-agent behavioral/self-report evidence; not human fun, retention, or market evidence",
    provider: { providerId: model.providerId },
    sessions: summary,
    calls: {
      count: calls.length,
      promptTokens: calls.reduce((sum, call) => sum + call.promptTokens, 0),
      completionTokens: calls.reduce((sum, call) => sum + call.completionTokens, 0),
      latencyMs: calls.map((call) => call.latencyMs),
      routesUsed: [...new Set(calls.map((call) => call.routeId).filter((route) => route !== null))].sort(),
    },
  }, null, 2));
} finally {
  await browser.close();
  await game.close();
  rmSync(directory, { recursive: true, force: true });
}
