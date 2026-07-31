import assert from "node:assert/strict";
import test from "node:test";

import { runControlBoundaryEvaluation } from "../src/evaluation/control-boundary.ts";

test("paired control-boundary matrix admits useful action and holds invalid action", async () => {
  const report = await runControlBoundaryEvaluation();
  assert.equal(report.metrics.pairCount, 7);
  assert.equal(report.metrics.shouldActSuccess, 7);
  assert.equal(report.metrics.shouldHoldAccuracy, 7);
  assert.equal(report.metrics.preCommitCorrectHolds, 4);
  assert.equal(report.metrics.postCommitCorrectRefusals, 2);
  assert.equal(report.metrics.terminalCorrectHolds, 1);
  assert.equal(report.metrics.falseCompletions, 0);
  assert.equal(report.metrics.duplicateEffects, 0);
  assert.equal(report.dispositions.newControlPlatform, "not-required");
  assert.equal(report.dispositions.falseCompletionInvariant, "retain-in-embedded-host-authority");
  assert.equal(report.dispositions.terminalTaskInvariant, "retain-in-team-store");
  for (const pair of report.pairs) {
    assert.equal(pair.act.shouldAct, true, pair.id);
    assert.equal(pair.act.acted, true, pair.id);
    assert.equal(pair.hold.shouldAct, false, pair.id);
    assert.equal(pair.hold.acted, false, pair.id);
  }
});
