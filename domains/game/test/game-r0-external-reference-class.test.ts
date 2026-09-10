import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const doc = readFileSync(new URL("../docs/GAME_R0_EXTERNAL_REFERENCE_CLASS_20260911.md", import.meta.url), "utf8");
const evidence = JSON.parse(readFileSync(new URL("../evidence/acceptance/game-r0-external-reference-class-20260911.json", import.meta.url), "utf8"));
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const agents = readFileSync(new URL("../AGENTS.md", import.meta.url), "utf8");
const project = readFileSync(new URL("../.ordivon/project.yaml", import.meta.url), "utf8");

test("R0 separates external success from product and G0 authority", () => {
  assert.equal(evidence.productSelected, false);
  assert.equal(evidence.g0Entered, false);
  assert.equal(evidence.runtimeAgentRequired, false);
  for (const law of [
    "SuccessfulGame != ValidProductionBaseline",
    "PopularNow != MatureReference",
    "DesignReference != CloneTarget",
    "ReferenceAdmission != G0Admission",
    "ObservedReferenceFact != InferredDesignCause != TransferableDesignLaw",
  ]) assert.ok(evidence.laws.includes(law));
  assert.match(doc, /Steam's current Charts are retained as a \*\*market pulse\*\*, not as product authority/);
});

test("R0 admits exactly three materially different first teardowns", () => {
  assert.deepEqual(evidence.firstR1Set, ["Balatro", "Vampire Survivors", "Mini Metro"]);
  const selected = evidence.references.filter((row: any) => row.tier === "A");
  assert.equal(selected.length, 3);
  assert.deepEqual(selected.map((row: any) => row.form), [
    "symbolic-turn-based-combinatorial",
    "real-time-action-density-growth",
    "continuous-systemic-optimization",
  ]);
  for (const row of selected) assert.equal(row.smallScopeReproducibility, "very_high");
  assert.match(doc, /This is a \*\*reference-learning portfolio\*\*, not a product portfolio/);
});

test("R0 keeps reserve and ceiling references instead of collapsing all success into clone targets", () => {
  assert.deepEqual(evidence.reserveSet, ["FTL: Faster Than Light", "Papers, Please", "Slay the Spire", "Into the Breach"]);
  assert.deepEqual(evidence.ceilingSet, ["Stardew Valley", "Hades", "Return of the Obra Dinn"]);
  assert.equal(evidence.references.filter((row: any) => row.tier === "B").length, 4);
  assert.equal(evidence.references.filter((row: any) => row.tier === "C").length, 3);
  assert.match(doc, /too much production\/content confounding for first baseline work/);
});

test("R0 uses a vector of comparability axes and preserves source provenance", () => {
  assert.equal(evidence.selectionAxes.length, 10);
  for (const axis of ["SuccessEvidence", "MaturityLongevity", "SmallScopeReproducibility", "ExpressionDependence", "ContentBurden", "ProductionScaleComparability"]) {
    assert.ok(evidence.selectionAxes.includes(axis));
  }
  for (const row of evidence.references) {
    assert.ok(Array.isArray(row.sourceUrls) && row.sourceUrls.length > 0);
    for (const url of row.sourceUrls) assert.match(url, /^https:\/\//);
  }
});

test("current navigation exposes the executed R0 corpus", () => {
  for (const carrier of [readme, agents, project]) assert.match(carrier, /GAME_R0_EXTERNAL_REFERENCE_CLASS_20260911\.md/);
  assert.match(readme, /Balatro, Vampire Survivors, and Mini Metro/);
});
