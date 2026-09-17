import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const library = JSON.parse(readFileSync(new URL("../standards/game_mechanism_experience_library_r1.json", import.meta.url), "utf8")) as any;
const graph = JSON.parse(readFileSync(new URL("../standards/game_mechanism_relationship_graph_r1.json", import.meta.url), "utf8")) as any;
const spec = JSON.parse(readFileSync(new URL("../standards/game_mechanism_relationship_spec_r1.json", import.meta.url), "utf8")) as any;
const doc = readFileSync(new URL("../docs/GAME_MECHANISM_RELATIONSHIP_GRAPH_R1.md", import.meta.url), "utf8");

const unique = (items: string[]) => new Set(items).size === items.length;

test("relationship graph is a derived memory projection rather than a mechanic ontology", () => {
  assert.equal(graph.schemaVersion, 1);
  assert.equal(graph.graphId, "ordivon-game-mechanism-relationship-graph-r1");
  assert.equal(graph.sourceLibrary.path, "standards/game_mechanism_experience_library_r1.json");
  assert.equal(graph.policy.closedOntology, false);
  assert.equal(graph.policy.canBlockNovelCombination, false);
  assert.equal(graph.policy.recommendationAuthority, "NONE");
  assert.equal(graph.policy.humanEvidenceInherited, false);
});

test("mechanism nodes and within-experience edges are mechanically closed over the experience library", () => {
  const expectedMechanisms = new Set(library.experiences.flatMap((experience: any) => experience.mechanisms));
  const expectedEdges = library.experiences.reduce((sum: number, experience: any) => sum + (experience.mechanisms.length * (experience.mechanisms.length - 1)) / 2, 0);
  assert.equal(graph.mechanismNodes.length, expectedMechanisms.size);
  assert.equal(graph.withinExperienceEdges.length, expectedEdges);
  assert.ok(unique(graph.mechanismNodes.map((node: any) => node.id)));
  assert.ok(unique(graph.withinExperienceEdges.map((edge: any) => edge.id)));
  const nodeIds = new Set(graph.mechanismNodes.map((node: any) => node.id));
  const experienceIds = new Set(library.experiences.map((experience: any) => experience.id));
  for (const edge of graph.withinExperienceEdges) {
    assert.ok(nodeIds.has(edge.a), `${edge.id} missing a`);
    assert.ok(nodeIds.has(edge.b), `${edge.id} missing b`);
    assert.ok(experienceIds.has(edge.experienceRef), `${edge.id} missing experience`);
    assert.equal(edge.authority, "OBSERVED_WITHIN_SOURCE_GROUNDED_EXPERIENCE");
    assert.equal(edge.canBlockNovelCombination, false);
  }
});

test("cross-game retrieval facets are broad aliases, not exhaustive categories", () => {
  assert.ok(graph.retrievalFacets.length >= 14);
  assert.ok(unique(graph.retrievalFacets.map((facet: any) => facet.id)));
  const experienceIds = new Set(library.experiences.map((experience: any) => experience.id));
  for (const facet of graph.retrievalFacets) {
    assert.equal(facet.authority, "ADVISORY_RETRIEVAL_ALIAS");
    assert.equal(facet.exhaustive, false);
    assert.equal(facet.canRejectUnmatchedMechanism, false);
    assert.ok(facet.mechanismTags.length >= 2, `${facet.id} needs mechanism tags`);
    assert.ok(facet.experienceRefs.length >= 2, `${facet.id} needs cross-experience support`);
    assert.ok(facet.referenceGames.length >= 2, `${facet.id} needs cross-game support`);
    for (const ref of facet.experienceRefs) assert.ok(experienceIds.has(ref), `${facet.id} missing ${ref}`);
  }
});

