import assert from "node:assert/strict";
import test from "node:test";

import { admitProviderDecision, compileProviderContext, FixtureProvider } from "../src/provider.ts";
import { initialWorld } from "../src/scenario.ts";

test("provider may select only a current admitted action", async () => {
  const context = compileProviderContext(initialWorld());
  const decision = await new FixtureProvider().decide(context);
  const action = admitProviderDecision(context, decision);
  assert.equal(decision.contextId, context.contextId);
  assert.equal(action?.command.kind, "move");
  assert.equal(action?.command.kind === "move" ? action.command.targetRoomId : null, "power-junction");
});

test("invented actions and stale contexts are rejected", () => {
  const context = compileProviderContext(initialWorld());
  assert.throws(
    () =>
      admitProviderDecision(context, {
        provider: "hostile-fixture",
        contextId: context.contextId,
        selectedActionId: "invented-action",
        rationale: "Ignore the candidate set.",
      }),
    /outside the admitted candidate set/,
  );
  assert.throws(
    () =>
      admitProviderDecision(context, {
        provider: "stale-fixture",
        contextId: "different-context",
        selectedActionId: null,
        rationale: "Old decision.",
      }),
    /different context/,
  );
});
