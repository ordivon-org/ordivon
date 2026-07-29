import { execFileSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

import { sha256 } from "../src/digest.ts";
import { scoreMission } from "../src/scoring.ts";
import { ENGINEER_ID, MEDIC_ID, SECURITY_ID } from "../src/scenario.ts";
import { GameStore } from "../src/storage.ts";
import { TeamCodexCliProvider } from "../src/team/codex-cli.ts";
import { TeamHost } from "../src/team/engine.ts";
import { TeamHermesCliProvider } from "../src/team/hermes-cli.ts";
import type { CompiledTeamContext, TeamProviderDecision } from "../src/team/model.ts";
import { FixtureTeamProvider, type TeamDecisionProvider } from "../src/team/providers.ts";

const modes = ["fixture-security", "fixture-engineer", "codex", "hermes", "mixed", "codex-hermes-switch"] as const;
type Mode = typeof modes[number];

interface ProviderCallRecord {
  sequence: number;
  phase: string;
  actorId: string;
  providerId: string;
  contextId: string;
  worldRevision: number;
  contextBytes: number;
  estimatedTokens: number;
  status: "succeeded" | "failed";
  selectedActionCandidateId: string | null;
  selectedActionId: string | null;
  commandKind: string | null;
  confidence: number | null;
  rationale: string | null;
  elapsedMs: number;
  evidence: Record<string, unknown> | null;
  errorCode: string | null;
  error: string | null;
}

class RecordingProvider implements TeamDecisionProvider {
  readonly providerId: string;
  readonly inner: TeamDecisionProvider;
  readonly records: ProviderCallRecord[];
  readonly phase: string;

  constructor(inner: TeamDecisionProvider, records: ProviderCallRecord[], phase: string) {
    this.inner = inner;
    this.records = records;
    this.phase = phase;
    this.providerId = inner.providerId;
  }

  evidenceMetadata(): Record<string, unknown> | null {
    return this.inner.evidenceMetadata?.() ?? null;
  }

  async decide(context: CompiledTeamContext): Promise<TeamProviderDecision> {
    const started = performance.now();
    try {
      const decision = await this.inner.decide(context);
      const candidate = context.allowedActions.find((entry) => entry.actionCandidateId === decision.selectedActionCandidateId) ?? null;
      this.records.push({
        sequence: this.records.length,
        phase: this.phase,
        actorId: context.actorId,
        providerId: decision.providerId,
        contextId: context.contextId,
        worldRevision: context.worldRevision,
        contextBytes: context.byteLength,
        estimatedTokens: context.manifest.estimatedTokens,
        status: "succeeded",
        selectedActionCandidateId: decision.selectedActionCandidateId,
        selectedActionId: candidate?.actionId ?? null,
        commandKind: candidate?.command.kind ?? null,
        confidence: decision.confidence,
        rationale: decision.rationale,
        elapsedMs: Number((performance.now() - started).toFixed(3)),
        evidence: this.inner.evidenceMetadata?.() ?? null,
        errorCode: null,
        error: null,
      });
      return decision;
    } catch (error) {
      this.records.push({
        sequence: this.records.length,
        phase: this.phase,
        actorId: context.actorId,
        providerId: this.inner.providerId,
        contextId: context.contextId,
        worldRevision: context.worldRevision,
        contextBytes: context.byteLength,
        estimatedTokens: context.manifest.estimatedTokens,
        status: "failed",
        selectedActionCandidateId: null,
        selectedActionId: null,
        commandKind: null,
        confidence: null,
        rationale: null,
        elapsedMs: Number((performance.now() - started).toFixed(3)),
        evidence: this.inner.evidenceMetadata?.() ?? null,
        errorCode: error && typeof error === "object" && "code" in error ? String(error.code) : null,
        error: error instanceof Error ? error.message : String(error),
      });
      throw error;
    }
  }
}

function argument(name: string, fallback: string | null = null): string | null {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] ?? fallback : fallback;
}

function commandVersion(executable: string): string | null {
  try { return execFileSync(executable, ["--version"], { encoding: "utf8" }).trim(); }
  catch { return null; }
}

