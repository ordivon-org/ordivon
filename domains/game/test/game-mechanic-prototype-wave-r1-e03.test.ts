import assert from 'node:assert/strict';
import test from 'node:test';
// @ts-expect-error JS experiment module intentionally has no TypeScript declaration.
import { exhaustiveOptimal, runWitnesses } from '../experiments/mechanic-prototype-wave-r1/e03-commitment-lag/core.js';

test('E03 lag changes the exhaustive optimum and makes anticipation mechanically useful', () => {
  const w = runWitnesses();
  assert.equal(w.optimalTraceChangesWithLag, true);
  assert.equal(w.staleViewCreatesCost, true);
  assert.equal(w.anticipationRepairsCost, true);
  assert.equal(w.gameCoreChanged, false);
  assert.equal(w.pass, true);
});

test('E03 exhaustive search still admits zero-cost play under both protocols', () => {
  assert.equal(exhaustiveOptimal(0).minCost, 0);
  assert.equal(exhaustiveOptimal(1).minCost, 0);
});
