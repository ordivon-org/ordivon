import assert from "node:assert/strict";
import test from "node:test";
import { boundedQueryLimit, normalizeQueryFilter } from "../src/query-input.ts";

test("shared Game query filters preserve optional case-insensitive matching", () => {
  assert.equal(normalizeQueryFilter(undefined), undefined);
  assert.equal(normalizeQueryFilter(" 	 "), undefined);
  assert.equal(normalizeQueryFilter("  Factorio  "), "factorio");
  assert.equal(normalizeQueryFilter("  Failure Signal  "), "failure signal");
});

test("query result limits preserve explicit per-query maximum and invalid-input fallback", () => {
  for (const cap of [100, 200]) {
    for (const input of [undefined, 0, -1, 1.5, NaN, Infinity, -Infinity]) {
      assert.equal(boundedQueryLimit(input, cap), 50);
    }
    for (let candidate = 1; candidate <= 250; candidate++) {
      assert.equal(boundedQueryLimit(candidate, cap), Math.min(candidate, cap));
    }
  }
});
