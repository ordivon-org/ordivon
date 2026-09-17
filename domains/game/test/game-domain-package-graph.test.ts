import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const graphPath = new URL("../standards/game_domain_package_graph_r1.json", import.meta.url);
const docPath = new URL("../docs/GAME_DOMAIN_PACKAGE_GRAPH_R1.md", import.meta.url);
const graph = JSON.parse(readFileSync(graphPath, "utf8")) as any;
const unique = (values: string[]) => new Set(values).size === values.length;

test("creative-open graph is knowledge/navigation rather than a closed game ontology", () => {
  assert.equal(graph.schemaVersion, 1);
  assert.equal(graph.graphId, "ordivon-game-domain-package-graph-r1");
  assert.equal(graph.authorityBoundary, "game-domain-architecture-projection");
  assert.equal(graph.creativePolicy.defaultCreativeDisposition, "OPEN_EXPLORATION");
  assert.equal(graph.creativePolicy.unmodeledMechanismDisposition, "EXPLORE_NOT_BLOCK");
  assert.equal(graph.creativePolicy.processModels, "OPTIONAL_SKILLS");
});

test("graph references remain closed after retiring kernel/stage/development law nodes", () => {
  assert.ok(unique(graph.nodes.map((x: any) => x.id)));
  assert.ok(unique(graph.constraints.map((x: any) => x.id)));
  const nodeIds = new Set(graph.nodes.map((x: any) => x.id));
  for (const edge of graph.edges) {
    assert.ok(nodeIds.has(edge.from), `missing edge source ${edge.from}`);
    assert.ok(nodeIds.has(edge.to), `missing edge target ${edge.to}`);
  }
  for (const constraint of graph.constraints) {
    assert.ok(constraint.scope.length > 0, `${constraint.id} needs a live scope`);
    for (const id of constraint.scope) assert.ok(nodeIds.has(id), `${constraint.id} scopes retired node ${id}`);
  }
  assert.equal(graph.contracts.length, graph.nodes.length);
  assert.ok(unique(graph.contracts.map((x: any) => x.nodeId)));
  for (const contract of graph.contracts) {
    assert.ok(nodeIds.has(contract.nodeId));
    for (const id of contract.dependencies ?? []) assert.ok(nodeIds.has(id), `${contract.nodeId} depends on retired node ${id}`);
  }
});

test("D1-D8, G0-G8 and four-part kernel are not machine graph law", () => {
  const retiredKinds = new Set(["kernel", "development-responsibility", "commitment-stage"]);
  assert.equal(graph.nodes.some((node: any) => retiredKinds.has(node.kind)), false);
  for (const id of [
    "constraint.invariant.kernel-minimality",
    "constraint.invariant.stage-core-separation",
    "constraint.admission.core-primitive-high-bar",
    "constraint.reopen.foundations",
  ]) assert.equal(graph.constraints.some((constraint: any) => constraint.id === id), false, `${id} should be retired`);
});

test("every remaining constraint has exactly one enforcement profile", () => {
  assert.equal(graph.constraintProfiles.length, graph.constraints.length);
  assert.ok(unique(graph.constraintProfiles.map((x: any) => x.constraintId)));
  const ids = new Set(graph.constraints.map((x: any) => x.id));
  for (const profile of graph.constraintProfiles) assert.ok(ids.has(profile.constraintId));
});

test("creative mechanisms/compositions remain reusable but evidence does not auto-compose", () => {
  const ids = new Set(graph.nodes.map((node: any) => node.id));
  for (const id of ["mechanic.e01", "mechanic.e02", "mechanic.e03", "composition.pc01", "composition.pc02", "composition.pc03"]) assert.ok(ids.has(id));
  const fence = graph.constraints.find((constraint: any) => constraint.id === "constraint.evidence.composition-noninheritance");
  assert.ok(fence);
  assert.match(fence.statement, /Evidence\(A\).*Evidence\(B\).*Evidence\(A\+B\)/);
  assert.match(fence.failureDisposition, /EXPLORE/);
});

test("optional skills and teardown patterns are first-class advisory knowledge", () => {
  assert.equal(graph.advisorySkills.length, 3);
  assert.ok(graph.advisorySkills.every((x: any) => x.authority === "ADVISORY" && x.removable && !x.canBlockCreativeComposition));
  assert.equal(graph.mechanismCombinationPatterns.length, 12);
  assert.ok(graph.mechanismCombinationPatterns.every((x: any) => x.authority === "ADVISORY_HYPOTHESIS_PATTERN" && !x.canBlockNovelCombination));
});

test("guarded decision operations apply only to claims/effects/runtime authority", () => {
  const ids = graph.decisionOperations.map((x: any) => x.id).sort();
  assert.deepEqual(ids, ["claim-human-value", "external-effect", "replace-provider"]);
  for (const retired of ["compose", "promote-shared-core", "select-product", "enter-g0", "replace-engine"]) assert.ok(!ids.includes(retired));
});

test("remaining hard boundaries protect truth/effects rather than choosing games", () => {
  const hard = graph.constraintProfiles.filter((x: any) => ["hard-invariant", "authority-boundary", "substitution-ban", "currentness-fence"].includes(x.profileKind));
  const creativeIds = new Set(["mechanic.e01", "mechanic.e02", "mechanic.e03", "composition.pc01", "composition.pc02", "composition.pc03"]);
  for (const profile of hard) {
    const constraint = graph.constraints.find((x: any) => x.id === profile.constraintId);
    assert.ok(constraint);
    assert.equal(constraint.scope.some((id: string) => creativeIds.has(id)), false, `${constraint.id} must not hard-block a creative mechanic/composition`);
  }
});

test("human graph doc states creative-open and anti-evidence-inheritance semantics", () => {
  const doc = readFileSync(docPath, "utf8");
  assert.match(doc, /Creative-Open/);
  assert.match(doc, /OPEN_EXPLORATION/);
  assert.match(doc, /Evidence\(A\) \+ Evidence\(B\) != Evidence\(A\+B\)/);
  assert.match(doc, /not:[\s\S]*universal Game ontology/);
});
