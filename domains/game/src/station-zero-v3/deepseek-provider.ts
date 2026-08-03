import { ProviderAdapterError } from "../team/provider-runtime.ts";
import { assertStationZeroV3AgentDecision } from "./agent-planning.ts";
import {
  StationZeroV3DeepSeekCredentialPool,
  type StationZeroV3DeepSeekCredentialFailureKind,
  type StationZeroV3DeepSeekCredentialHandle,
  type StationZeroV3DeepSeekCredentialPoolSnapshot,
} from "./deepseek-credentials.ts";
import type {
  StationZeroV3AgentContext,
  StationZeroV3AgentDecision,
  StationZeroV3AgentProvider,
  StationZeroV3AgentProviderFactory,
} from "./p3-model.ts";

export type StationZeroV3DeepSeekThinkingMode = "disabled" | "enabled";

export interface StationZeroV3DeepSeekProviderOptions {
  /** Files or directories. Directories discover every private deepseek*.json file. */
  credentialSources?: string[];
  /** @deprecated Use credentialSources. Files and directories are both accepted. */
  secretPaths?: string[];
  timeoutMs?: number;
  maxTokens?: number;
  temperature?: number;
  thinkingMode?: StationZeroV3DeepSeekThinkingMode;
  reasoningEffort?: "high" | "max";
  maximumConcurrencyPerCredential?: number;
  maximumAttempts?: number;
  retryBaseDelayMs?: number;
  credentialReloadIntervalMs?: number;
  credentialCooldownMaximumMs?: number;
  fetchImplementation?: typeof fetch;
}

export type StationZeroV3DeepSeekCallOutcome =
  | "success"
  | "http_error"
  | "rate_limited"
  | "authentication_error"
  | "server_error"
  | "timeout"
  | "transport_error"
  | "invalid_output"
  | "invalid_usage";

export interface StationZeroV3DeepSeekCallEvidence {
  callId: string;
  contextId: string;
  actorId: string;
  factionId: string;
  credentialId: string;
  attempt: number;
  startedAt: string;
  latencyMs: number;
  outcome: StationZeroV3DeepSeekCallOutcome;
  httpStatus: number | null;
  reportedModel: string | null;
  finishReason: string | null;
  requestBytes: number;
  responseBytes: number;
  promptTokens: number;
  completionTokens: number;
  reasoningTokens: number;
  totalTokens: number;
  cacheHitTokens: number;
  candidateId: string | null;
  directiveId: string | null;
  errorCode: string | null;
  errorMessage: string | null;
}

export interface StationZeroV3DeepSeekEvidenceSnapshot {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-deepseek-evidence";
  providerId: string;
  thinkingMode: StationZeroV3DeepSeekThinkingMode;
  maxTokens: number;
  maximumAttempts: number;
  retryBaseDelayMs: number;
  credentialPool: StationZeroV3DeepSeekCredentialPoolSnapshot;
  credentials: StationZeroV3DeepSeekCredentialPoolSnapshot["credentials"];
  calls: StationZeroV3DeepSeekCallEvidence[];
}

interface DeepSeekUsage {
  prompt_tokens?: unknown;
  completion_tokens?: unknown;
  total_tokens?: unknown;
  prompt_cache_hit_tokens?: unknown;
  completion_tokens_details?: {
    reasoning_tokens?: unknown;
  };
}

interface AttemptMetadata {
  httpStatus: number | null;
  reportedModel: string | null;
  finishReason: string | null;
  responseBytes: number;
  promptTokens: number;
  completionTokens: number;
  reasoningTokens: number;
  totalTokens: number;
  cacheHitTokens: number;
}

interface ParsedDecisionBody {
  candidateId: string;
  directiveId: string | null;
  rationale: string;
  confidence: number;
}

const PIRATE_DIRECTIVES: Record<string, string> = {
  "steal-core": "Secure the Research Core and create a safe route to the Pirate extraction point.",
  "capture-prize": "Disable and capture a valuable specialist while preserving Pirate combat power.",
  "extract-crew": "Disengage and extract carried cargo or captives before the station becomes untenable.",
};

