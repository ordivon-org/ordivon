import assert from 'node:assert/strict';
import test from 'node:test';
// @ts-expect-error JS experiment module intentionally has no TypeScript declaration.
import { runWitnesses } from '../experiments/mechanic-prototype-wave-r1/e02-transfer-route/core.js';

test('E02 relational rule transfers while timing-insensitive behavior fails route2', () => {
  const w = runWitnesses();
  assert.equal(w.transferSucceeds, true);
  assert.equal(w.timingMattersOnRoute2, true);
  assert.equal(w.sameRuleAcrossRoutes, true);
  assert.equal(w.spatiallyDistinct, true);
  assert.equal(w.noKnowledgeAuthorizationState, true);
  assert.equal(w.pass, true);
});
