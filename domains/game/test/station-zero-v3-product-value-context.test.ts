import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, writeFileSync, mkdirSync, cpSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import test from "node:test";

import { stationZeroV3ProductValueContext } from "../scripts/product-value-context.ts";

const root = resolve(new URL("..", import.meta.url).pathname);

test("Product Value context projects exact current evidence without gaining product authority", () => {
  const value = stationZeroV3ProductValueContext(root);
  assert.equal(value.kind, "ordivon.game.station-zero-v3-product-value-context");
  assert.equal(value.truthRole, "derived-read-only-evidence-projection");
  assert.equal(value.currentness.state, "CURRENT");
  assert.equal(value.currentness.usableForCurrentDecision, true);
  assert.deepEqual(value.currentness.stalePaths, []);
  assert.ok(value.retainedConsequences.some((entry: any) => entry.target === "lootPolicy" && entry.disposition === "NO_CHANGE"));
  assert.ok(value.boundaries.some((entry: string) => /Human Player Value/.test(entry)));
});

test("Product Value context fails currentness when one fenced semantic source changes", () => {
  const temp = mkdtempSync(join(tmpdir(), "ordivon-game-product-value-context-"));
  try {
    const receipt = JSON.parse(readFileSync(join(root, "evidence/station-zero-v3/product-value-current.json"), "utf8"));
    for (const fence of receipt.sourceFences) {
      const source = join(root, fence.path);
      const target = join(temp, fence.path);
      mkdirSync(dirname(target), { recursive: true });
      cpSync(source, target);
    }
    const receiptTarget = join(temp, "evidence/station-zero-v3/product-value-current.json");
    mkdirSync(dirname(receiptTarget), { recursive: true });
    writeFileSync(receiptTarget, `${JSON.stringify(receipt, null, 2)}\n`);
    const evaluator = join(temp, "scripts/eval-station-zero-v3-product-value.ts");
    writeFileSync(evaluator, `${readFileSync(evaluator, "utf8")}\n// semantic drift fixture\n`);
    const value = stationZeroV3ProductValueContext(temp);
    assert.equal(value.currentness.state, "STALE");
    assert.equal(value.currentness.usableForCurrentDecision, false);
    assert.deepEqual(value.currentness.stalePaths, ["scripts/eval-station-zero-v3-product-value.ts"]);
    assert.deepEqual(value.lanes, []);
    assert.deepEqual(value.retainedConsequences, []);
    assert.equal(value.historicalEvidence?.state, "WITHHELD_STALE");
    assert.equal(value.historicalEvidence?.retainedConsequenceCount, 1);
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
});