const SWARM_DIRECTIVES: Record<string, string> = {
  "hunt-biomass": "Attack exposed life, create casualties, and convert bodies into Biomass.",
  "infect-life-support": "Reach and infect Life Support to make the station hostile to non-Swarm life.",
  "preserve-hive": "Reduce risk to the Hive Alpha, hold defensible ground, and preserve future growth.",
};

const SYSTEM_PROMPT = `You are one bounded tactical actor in Station Zero.
You do not control the World and you cannot invent actions, objects, targets, observations, or facts.
Use only the supplied faction knowledge and choose exactly one supplied candidateId.
When allowedDirectives is non-empty, choose exactly one supplied directiveId and make the local action reasonably consistent with it.
When allowedDirectives is empty, directiveId must be null.
Respect the player's Commander Order when it is present. Primary objective, role competence, formation, survival, and local evidence determine local action. Remote Mission Control abilities are deliberately absent and must not be inferred.
Role doctrine: Engineers prioritize systems, technical routes, and mission cargo; Medics prioritize wounded people, civilians, escort, and extraction; Security prioritizes protection, guard, hostile interception, and safe access. A split formation means specialists should pursue different role-appropriate fronts when possible; a cohesive formation means mutual support is preferred. Pirate Captains preserve their crew while pursuing profit. Hive Alphas pursue biomass, infection, growth, or survival according to the selected directive.
Do not mention or rely on hidden information. Do not reveal chain-of-thought. Give only a short operational rationale of at most 240 characters.
Return JSON only. Exact example: {"candidateId":"candidate:exact-id","directiveId":null,"rationale":"Short operational reason.","confidence":0.8}
The JSON object must contain exactly these fields: candidateId, directiveId, rationale, confidence. Confidence must be a number from 0 to 1.`;

function finiteNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function directiveDescriptions(context: StationZeroV3AgentContext): Record<string, string> {
  const source = context.factionId === "pirate" ? PIRATE_DIRECTIVES : context.factionId === "swarm" ? SWARM_DIRECTIVES : {};
  return Object.fromEntries(context.allowedDirectiveIds.map((directiveId) => [directiveId, source[directiveId] ?? directiveId]));
}

function compactContext(context: StationZeroV3AgentContext): Record<string, unknown> {
  const order = context.playerOrder;
  return {
    turn: context.worldRevision,
    factionId: context.factionId,
    actor: context.actor,
    environment: context.environment,
    known: {
      zoneIds: context.known.zoneIds,
      frontierZoneIds: context.known.frontierZoneIds,
      actors: context.known.actors,
      systemIds: context.known.systemIds,
      hazardIds: context.known.hazardIds,
      groundItemIds: context.known.groundItemIds,
    },
    objectiveIds: context.objectiveIds,
    playerOrder: order ? {
      primaryObjectiveId: order.primaryObjectiveId,
      posture: order.posture,
      formation: order.formation,
      retreatHealthThreshold: order.retreatHealthThreshold,
      lethalForce: order.lethalForce,
      collateralPolicy: order.collateralPolicy,
      lootPolicy: order.lootPolicy,
      protectedActorId: order.protectedActorId,
      priorityTargetActorId: order.priorityTargetActorId,
    } : null,
    allowedDirectives: directiveDescriptions(context),
    candidates: context.candidates.map((candidate) => ({
      candidateId: candidate.candidateId,
      label: candidate.label,
      tags: candidate.tags,
    })),
  };
}

