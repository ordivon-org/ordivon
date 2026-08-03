import { createHash } from "node:crypto";
import { readFileSync, readdirSync, realpathSync, statSync } from "node:fs";
import { basename, extname, resolve } from "node:path";

import { ProviderAdapterError } from "../team/provider-runtime.ts";

export interface StationZeroV3DeepSeekCredentialConfig {
  schemaVersion: 1;
  id?: string;
  enabled?: boolean;
  apiKey: string;
  baseUrl: string;
  model: string;
  provider: string;
  maximumConcurrency?: number;
  weight?: number;
}

export type StationZeroV3DeepSeekCredentialFailureKind =
  | "rate_limit"
  | "authentication"
  | "server"
  | "timeout"
  | "transport"
  | "invalid_output"
  | "invalid_usage";

export interface StationZeroV3DeepSeekCredentialPoolOptions {
  sources: string[];
  defaultMaximumConcurrency: number;
  reloadIntervalMs?: number;
  cooldownBaseMs?: number;
  cooldownMaximumMs?: number;
}

export interface StationZeroV3DeepSeekCredentialSnapshot {
  credentialId: string;
  sourceId: string;
  provider: string;
  model: string;
  baseUrl: string;
  maximumConcurrency: number;
  weight: number;
  active: number;
  queued: number;
  reserved: number;
  successes: number;
  failures: number;
  consecutiveFailures: number;
  averageLatencyMs: number | null;
  cooldownUntil: string | null;
  quarantined: boolean;
  quarantineReason: string | null;
}

export interface StationZeroV3DeepSeekCredentialPoolSnapshot {
  sources: string[];
  reloadIntervalMs: number;
  lastReloadAt: string;
  discoveredFiles: number;
  duplicateCredentialsSkipped: number;
  discoveryErrors: Array<{ sourceId: string; message: string }>;
  credentials: StationZeroV3DeepSeekCredentialSnapshot[];
}

interface ParsedCredential {
  credentialId: string;
  sourcePath: string;
  sourceId: string;
  fingerprint: string;
  apiKey: string;
  baseUrl: string;
  model: string;
  provider: string;
  maximumConcurrency: number;
  weight: number;
}

interface CredentialHealth {
  successes: number;
  failures: number;
  consecutiveFailures: number;
  averageLatencyMs: number | null;
  cooldownUntilMs: number;
  quarantined: boolean;
  quarantineReason: string | null;
  virtualRuntime: number;
}

export interface StationZeroV3DeepSeekCredentialHandle {
  readonly credentialId: string;
  readonly sourceId: string;
  readonly fingerprint: string;
  readonly apiKey: string;
  readonly baseUrl: string;
  readonly model: string;
  readonly provider: string;
  readonly maximumConcurrency: number;
  readonly weight: number;
  readonly active: number;
  readonly queued: number;
  readonly reserved: number;
  run<T>(operation: () => Promise<T>): Promise<T>;
}

class AsyncSemaphore {
  private activeCount = 0;
  private readonly queue: Array<() => void> = [];
  readonly maximum: number;

  constructor(maximum: number) {
    if (!Number.isSafeInteger(maximum) || maximum < 1) throw new TypeError("maximum concurrency must be a positive integer");
    this.maximum = maximum;
  }

  get active(): number {
    return this.activeCount;
  }

  get queued(): number {
    return this.queue.length;
  }

  private async acquire(): Promise<void> {
    if (this.activeCount < this.maximum) {
      this.activeCount += 1;
      return;
    }
    await new Promise<void>((resolveQueue) => this.queue.push(resolveQueue));
  }

  private release(): void {
    const next = this.queue.shift();
    if (next) {
      next();
      return;
    }
    this.activeCount -= 1;
  }

  async run<T>(operation: () => Promise<T>): Promise<T> {
    await this.acquire();
    try {
      return await operation();
    } finally {
      this.release();
    }
  }
}