function providersFor(
  mode: Mode,
  records: ProviderCallRecord[],
  phase: string,
): TeamDecisionProvider | Record<string, TeamDecisionProvider> {
  if (mode === "fixture-security") return new RecordingProvider(new FixtureTeamProvider(), records, phase);
  if (mode === "fixture-engineer") return new RecordingProvider(new FixtureTeamProvider({ breachStrategy: "engineer-seal" }), records, phase);
  const wrap = (provider: TeamDecisionProvider) => new RecordingProvider(provider, records, phase);
  if (mode === "codex") {
    return {
      [ENGINEER_ID]: wrap(new TeamCodexCliProvider({ timeoutMs: 240_000 })),
      [MEDIC_ID]: wrap(new TeamCodexCliProvider({ timeoutMs: 240_000 })),
      [SECURITY_ID]: wrap(new TeamCodexCliProvider({ timeoutMs: 240_000 })),
    };
  }
  if (mode === "hermes") {
    return {
      [ENGINEER_ID]: wrap(new TeamHermesCliProvider({ timeoutMs: 240_000 })),
      [MEDIC_ID]: wrap(new TeamHermesCliProvider({ timeoutMs: 240_000 })),
      [SECURITY_ID]: wrap(new TeamHermesCliProvider({ timeoutMs: 240_000 })),
    };
  }
  if (mode === "mixed") {
    return {
      [ENGINEER_ID]: wrap(new TeamCodexCliProvider({ timeoutMs: 240_000 })),
      [MEDIC_ID]: wrap(new TeamHermesCliProvider({ timeoutMs: 240_000 })),
      [SECURITY_ID]: wrap(new TeamHermesCliProvider({ timeoutMs: 240_000 })),
    };
  }
  return {
    [ENGINEER_ID]: wrap(new TeamCodexCliProvider({ timeoutMs: 240_000 })),
    [MEDIC_ID]: wrap(new TeamCodexCliProvider({ timeoutMs: 240_000 })),
    [SECURITY_ID]: wrap(new TeamCodexCliProvider({ timeoutMs: 240_000 })),
  };
}

function numericEvidence(records: ProviderCallRecord[], key: string): number {
  return records.reduce((sum, record) => {
    const value = record.evidence?.[key];
    return sum + (typeof value === "number" && Number.isFinite(value) ? value : 0);
  }, 0);
}

const modeValue = argument("--mode", "fixture-security");
if (!modes.includes(modeValue as Mode)) throw new Error(`unsupported M3 evaluation mode: ${modeValue}`);
const mode = modeValue as Mode;
const outputPath = resolve(argument("--output", `/tmp/ordivon-game-m3-${mode}.json`) ?? `/tmp/ordivon-game-m3-${mode}.json`);
const maximumSteps = Number(argument("--maximum-steps", "512"));
if (!Number.isSafeInteger(maximumSteps) || maximumSteps < 1) throw new Error("--maximum-steps must be a positive integer");

const sourceRevision = execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim();
const runId = `run:m3-evaluation:${mode}:${randomUUID()}`;
const game = new GameStore(":memory:");
game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
game.setActiveRun(runId);
const records: ProviderCallRecord[] = [];
const started = performance.now();
let firstReceipt: Awaited<ReturnType<TeamHost["run"]>> | null = null;
let finalReceipt: Awaited<ReturnType<TeamHost["run"]>>;