function parseDecisionBody(context: StationZeroV3AgentContext, content: string): ParsedDecisionBody {
  let value: unknown;
  try {
    value = JSON.parse(content);
  } catch (error) {
    throw new ProviderAdapterError("invalid_output", "DeepSeek did not return valid JSON", { cause: error });
  }
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new ProviderAdapterError("invalid_output", "DeepSeek Decision must be one JSON object");
  }
  const record = value as Record<string, unknown>;
  const expected = ["candidateId", "confidence", "directiveId", "rationale"];
  if (Object.keys(record).sort().join("|") !== expected.join("|")) {
    throw new ProviderAdapterError("invalid_output", "DeepSeek Decision fields differ from the exact contract");
  }
  if (
    typeof record.candidateId !== "string" ||
    (record.directiveId !== null && typeof record.directiveId !== "string") ||
    typeof record.rationale !== "string" ||
    typeof record.confidence !== "number"
  ) throw new ProviderAdapterError("invalid_output", "DeepSeek Decision field types are invalid");
  const rationale = record.rationale.trim();
  if (!rationale || rationale.length > 240) throw new ProviderAdapterError("invalid_output", "DeepSeek rationale must contain 1–240 characters");
  if (!Number.isFinite(record.confidence) || record.confidence < 0 || record.confidence > 1) {
    throw new ProviderAdapterError("invalid_output", "DeepSeek confidence must be between zero and one");
  }
  if (!context.candidates.some((candidate) => candidate.candidateId === record.candidateId)) {
    throw new ProviderAdapterError("invalid_output", "DeepSeek invented a Candidate identity");
  }
  if (context.allowedDirectiveIds.length === 0 && record.directiveId !== null) {
    throw new ProviderAdapterError("invalid_output", "DeepSeek invented a Directive for an Actor without directive authority");
  }
  if (context.allowedDirectiveIds.length > 0 && (record.directiveId === null || !context.allowedDirectiveIds.includes(record.directiveId))) {
    throw new ProviderAdapterError("invalid_output", "DeepSeek omitted or invented the required faction Directive");
  }
  return {
    candidateId: record.candidateId,
    directiveId: record.directiveId,
    rationale,
    confidence: record.confidence,
  };
}

function metadataFromUsage(usage: DeepSeekUsage | undefined): Pick<AttemptMetadata,
  "promptTokens" | "completionTokens" | "reasoningTokens" | "totalTokens" | "cacheHitTokens"> {
  return {
    promptTokens: finiteNumber(usage?.prompt_tokens),
    completionTokens: finiteNumber(usage?.completion_tokens),
    reasoningTokens: finiteNumber(usage?.completion_tokens_details?.reasoning_tokens),
    totalTokens: finiteNumber(usage?.total_tokens),
    cacheHitTokens: finiteNumber(usage?.prompt_cache_hit_tokens),
  };
}

function outcomeForError(error: unknown, httpStatus: number | null): StationZeroV3DeepSeekCallOutcome {
  if (httpStatus === 429) return "rate_limited";
  if (httpStatus === 401 || httpStatus === 403) return "authentication_error";
  if (httpStatus !== null && httpStatus >= 500) return "server_error";
  if (error instanceof ProviderAdapterError) {
    if (error.code === "timeout") return "timeout";
    if (error.code === "invalid_output") return "invalid_output";
    if (error.code === "invalid_usage") return "invalid_usage";
    if (error.code === "process_failed") return "http_error";
  }
  return "transport_error";
}

function failureKind(error: unknown, httpStatus: number | null): StationZeroV3DeepSeekCredentialFailureKind {
  if (httpStatus === 429) return "rate_limit";
  if (httpStatus === 401 || httpStatus === 403) return "authentication";
  if (httpStatus !== null && httpStatus >= 500) return "server";
  if (error instanceof ProviderAdapterError) {
    if (error.code === "timeout") return "timeout";
    if (error.code === "invalid_output") return "invalid_output";
    if (error.code === "invalid_usage") return "invalid_usage";
  }
  return "transport";
}

function retryAfterMilliseconds(value: string | null): number | null {
  if (!value) return null;
  const seconds = Number(value);
  if (Number.isFinite(seconds) && seconds >= 0) return Math.round(seconds * 1_000);
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? Math.max(0, timestamp - Date.now()) : null;
}

export class StationZeroV3DeepSeekProviderPool {
  readonly providerId: string;
  readonly timeoutMs: number;
  readonly maxTokens: number;
  readonly temperature: number;
  readonly thinkingMode: StationZeroV3DeepSeekThinkingMode;
  readonly reasoningEffort: "high" | "max";
  readonly retryBaseDelayMs: number;
  private readonly configuredMaximumAttempts: number | null;
  private readonly credentialPool: StationZeroV3DeepSeekCredentialPool;
  private readonly fetchImplementation: typeof fetch;
  private readonly calls: StationZeroV3DeepSeekCallEvidence[] = [];
  private nextCall = 0;

