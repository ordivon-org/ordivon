import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { queryMechanismRelationships } from "../scripts/mechanism-relationship-query.ts";
import { exploreGameComposition, loadGameCreativeGraph } from "../scripts/composition-explorer.ts";

const pkg = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));
const graph = loadGameCreativeGraph();

test("relationship retrieval is exposed without a decision command", () => {
  assert.equal(pkg.scripts["knowledge:relationships"], "node scripts/mechanism-relationship-query.ts");
  assert.equal(pkg.scripts["decide:relationships"], undefined);
});

test("query retrieves facets and conditionalities by exact mechanism", () => {
  const facetResult = queryMechanismRelationships({ type: "facets", mechanism: "fast-retry" });
  assert.ok(facetResult.items.some((item: any) => item.id === "facet.failure-reset-persistence"));

  const conditionalResult = queryMechanismRelationships({ type: "conditionalities", mechanism: "fast-retry" });
  assert.ok(conditionalResult.items.some((item: any) => item.id === "conditional.fast-retry-vs-consequence-carrying-failure"));
});

test("query can search apparent conflicts without claiming a verdict", () => {
  const result = queryMechanismRelationships({ type: "conditionalities", q: "opacity" });
  assert.ok(result.items.some((item: any) => item.id === "conditional.guidance-vs-productive-opacity"));
  assert.equal(result.semanticAuthorityClaimed, false);
  assert.equal(result.recommendationClaimed, false);
  assert.equal(result.compatibilityVerdictClaimed, false);
  assert.ok(result.items.every((item: any) => item.canBlockNovelCombination === false));
});

test("composition explorer recalls retrieval facets and conditionalities but remains creative-open", () => {
  const result = exploreGameComposition(
    {
      intent: "explore",
      elements: ["new.precision-loop"],
      mechanisms: ["fast-retry"],
    },
    graph,
  );
  assert.equal(result.disposition, "OPEN_EXPLORATION");
  assert.ok(result.relationshipFacetMatches.some((item: any) => item.id === "facet.failure-reset-persistence"));
  assert.ok(result.conditionalityMatches.some((item: any) => item.id === "conditional.fast-retry-vs-consequence-carrying-failure"));
  assert.ok(result.conditionalityMatches.every((item: any) => item.authority === "ADVISORY_CONDITIONAL_HYPOTHESIS"));
  assert.equal(result.compositionEvidenceInherited, false);
});

test("affordance query surfaces the omission conditionality rather than a universal rule", () => {
  const result = exploreGameComposition(
    {
      intent: "explore",
      elements: ["new.simulation"],
      mechanisms: ["visual-affordance", "system-consistency"],
    },
    graph,
  );
  const match = result.conditionalityMatches.find((item: any) => item.id === "conditional.affordance-consistency-vs-strategic-omission");
  assert.ok(match);
  assert.ok(match.falseUniversalizations.length >= 2);
  assert.match(match.cheapDiscriminator, /affordance|semantic|remove/i);
  assert.equal((match as any).verdict, undefined);
});

test("novel mechanisms with no relationship alias stay open and unmatched", () => {
  const result = exploreGameComposition(
    {
      intent: "explore",
      elements: ["unknown.rhythmic-contract-mutation"],
      mechanisms: ["rhythmic-contract-mutation"],
    },
    graph,
  );
  assert.equal(result.disposition, "OPEN_EXPLORATION");
  assert.deepEqual(result.relationshipFacetMatches, []);
  assert.deepEqual(result.conditionalityMatches, []);
});
