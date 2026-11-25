import assert from "node:assert/strict";
import { test } from "node:test";
import { WebStore } from "../src/store.ts";
import { stableDigest } from "../src/identity-digests.ts";
import { WebProblem } from "../src/errors.ts";

const now = 1800000000;
const principalId = "principal:receipt-fixture";
const agentId = "oauth-client:receipt-fixture";
const audience = "https://example.test";

// The fixture uses only Node's SQLite owner and no HTTP or external service.
for (const kind of ["create", "publish"] as const) {
  const receiptMutations = [
    ["valid-null", "result_json = 'null'"],
    ["wrong-note", "result_json = json_set(result_json, '$.note.content', 'other')"],
    ["different-bytes", "result_json = ' ' || result_json"],
    ["wrong-digest", "effect_digest = 'sha256:other'"],
    ["wrong-time", "committed_at = committed_at + 1"],
    ["wrong-agent", "agent_id = 'other-agent'"],
    ["wrong-action", "action = 'other-action'"],
    ["wrong-resource", "resource = '/other-resource'"],
  ] as const;
  const businessMutations = [
    ["ignore-note", kind === "create" ? "BEFORE INSERT ON canary_notes" : "BEFORE UPDATE ON canary_notes"],
    ["ignore-quota", "BEFORE UPDATE ON agent_grants"],
    ["ignore-audit", "BEFORE INSERT ON audit_events"],
    ...(kind === "publish" ? [["ignore-approval", "BEFORE UPDATE ON effect_approvals"]] as const : []),
  ] as const;
  const cases = [
    ...receiptMutations.map(([name, mutation]) => ({
      name, trigger: "AFTER INSERT ON agent_effects BEGIN UPDATE agent_effects SET "
        + mutation + " WHERE effect_id = NEW.effect_id; END",
      expectedError: "effect-receipt-mismatch",
    })),
    ...businessMutations.map(([name, mutation]) => ({
      name, trigger: mutation + " BEGIN SELECT RAISE(IGNORE); END",
      expectedError: "effect-write-not-applied",
    })),
  ];
  for (const { name, trigger, expectedError } of cases) {
    test("native " + kind + " rolls back invalid owner effect: " + name, () => {
      const store = new WebStore(":memory:");
      try {
        store.ensurePrincipal(principalId, "fixture", "Fixture", now);
        store.putCredential(principalId, {
          id: "credential:fixture", publicKey: new Uint8Array([1, 2, 3]),
          counter: 0, transports: ["internal"], deviceType: "singleDevice",
          backedUp: false,
        }, now);
        const grant = store.createAgentGrant({
          grantId: "grant:fixture", principalId, agentId, audience,
          allowedActions: ["canary.note.create", "canary.note.publish"],
          resourcePrefixes: ["/canary/notes"], expiresAtEpochSeconds: now + 60,
          maxRiskClass: "R4", stepUpAtOrAbove: "R4", remainingEffects: 2,
        }, now);
        const note = kind === "publish" ? store.createCanaryNote(principalId, "draft", now) : null;
        const effect = {
          effectId: stableDigest([kind, name]), effectDigest: stableDigest("content"),
          action: "canary.note." + kind,
          resource: note === null ? "/canary/notes" : "/canary/notes/" + note.noteId,
          audience, riskClass: "R2" as const, effectType: "website.canary.note." + kind,
        };
        if (note !== null) {
          store.putEffectApproval(principalId, "credential:fixture", effect.effectId, effect.effectDigest, now);
        }
        const commit = () => note === null
          ? store.commitAgentCanaryCreate(grant, agentId, effect, "draft", now)
          : store.commitAgentCanaryPublish(grant, agentId, effect, note.noteId, now);
        const before = store.db.prepare("SELECT COUNT(*) AS n FROM audit_events").get()?.n;
        store.db.exec("CREATE TEMP TRIGGER mutate_effect " + trigger);
        let failure: unknown;
        try { commit(); } catch (error) { failure = error; }
        assert.deepEqual({
          error: failure instanceof WebProblem ? failure.code : null,
          quota: store.getAgentGrant(grant.grantId).remainingEffects,
          revision: store.getAgentGrant(grant.grantId).revision,
          receipt: store.getAgentEffect(effect.effectId),
          notes: store.db.prepare("SELECT state FROM canary_notes").all().map(row => row.state),
          approval: note === null ? null : store.effectApproval(principalId, effect, now).verified,
          audit: store.db.prepare("SELECT COUNT(*) AS n FROM audit_events").get()?.n,
        }, {
          error: expectedError, quota: grant.remainingEffects,
          revision: grant.revision, receipt: null, notes: note === null ? [] : ["DRAFT"],
          approval: note === null ? null : true, audit: before,
        });
        store.db.exec("DROP TRIGGER mutate_effect");
        const outcome = commit();
        assert.equal(outcome.replayed, false);
        assert.deepEqual(commit(), { receipt: outcome.receipt, replayed: true });
        assert.equal(store.getAgentGrant(grant.grantId).remainingEffects, grant.remainingEffects - 1);
      } finally {
        store.close();
      }
    });
  }
}
