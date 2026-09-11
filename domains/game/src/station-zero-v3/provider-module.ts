import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

import type { StationZeroV3AgentProviderFactory } from "./p3-model.ts";

export interface StationZeroV3ExternalProviderCallEvidence {
  callId: string;
  contextId: string;
  actorId: string;
  factionId: string;
  attempt: number;
  latencyMs: number;
  outcome: string;
  routeId: string | null;
  modelId: string | null;
  finishReason: string | null;
  inputTokens: number;
  outputTokens: number;
  reasoningTokens: number;
  totalTokens: number;
  cacheHitTokens: number;
  errorCode: string | null;
  errorMessage: string | null;
}

export interface StationZeroV3ExternalProviderEvidence {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-external-provider-evidence";
  providerId: string;
  calls: StationZeroV3ExternalProviderCallEvidence[];
  metadata?: Record<string, unknown>;
}

export interface StationZeroV3ExternalProviderModule {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-external-provider-module";
  providerId: string;
  providerFactory: StationZeroV3AgentProviderFactory;
  evidenceSnapshot?: () => StationZeroV3ExternalProviderEvidence;
}

function importTarget(specifier: string): string {
  if (!specifier || specifier !== specifier.trim()) throw new TypeError("external v3 Provider module specifier must be non-empty and trimmed");
  return specifier.startsWith(".") || specifier.startsWith("/")
    ? pathToFileURL(resolve(specifier)).href
    : specifier;
}

export function assertStationZeroV3ExternalProviderModule(value: unknown): asserts value is StationZeroV3ExternalProviderModule {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new TypeError("external v3 Provider module must export one object");
  const module = value as Record<string, unknown>;
  if (module.schemaVersion !== 1 || module.kind !== "ordivon.game.station-zero-v3-external-provider-module") {
    throw new TypeError("external v3 Provider module has an unsupported contract");
  }
  if (typeof module.providerId !== "string" || !module.providerId.trim() || module.providerId !== module.providerId.trim()) {
    throw new TypeError("external v3 Provider module providerId must be non-empty and trimmed");
  }
  if (typeof module.providerFactory !== "function") throw new TypeError("external v3 Provider module must expose providerFactory");
  if (module.evidenceSnapshot !== undefined && typeof module.evidenceSnapshot !== "function") {
    throw new TypeError("external v3 Provider module evidenceSnapshot must be a function when supplied");
  }
}

export async function loadStationZeroV3ExternalProviderModule(specifier: string): Promise<StationZeroV3ExternalProviderModule> {
  const imported = await import(importTarget(specifier)) as Record<string, unknown>;
  const value = imported.providerModule ?? imported.default;
  assertStationZeroV3ExternalProviderModule(value);
  return value;
}
