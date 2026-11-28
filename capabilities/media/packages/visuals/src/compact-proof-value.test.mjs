import assert from 'node:assert/strict';
import {test} from 'node:test';
import {compactProofValue} from './compact-proof-value.ts';

test('keeps short and exact-threshold evidence IDs unchanged', () => {
  for (const value of ['', 'abc', 'x'.repeat(22), 'x'.repeat(23)]) {
    assert.equal(compactProofValue(value), value);
  }
});
test('preserves explicit head and tail display budgets', () => {
  const value = '0123456789abcdefghijklmnopqrstuvwxyz';
  assert.equal(compactProofValue(value), '0123456789abcd…stuvwxyz');
  assert.equal(compactProofValue(value, 4, 3), '0123…xyz');
  assert.equal(compactProofValue(value, 1, 1), '0…z');
});
test('preserves existing UTF-16 display semantics', () => {
  assert.equal(compactProofValue('非ASCII😀123456789', 3, 3), '非AS…789');
});