try {
  if (mode === "codex-hermes-switch") {
    const first = new TeamHost(game, providersFor(mode, records, "codex"));
    firstReceipt = await first.run(runId, 28);
    const switchedProviders: Record<string, TeamDecisionProvider> = {
      [ENGINEER_ID]: new RecordingProvider(new TeamHermesCliProvider({ timeoutMs: 240_000 }), records, "hermes"),
      [MEDIC_ID]: new RecordingProvider(new TeamHermesCliProvider({ timeoutMs: 240_000 }), records, "hermes"),
      [SECURITY_ID]: new RecordingProvider(new TeamHermesCliProvider({ timeoutMs: 240_000 }), records, "hermes"),
    };
    finalReceipt = await new TeamHost(game, switchedProviders).run(runId, maximumSteps);
  } else {
    finalReceipt = await new TeamHost(game, providersFor(mode, records, mode)).run(runId, maximumSteps);
  }
  const state = game.loadState(runId);
  const team = new TeamHost(game, new FixtureTeamProvider());
  team.team.verify(runId);
  const replay = game.verifyReplay(runId);
  const events = game.events(runId);
  const rounds = team.execution.listRounds(runId);
  const proposals = rounds.flatMap((round) => team.execution.listProposals(round.roundId));
  const journal = team.team.host.listJournal(runId);
  const result = {
    schemaVersion: 1,
    kind: "ordivon.game.m3-evaluation",
    generatedAt: new Date().toISOString(),
    sourceRevision,
    mode,
    runId,
    cliVersions: { codex: commandVersion("codex"), hermes: commandVersion("hermes") },
    elapsedMs: Number((performance.now() - started).toFixed(3)),
    firstPhase: firstReceipt ? {
      worldRevision: firstReceipt.worldRevision,
      worldDigest: firstReceipt.worldDigest,
      rounds: firstReceipt.rounds.length,
    } : null,
    terminal: {
      mission: state.mission,
      worldRevision: state.revision,
      simulationTick: state.turn,
      worldDigest: sha256(state),
      score: scoreMission(state),
      resources: state.resources,
      hazard: state.hazards["maintenance-breach"],
      crew: state.crew["crew-01"],
      actors: state.agents,
      systems: state.systems,
    },
    evidence: {
      worldEvents: events.length,
      rounds: rounds.length,
      completedRounds: rounds.filter((round) => round.status === "completed").length,
      blockedRounds: rounds.filter((round) => round.status === "blocked").length,
      contexts: rounds.reduce((count, round) => count + team.execution.listContexts(round.roundId).length, 0),
      proposals: proposals.length,
      selectedProposals: proposals.filter((proposal) => ["selected", "executed", "verified"].includes(proposal.status)).length,
      verifiedProposals: proposals.filter((proposal) => proposal.status === "verified").length,
      effects: team.execution.authority.listEffects(runId).length,
      dispatches: team.execution.authority.listDispatches(runId).length,
      observations: team.execution.authority.listObservations(runId).length,
      authorityDecisions: team.team.listAuthorityDecisions(runId).length,
      authorityGrants: team.team.listAuthorityGrants(runId).length,
      messages: team.team.listMessages(runId).length,
      hostJournalEvents: journal.length,
      hostJournalDigest: journal.at(-1)?.recordDigest ?? null,
      replayVerified: replay.verified,
      replayDigest: replay.digest,
      allRoundsCompleted: rounds.every((round) => round.status === "completed"),
      allEffectsVerified: team.execution.authority.contracts.transcript(runId).filter((entry) => entry.contractKind === "ordivon.task-outcome").length === rounds.length,
      allDispatchesSucceeded: team.execution.authority.listObservations(runId).every((observation) => observation.status === "succeeded"),
      maximumContextBytes: records.reduce((maximum, record) => Math.max(maximum, record.contextBytes), 0),
      maximumContextTokens: records.reduce((maximum, record) => Math.max(maximum, record.estimatedTokens), 0),
    },
    providerSummary: {
      calls: records.length,
      succeeded: records.filter((record) => record.status === "succeeded").length,
      failed: records.filter((record) => record.status === "failed").length,
      inputTokens: numericEvidence(records, "inputTokens"),
      cachedInputTokens: numericEvidence(records, "cachedInputTokens"),
      outputTokens: numericEvidence(records, "outputTokens"),
      reasoningTokens: numericEvidence(records, "reasoningTokens"),
      totalTokens: numericEvidence(records, "totalTokens"),
      estimatedCostUsd: Number(numericEvidence(records, "estimatedCostUsd").toFixed(8)),
    },
    providerCalls: records,
    rounds,
    proposals,
    tasks: finalReceipt.projection.tasks,
  };
  mkdirSync(dirname(outputPath), { recursive: true });
  writeFileSync(outputPath, JSON.stringify(result, null, 2) + "\n");
  console.log(JSON.stringify({ outputPath, mode, terminal: result.terminal, evidence: result.evidence, providerSummary: result.providerSummary }, null, 2));
} finally {
  game.close();
}
