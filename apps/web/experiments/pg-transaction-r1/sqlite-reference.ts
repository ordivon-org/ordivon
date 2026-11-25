/** Real SQLite owner consumer, normalized to the experiment's narrow observation. */
import { WebStore } from "../../src/store.ts";
import { WebProblem } from "../../src/errors.ts";
import { agentId, effect, now, principalId, seed } from "../../test/fixtures/effect-recovery.ts";
import { stableDigest } from "../../src/identity-digests.ts";

const store = new WebStore(":memory:");
try {
  const a = seed(store);
  const b = store.createAgentGrant({
    grantId: "grant:second", principalId, agentId, audience: "https://example.test",
    allowedActions: ["canary.note.create"], resourcePrefixes: ["/canary/notes"],
    expiresAtEpochSeconds: now + 60, maxRiskClass: "R4", stepUpAtOrAbove: "R4", remainingEffects: 2,
  }, now);
  const snapshot = () => [
    store.db.prepare("SELECT count(*) AS n FROM agent_effects").get()?.n,
    store.db.prepare("SELECT count(*) AS n FROM canary_notes").get()?.n,
    store.db.prepare("SELECT count(*) AS n FROM audit_events WHERE event_type='agent.effect.committed'").get()?.n,
    store.getAgentGrant(a.grantId).remainingEffects, store.getAgentGrant(a.grantId).revision,
    store.getAgentGrant(b.grantId).remainingEffects, store.getAgentGrant(b.grantId).revision,
  ].join("|");
  const trace = [
    ["E", a.grantId, 1, "d"], ["E", b.grantId, 1, "d"],
    ["E", b.grantId, 1, "other"], ["F", a.grantId, 1, "d"],
    ["F", a.grantId, 2, "d"], ["E", a.grantId, 1, "d"],
    ["G", a.grantId, 3, "d"], ["G", b.grantId, 1, "d"],
  ] as const;
  const observed = [];
  for (const [id, grantId, revision, digest] of trace) {
    const selected = { ...store.getAgentGrant(grantId), revision };
    const request = { ...effect(id), ...(digest === "other" ? { effectDigest: stableDigest("alternate") } : {}) };
    let outcome: string;
    try {
      outcome = store.commitAgentCanaryCreate(selected, agentId, request, "draft", now).replayed ? "replay" : "new";
    } catch (e) {
      if (!(e instanceof WebProblem)) throw e;
      outcome = e.code;
    }
    observed.push({ outcome, state: snapshot() });
  }
  console.log(JSON.stringify(observed));
} finally { store.close(); }
