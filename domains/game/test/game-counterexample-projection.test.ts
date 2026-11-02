import assert from "node:assert/strict";
import test from "node:test";
import {
  projectCounterexamples,
  projectCounterexampleThemes,
  type CounterexampleTheme,
} from "../src/counterexample-projection.ts";

const experiences = [
  { id: "e1", mechanisms: ["trade", "craft"] },
  { id: "e2", mechanisms: ["craft", "risk"] },
];
const failures = [
  { id: "c1", experienceRefs: ["e1", "e2"], referenceGames: ["g1"], sourceRefs: ["source-a"] },
];
const themes: CounterexampleTheme[] = [{
  id: "t1", label: "Trade risk", summary: "A scoped case",
  counterexampleRefs: ["c1"], retrievalQuestions: [], falseUniversalizations: [],
  authority: "ADVISORY_RETRIEVAL_THEME", exhaustive: false,
  canRankDesigns: false, canBlockNovelCombination: false, canMintRecommendation: false,
}];

test("projection resolves real source references without changing source records", () => {
  const before = JSON.stringify([experiences, failures, themes]);
  const projected = projectCounterexamples(failures, experiences);
  const enriched = projectCounterexampleThemes(themes, failures, experiences);
  assert.deepEqual(projected[0]?.mechanisms, ["craft", "risk", "trade"]);
  assert.deepEqual(enriched[0]?.mechanisms, projected[0]?.mechanisms);
  assert.deepEqual(enriched[0]?.counterexampleMechanisms, [
    { counterexampleRef: "c1", mechanisms: ["craft", "risk", "trade"] },
  ]);
  assert.equal(JSON.stringify([experiences, failures, themes]), before);
});

test("unknown reference is not silently converted to a successful derived fact", () => {
  assert.throws(() => projectCounterexamples([{...failures[0]!, experienceRefs: ["missing"]}], experiences), /unknown Experience missing/);
  assert.throws(() => projectCounterexampleThemes([{...themes[0]!, counterexampleRefs: ["missing"]}], failures, experiences), /unknown Counterexample missing/);
});
