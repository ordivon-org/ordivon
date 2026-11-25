import type { AgentGrantSnapshot } from "./model.ts";

export type GrantAvailability = "revoked" | "expired" | "exhausted" | "candidate";
export interface GrantObservation {
  readonly principalId: string;
  readonly displayName: string;
  readonly observedAt: number;
  readonly grants: readonly AgentGrantSnapshot[];
}

export function grantAvailability(grant: Pick<AgentGrantSnapshot, "active" | "expiresAtEpochSeconds" | "remainingEffects">, observedAt: number): GrantAvailability {
  if (!grant.active) return "revoked";
  if (grant.expiresAtEpochSeconds <= observedAt) return "expired";
  if (grant.remainingEffects <= 0) return "exhausted";
  return "candidate";
}