class LoadedCredential implements StationZeroV3DeepSeekCredentialHandle {
  readonly credentialId: string;
  readonly sourcePath: string;
  readonly sourceId: string;
  readonly fingerprint: string;
  readonly apiKey: string;
  readonly baseUrl: string;
  readonly model: string;
  readonly provider: string;
  readonly maximumConcurrency: number;
  readonly weight: number;
  readonly semaphore: AsyncSemaphore;
  readonly health: CredentialHealth;
  private reservedCount = 0;

  constructor(parsed: ParsedCredential, retainedHealth?: CredentialHealth, initialVirtualRuntime = 0) {
    this.credentialId = parsed.credentialId;
    this.sourcePath = parsed.sourcePath;
    this.sourceId = parsed.sourceId;
    this.fingerprint = parsed.fingerprint;
    this.apiKey = parsed.apiKey;
    this.baseUrl = parsed.baseUrl;
    this.model = parsed.model;
    this.provider = parsed.provider;
    this.maximumConcurrency = parsed.maximumConcurrency;
    this.weight = parsed.weight;
    this.semaphore = new AsyncSemaphore(parsed.maximumConcurrency);
    this.health = retainedHealth ?? {
      successes: 0,
      failures: 0,
      consecutiveFailures: 0,
      averageLatencyMs: null,
      cooldownUntilMs: 0,
      quarantined: false,
      quarantineReason: null,
      virtualRuntime: initialVirtualRuntime,
    };
  }

  get active(): number {
    return this.semaphore.active;
  }

  get queued(): number {
    return this.semaphore.queued;
  }

  get reserved(): number {
    return this.reservedCount;
  }

  reserve(): void {
    this.reservedCount += 1;
  }

  releaseReservation(): void {
    if (this.reservedCount > 0) this.reservedCount -= 1;
  }

  run<T>(operation: () => Promise<T>): Promise<T> {
    this.releaseReservation();
    return this.semaphore.run(operation);
  }
}

