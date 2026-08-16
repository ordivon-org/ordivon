import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { chromium, type Page } from "playwright";
import { resolveChromiumExecutable } from "./browser-equipment.ts";
import { createGameServer } from "../src/server.ts";
import {
  StationZeroV3DeepSeekCredentialPool,
  stationZeroV3DeepSeekCredentialSources,
} from "../src/station-zero-v3/deepseek-credentials.ts";

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
  credentialId: string;
  model: string;
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

const pool = new StationZeroV3DeepSeekCredentialPool({
  sources: stationZeroV3DeepSeekCredentialSources(
    process.env.ORDIVON_GAME_V3_DEEPSEEK_SOURCES ?? process.env.ORDIVON_GAME_V3_DEEPSEEK_SECRETS,
  ),
  defaultMaximumConcurrency: 1,
  reloadIntervalMs: 0,
  cooldownBaseMs: 250,
  cooldownMaximumMs: 2_000,
});

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
  const excluded = new Set<string>();
  let lastError: unknown = null;
  for (let attempt = 0; attempt < Math.min(3, pool.usableSize); attempt += 1) {
    const credential = await pool.select(excluded);
    excluded.add(credential.fingerprint);
    try {
      return await credential.run(async () => {
        const started = performance.now();
        const response = await fetch(`${credential.baseUrl}/chat/completions`, {
          method: "POST",
          headers: {
            authorization: `Bearer ${credential.apiKey}`,
            "content-type": "application/json",
          },
          body: JSON.stringify({
            model: credential.model,
            messages: [
              { role: "system", content: system },
              { role: "user", content: JSON.stringify(payload) },
            ],
            thinking: { type: "disabled" },
            temperature: 0.1,
            max_tokens: 512,
            response_format: { type: "json_object" },
            stream: false,
          }),
          signal: AbortSignal.timeout(20_000),
        });
        const body = await response.text();
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${body.slice(0, 200)}`);
        const envelope = parseObject(body);
        const choices = Array.isArray(envelope.choices) ? envelope.choices : [];
        const first = choices[0] as Record<string, unknown> | undefined;
        const message = first?.message as Record<string, unknown> | undefined;
        const content = message?.content;
        if (typeof content !== "string" || !content.trim()) throw new TypeError("model returned no content");
        const usage = envelope.usage as Record<string, unknown> | undefined;
        calls.push({
          concept,
          treatment,
          stage,
          step,
          credentialId: credential.credentialId,
          model: credential.model,
          latencyMs: Math.round(performance.now() - started),
          promptTokens: typeof usage?.prompt_tokens === "number" ? usage.prompt_tokens : 0,
          completionTokens: typeof usage?.completion_tokens === "number" ? usage.completion_tokens : 0,
        });
        pool.reportSuccess(credential, Math.round(performance.now() - started));
        return parseObject(content);
      });
    } catch (error) {
      lastError = error;
      pool.reportFailure(credential, "transport");
    }
  }
  throw lastError instanceof Error ? lastError : new Error("fresh-player model call failed");
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

process.env.TMPDIR = process.env.ORDIVON_BROWSER_TMPDIR ?? "/tmp";
const directory = mkdtempSync(join(tmpdir(), "ordivon-game-core-fresh-agent-"));
const game = createGameServer({ dbPath: join(directory, "v2.sqlite3"), v3DbPath: join(directory, "v3.sqlite3") });
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
    provider: pool.identity(),
    sessions: summary,
    calls: {
      count: calls.length,
      promptTokens: calls.reduce((sum, call) => sum + call.promptTokens, 0),
      completionTokens: calls.reduce((sum, call) => sum + call.completionTokens, 0),
      latencyMs: calls.map((call) => call.latencyMs),
      credentialsUsed: [...new Set(calls.map((call) => call.credentialId))].sort(),
    },
  }, null, 2));
} finally {
  await browser.close();
  await game.close();
  rmSync(directory, { recursive: true, force: true });
}
