import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

export interface ExternalJsonModelCallEvidence {
  providerId: string;
  modelId?: string | null;
  routeId?: string | null;
  latencyMs?: number | null;
  inputTokens?: number | null;
  outputTokens?: number | null;
}

export interface ExternalJsonModelResult {
  value: Record<string, unknown>;
  evidence?: ExternalJsonModelCallEvidence;
}

export interface ExternalJsonModel {
  providerId: string;
  json(system: string, payload: unknown): Promise<ExternalJsonModelResult>;
}

function importTarget(specifier: string): string {
  if (!specifier || specifier !== specifier.trim()) throw new TypeError("external JSON model module specifier must be non-empty and trimmed");
  return specifier.startsWith(".") || specifier.startsWith("/")
    ? pathToFileURL(resolve(specifier)).href
    : specifier;
}

export async function loadExternalJsonModel(
  specifier = process.env.ORDIVON_GAME_EXTERNAL_JSON_MODEL_MODULE ?? "",
): Promise<ExternalJsonModel> {
  if (!specifier) throw new TypeError("ORDIVON_GAME_EXTERNAL_JSON_MODEL_MODULE is required; Game no longer owns model credentials or HTTP transport");
  const imported = await import(importTarget(specifier)) as Record<string, unknown>;
  const value = imported.jsonModel ?? imported.default;
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new TypeError("external JSON model module must export one object");
  const model = value as Record<string, unknown>;
  if (typeof model.providerId !== "string" || !model.providerId.trim()) throw new TypeError("external JSON model providerId is required");
  if (typeof model.json !== "function") throw new TypeError("external JSON model must expose json(system, payload)");
  return model as unknown as ExternalJsonModel;
}
