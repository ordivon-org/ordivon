import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { sha256 } from "../src/digest.ts";
import type { CompiledAgentContext } from "../src/host/context.ts";
import { AgentHost } from "../src/host/engine.ts";
import { scoreMission } from "../src/scoring.ts";
import { CodexCliProvider } from "../src/providers/codex-cli.ts";
import { HermesCliProvider } from "../src/providers/hermes-cli.ts";
import type { OperationDecision, OperationProvider } from "../src/providers/types.ts";
import { GameStore } from "../src/storage.ts";

type Mode = "codex" | "hermes" | "codex-hermes" | "hermes-codex";

function argument(name: string): string | null {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] ?? null : null;
}

function commandVersion(executable: string): string | null {
  try { return execFileSync(executable, ["--version"], { encoding: "utf8" }).trim(); }
  catch { return null; }
}

class EvaluatedProvider implements OperationProvider {
  readonly providerId: string;
  readonly mode: Mode;
  readonly codex = new CodexCliProvider({ timeoutMs: 240_000 });
  readonly hermes = new HermesCliProvider({ timeoutMs: 240_000 });
  readonly calls: Array<Record<string, unknown>> = [];
  private last: Record<string, unknown> | null = null;

  constructor(mode: Mode) {
    this.mode = mode;
    this.providerId = `m2-live:${mode}`;
  }

  private selected(context: CompiledAgentContext): OperationProvider {
    if (this.mode === "codex") return this.codex;
    if (this.mode === "hermes") return this.hermes;
    const completed = context.payload.task.completedAttemptIds.length;
    if (this.mode === "codex-hermes") return completed < 5 ? this.codex : this.hermes;
    return completed < 5 ? this.hermes : this.codex;
  }

  evidenceMetadata(): Record<string, unknown> | null {
    return this.last ? structuredClone(this.last) : null;
  }

  async decide(context: CompiledAgentContext): Promise<OperationDecision> {
    const provider = this.selected(context);
    const index = this.calls.length;
    const startedAt = performance.now();
    console.error(`[m2-live] call=${index + 1} provider=${provider.providerId} taskRevision=${context.payload.task.revision} worldRevision=${context.payload.run.worldRevision}`);
    try {
      const decision = await provider.decide(context);
      const evidence = provider.evidenceMetadata?.() ?? null;
      const receipt = {
        call: index + 1,
        status: "succeeded",
        providerId: provider.providerId,
        elapsedMs: Number((performance.now() - startedAt).toFixed(3)),
        contextId: context.contextId,
        contextBytes: context.byteLength,
        selectedOperationCandidateId: decision.selectedOperationCandidateId,
        riskLevel: decision.riskLevel,
        confidence: decision.confidence,
        rationale: decision.rationale,
        evidence,
      };
      this.calls.push(receipt);
      this.last = receipt;
      console.error(`[m2-live] result=succeeded operation=${decision.selectedOperationCandidateId}`);
      return decision;
    } catch (error) {
      const receipt = {
        call: index + 1,
        status: "failed",
        providerId: provider.providerId,
        elapsedMs: Number((performance.now() - startedAt).toFixed(3)),
        contextId: context.contextId,
        contextBytes: context.byteLength,
        error: error instanceof Error ? error.message : String(error),
        code: error && typeof error === "object" && "code" in error ? String(error.code) : null,
        evidence: provider.evidenceMetadata?.() ?? null,
      };
      this.calls.push(receipt);
      this.last = receipt;
      console.error(`[m2-live] result=failed error=${receipt.error}`);
      throw error;
    }
  }
}

const mode = argument("--mode") as Mode | null;
const output = argument("--output");
if (!mode || !["codex", "hermes", "codex-hermes", "hermes-codex"].includes(mode)) {
  throw new Error("--mode must be codex, hermes, codex-hermes, or hermes-codex");
}
if (!output) throw new Error("--output is required");

const directory = mkdtempSync(join(tmpdir(), `ordivon-game-m2-live-${mode}-`));
const startedAt = performance.now();
try {
  const game = new GameStore(join(directory, "world.sqlite3"));
  const provider = new EvaluatedProvider(mode);
  const agent = new AgentHost(game, provider);
  const run = await agent.run(game.activeRunId, 256);
  const state = game.loadState();
  const projection = agent.projection();
  agent.host.verifyJournal(game.activeRunId);
  game.verifyStream(game.activeRunId);
  const replay = game.verifyReplay(game.activeRunId);
  const contextArtifacts = projection.attempts
    .filter((attempt) => attempt.contextDigest)
    .map((attempt) => agent.host.getArtifact(attempt.contextDigest!).byteLength);
  const costs = provider.calls
    .map((call) => call.evidence)
    .filter((value): value is Record<string, unknown> => Boolean(value) && typeof value === "object")
    .map((value) => Number(value.estimatedCostUsd ?? 0));
  const report = {
    schemaVersion: 1,
    kind: "ordivon.game.m2-live-run",
    mode,
    sourceRevision: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(),
    createdAt: new Date().toISOString(),
    environment: {
      node: process.version,
      platform: `${process.platform}/${process.arch}`,
      codexVersion: commandVersion("/usr/bin/codex"),
      hermesVersion: commandVersion("/root/.local/bin/hermes"),
    },
    originalTranscriptLoaded: false,
    humanCorrectionCount: 0,
    elapsedMs: Number((performance.now() - startedAt).toFixed(3)),
    providerCalls: provider.calls,
    providerCallCount: provider.calls.length,
    hostStepCount: run.steps.length,
    attempts: projection.attempts.map((attempt) => ({
      attemptId: attempt.attemptId,
      status: attempt.status,
      providerId: attempt.providerId,
      operationCandidateId: attempt.operationCandidateId,
      skillStepCount: attempt.skillStepCount,
      blocker: attempt.blocker,
    })),
    goalStatus: projection.goal.status,
    taskPhase: projection.task.phase,
    blockers: projection.task.blockers,
    world: {
      missionStatus: state.mission.status,
      missionReason: state.mission.reason,
      turn: state.turn,
      revision: state.revision,
      digest: sha256(state),
      score: scoreMission(state),
      batteryCharge: state.resources.batteryCharge,
      oxygen: state.resources.oxygen,
      reactorHeat: state.resources.reactorHeat,
      engineerHealth: state.agents["engineer-01"]?.health ?? null,
      crewHealth: state.crew["crew-01"]?.health ?? null,
    },
    evidence: {
      worldEventCount: game.eventCount(),
      effectCount: agent.authority.listEffects(game.activeRunId).length,
      dispatchCount: agent.authority.listDispatches(game.activeRunId).length,
      observationCount: agent.authority.listObservations(game.activeRunId).length,
      hostJournalCount: agent.host.listJournal(game.activeRunId).length,
      hostJournalTerminalDigest: agent.host.listJournal(game.activeRunId).at(-1)?.recordDigest ?? null,
      replayVerified: replay.verified,
      replayDigest: replay.digest,
      contextBytes: contextArtifacts,
      maximumContextBytes: contextArtifacts.length ? Math.max(...contextArtifacts) : 0,
      estimatedCostUsd: costs.reduce((total, cost) => total + cost, 0),
    },
  };
  writeFileSync(output, JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify(report, null, 2));
  game.close();
} finally {
  rmSync(directory, { recursive: true, force: true });
}