  get maximumAttempts(): number {
    return this.configuredMaximumAttempts ?? Math.max(4, this.credentialPool.usableSize * 2);
  }

  constructor(options: StationZeroV3DeepSeekProviderOptions) {
    const sources = options.credentialSources ?? options.secretPaths;
    if (!Array.isArray(sources) || sources.length === 0) {
      throw new TypeError("at least one DeepSeek credential source is required");
    }
    this.timeoutMs = options.timeoutMs ?? 60_000;
    this.thinkingMode = options.thinkingMode ?? "disabled";
    this.reasoningEffort = options.reasoningEffort ?? "high";
    this.maxTokens = options.maxTokens ?? (this.thinkingMode === "enabled" ? 2_048 : 512);
    this.temperature = options.temperature ?? 0.1;
    const maximumConcurrency = options.maximumConcurrencyPerCredential ?? 4;
    this.configuredMaximumAttempts = options.maximumAttempts ?? null;
    this.retryBaseDelayMs = options.retryBaseDelayMs ?? 1_000;
    if (!Number.isSafeInteger(this.timeoutMs) || this.timeoutMs < 1_000) throw new TypeError("DeepSeek timeout must be at least 1000 ms");
    if (!Number.isSafeInteger(this.maxTokens) || this.maxTokens < 128) throw new TypeError("DeepSeek maxTokens must be at least 128");
    if (!Number.isFinite(this.temperature) || this.temperature < 0 || this.temperature > 2) throw new TypeError("DeepSeek temperature must be between zero and two");
    if (this.configuredMaximumAttempts !== null && (!Number.isSafeInteger(this.configuredMaximumAttempts) || this.configuredMaximumAttempts < 1)) {
      throw new TypeError("DeepSeek maximumAttempts must be a positive integer");
    }
    if (!Number.isSafeInteger(this.retryBaseDelayMs) || this.retryBaseDelayMs < 0) throw new TypeError("DeepSeek retryBaseDelayMs must be a non-negative integer");
    this.credentialPool = new StationZeroV3DeepSeekCredentialPool({
      sources,
      defaultMaximumConcurrency: maximumConcurrency,
      cooldownBaseMs: this.retryBaseDelayMs,
      ...(options.credentialReloadIntervalMs === undefined ? {} : { reloadIntervalMs: options.credentialReloadIntervalMs }),
      ...(options.credentialCooldownMaximumMs === undefined ? {} : { cooldownMaximumMs: options.credentialCooldownMaximumMs }),
    });
    const identity = this.credentialPool.identity();
    this.providerId = `deepseek-station-zero-v3-v1:${identity.provider}/${identity.model}:${this.thinkingMode}`;
    this.fetchImplementation = options.fetchImplementation ?? fetch;
  }

  providerFactory(): StationZeroV3AgentProviderFactory {
    const provider = new StationZeroV3DeepSeekAgentProvider(this);
    return () => provider;
  }

  evidenceSnapshot(): StationZeroV3DeepSeekEvidenceSnapshot {
    this.credentialPool.refresh(false);
    const credentialPool = this.credentialPool.snapshot();
    return {
      schemaVersion: 1,
      kind: "ordivon.game.station-zero-v3-deepseek-evidence",
      providerId: this.providerId,
      thinkingMode: this.thinkingMode,
      maxTokens: this.maxTokens,
      maximumAttempts: this.maximumAttempts,
      retryBaseDelayMs: this.retryBaseDelayMs,
      credentialPool,
      credentials: credentialPool.credentials,
      calls: structuredClone(this.calls),
    };
  }

  resetEvidence(): void {
    this.calls.length = 0;
  }

