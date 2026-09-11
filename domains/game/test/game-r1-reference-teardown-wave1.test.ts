import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const data = JSON.parse(readFileSync(new URL("../evidence/acceptance/game-r1-reference-teardown-wave1-20260911.json", import.meta.url), "utf8"));
const doc = readFileSync(new URL("../docs/GAME_R1_REFERENCE_TEARDOWN_WAVE1_20260911.md", import.meta.url), "utf8");
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const agents = readFileSync(new URL("../AGENTS.md", import.meta.url), "utf8");
const project = readFileSync(new URL("../.ordivon/project.yaml", import.meta.url), "utf8");
const authority = readFileSync(new URL("../docs/authority.md", import.meta.url), "utf8");

test("R1 desk teardown covers the exact twelve admitted references without selecting a product", () => {
  assert.equal(data.references.length, 12);
  assert.deepEqual(data.references.map((x: any) => x.title), [
    "Counter-Strike 2", "Dota 2", "Fortnite", "Minecraft", "Grand Theft Auto V", "ELDEN RING",
    "Baldur's Gate 3", "Factorio", "Mario Kart 8 Deluxe", "Animal Crossing: New Horizons", "Candy Crush Saga", "Beat Saber"
  ]);
  assert.equal(data.productSelected, false);
  assert.equal(data.g0Entered, false);
  assert.equal(data.cloneImplementationAdmitted, false);
});

test("every teardown separates observation inference confounds and falsifiable baseline", () => {
  for (const row of data.references) {
    assert.ok(row.observedFacts.length >= 2, row.title);
    assert.ok(row.causalHypotheses.length >= 2, row.title);
    assert.ok(row.alternativeExplanations.length >= 4, row.title);
    assert.ok(row.expressionDependencies.length >= 3, row.title);
    assert.ok(row.transferHypotheses.length >= 1, row.title);
    assert.ok(row.smallestFalsifiableBaseline.length > 40, row.title);
    assert.ok(row.baselineFalsifier.length > 40, row.title);
    assert.match(row.directPlayStanding, /^PENDING_DIRECT_PLAY/);
    assert.ok(row.sources.every((x: string) => /^https:\/\//.test(x)), row.title);
  }
});

test("R1 remains below direct experience evidence and R2 reproduction", () => {
  assert.equal(data.standing, "DESK_TEARDOWN_COMPLETE_DIRECT_PLAY_PENDING");
  assert.equal(data.directPlayRequiredBeforeExperienceClaim, true);
  assert.equal(data.nextStanding.R1DeskTeardown, "COMPLETE_WAVE1");
  assert.equal(data.nextStanding.R1DirectPlay, "PENDING");
  assert.equal(data.nextStanding.R2BaselineReproduction, "NOT_ADMITTED");
  assert.match(doc, /DeskTeardown\s*!= ExperienceEvidence/);
  assert.match(doc, /R2 Baseline Reproduction\s+NOT_ADMITTED/);
});

test("cross-reference synthesis refuses to collapse commercial success into mechanic causality", () => {
  for (const law of [
    "ObservedReferenceFact != InferredDesignCause",
    "CommercialSuccess != CoreMechanicCausality",
    "ReferenceTeardown != ProductSelection",
    "LargeProduct != LargeExperiment"
  ]) assert.ok(data.laws.includes(law));
  assert.match(doc, /commercial success is heavily multiplexed/i);
  assert.match(doc, /one causal claim at a time/i);
});

test("repository navigation exposes current R1 teardown authority", () => {
  for (const carrier of [readme, agents, project, authority]) assert.match(carrier, /GAME_R1_REFERENCE_TEARDOWN_WAVE1_20260911\.md/);
  assert.match(readme, /desk teardown/i);
  assert.match(agents, /direct-play experience claims remain pending/i);
});
