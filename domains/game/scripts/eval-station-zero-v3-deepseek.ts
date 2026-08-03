import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  StationZeroV3DeepSeekProviderPool,
  StationZeroV3PlayService,
  StationZeroV3Store,
  stationZeroV3DeepSeekCredentialSources,
  type StationZeroV3AgentContext,
  type StationZeroV3CommanderOrder,
  type StationZeroV3CommanderOrderPatch,
  type StationZeroV3DeepSeekCallEvidence,
  type StationZeroV3PlanPreview,
  type StationZeroV3PlayView,
  type StationZeroV3WorldState,
} from "../src/station-zero-v3/index.ts";

interface EvaluationProfile {
  profileId: string;
  label: string;
  order: StationZeroV3CommanderOrderPatch;
}

interface EvaluatedDecision {
  runId: string;
  turn: number;
  actorId: string;
  factionId: string;
  roleId: string;
  candidateId: string;
  label: string;
  tags: string[];
  directiveId: string | null;
  rationale: string;
  confidence: number;
  hiddenReferences: string[];
}

interface EvaluatedTurn {
  turn: number;
  previewLatencyMs: number;
  commitLatencyMs: number;
  commanderDirectiveId: string;
  decisions: EvaluatedDecision[];
  rescueDestinationCollisions: string[];
  ownIntentResults: Array<{
    actorId: string;
    status: string;
    reason: string;
  }>;
  resourcesAfter: StationZeroV3PlayView["resources"];
}

interface EvaluatedRun {
  runId: string;
  profileId: string;
  replica: number;
  status: "completed" | "provider_failed" | "execution_failed";
  startedAt: string;
  elapsedMs: number;
  turnsCommitted: number;
  failure: { name: string; code: string | null; message: string } | null;
  outcomes: StationZeroV3PlayView["outcomes"];
  objectives: StationZeroV3PlayView["objectives"];
  resources: StationZeroV3PlayView["resources"];
  ownActors: StationZeroV3PlayView["ownActors"];
  verified: boolean;
  firstTurnSignature: string[];
  turns: EvaluatedTurn[];
}

const PROFILES: EvaluationProfile[] = [
  {
    profileId: "rescue-cautious",
    label: "Rescue / cautious / split",
    order: {
      primaryObjectiveId: "rescue-two-civilians",
      posture: "cautious",
      formation: "split",
      retreatHealthThreshold: 0.45,
      lethalForce: "forbidden",
      collateralPolicy: "forbidden",
      lootPolicy: "mission-only",
      protectedActorId: "medic-reyes",
    },
  },
  {
    profileId: "rescue-balanced",
    label: "Rescue / balanced / split",
    order: {
      primaryObjectiveId: "rescue-two-civilians",
      posture: "balanced",
      formation: "split",
      retreatHealthThreshold: 0.3,
      lethalForce: "permitted",
      collateralPolicy: "forbidden",
      lootPolicy: "mission-only",
      protectedActorId: "medic-reyes",
    },
  },
  {
    profileId: "core-aggressive",
    label: "Research Core / aggressive / split",
    order: {
      primaryObjectiveId: "recover-research-core",
      posture: "aggressive",
      formation: "split",
      retreatHealthThreshold: 0.2,
      lethalForce: "preferred",
      collateralPolicy: "limited",
      lootPolicy: "opportunistic",
      protectedActorId: "engineer-imani",
    },
  },
  {
    profileId: "hive-hunt",
    label: "Hive Alpha / aggressive / cohesive",
    order: {
      primaryObjectiveId: "eliminate-hive-alpha",
      posture: "aggressive",
      formation: "cohesive",
      retreatHealthThreshold: 0.25,
      lethalForce: "preferred",
      collateralPolicy: "limited",
      lootPolicy: "ignore",
      protectedActorId: "security-chen",
    },
  },
];

function positiveInteger(value: string | undefined, fallback: number, label: string): number {
  if (value === undefined || value === "") return fallback;
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < 1) throw new TypeError(`${label} must be a positive integer`);
  return parsed;
}

function percentile(values: number[], proportion: number): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((left, right) => left - right);
  return sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * proportion))] ?? null;
}

function countBy<T>(values: T[], key: (value: T) => string): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const value of values) counts[key(value)] = (counts[key(value)] ?? 0) + 1;
  return Object.fromEntries(Object.entries(counts).sort(([left], [right]) => left.localeCompare(right)));
}

