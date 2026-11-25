import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { WebStore } from "../src/store.ts";
import { WebProblem } from "../src/errors.ts";
import { stableDigest } from "../src/identity-digests.ts";
import type { AgentEffectReceipt, AgentEffectRequest } from "../src/model.ts";

const now = 1800000000;
const principalId = "principal:concurrency-fixture";
const agentId = "agent:concurrency-fixture";
const audience = "https://example.test";

for (const kind of ["create", "publish"] as const) {
  for (const scenario of ["exact", "conflict", "distinct-effect"] as const) {
    test(kind + " resolves " + scenario + " across the native writer admission boundary", () => {
      const dir = mkdtempSync(join(tmpdir(), "ordivon-effect-race-"));
      const path = join(dir, "web.sqlite");
      const first = new WebStore(path);
      const second = new WebStore(path);
      try {
        first.ensurePrincipal(principalId, "fixture", "Fixture", now);
        first.putCredential(principalId, {
          id: "credential:fixture", publicKey: new Uint8Array([1, 2, 3]),
          counter: 0, transports: ["internal"], deviceType: "singleDevice", backedUp: false,
        }, now);
        const grant = first.createAgentGrant({
          grantId: "grant:fixture", principalId, agentId, audience,
          allowedActions: ["canary.note.create", "canary.note.publish"],
          resourcePrefixes: ["/canary/notes"], expiresAtEpochSeconds: now + 60,
          maxRiskClass: "R4", stepUpAtOrAbove: "R4", remainingEffects: 2,
        }, now);
        const note = kind === "publish" ? first.createCanaryNote(principalId, "draft", now) : null;
        const effect: AgentEffectRequest = {
          effectId: stableDigest([kind, scenario]), effectDigest: stableDigest("content"),
          action: "canary.note." + kind, resource: note === null ? "/canary/notes" : "/canary/notes/" + note.noteId,
          audience, riskClass: kind === "publish" ? "R4" : "R2", effectType: "website.canary.note." + kind,
        };
        const contender = scenario === "conflict"
          ? { ...effect, effectDigest: stableDigest("other content") }
          : scenario === "distinct-effect" ? { ...effect, effectId: stableDigest(["different", kind]) } : effect;
        if (note !== null) {
          first.putEffectApproval(principalId, "credential:fixture", effect.effectId, effect.effectDigest, now);
        }
        const commit = (store: WebStore, request: AgentEffectRequest) => note === null
          ? store.commitAgentCanaryCreate(grant, agentId, request, "draft", now)
          : store.commitAgentCanaryPublish(grant, agentId, request, note.noteId, now);
        // Both handles are real connections to one on-disk WAL database.
        // The hook deterministically schedules a peer commit immediately before
        // this connection acquires the writer transaction, without mocking SQL.
        const nativeExec = second.db.exec.bind(second.db);
        const descriptor = Object.getOwnPropertyDescriptor(second.db, "exec");
        let winner: AgentEffectReceipt | undefined;
        Object.defineProperty(second.db, "exec", { configurable: true, value: (sql: string) => {
          if (sql === "BEGIN IMMEDIATE" && winner === undefined) {
            const result = commit(first, effect);
            assert.equal(result.replayed, false);
            winner = result.receipt;
          }
          nativeExec(sql);
        }});
        try {
          if (scenario === "exact") {
            const outcome = commit(second, contender);
            assert.ok(winner);
            assert.deepEqual(outcome, { receipt: winner, replayed: true });
          } else {
            const expected = scenario === "conflict" ? "effect-conflict"
              : kind === "create" ? "agent-grant-changed" : "effect-fence-rejected";
            assert.throws(() => commit(second, contender),
              (error: unknown) => error instanceof WebProblem && error.code === expected);
            assert.ok(winner);
          }
        } finally {
          if (descriptor) Object.defineProperty(second.db, "exec", descriptor);
          else Reflect.deleteProperty(second.db, "exec");
        }
        assert.deepEqual(second.getAgentEffect(effect.effectId), winner);
        assert.equal(second.getAgentGrant(grant.grantId).remainingEffects, 1);
        assert.equal(second.getAgentGrant(grant.grantId).revision, grant.revision + 1);
        assert.equal(second.db.prepare("SELECT count(*) AS n FROM canary_notes").get()?.n, 1);
        assert.equal(second.db.prepare("SELECT count(*) AS n FROM agent_effects").get()?.n, 1);
        assert.equal(second.db.prepare("SELECT count(*) AS n FROM audit_events WHERE event_type = 'agent.effect.committed'").get()?.n, 1);
        if (note !== null) assert.equal(second.effectApproval(principalId, effect, now).verified, false);
      } finally {
        second.close();
        first.close();
        rmSync(dir, { recursive: true, force: true });
      }
    });
  }
}