function requiredString(value: unknown, label: string): string {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} must be a non-empty string`);
  return value.trim();
}

function optionalPositiveInteger(value: unknown, fallback: number, label: string): number {
  if (value === undefined) return fallback;
  if (!Number.isSafeInteger(value) || (value as number) < 1) throw new TypeError(`${label} must be a positive integer`);
  return value as number;
}

function optionalPositiveNumber(value: unknown, fallback: number, label: string): number {
  if (value === undefined) return fallback;
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) throw new TypeError(`${label} must be positive`);
  return value;
}

function sourceId(path: string): string {
  return basename(path);
}

function credentialFileName(name: string): boolean {
  const normalized = name.toLowerCase();
  return normalized.startsWith("deepseek") && normalized.endsWith(".json");
}

function discoverFiles(sources: string[]): {
  files: string[];
  errors: Array<{ sourceId: string; message: string }>;
} {
  const files = new Set<string>();
  const errors: Array<{ sourceId: string; message: string }> = [];
  for (const source of sources) {
    const absolute = resolve(source);
    let metadata;
    try {
      metadata = statSync(absolute);
    } catch (error) {
      errors.push({ sourceId: absolute, message: sanitizedDiscoveryMessage(error) });
      continue;
    }
    if (metadata.isFile()) {
      try {
        files.add(realpathSync(absolute));
      } catch (error) {
        errors.push({ sourceId: absolute, message: sanitizedDiscoveryMessage(error) });
      }
      continue;
    }
    if (!metadata.isDirectory()) {
      errors.push({ sourceId: absolute, message: "DeepSeek credential source is neither a file nor directory" });
      continue;
    }
    try {
      for (const entry of readdirSync(absolute, { withFileTypes: true })) {
        if (!entry.isFile() || !credentialFileName(entry.name)) continue;
        try {
          files.add(realpathSync(resolve(absolute, entry.name)));
        } catch (error) {
          errors.push({ sourceId: entry.name, message: sanitizedDiscoveryMessage(error) });
        }
      }
    } catch (error) {
      errors.push({ sourceId: absolute, message: sanitizedDiscoveryMessage(error) });
    }
  }
  return { files: [...files].sort(), errors };
}

function parseCredentialFile(path: string, defaultMaximumConcurrency: number): ParsedCredential | null {
  const file = statSync(path);
  if (!file.isFile()) throw new TypeError(`DeepSeek credential path is not a file: ${path}`);
  if ((file.mode & 0o077) !== 0) {
    throw new ProviderAdapterError("unavailable", `DeepSeek credential file must not be readable by group or others: ${path}`);
  }
  let value: unknown;
  try {
    value = JSON.parse(readFileSync(path, "utf8"));
  } catch (error) {
    throw new ProviderAdapterError("unavailable", `DeepSeek credential file is invalid JSON: ${path}`, { cause: error });
  }
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new TypeError(`DeepSeek credential must be one JSON object: ${path}`);
  const record = value as Record<string, unknown>;
  if (record.schemaVersion !== 1) throw new TypeError(`Unsupported DeepSeek credential schema: ${path}`);
  if (record.enabled === false) return null;
  if (record.enabled !== undefined && typeof record.enabled !== "boolean") throw new TypeError(`enabled must be boolean: ${path}`);
  const baseUrl = requiredString(record.baseUrl, "baseUrl").replace(/\/$/, "");
  if (!/^https?:\/\//.test(baseUrl)) throw new TypeError(`DeepSeek baseUrl must be HTTP(S): ${path}`);
  const apiKey = requiredString(record.apiKey, "apiKey");
  const provider = requiredString(record.provider, "provider");
  const model = requiredString(record.model, "model");
  const configuredId = record.id === undefined ? basename(path, extname(path)) : requiredString(record.id, "id");
  const maximumConcurrency = optionalPositiveInteger(record.maximumConcurrency, defaultMaximumConcurrency, "maximumConcurrency");
  const weight = optionalPositiveNumber(record.weight, 1, "weight");
  const fingerprint = createHash("sha256")
    .update(`${provider}\u0000${apiKey}`)
    .digest("hex");
  return {
    credentialId: configuredId,
    sourcePath: path,
    sourceId: sourceId(path),
    fingerprint,
    apiKey,
    baseUrl,
    model,
    provider,
    maximumConcurrency,
    weight,
  };
}

function sanitizedDiscoveryMessage(error: unknown): string {
  return (error instanceof Error ? error.message : String(error)).slice(0, 500);
}

function stableUniqueCredentialIds(credentials: ParsedCredential[]): ParsedCredential[] {
  const counts = new Map<string, number>();
  return credentials.map((credential) => {
    const count = (counts.get(credential.credentialId) ?? 0) + 1;
    counts.set(credential.credentialId, count);
    if (count === 1) return credential;
    return { ...credential, credentialId: `${credential.credentialId}-${count}` };
  });
}

function delay(ms: number): Promise<void> {
  return ms <= 0 ? Promise.resolve() : new Promise((resolveDelay) => setTimeout(resolveDelay, ms));
}

export class StationZeroV3DeepSeekCredentialPool {
  readonly sources: string[];
  readonly defaultMaximumConcurrency: number;
  readonly reloadIntervalMs: number;
  readonly cooldownBaseMs: number;
  readonly cooldownMaximumMs: number;
  private credentials: LoadedCredential[] = [];
  private lastReloadAtMs = 0;
  private discoveredFiles = 0;
  private duplicateCredentialsSkipped = 0;
  private discoveryErrors: Array<{ sourceId: string; message: string }> = [];
  private selectionCursor = 0;

  constructor(options: StationZeroV3DeepSeekCredentialPoolOptions) {
    if (!Array.isArray(options.sources) || options.sources.length === 0) throw new TypeError("at least one DeepSeek credential source is required");
    if (!Number.isSafeInteger(options.defaultMaximumConcurrency) || options.defaultMaximumConcurrency < 1) {
      throw new TypeError("defaultMaximumConcurrency must be a positive integer");
    }
    this.sources = [...new Set(options.sources.map((source) => resolve(source)))];
    this.defaultMaximumConcurrency = options.defaultMaximumConcurrency;
    this.reloadIntervalMs = options.reloadIntervalMs ?? 15_000;
    this.cooldownBaseMs = options.cooldownBaseMs ?? 1_000;
    this.cooldownMaximumMs = options.cooldownMaximumMs ?? 30_000;
    if (!Number.isSafeInteger(this.reloadIntervalMs) || this.reloadIntervalMs < 0) throw new TypeError("reloadIntervalMs must be non-negative");
    if (!Number.isSafeInteger(this.cooldownBaseMs) || this.cooldownBaseMs < 0) throw new TypeError("cooldownBaseMs must be non-negative");
    if (!Number.isSafeInteger(this.cooldownMaximumMs) || this.cooldownMaximumMs < this.cooldownBaseMs) {
      throw new TypeError("cooldownMaximumMs must be at least cooldownBaseMs");
    }
    this.refresh(true);
  }

  get size(): number {
    return this.credentials.length;
  }

  get usableSize(): number {
    return this.credentials.filter((credential) => !credential.health.quarantined).length;
  }

  usableFingerprints(): string[] {
    return this.credentials
      .filter((credential) => !credential.health.quarantined)
      .map((credential) => credential.fingerprint);
  }

  identity(): { provider: string; model: string } {
    const first = this.credentials[0];
    if (!first) throw new ProviderAdapterError("unavailable", "DeepSeek credential pool is empty");
    return { provider: first.provider, model: first.model };
  }

  refresh(force = false): boolean {
    const now = Date.now();
    if (!force && now - this.lastReloadAtMs < this.reloadIntervalMs) return false;
    const retainedByFingerprint = new Map(this.credentials.map((credential) => [credential.fingerprint, credential]));
    const discovery = discoverFiles(this.sources);
    const files = discovery.files;
    const errors: Array<{ sourceId: string; message: string }> = [...discovery.errors];
    const parsed: ParsedCredential[] = [];
    for (const path of files) {
      try {
        const credential = parseCredentialFile(path, this.defaultMaximumConcurrency);
        if (credential) parsed.push(credential);
      } catch (error) {
        errors.push({ sourceId: sourceId(path), message: sanitizedDiscoveryMessage(error) });
      }
    }
    const expectedProvider = this.credentials[0]?.provider ?? parsed[0]?.provider ?? null;
    const expectedModel = this.credentials[0]?.model ?? parsed[0]?.model ?? null;
    const compatible = parsed.filter((credential) => {
      if (credential.provider === expectedProvider && credential.model === expectedModel) return true;
      errors.push({
        sourceId: credential.sourceId,
        message: `credential uses incompatible ${credential.provider}/${credential.model}; expected ${expectedProvider}/${expectedModel}`,
      });
      return false;
    });
    const grouped = Object.groupBy(compatible, (credential) => credential.fingerprint);
    const deduplicated = new Map<string, ParsedCredential>();
    for (const [fingerprint, candidates] of Object.entries(grouped)) {
      const retainedSourcePath = retainedByFingerprint.get(fingerprint)?.sourcePath;
      const selected = candidates?.find((credential) => credential.sourcePath === retainedSourcePath) ??
        [...(candidates ?? [])].sort((left, right) => left.sourcePath.localeCompare(right.sourcePath))[0];
      if (selected) deduplicated.set(fingerprint, selected);
    }
    const duplicateCount = compatible.length - deduplicated.size;
    const unique = stableUniqueCredentialIds([...deduplicated.values()]);
    const retainedRuntime = this.credentials.map((credential) => credential.health.virtualRuntime);
    const initialVirtualRuntime = retainedRuntime.length > 0
      ? retainedRuntime.reduce((sum, value) => sum + value, 0) / retainedRuntime.length
      : 0;
    const loaded = unique.map((credential) => {
      const retained = retainedByFingerprint.get(credential.fingerprint);
      if (
        retained &&
        retained.maximumConcurrency === credential.maximumConcurrency &&
        retained.weight === credential.weight &&
        retained.credentialId === credential.credentialId
      ) return retained;
      return new LoadedCredential(credential, retained?.health, initialVirtualRuntime);
    });
    if (loaded.length === 0) {
      this.credentials = [];
      this.discoveredFiles = files.length;
      this.duplicateCredentialsSkipped = duplicateCount;
      this.discoveryErrors = errors.length > 0 ? errors : [{ sourceId: "sources", message: "no enabled compatible credential remains" }];
      this.lastReloadAtMs = now;
      const detail = this.discoveryErrors.map((entry) => `${entry.sourceId}: ${entry.message}`).join("; ");
      throw new ProviderAdapterError("unavailable", `No valid enabled DeepSeek credentials were discovered: ${detail}`);
    }
    this.credentials = loaded;
    this.discoveredFiles = files.length;
    this.duplicateCredentialsSkipped = duplicateCount;
    this.discoveryErrors = errors;
    this.lastReloadAtMs = now;
    return true;
  }

  async select(excludedFingerprints: Set<string> = new Set()): Promise<StationZeroV3DeepSeekCredentialHandle> {
    this.refresh(false);
    while (true) {
      const now = Date.now();
      const nonQuarantined = this.credentials.filter((credential) => !credential.health.quarantined);
      if (nonQuarantined.length === 0) throw new ProviderAdapterError("unavailable", "Every DeepSeek credential is quarantined or unavailable");
      const untried = nonQuarantined.filter((credential) => !excludedFingerprints.has(credential.fingerprint));
      if (untried.length === 0) throw new ProviderAdapterError("unavailable", "Every usable DeepSeek credential was already attempted in this retry cycle");
      const eligible = untried.filter((credential) => credential.health.cooldownUntilMs <= now);
      if (eligible.length === 0) {
        const earliest = Math.min(...untried.map((credential) => credential.health.cooldownUntilMs));
        await delay(Math.max(1, earliest - now));
        this.refresh(false);
        continue;
      }
      const minimumRuntime = Math.min(...nonQuarantined.map((credential) => credential.health.virtualRuntime));
      if (minimumRuntime > 1_000_000) {
        for (const credential of nonQuarantined) credential.health.virtualRuntime -= minimumRuntime;
      }
      const ordered = [...eligible].sort((left, right) => left.credentialId.localeCompare(right.credentialId));
      const cursor = this.selectionCursor++ % ordered.length;
      const tieRank = new Map(ordered.map((credential, index) => [credential.fingerprint, (index - cursor + ordered.length) % ordered.length]));
      ordered.sort((left, right) => {
        const leftLoad = (left.active + left.queued + left.reserved) / left.maximumConcurrency;
        const rightLoad = (right.active + right.queued + right.reserved) / right.maximumConcurrency;
        const leftLatency = left.health.averageLatencyMs ?? 0;
        const rightLatency = right.health.averageLatencyMs ?? 0;
        const leftScore = left.health.virtualRuntime + leftLoad * 4 + left.health.consecutiveFailures * 3 + leftLatency / 30_000;
        const rightScore = right.health.virtualRuntime + rightLoad * 4 + right.health.consecutiveFailures * 3 + rightLatency / 30_000;
        if (leftScore !== rightScore) return leftScore - rightScore;
        return (tieRank.get(left.fingerprint) ?? 0) - (tieRank.get(right.fingerprint) ?? 0);
      });
      const selected = ordered[0]!;
      selected.health.virtualRuntime += 1 / selected.weight;
      selected.reserve();
      return selected;
    }
  }

  reportSuccess(handle: StationZeroV3DeepSeekCredentialHandle, latencyMs: number): void {
    const credential = this.credentials.find((entry) => entry.fingerprint === handle.fingerprint);
    if (!credential) return;
    credential.health.successes += 1;
    credential.health.consecutiveFailures = 0;
    credential.health.averageLatencyMs = credential.health.averageLatencyMs === null
      ? latencyMs
      : Math.round(credential.health.averageLatencyMs * 0.8 + latencyMs * 0.2);
  }

  reportFailure(
    handle: StationZeroV3DeepSeekCredentialHandle,
    kind: StationZeroV3DeepSeekCredentialFailureKind,
    retryAfterMs?: number | null,
  ): void {
    const credential = this.credentials.find((entry) => entry.fingerprint === handle.fingerprint);
    if (!credential) return;
    credential.health.failures += 1;
    if (kind === "invalid_output") return;
    credential.health.consecutiveFailures += 1;
    if (kind === "authentication" || kind === "invalid_usage") {
      credential.health.quarantined = true;
      credential.health.quarantineReason = kind;
      credential.health.cooldownUntilMs = Number.MAX_SAFE_INTEGER;
      return;
    }
    const exponential = Math.min(
      this.cooldownMaximumMs,
      this.cooldownBaseMs * 2 ** Math.min(8, Math.max(0, credential.health.consecutiveFailures - 1)),
    );
    const cooldown = kind === "rate_limit" && retryAfterMs !== null && retryAfterMs !== undefined
      ? Math.min(this.cooldownMaximumMs, Math.max(exponential, retryAfterMs))
      : exponential;
    credential.health.cooldownUntilMs = Math.max(credential.health.cooldownUntilMs, Date.now() + cooldown);
  }

  snapshot(): StationZeroV3DeepSeekCredentialPoolSnapshot {
    const now = Date.now();
    return {
      sources: [...this.sources],
      reloadIntervalMs: this.reloadIntervalMs,
      lastReloadAt: new Date(this.lastReloadAtMs).toISOString(),
      discoveredFiles: this.discoveredFiles,
      duplicateCredentialsSkipped: this.duplicateCredentialsSkipped,
      discoveryErrors: structuredClone(this.discoveryErrors),
      credentials: this.credentials.map((credential) => ({
        credentialId: credential.credentialId,
        sourceId: credential.sourceId,
        provider: credential.provider,
        model: credential.model,
        baseUrl: credential.baseUrl,
        maximumConcurrency: credential.maximumConcurrency,
        weight: credential.weight,
        active: credential.active,
        queued: credential.queued,
        reserved: credential.reserved,
        successes: credential.health.successes,
        failures: credential.health.failures,
        consecutiveFailures: credential.health.consecutiveFailures,
        averageLatencyMs: credential.health.averageLatencyMs,
        cooldownUntil: credential.health.cooldownUntilMs > now && credential.health.cooldownUntilMs < Number.MAX_SAFE_INTEGER
          ? new Date(credential.health.cooldownUntilMs).toISOString()
          : null,
        quarantined: credential.health.quarantined,
        quarantineReason: credential.health.quarantineReason,
      })),
    };
  }
}

export function stationZeroV3DeepSeekCredentialSources(value: string | undefined): string[] {
  const source = value?.trim() ? value : "/root/.config/ordivon/secrets";
  const sources = source.split(",").map((entry) => entry.trim()).filter(Boolean);
  if (sources.length === 0) throw new TypeError("no DeepSeek credential source was configured");
  return [...new Set(sources)];
}

/** @deprecated Use stationZeroV3DeepSeekCredentialSources. Directories and files are both accepted. */
export const stationZeroV3DeepSeekSecretPaths = stationZeroV3DeepSeekCredentialSources;
