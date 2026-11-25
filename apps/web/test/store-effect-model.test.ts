import assert from "node:assert/strict";
import { test } from "node:test";
import { WebStore } from "../src/store.ts";
import { WebProblem } from "../src/errors.ts";
import { stableDigest } from "../src/identity-digests.ts";
import { agentId, effect, now, seed } from "./fixtures/effect-recovery.ts";
import type { AgentEffectReceipt } from "../src/model.ts";

// Bounded exhaustive model-based test: independent state tracks only observable
// receipt identity, digest, quota and revision. No production algorithm is copied.
const commands = ["A", "B", "conflictA", "staleB", "readA"] as const;
type Command = typeof commands[number];
function* traces(depth: number, prefix: Command[] = []): Generator<Command[]> {
  if (depth === 0) { yield prefix; return; }
  for (const command of commands) yield* traces(depth - 1, [...prefix, command]);
}

test("bounded effect trace model agrees with native SQLite for every length-three trace", () => {
  let traceCount = 0;
  let stepCount = 0;
  for (const trace of traces(3)) {
    const store = new WebStore(":memory:");
    try {
      const initial = seed(store);
      const receipts = new Map<string, { digest: string; receipt: AgentEffectReceipt }>();
      for (const command of trace) {
        const key = command === "B" || command === "staleB" ? "B" : "A";
        const request = command === "conflictA" ? { ...effect(key), effectDigest: stableDigest("alternate") } : effect(key);
        const known = receipts.get(key);
        if (command === "readA") {
          assert.deepEqual(store.getAgentEffect(request.effectId), known?.receipt ?? null, trace.join("/"));
        } else {
          const selected = command === "staleB" ? initial : store.getAgentGrant(initial.grantId);
          const run = () => store.commitAgentCanaryCreate(selected, agentId, request, "draft", now);
          if (known !== undefined) {
            if (known.digest !== request.effectDigest) {
              assert.throws(run, (error: unknown) => error instanceof WebProblem && error.code === "effect-conflict", trace.join("/"));
            } else {
              assert.deepEqual(run(), { receipt: known.receipt, replayed: true }, trace.join("/"));
            }
          } else if (receipts.size === 2 || (command === "staleB" && receipts.size !== 0)) {
            assert.throws(run, (error: unknown) => error instanceof WebProblem && error.code === "agent-grant-changed", trace.join("/"));
          } else {
            const result = run();
            assert.equal(result.replayed, false, trace.join("/"));
            assert.equal(result.receipt.effectDigest, request.effectDigest);
            receipts.set(key, { digest: request.effectDigest, receipt: result.receipt });
          }
        }
        const observed = store.getAgentGrant(initial.grantId);
        assert.equal(observed.remainingEffects, 2 - receipts.size, trace.join("/"));
        assert.equal(observed.revision, initial.revision + receipts.size, trace.join("/"));
        for (const [id, value] of receipts) assert.deepEqual(store.getAgentEffect(effect(id).effectId), value.receipt);
        for (const table of ["canary_notes", "agent_effects"]) {
          assert.equal(store.db.prepare("SELECT count(*) AS n FROM " + table).get()?.n, receipts.size, trace.join("/"));
        }
        assert.equal(store.db.prepare("SELECT count(*) AS n FROM audit_events WHERE event_type = 'agent.effect.committed'").get()?.n, receipts.size);
        assert.equal(store.db.isTransaction, false);
        stepCount++;
      }
      traceCount++;
    } finally { store.close(); }
  }
  assert.equal(traceCount, 125);
  assert.equal(stepCount, 375);
});