  async decide(context: StationZeroV3AgentContext): Promise<StationZeroV3AgentDecision> {
    if (context.candidates.length === 0) throw new ProviderAdapterError("invalid_output", `Agent Context has no Candidate: ${context.contextId}`);
    this.credentialPool.refresh(false);
    const attemptedFingerprints = new Set<string>();
    let lastError: unknown = null;
    for (let attempt = 1; attempt <= this.maximumAttempts; attempt += 1) {
      const usableFingerprints = this.credentialPool.usableFingerprints();
      const usableCredentials = usableFingerprints.length;
      if (usableCredentials === 0) throw new ProviderAdapterError("unavailable", "No usable DeepSeek credential remains");
      const attemptedUsable = usableFingerprints.filter((fingerprint) => attemptedFingerprints.has(fingerprint)).length;
      if (attemptedUsable >= usableCredentials) {
        attemptedFingerprints.clear();
        const cycle = Math.floor((attempt - 1) / usableCredentials);
        const jitter = [...context.actor.actorId].reduce((sum, character) => sum + character.charCodeAt(0), context.worldRevision) % Math.max(1, this.retryBaseDelayMs);
        await new Promise((resolveDelay) => setTimeout(resolveDelay, this.retryBaseDelayMs * Math.max(1, cycle) + jitter));
      }
      const credential = await this.credentialPool.select(attemptedFingerprints);
      attemptedFingerprints.add(credential.fingerprint);
      try {
        return await this.attempt(context, credential, attempt);
      } catch (error) {
        lastError = error;
      }
    }
    if (lastError instanceof Error) throw lastError;
    throw new ProviderAdapterError("unavailable", "Every DeepSeek credential failed without a retained Error");
  }

