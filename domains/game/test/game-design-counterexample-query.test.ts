import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { queryDesignCounterexamples } from "../scripts/design-counterexample-query.ts";
import { exploreGameComposition, loadGameCreativeGraph } from "../scripts/composition-explorer.ts";

const pkg = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));
const graph = loadGameCreativeGraph();

test("counterexample retrieval is exposed without a decision command", () => {
  assert.equal(pkg.scripts["knowledge:counterexamples"], "node scripts/design-counterexample-query.ts");
  assert.equal(pkg.scripts["decide:counterexamples"], undefined);
});

test("query retrieves a contextual counterexample by mechanism", () => {
  const result = queryDesignCounterexamples({ mechanism: "strict-error-prevention" });
  assert.ok(result.items.some((item: any) => item.id === "counterexample.factorio.strict-prevention-complexity"));
  assert.equal(result.semanticAuthorityClaimed, false);
  assert.equal(result.recommendationClaimed, false);
  assert.equal(result.blacklistClaimed, false);
});

test("query retrieves Diablo incentive displacement without converting removal into law", () => {
  const result = queryDesignCounterexamples({ q: "auction" });
  const item = result.items.find((entry: any) => entry.id === "counterexample.diablo3.secondary-system-displaced-core-loop");
  assert.ok(item);
  assert.ok(item.falseUniversalizations.includes("Player trading is bad for loot games."));
  assert.equal(item.canBlockNovelCombination, false);
});

test("composition explorer recalls counterexamples as attack surfaces and stays open", () => {
  const result = exploreGameComposition(
    {
      intent: "explore",
      elements: ["new.fluid-construction"],
      mechanisms: ["strict-error-prevention", "fast-error-recovery"],
    },
    graph,
  );
  assert.equal(result.disposition, "OPEN_EXPLORATION");
  const match = result.counterexampleMatches.find((item: any) => item.id === "counterexample.factorio.strict-prevention-complexity");
  assert.ok(match);
  assert.deepEqual(match.matchedMechanisms.sort(), ["fast-error-recovery", "strict-error-prevention"]);
  assert.match(match.cheapDiscriminator, /prevention|recovery/i);
  assert.equal(match.canBlockNovelCombination, false);
  assert.equal(result.compositionEvidenceInherited, false);
});

test("constraint counterexample can be recalled without saying constraints are good", () => {
  const result = exploreGameComposition(
    {
      intent: "explore",
      elements: ["new.empathy-constrained-design"],
      mechanisms: ["creative-constraint", "design-possibility-expansion"],
    },
    graph,
  );
  const match = result.counterexampleMatches.find((item: any) => item.id === "counterexample.psychonauts2.constraints-can-expand-search");
  assert.ok(match);
  assert.ok(match.falseUniversalizations.includes("Strong values automatically improve creative work."));
  assert.equal((match as any).recommendation, undefined);
});

test("unknown mechanisms have no forced counterexample classification", () => {
  const result = exploreGameComposition(
    {
      intent: "explore",
      elements: ["unknown.temporal-scent-market"],
      mechanisms: ["temporal-scent-market"],
    },
    graph,
  );
  assert.equal(result.disposition, "OPEN_EXPLORATION");
  assert.deepEqual(result.counterexampleMatches, []);
});
