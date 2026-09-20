import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { exploreGameComposition, loadGameCreativeGraph } from "../scripts/composition-explorer.ts";
import { queryCounterexampleSynthesis } from "../scripts/counterexample-synthesis-query.ts";

const synthesis = JSON.parse(readFileSync(new URL("../standards/game_counterexample_synthesis_r1.json", import.meta.url), "utf8")) as any;
const memory = JSON.parse(readFileSync(new URL("../standards/game_design_counterexample_memory_r1.json", import.meta.url), "utf8")) as any;
const pkg = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8")) as any;
const graph = loadGameCreativeGraph();

test("counterexample synthesis is an overlapping retrieval memory, not a failure ontology", () => {
  assert.equal(synthesis.schemaVersion, 1);
  assert.equal(synthesis.policy.themesAreOntology, false);
  assert.equal(synthesis.policy.exhaustiveClassification, false);
  assert.equal(synthesis.policy.canRankDesigns, false);
  assert.equal(synthesis.policy.canBlockNovelCombination, false);
  assert.equal(synthesis.policy.canMintRecommendation, false);
  assert.equal(synthesis.themes.length, 8);

  const valid = new Set(memory.counterexamples.map((item: any) => item.id));
  const membership = new Map<string, number>();
  for (const theme of synthesis.themes) {
    assert.equal(theme.authority, "ADVISORY_RETRIEVAL_THEME");
    assert.equal(theme.exhaustive, false);
    assert.equal(theme.canRankDesigns, false);
    assert.equal(theme.canBlockNovelCombination, false);
    assert.equal(theme.canMintRecommendation, false);
    assert.ok(theme.counterexampleRefs.length >= 4, `${theme.id} too small`);
    assert.equal(new Set(theme.counterexampleRefs).size, theme.counterexampleRefs.length, `${theme.id} duplicate member`);
    assert.ok(theme.retrievalQuestions.length >= 2, `${theme.id} lacks retrieval questions`);
    assert.ok(theme.falseUniversalizations.length >= 2, `${theme.id} lacks anti-law fences`);
    for (const ref of theme.counterexampleRefs) {
      assert.ok(valid.has(ref), `${theme.id} references unknown ${ref}`);
      membership.set(ref, (membership.get(ref) ?? 0) + 1);
    }
  }
  assert.ok([...membership.values()].some((count) => count >= 2), "themes must overlap");
  assert.ok(membership.size < memory.counterexamples.length, "R1 themes must stay non-exhaustive");
});

test("synthesis has a retrieval command but no decision command", () => {
  assert.equal(pkg.scripts["knowledge:counterexample-themes"], "node scripts/counterexample-synthesis-query.ts");
  assert.equal(pkg.scripts["decide:counterexample-themes"], undefined);
});

test("query resolves mechanisms through member Counterexamples and Experiences", () => {
  const result = queryCounterexampleSynthesis({ mechanism: "legacy-product-vision" });
  assert.ok(result.items.some((item: any) => item.id === "theme.premature-commitment-and-premise-drift"));
  assert.ok(result.items.some((item: any) => item.id === "theme.legacy-coupling-and-sunk-investment"));
  for (const item of result.items) {
    assert.ok(item.matchedMechanisms.includes("legacy-product-vision"));
    assert.ok(item.matchedCounterexampleRefs.length >= 1);
    assert.equal((item as any).score, undefined);
    assert.equal((item as any).recommendation, undefined);
  }
  assert.equal(result.semanticAuthorityClaimed, false);
  assert.equal(result.recommendationClaimed, false);
  assert.equal(result.rankingClaimed, false);
  assert.equal(result.blacklistClaimed, false);
});

test("authority collision is recalled as a cross-counterexample theme without blocking exploration", () => {
  const result = exploreGameComposition(
    {
      intent: "explore",
      elements: ["new.multi-reasoner-npc"],
      mechanisms: ["dual-behavior-authority", "npc-control-interruption"],
    },
    graph,
  ) as any;
  assert.equal(result.disposition, "OPEN_EXPLORATION");
  const theme = result.counterexampleThemeMatches.find((item: any) => item.id === "theme.authority-and-coordination-collision");
  assert.ok(theme);
  assert.ok(theme.matchedCounterexampleRefs.includes("counterexample.odyssey.multiple-ai-authorities-can-fight-over-one-agent"));
  assert.equal(theme.canBlockNovelCombination, false);
  assert.equal(theme.canRankDesigns, false);
  assert.equal(theme.canMintRecommendation, false);
  assert.equal(result.compositionEvidenceInherited, false);
});

test("local success can retrieve a global-harm theme without turning correlation into law", () => {
  const result = queryCounterexampleSynthesis({ q: "local success" });
  const theme = result.items.find((item: any) => item.id === "theme.local-success-global-harm");
  assert.ok(theme);
  assert.ok(theme.counterexampleRefs.includes("counterexample.factorio.local-success-product-mismatch"));
  assert.ok(theme.counterexampleRefs.includes("counterexample.artifact.game-side-fix-does-not-prove-viability"));
  assert.ok(theme.falseUniversalizations.includes("Local success implies global product value."));
});

test("unknown mechanisms remain unmatched and open", () => {
  const result = exploreGameComposition(
    {
      intent: "explore",
      elements: ["unknown.memory-weather-market"],
      mechanisms: ["memory-weather-market"],
    },
    graph,
  ) as any;
  assert.equal(result.disposition, "OPEN_EXPLORATION");
  assert.deepEqual(result.counterexampleThemeMatches, []);
});

test("synthesis is documented and managed as advisory retrieval memory", () => {
  const doc = readFileSync(new URL("../docs/GAME_COUNTEREXAMPLE_SYNTHESIS_R1.md", import.meta.url), "utf8");
  const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
  const authority = readFileSync(new URL("../docs/authority.md", import.meta.url), "utf8");
  const project = readFileSync(new URL("../.ordivon/project.yaml", import.meta.url), "utf8");
  assert.match(doc, /overlap/i);
  assert.match(doc, /not.*taxonomy|not.*ontology/i);
  assert.match(doc, /cannot.*block|cannot.*reject/i);
  assert.match(readme, /GAME_COUNTEREXAMPLE_SYNTHESIS_R1\.md/);
  assert.match(authority, /Counterexample Synthesis/i);
  for (const path of [
    "docs/GAME_COUNTEREXAMPLE_SYNTHESIS_R1.md",
    "standards/game_counterexample_synthesis_r1.json",
    "scripts/counterexample-synthesis-query.ts",
  ]) assert.match(project, new RegExp(path.replaceAll("/", "\\/")));
});