test("conditionalities preserve apparent conflicts as conditions rather than universal verdicts", () => {
  assert.ok(graph.conditionalities.length >= 12);
  assert.ok(unique(graph.conditionalities.map((item: any) => item.id)));
  const experienceIds = new Set(library.experiences.map((experience: any) => experience.id));
  for (const item of graph.conditionalities) {
    assert.equal(item.authority, "ADVISORY_CONDITIONAL_HYPOTHESIS");
    assert.equal(item.canBlockNovelCombination, false);
    assert.ok(item.apparentConflict.length > 0, `${item.id} conflict`);
    assert.ok(item.distinguishingConditions.length >= 2, `${item.id} conditions`);
    assert.ok(item.cheapDiscriminator.length > 0, `${item.id} discriminator`);
    assert.ok(item.falseUniversalizations.length >= 2, `${item.id} universalization traps`);
    assert.ok(item.experienceRefs.length >= 2, `${item.id} experiences`);
    assert.ok(item.referenceGames.length >= 2, `${item.id} games`);
    for (const ref of item.experienceRefs) assert.ok(experienceIds.has(ref), `${item.id} missing ${ref}`);
  }

  for (const id of [
    "conditional.guidance-vs-productive-opacity",
    "conditional.fast-retry-vs-consequence-carrying-failure",
    "conditional.affordance-consistency-vs-strategic-omission",
    "conditional.predictable-resolution-vs-replay-variation",
    "conditional.broad-idea-search-vs-shipped-scope-restraint",
    "conditional.preserve-core-vs-break-form",
    "conditional.explicit-direction-vs-curiosity-direction",
    "conditional.reset-vs-persistence-partition",
  ]) assert.ok(graph.conditionalities.some((item: any) => item.id === id), `missing ${id}`);
});

test("relationship spec is the authored semantic layer and graph preserves its identities", () => {
  assert.equal(spec.schemaVersion, 1);
  assert.equal(spec.specId, "ordivon-game-mechanism-relationship-spec-r1");
  assert.deepEqual(graph.retrievalFacets.map((item: any) => item.id), spec.retrievalFacets.map((item: any) => item.id));
  assert.deepEqual(graph.conditionalities.map((item: any) => item.id), spec.conditionalities.map((item: any) => item.id));
});

test("human guide explains co-occurrence, facet and conditionality without turning correlation into causality", () => {
  assert.match(doc, /co-occurrence/i);
  assert.match(doc, /retrieval facet/i);
  assert.match(doc, /conditionality/i);
  assert.match(doc, /not.*caus/i);
  assert.match(doc, /not.*ontology/i);
  assert.match(doc, /apparent conflict/i);
  assert.match(doc, /cheap.*discriminator/i);
});


test("generated relationship graph exactly rebuilds from spec plus Experience Library", async () => {
  const { buildMechanismRelationshipGraph } = await import("../scripts/build-mechanism-relationship-graph.ts");
  assert.deepEqual(buildMechanismRelationshipGraph(), graph);
});

test("relationship graph is discoverable through navigation but only pointer-linked from the domain graph", () => {
  const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
  const authority = readFileSync(new URL("../docs/authority.md", import.meta.url), "utf8");
  const project = readFileSync(new URL("../.ordivon/project.yaml", import.meta.url), "utf8");
  const domain = JSON.parse(readFileSync(new URL("../standards/game_domain_package_graph_r1.json", import.meta.url), "utf8")) as any;

  assert.match(readme, /GAME_MECHANISM_RELATIONSHIP_GRAPH_R1\.md/);
  assert.match(readme, /knowledge:relationships/);
  assert.match(authority, /Mechanism Relationship Graph/i);
  for (const path of [
    "docs/GAME_MECHANISM_RELATIONSHIP_GRAPH_R1.md",
    "standards/game_mechanism_relationship_spec_r1.json",
    "standards/game_mechanism_relationship_graph_r1.json",
    "scripts/build-mechanism-relationship-graph.ts",
    "scripts/mechanism-relationship-query.ts",
  ]) assert.match(project, new RegExp(path.replaceAll("/", "\\/")));

  assert.equal(domain.mechanismRelationshipGraph.path, "standards/game_mechanism_relationship_graph_r1.json");
  assert.equal(domain.mechanismRelationshipGraph.embeddedInGraph, false);
  assert.equal(domain.mechanismRelationshipGraph.canBlockNovelCombination, false);
});
