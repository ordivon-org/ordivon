import { execFileSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import { existsSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

import { sha256 } from "../src/digest.ts";
import {
  captureLiveEvaluationReceipt,
  LiveEvaluationInterruption,
  readLiveEvaluationReceipt,
  writeLiveEvaluationReceipt,
  type LiveEvaluationSpec,
  type LiveEvaluationTermination,
} from "../src/evaluation/live-receipt.ts";
import type { CompiledAgentContext } from "../src/host/context.ts";
import { AgentHost } from "../src/host/engine.ts";
import { CodexCliProvider } from "../src/providers/codex-cli.ts";
import { HermesCliProvider } from "../src/providers/hermes-cli.ts";
import { ProcessAbortError } from "../src/providers/process.ts";
import type { OperationDecision, OperationProvider } from "../src/providers/types.ts";
import { scoreMission } from "../src/scoring.ts";
import { GameStore } from "../src/storage.ts";

type Mode = "codex" | "hermes" | "codex-hermes" | "hermes-codex";

function argument(name: string): string | null {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] ?? null : null;
}

function flag(name: string): boolean {
  return process.argv.includes(name);
}

function positiveInteger(name: string, fallback: number | null): number | null {
  const value = argument(name);
  if (value === null) return fallback;
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < 1) throw new Error(`${name} must be a positive integer`);
  return parsed;
}

function commandVersion(executable: string): string | null {
  try { return execFileSync(executable, ["--version"], { encoding: "utf8" }).trim(); }
  catch { return null; }
}

class EvaluatedProvider implements OperationProvider {
  readonly providerId: string;
  readonly mode: Mode;
  readonly codex: CodexCliProvider;
  readonly hermes: HermesCliProvider;
  readonly calls: Array<Record<string, unknown>> = [];
  private last: Record<string, unknown> | null = null;

  constructor(mode: Mode, signal: AbortSignal) {
    this.mode = mode;
    this.providerId = `m2-live:${mode}`;
    this.codex = new CodexCliProvider({ timeoutMs: 240_000, signal });
    this.hermes = new HermesCliProvider({ timeoutMs: 240_000, signal });
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
      const interruption = error instanceof ProcessAbortError && error.reason instanceof LiveEvaluationInterruption
        ? error.reason
        : null;
      const receipt = {
        call: index + 1,
        status: interruption ? "interrupted" : "failed",
        providerId: provider.providerId,
        elapsedMs: Number((performance.now() - startedAt).toFixed(3)),
        contextId: context.contextId,
        contextBytes: context.byteLength,
        error: error instanceof Error ? error.message : String(error),
        code: interruption?.kind ??
          (error && typeof error === "object" && "code" in error ? String(error.code) : null),
        evidence: provider.evidenceMetadata?.() ?? null,
      };
      this.calls.push(receipt);
      this.last = receipt;
      console.error(`[m2-live] result=${receipt.status} error=${receipt.error}`);
      throw error;
    }
  }
}

function terminationFromError(
  error: unknown,
  requested: LiveEvaluationInterruption | null,
): LiveEvaluationTermination {
  const interruption = requested ??
    (error instanceof ProcessAbortError && error.reason instanceof LiveEvaluationInterruption ? error.reason : null);
  if (interruption) {
    return {
      kind: interruption.kind,
      reason: interruption.message,
      signal: interruption.signal,
      errorName: interruption.name,
      errorCode: interruption.kind,
    };
  }
  const code = error && typeof error === "object" && "code" in error ? String(error.code) : null;
  return {
    kind: code?.startsWith("provider_") ? "provider_failure" : "evaluation_failure",
    reason: error instanceof Error ? error.message : String(error),
    signal: null,
    errorName: error instanceof Error ? error.name : null,
    errorCode: code,
  };
}