  private async attempt(
    context: StationZeroV3AgentContext,
    credential: StationZeroV3DeepSeekCredentialHandle,
    attempt: number,
  ): Promise<StationZeroV3AgentDecision> {
    return await credential.run(async () => {
      const callId = `deepseek-call:${++this.nextCall}`;
      const startedAt = new Date().toISOString();
      const started = performance.now();
      const requestBody = JSON.stringify({
        model: credential.model,
        messages: [
          { role: "system", content: SYSTEM_PROMPT },
          { role: "user", content: JSON.stringify(compactContext(context)) },
        ],
        thinking: { type: this.thinkingMode },
        ...(this.thinkingMode === "enabled"
          ? { reasoning_effort: this.reasoningEffort }
          : { temperature: this.temperature }),
        max_tokens: this.maxTokens,
        response_format: { type: "json_object" },
        stream: false,
      });
      let retryAfterMs: number | null = null;
      let metadata: AttemptMetadata = {
        httpStatus: null,
        reportedModel: null,
        finishReason: null,
        responseBytes: 0,
        promptTokens: 0,
        completionTokens: 0,
        reasoningTokens: 0,
        totalTokens: 0,
        cacheHitTokens: 0,
      };
      try {
        const response = await this.fetchImplementation(`${credential.baseUrl}/chat/completions`, {
          method: "POST",
          headers: {
            authorization: `Bearer ${credential.apiKey}`,
            "content-type": "application/json",
          },
          body: requestBody,
          signal: AbortSignal.timeout(this.timeoutMs),
        });
        const responseText = await response.text();
        metadata.httpStatus = response.status;
        retryAfterMs = retryAfterMilliseconds(response.headers.get("retry-after"));
        metadata.responseBytes = Buffer.byteLength(responseText);
        if (!response.ok) {
          throw new ProviderAdapterError("process_failed", `DeepSeek HTTP ${response.status}: ${responseText.slice(0, 500)}`);
        }
        let payload: unknown;
        try {
          payload = JSON.parse(responseText);
        } catch (error) {
          throw new ProviderAdapterError("invalid_output", "DeepSeek HTTP response is not JSON", { cause: error });
        }
        if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
          throw new ProviderAdapterError("invalid_output", "DeepSeek HTTP response must be one JSON object");
        }
        const record = payload as Record<string, unknown>;
        metadata.reportedModel = typeof record.model === "string" ? record.model : null;
        if (metadata.reportedModel !== credential.model) {
          throw new ProviderAdapterError("invalid_usage", `DeepSeek reported model ${metadata.reportedModel ?? "missing"} instead of ${credential.model}`);
        }
        const usage = record.usage && typeof record.usage === "object" && !Array.isArray(record.usage)
          ? record.usage as DeepSeekUsage
          : undefined;
        metadata = { ...metadata, ...metadataFromUsage(usage) };
        const choices = Array.isArray(record.choices) ? record.choices : [];
        const choice = choices[0];
        if (!choice || typeof choice !== "object" || Array.isArray(choice)) {
          throw new ProviderAdapterError("invalid_output", "DeepSeek response has no first Choice");
        }
        const choiceRecord = choice as Record<string, unknown>;
        metadata.finishReason = typeof choiceRecord.finish_reason === "string" ? choiceRecord.finish_reason : null;
        if (metadata.finishReason !== "stop") {
          throw new ProviderAdapterError("invalid_output", `DeepSeek completion ended with ${metadata.finishReason ?? "no finish reason"}`);
        }
        const message = choiceRecord.message;
        if (!message || typeof message !== "object" || Array.isArray(message)) {
          throw new ProviderAdapterError("invalid_output", "DeepSeek response has no Assistant message");
        }
        const content = (message as Record<string, unknown>).content;
        if (typeof content !== "string" || !content.trim()) {
          throw new ProviderAdapterError("invalid_output", "DeepSeek Assistant content is empty");
        }
        const body = parseDecisionBody(context, content);
        const decision: StationZeroV3AgentDecision = {
          schemaVersion: 1,
          kind: "ordivon.game.station-zero-v3-agent-decision",
          contextId: context.contextId,
          contextDigest: context.contextDigest,
          actorId: context.actor.actorId,
          factionId: context.factionId,
          candidateId: body.candidateId,
          directiveId: body.directiveId,
          rationale: body.rationale,
          confidence: body.confidence,
          providerId: this.providerId,
        };
        assertStationZeroV3AgentDecision(context, decision);
        const latencyMs = Math.round(performance.now() - started);
        this.credentialPool.reportSuccess(credential, latencyMs);
        this.calls.push({
          callId,
          contextId: context.contextId,
          actorId: context.actor.actorId,
          factionId: context.factionId,
          credentialId: credential.credentialId,
          attempt,
          startedAt,
          latencyMs,
          outcome: "success",
          ...metadata,
          requestBytes: Buffer.byteLength(requestBody),
          candidateId: decision.candidateId,
          directiveId: decision.directiveId,
          errorCode: null,
          errorMessage: null,
        });
        return decision;
      } catch (error) {
        const timeout = error instanceof DOMException && error.name === "TimeoutError";
        const normalized = timeout
          ? new ProviderAdapterError("timeout", `DeepSeek request exceeded ${this.timeoutMs} ms`, { cause: error })
          : error instanceof ProviderAdapterError
            ? error
            : new ProviderAdapterError(
              "unavailable",
              `DeepSeek request failed before a valid Decision: ${error instanceof Error ? `${error.name}: ${error.message}` : String(error)}`,
              { cause: error },
            );
        const sanitized = normalized.message.replaceAll(credential.apiKey, "<redacted>").slice(0, 500);
        this.credentialPool.reportFailure(credential, failureKind(normalized, metadata.httpStatus), retryAfterMs);
        this.calls.push({
          callId,
          contextId: context.contextId,
          actorId: context.actor.actorId,
          factionId: context.factionId,
          credentialId: credential.credentialId,
          attempt,
          startedAt,
          latencyMs: Math.round(performance.now() - started),
          outcome: outcomeForError(normalized, metadata.httpStatus),
          ...metadata,
          requestBytes: Buffer.byteLength(requestBody),
          candidateId: null,
          directiveId: null,
          errorCode: normalized.code,
          errorMessage: sanitized,
        });
        throw normalized;
      }
    });
  }
}

export class StationZeroV3DeepSeekAgentProvider implements StationZeroV3AgentProvider {
  readonly providerId: string;
  private readonly pool: StationZeroV3DeepSeekProviderPool;

  constructor(pool: StationZeroV3DeepSeekProviderPool) {
    this.pool = pool;
    this.providerId = pool.providerId;
  }

  decide(context: StationZeroV3AgentContext): Promise<StationZeroV3AgentDecision> {
    return this.pool.decide(context);
  }
}

