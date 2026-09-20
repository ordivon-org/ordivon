import assert from 'node:assert/strict';
import test from 'node:test';
// @ts-expect-error JS experiment module intentionally has no TypeScript declaration.
import { ACTIONS, FAULTS, createState, publicView, runWitnesses, step } from '../experiments/mechanic-prototype-wave-r1/e01-counterfactual-probe/core.js';

test('E01 starts observationally identical across latent faults', () => {
  assert.deepEqual(publicView(createState(FAULTS.BLOCKAGE)), publicView(createState(FAULTS.DEPLETION)));
});

test('E01 requires different repairs for the two latent faults', () => {
  const a = createState(FAULTS.BLOCKAGE);
  const b = createState(FAULTS.DEPLETION);
  assert.equal(step(a, ACTIONS.PURGE).success, true);
  assert.equal(step(b, ACTIONS.PURGE).success, false);
});

test('E01 bounded inspection changes the successful action', () => {
  const witness = runWitnesses();
  assert.equal(witness.initialViewsMatch, true);
  assert.equal(witness.fixedRepairCannotSolveBoth, true);
  assert.equal(witness.inspectionSeparatesFaults, true);
  assert.equal(witness.informedSolvesBoth, true);
  assert.equal(witness.boundedInspection, true);
  assert.equal(witness.pass, true);
});