async function main(): Promise<void> {
  const mode = argument("--mode") as Mode | null;
  const outputValue = argument("--output");
  if (!mode || !["codex", "hermes", "codex-hermes", "hermes-codex"].includes(mode)) {
    throw new Error("--mode must be codex, hermes, codex-hermes, or hermes-codex");
  }
  if (!outputValue) throw new Error("--output is required");
  const output = resolve(outputValue);
  const receiptOutput = resolve(argument("--receipt-output") ?? `${output}.receipt.json`);
  const partialOutput = resolve(argument("--partial-output") ?? `${output}.partial.json`);
  const maximumSteps = positiveInteger("--maximum-steps", 256)!;
  const wallClockLimitMs = positiveInteger("--wall-clock-ms", null);
  const resume = flag("--resume");
  const retainDatabase = flag("--retain-database");
  const databaseValue = argument("--database");
  const recoveryPath = argument("--recovery-of");
  if (resume && !databaseValue) throw new Error("--resume requires --database");
  if (resume && !recoveryPath) throw new Error("--resume requires --recovery-of");

  const previous = recoveryPath ? readLiveEvaluationReceipt(resolve(recoveryPath)) : null;
  const generatedDirectory = databaseValue ? null : mkdtempSync(join(tmpdir(), `ordivon-game-m2-live-${mode}-`));
  const databasePath = resolve(databaseValue ?? join(generatedDirectory!, "world.sqlite3"));
  if (resume && !existsSync(databasePath)) throw new Error(`resume database does not exist: ${databasePath}`);
  if (previous && resolve(previous.receipt.evaluation.databasePath) !== databasePath) {
    throw new Error("recovery receipt is bound to another database path");
  }
  const sourceRevision = execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim();
  const startedAt = new Date().toISOString();
  const evaluationId = `evaluation:m2:${randomUUID()}`;
  const controller = new AbortController();
  let requestedInterruption: LiveEvaluationInterruption | null = null;
  let game: GameStore | null = null;
  let agent: AgentHost | null = null;
  let provider: EvaluatedProvider | null = null;
  let hostStepCount = 0;
  let preserveGeneratedDatabase = retainDatabase;

  const interrupt = (interruption: LiveEvaluationInterruption): void => {
    if (controller.signal.aborted) return;
    requestedInterruption = interruption;
    preserveGeneratedDatabase = true;
    controller.abort(interruption);
  };
  const onSigint = (): void => interrupt(new LiveEvaluationInterruption("external_signal", "received SIGINT", "SIGINT"));
  const onSigterm = (): void => interrupt(new LiveEvaluationInterruption("external_signal", "received SIGTERM", "SIGTERM"));
  process.once("SIGINT", onSigint);
  process.once("SIGTERM", onSigterm);
  const wallTimer = wallClockLimitMs === null ? null : setTimeout(() => {
    interrupt(new LiveEvaluationInterruption(
      "evaluation_timeout",
      `evaluation exceeded ${wallClockLimitMs} ms`,
    ));
  }, wallClockLimitMs);

  const spec = (databaseRetained: boolean): LiveEvaluationSpec => ({
    evaluationId,
    mode,
    sourceRevision,
    startedAt,
    wallClockLimitMs,
    maximumSteps,
    databasePath,
    databaseRetained,
    recoveryOfReceiptDigest: previous?.receiptDigest ?? null,
  });

  try {
    const activeRunId = previous?.receipt.run.runId;
    game = new GameStore(databasePath, activeRunId ? { activeRunId } : {});
    provider = new EvaluatedProvider(mode, controller.signal);
    agent = new AgentHost(game, provider);
    agent.initialize(game.activeRunId);
    writeLiveEvaluationReceipt(receiptOutput, captureLiveEvaluationReceipt({
      phase: "started",
      spec: spec(Boolean(databaseValue) || retainDatabase || wallClockLimitMs !== null),
      game, agent, providerCalls: provider.calls, hostStepCount,
    }));

    const run = await agent.run(game.activeRunId, maximumSteps);
    hostStepCount = run.steps.length;
    const state = game.loadState();
    const projection = agent.projection();
    agent.host.verifyJournal(game.activeRunId);
    game.verifyStream(game.activeRunId);
    const replay = game.verifyReplay(game.activeRunId);
    const contextArtifacts = projection.attempts
      .filter((attempt) => attempt.contextDigest)
      .map((attempt) => agent!.host.getArtifact(attempt.contextDigest!).byteLength);
    const costs = provider.calls
      .map((call) => call.evidence)
      .filter((value): value is Record<string, unknown> => Boolean(value) && typeof value === "object")
      .map((value) => Number(value.estimatedCostUsd ?? 0));
    const databaseWillRemain = Boolean(databaseValue) || retainDatabase;
    const providerBlocker = projection.task.blockers.find((blocker) => blocker.startsWith("provider_")) ?? null;
    const finalTermination: LiveEvaluationTermination = state.mission.status !== "running"
      ? { kind: "domain_terminal", reason: state.mission.reason, signal: null, errorName: null, errorCode: null }
      : providerBlocker
        ? { kind: "provider_failure", reason: providerBlocker, signal: null, errorName: null, errorCode: providerBlocker }
        : { kind: "none", reason: "maximum Host steps reached before domain terminal state", signal: null, errorName: null, errorCode: null };
    const finalEnvelope = writeLiveEvaluationReceipt(receiptOutput, captureLiveEvaluationReceipt({
      phase: "completed",
      spec: spec(databaseWillRemain),
      game, agent, providerCalls: provider.calls, hostStepCount, termination: finalTermination,
    }));
    const report = {
      schemaVersion: 2,
      kind: "ordivon.game.m2-live-run",
      mode,
      sourceRevision,
      createdAt: new Date().toISOString(),
      evaluation: {
        evaluationId,
        wallClockLimitMs,
        maximumSteps,
        databasePath,
        databaseRetained: databaseWillRemain,
        receiptPath: receiptOutput,
        receiptDigest: finalEnvelope.receiptDigest,
        recoveryOfReceiptDigest: previous?.receiptDigest ?? null,
      },
      environment: {
        node: process.version,
        platform: `${process.platform}/${process.arch}`,
        codexVersion: commandVersion("/usr/bin/codex"),
        hermesVersion: commandVersion("/root/.local/bin/hermes"),
      },
      originalTranscriptLoaded: false,
      humanCorrectionCount: 0,
      elapsedMs: Date.now() - Date.parse(startedAt),
      providerCalls: provider.calls,
      providerCallCount: provider.calls.length,
      hostStepCount,
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
  } catch (error) {
    preserveGeneratedDatabase = true;
    if (game && agent && provider) {
      const termination = terminationFromError(error, requestedInterruption);
      const partial = captureLiveEvaluationReceipt({
        phase: termination.kind === "evaluation_failure" || termination.kind === "provider_failure" ? "failed" : "partial",
        spec: spec(true),
        game, agent, providerCalls: provider.calls, hostStepCount: null, termination,
      });
      const envelope = writeLiveEvaluationReceipt(partialOutput, partial);
      writeLiveEvaluationReceipt(receiptOutput, partial);
      console.error(JSON.stringify({
        kind: partial.kind,
        phase: partial.phase,
        termination: partial.termination,
        receiptPath: partialOutput,
        receiptDigest: envelope.receiptDigest,
        databasePath,
        activeAttemptId: partial.run.activeAttemptId,
        activeAttemptStatus: partial.run.activeAttemptStatus,
        worldRevision: partial.world.revision,
        worldDigest: partial.world.digest,
      }, null, 2));
      if (termination.kind === "evaluation_timeout") { process.exitCode = 124; return; }
      if (termination.kind === "external_signal") { process.exitCode = termination.signal === "SIGINT" ? 130 : 143; return; }
      if (termination.kind === "cancelled") { process.exitCode = 125; return; }
    }
    throw error;
  } finally {
    if (wallTimer) clearTimeout(wallTimer);
    process.removeListener("SIGINT", onSigint);
    process.removeListener("SIGTERM", onSigterm);
    game?.close();
    if (generatedDirectory && !preserveGeneratedDatabase) {
      rmSync(generatedDirectory, { recursive: true, force: true });
    }
  }
}

await main();
