/** Deterministic identity, grant, and challenge digests without store authority. */

import { createHash } from "node:crypto";

import type { AgentGrantCreate } from "./model.ts";

export function stableDigest(value: unknown): string {
  return "sha256:" + createHash("sha256").update(JSON.stringify(value)).digest("hex");
}

export function hashToken(token: string): string {
  return createHash("sha256").update(token).digest("hex");
}

export function normalizeStrings(values: readonly string[]): string[] {
  return [...new Set(values)].sort();
}

export function grantDigest(input: AgentGrantCreate): string {
  return stableDigest({
    grantId: input.grantId,
    principalId: input.principalId,
    agentId: input.agentId,
    audience: input.audience,
    allowedActions: normalizeStrings(input.allowedActions),
    resourcePrefixes: normalizeStrings(input.resourcePrefixes),
    expiresAtEpochSeconds: input.expiresAtEpochSeconds,
    maxRiskClass: input.maxRiskClass,
    stepUpAtOrAbove: input.stepUpAtOrAbove,
  });
}