function round(value: number, digits = 3): number {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function hiddenReferences(
  context: StationZeroV3AgentContext,
  actors: StationZeroV3WorldState["actors"],
  rationale: string,
): string[] {
  const known = new Set([context.actor.actorId, ...context.known.actors.map((actor) => actor.actorId)]);
  const explicitlyNamedIds = new Set<string>();
  const objectiveIds = [context.playerOrder?.primaryObjectiveId, context.playerOrder?.priorityTargetActorId, ...context.objectiveIds]
    .filter((value): value is string => Boolean(value));
  for (const actorId of Object.keys(actors)) {
    if (objectiveIds.some((objectiveId) => objectiveId.includes(actorId))) explicitlyNamedIds.add(actorId);
  }
  const normalized = rationale.toLowerCase();
  const leaked: string[] = [];
  for (const [actorId, actor] of Object.entries(actors)) {
    if (known.has(actorId) || explicitlyNamedIds.has(actorId)) continue;
    for (const token of [actorId, actor.name]) {
      if (token.length >= 4 && normalized.includes(token.toLowerCase())) leaked.push(token);
    }
  }
  return [...new Set(leaked)].sort();
}

function rescueDestinationCollisions(preview: StationZeroV3PlanPreview): string[] {
  const destinations = preview.factionPlans.rescue.actorIntents
    .filter((intent) => intent.kind === "move")
    .map((intent) => intent.targetZoneId);
  return Object.entries(countBy(destinations, (destination) => destination))
    .filter(([, count]) => count > 1)
    .map(([destination]) => destination)
    .sort();
}

function decisionRecord(
  preview: StationZeroV3PlanPreview,
  turn: number,
  runId: string,
  actors: StationZeroV3WorldState["actors"],
): EvaluatedDecision[] {
  return preview.agentDecisions.map((decision) => {
    const context = preview.contexts.find((entry) => entry.contextId === decision.contextId);
    if (!context) throw new Error(`missing retained Context for ${decision.contextId}`);
    const candidate = context.candidates.find((entry) => entry.candidateId === decision.candidateId);
    if (!candidate) throw new Error(`missing retained Candidate for ${decision.candidateId}`);
    return {
      runId,
      turn,
      actorId: decision.actorId,
      factionId: decision.factionId,
      roleId: context.actor.roleId,
      candidateId: decision.candidateId,
      label: candidate.label,
      tags: [...candidate.tags],
      directiveId: decision.directiveId,
      rationale: decision.rationale,
      confidence: decision.confidence,
      hiddenReferences: hiddenReferences(context, actors, decision.rationale),
    };
  });
}

function normalizedError(error: unknown): EvaluatedRun["failure"] {
  return {
    name: error instanceof Error ? error.name : "UnknownError",
    code: error && typeof error === "object" && "code" in error && typeof error.code === "string" ? error.code : null,
    message: (error instanceof Error ? error.message : String(error)).slice(0, 500),
  };
}

async function evaluateRun(
  pool: StationZeroV3DeepSeekProviderPool,
  profile: EvaluationProfile,
  replica: number,
): Promise<EvaluatedRun> {
  const runId = `run:deepseek-eval:${profile.profileId}:${replica}`;
  const store = new StationZeroV3Store(":memory:");
  const play = new StationZeroV3PlayService(store, { providerFactory: pool.providerFactory() });
  const startedAt = new Date().toISOString();
  const started = performance.now();
  const turns: EvaluatedTurn[] = [];
  let view = play.initialize({ runId, seed: `deepseek-eval:${profile.profileId}:${replica}` });
  let status: EvaluatedRun["status"] = "completed";
  let failure: EvaluatedRun["failure"] = null;
  let verified = false;

  try {
    while (view.run.status === "running") {
      play.saveOrder(runId, profile.order);
      const sourceState = store.loadState(runId);
      const previewStarted = performance.now();
      let generated: Awaited<ReturnType<StationZeroV3PlayService["generatePreview"]>>;
      try {
        generated = await play.generatePreview(runId);
      } catch (error) {
        status = "provider_failed";
        failure = normalizedError(error);
        break;
      }
      const previewLatencyMs = Math.round(performance.now() - previewStarted);
      const preview = generated.preview;
      const decisions = decisionRecord(preview, view.run.turn, runId, sourceState.actors);
      const commitStarted = performance.now();
      try {
        view = (await play.commitPreview(runId, preview.previewId)).view;
      } catch (error) {
        status = "execution_failed";
        failure = normalizedError(error);
        break;
      }
      turns.push({
        turn: view.run.turn - 1,
        previewLatencyMs,
        commitLatencyMs: Math.round(performance.now() - commitStarted),
        commanderDirectiveId: preview.playerOrder.commanderDirectiveId,
        decisions,
        rescueDestinationCollisions: rescueDestinationCollisions(preview),
        ownIntentResults: (view.aftermath?.ownIntentResults ?? []).map((result) => ({
          actorId: result.actorId,
          status: result.status,
          reason: result.reason,
        })),
        resourcesAfter: structuredClone(view.resources),
      });
      console.log(JSON.stringify({
        kind: "ordivon.game.station-zero-v3-deepseek-eval-progress",
        runId,
        profileId: profile.profileId,
        turn: view.run.turn,
        turnLimit: view.run.turnLimit,
        previewLatencyMs,
        outcome: view.outcomes.rescue,
      }));
    }
    play.planning.verifyRun(runId);
    play.turns.recover(runId);
    verified = true;
  } catch (error) {
    status = "execution_failed";
    failure ??= normalizedError(error);
  }

  const finalView = play.state(runId);
  store.close();
  return {
    runId,
    profileId: profile.profileId,
    replica,
    status,
    startedAt,
    elapsedMs: Math.round(performance.now() - started),
    turnsCommitted: turns.length,
    failure,
    outcomes: structuredClone(finalView.outcomes),
    objectives: structuredClone(finalView.objectives),
    resources: structuredClone(finalView.resources),
    ownActors: structuredClone(finalView.ownActors),
    verified,
    firstTurnSignature: turns[0]?.decisions.map((decision) => `${decision.actorId}=${decision.label}`) ?? [],
    turns,
  };
}

async function mapConcurrent<T, R>(values: T[], concurrency: number, operation: (value: T) => Promise<R>): Promise<R[]> {
  const results: R[] = new Array(values.length);
  let next = 0;
  const workers = Array.from({ length: Math.min(concurrency, values.length) }, async () => {
    while (true) {
      const index = next;
      next += 1;
      if (index >= values.length) return;
      results[index] = await operation(values[index]!);
    }
  });
  await Promise.all(workers);
  return results;
}

function actionSuffix(candidateId: string): string {
  const marker = candidateId.lastIndexOf(":");
  return marker >= 0 ? candidateId.slice(marker + 1) : candidateId;
}

function oscillations(decisions: EvaluatedDecision[]): Array<{ runId: string; actorId: string; turns: [number, number, number]; actions: [string, string, string] }> {
  const result: Array<{ runId: string; actorId: string; turns: [number, number, number]; actions: [string, string, string] }> = [];
  const byActor = Object.groupBy(decisions, (decision) => `${decision.runId}\u0000${decision.actorId}`);
  for (const [identity, actorDecisions] of Object.entries(byActor)) {
    const [runId, actorId] = identity.split("\u0000");
    if (!actorDecisions) continue;
    const ordered = [...actorDecisions].sort((left, right) => left.turn - right.turn);
    for (let index = 2; index < ordered.length; index += 1) {
      const a = ordered[index - 2]!;
      const b = ordered[index - 1]!;
      const c = ordered[index]!;
      const aa = actionSuffix(a.candidateId);
      const ba = actionSuffix(b.candidateId);
      const ca = actionSuffix(c.candidateId);
      if (aa === ca && aa !== ba && a.label.startsWith("Move") && b.label.startsWith("Move") && c.label.startsWith("Move")) {
        result.push({ runId: runId!, actorId: actorId!, turns: [a.turn, b.turn, c.turn], actions: [aa, ba, ca] });
      }
    }
  }
  return result;
}

function aggregate(calls: StationZeroV3DeepSeekCallEvidence[], runs: EvaluatedRun[]) {
  const decisions = runs.flatMap((run) => run.turns.flatMap((turn) => turn.decisions));
  const intentResults = runs.flatMap((run) => run.turns.flatMap((turn) => turn.ownIntentResults));
  const previewLatencies = runs.flatMap((run) => run.turns.map((turn) => turn.previewLatencyMs));
  const callLatencies = calls.map((call) => call.latencyMs);
  const confidenceValues = decisions.map((decision) => decision.confidence);
  const hidden = decisions.filter((decision) => decision.hiddenReferences.length > 0);
  const collisionTurns = runs.flatMap((run) => run.turns
    .filter((turn) => turn.rescueDestinationCollisions.length > 0)
    .map((turn) => ({ runId: run.runId, turn: turn.turn, destinations: turn.rescueDestinationCollisions })));
  const movementOscillations = oscillations(decisions);
  const successfulCalls = calls.filter((call) => call.outcome === "success");
  const retryCalls = calls.filter((call) => call.attempt > 1);
  return {
    runs: {
      requested: runs.length,
      completed: runs.filter((run) => run.status === "completed").length,
      providerFailed: runs.filter((run) => run.status === "provider_failed").length,
      executionFailed: runs.filter((run) => run.status === "execution_failed").length,
      verified: runs.filter((run) => run.verified).length,
      byProfile: Object.fromEntries(PROFILES.map((profile) => {
        const profileRuns = runs.filter((run) => run.profileId === profile.profileId);
        return [profile.profileId, {
          requested: profileRuns.length,
          completed: profileRuns.filter((run) => run.status === "completed").length,
          averageTurns: profileRuns.length ? round(profileRuns.reduce((sum, run) => sum + run.turnsCommitted, 0) / profileRuns.length, 2) : 0,
          rescueOutcomes: countBy(profileRuns, (run) => run.outcomes.rescue),
          pirateOutcomes: countBy(profileRuns, (run) => run.outcomes.pirate),
          swarmOutcomes: countBy(profileRuns, (run) => run.outcomes.swarm),
          firstTurnSignatures: profileRuns.map((run) => run.firstTurnSignature),
        }];
      })),
    },
    provider: {
      attempts: calls.length,
      successfulCalls: successfulCalls.length,
      successRate: calls.length ? round(successfulCalls.length / calls.length) : 0,
      retryAttempts: retryCalls.length,
      outcomes: countBy(calls, (call) => call.outcome),
      credentials: countBy(calls, (call) => call.credentialId),
      finishReasons: countBy(calls, (call) => call.finishReason ?? "none"),
      latencyMs: {
        min: callLatencies.length ? Math.min(...callLatencies) : null,
        p50: percentile(callLatencies, 0.5),
        p95: percentile(callLatencies, 0.95),
        max: callLatencies.length ? Math.max(...callLatencies) : null,
      },
      previewLatencyMs: {
        min: previewLatencies.length ? Math.min(...previewLatencies) : null,
        p50: percentile(previewLatencies, 0.5),
        p95: percentile(previewLatencies, 0.95),
        max: previewLatencies.length ? Math.max(...previewLatencies) : null,
      },
      tokens: {
        prompt: calls.reduce((sum, call) => sum + call.promptTokens, 0),
        completion: calls.reduce((sum, call) => sum + call.completionTokens, 0),
        reasoning: calls.reduce((sum, call) => sum + call.reasoningTokens, 0),
        total: calls.reduce((sum, call) => sum + call.totalTokens, 0),
        cacheHit: calls.reduce((sum, call) => sum + call.cacheHitTokens, 0),
      },
    },
    decisions: {
      total: decisions.length,
      byActor: countBy(decisions, (decision) => decision.actorId),
      byDirective: countBy(decisions.filter((decision) => decision.directiveId !== null), (decision) => decision.directiveId!),
      waitCount: decisions.filter((decision) => decision.tags.includes("wait")).length,
      attackCount: decisions.filter((decision) => decision.tags.includes("combat")).length,
      guardCount: decisions.filter((decision) => decision.tags.includes("guard")).length,
      interactionCount: decisions.filter((decision) => decision.tags.includes("interaction")).length,
      averageConfidence: confidenceValues.length ? round(confidenceValues.reduce((sum, value) => sum + value, 0) / confidenceValues.length) : null,
      minimumConfidence: confidenceValues.length ? Math.min(...confidenceValues) : null,
      maximumConfidence: confidenceValues.length ? Math.max(...confidenceValues) : null,
      hiddenReferenceCount: hidden.length,
      hiddenReferences: hidden,
      rescueDestinationCollisionTurns: collisionTurns.length,
      collisionDetails: collisionTurns,
      movementOscillationCount: movementOscillations.length,
      movementOscillations,
    },
    resolution: {
      totalOwnIntents: intentResults.length,
      statuses: countBy(intentResults, (result) => result.status),
      reasons: countBy(intentResults, (result) => result.reason),
      executedRate: intentResults.length
        ? round(intentResults.filter((result) => result.status === "executed").length / intentResults.length)
        : null,
    },
  };
}

const replicasPerProfile = positiveInteger(process.env.ORDIVON_EVAL_REPLICAS_PER_PROFILE, 2, "ORDIVON_EVAL_REPLICAS_PER_PROFILE");
const runConcurrency = positiveInteger(process.env.ORDIVON_EVAL_RUN_CONCURRENCY, 4, "ORDIVON_EVAL_RUN_CONCURRENCY");
const thinkingMode = process.env.ORDIVON_GAME_V3_DEEPSEEK_THINKING === "enabled" ? "enabled" : "disabled";
const pool = new StationZeroV3DeepSeekProviderPool({
  credentialSources: stationZeroV3DeepSeekCredentialSources(process.env.ORDIVON_GAME_V3_DEEPSEEK_SOURCES ?? process.env.ORDIVON_GAME_V3_DEEPSEEK_SECRETS),
  thinkingMode,
  reasoningEffort: process.env.ORDIVON_GAME_V3_DEEPSEEK_REASONING_EFFORT === "max" ? "max" : "high",
  timeoutMs: positiveInteger(process.env.ORDIVON_GAME_V3_DEEPSEEK_TIMEOUT_MS, 30_000, "ORDIVON_GAME_V3_DEEPSEEK_TIMEOUT_MS"),
  maxTokens: positiveInteger(
    process.env.ORDIVON_GAME_V3_DEEPSEEK_MAX_TOKENS,
    thinkingMode === "enabled" ? 2_048 : 512,
    "ORDIVON_GAME_V3_DEEPSEEK_MAX_TOKENS",
  ),
  maximumConcurrencyPerCredential: positiveInteger(
    process.env.ORDIVON_GAME_V3_DEEPSEEK_CONCURRENCY,
    4,
    "ORDIVON_GAME_V3_DEEPSEEK_CONCURRENCY",
  ),
  retryBaseDelayMs: Number(process.env.ORDIVON_GAME_V3_DEEPSEEK_RETRY_BASE_DELAY_MS ?? 1_000),
  credentialReloadIntervalMs: Number(process.env.ORDIVON_GAME_V3_DEEPSEEK_RELOAD_INTERVAL_MS ?? 15_000),
  credentialCooldownMaximumMs: Number(process.env.ORDIVON_GAME_V3_DEEPSEEK_COOLDOWN_MAXIMUM_MS ?? 30_000),
  ...(process.env.ORDIVON_GAME_V3_DEEPSEEK_MAX_ATTEMPTS
    ? { maximumAttempts: positiveInteger(process.env.ORDIVON_GAME_V3_DEEPSEEK_MAX_ATTEMPTS, 4, "ORDIVON_GAME_V3_DEEPSEEK_MAX_ATTEMPTS") }
    : {}),
  temperature: Number(process.env.ORDIVON_GAME_V3_DEEPSEEK_TEMPERATURE ?? 0.1),
});

const cases = PROFILES.flatMap((profile) => Array.from({ length: replicasPerProfile }, (_, index) => ({
  profile,
  replica: index + 1,
})));
const evaluationStartedAt = new Date().toISOString();
const evaluationStarted = performance.now();
const runs = await mapConcurrent(cases, runConcurrency, ({ profile, replica }) => evaluateRun(pool, profile, replica));
const providerEvidence = pool.evidenceSnapshot();
const calls = providerEvidence.calls;
const report = {
  schemaVersion: 1,
  kind: "ordivon.game.station-zero-v3-deepseek-evaluation",
  generatedAt: new Date().toISOString(),
  evaluationStartedAt,
  elapsedMs: Math.round(performance.now() - evaluationStarted),
  configuration: {
    providerId: pool.providerId,
    thinkingMode,
    replicasPerProfile,
    runConcurrency,
    credentialPool: providerEvidence.credentialPool,
    configuredTotalConcurrency: providerEvidence.credentials.reduce((sum, credential) => sum + credential.maximumConcurrency, 0),
    profiles: PROFILES,
  },
  aggregate: aggregate(calls, runs),
  calls,
  runs,
};
const artifactDirectory = resolve(process.env.ORDIVON_EVAL_ARTIFACT_DIR ?? "artifacts/evaluations");
mkdirSync(artifactDirectory, { recursive: true });
const outputPath = resolve(artifactDirectory, `station-zero-v3-deepseek-${Date.now()}.json`);
writeFileSync(outputPath, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify({
  kind: "ordivon.game.station-zero-v3-deepseek-evaluation-summary",
  outputPath,
  elapsedMs: report.elapsedMs,
  aggregate: report.aggregate,
}, null, 2));
