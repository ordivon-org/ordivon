import { WebStore } from "../../src/store.ts";
import { stableDigest } from "../../src/identity-digests.ts";
import type { AgentEffectRequest, AgentGrantSnapshot } from "../../src/model.ts";

export const now = 1800000000;
export const principalId = "principal:recovery-fixture";
export const agentId = "agent:recovery-fixture";
const audience = "https://example.test";
export function seed(store: WebStore): AgentGrantSnapshot {
  store.ensurePrincipal(principalId, "recovery", "Recovery", now);
  return store.createAgentGrant({
    grantId: "grant:recovery", principalId, agentId, audience,
    allowedActions: ["canary.note.create"], resourcePrefixes: ["/canary/notes"],
    expiresAtEpochSeconds: now + 60, maxRiskClass: "R4", stepUpAtOrAbove: "R4", remainingEffects: 2,
  }, now);
}
export function effect(id: string): AgentEffectRequest {
  return {
    effectId: stableDigest(id), effectDigest: stableDigest("content"), action: "canary.note.create",
    resource: "/canary/notes", audience, riskClass: "R2", effectType: "website.canary.note.create",
  };
}
export function commit(store: WebStore, grant: AgentGrantSnapshot, id: string) {
  return store.commitAgentCanaryCreate(grant, agentId, effect(id), "draft", now);
}
