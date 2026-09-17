import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { evaluateGameComposition, loadGameDomainGraph } from "../scripts/composition-legality.ts";

const graph = loadGameDomainGraph();

test("E03 into PC02 is mechanically composable but keeps explicit claim fences", () => {
  const result = evaluateGameComposition(
    {
      operation: "compose",
      nodes: ["mechanic.e03", "composition.pc02"],
      evidenceClasses: ["evidence.mechanical-causal"],
    },
    graph,
  );

  assert.equal(result.disposition, "NO_GRAPH_BLOCK_WITH_FENCES");
  assert.deepEqual(result.request.nodes, ["mechanic.e03", "composition.pc02"]);
  assert.ok(result.claimFences.includes("constraint.claim.mechanic-wave-r1"));
  assert.ok(result.claimFences.includes("constraint.claim.pre-g0-compositions"));
  assert.ok(result.trace.some((entry) => /mechanical/i.test(entry.explanation)));
  assert.equal(result.semanticAuthorityClaimed, false);
  assert.equal(result.productSelected, false);
  assert.equal(result.g0Entered, false);
});

test("shared-core promotion blocks when promotion/reopen evidence is absent", () => {
  const result = evaluateGameComposition(
    {
      operation: "promote-shared-core",
      nodes: ["mechanic.e03", "composition.pc02"],
      evidenceClasses: ["evidence.mechanical-causal"],
    },
    graph,
  );

  assert.equal(result.disposition, "BLOCKED_PENDING_EVIDENCE_OR_ADJUDICATION");
  assert.ok(result.hardInvariants.includes("constraint.invariant.kernel-minimality"));
  assert.ok(result.unsatisfiedGates.includes("constraint.admission.cross-game-promotion"));
  assert.ok(result.unsatisfiedGates.includes("constraint.admission.core-primitive-high-bar"));
  assert.ok(result.requiredEvidenceClasses.includes("evidence.cross-product-consumer"));
  assert.ok(result.requiredEvidenceClasses.includes("evidence.semantic-counterexample"));
});

test("counterexample and cross-product evidence permit review but never auto-promote shared core", () => {
  const result = evaluateGameComposition(
    {
      operation: "promote-shared-core",
      nodes: ["mechanic.e03", "composition.pc02"],
      evidenceClasses: [
        "evidence.mechanical-causal",
        "evidence.cross-product-consumer",
        "evidence.semantic-counterexample",
      ],
    },
    graph,
  );

  assert.equal(result.disposition, "AUTHORITY_ADJUDICATION_REQUIRED");
  assert.ok(result.adjudicationRules.includes("adjudication.cross-game-promotion"));
  assert.ok(result.adjudicationRules.length >= 1);
  assert.ok(result.reopenReviews.includes("constraint.reopen.foundations"));
  assert.equal(result.semanticAuthorityClaimed, false);
  assert.ok(result.trace.some((entry) => /does not auto/i.test(entry.explanation)));
});

test("Human-value claim stays blocked with mechanical evidence and becomes reviewable with Human evidence", () => {
  const mechanicalOnly = evaluateGameComposition(
    {
      operation: "claim-human-value",
      nodes: ["mechanic.e03", "composition.pc02"],
      evidenceClasses: ["evidence.mechanical-causal"],
    },
    graph,
  );
  assert.equal(mechanicalOnly.disposition, "BLOCKED_PENDING_EVIDENCE_OR_ADJUDICATION");
  assert.ok(mechanicalOnly.unsatisfiedGates.includes("constraint.evidence.mechanical-not-human"));
  assert.ok(mechanicalOnly.requiredEvidenceClasses.includes("evidence.human-participant"));

  const withHumanEvidence = evaluateGameComposition(
    {
      operation: "claim-human-value",
      nodes: ["mechanic.e03", "composition.pc02"],
      evidenceClasses: ["evidence.mechanical-causal", "evidence.human-participant"],
    },
    graph,
  );
  assert.notEqual(withHumanEvidence.disposition, "BLOCKED_PENDING_EVIDENCE_OR_ADJUDICATION");
  assert.equal(withHumanEvidence.semanticAuthorityClaimed, false);
  assert.ok(withHumanEvidence.claimFences.length > 0, "Human evidence should not erase unrelated claim fences");
});

test("provider replacement exposes authority adjudication instead of treating replaceability as permission", () => {
  const result = evaluateGameComposition(
    {
      operation: "replace-provider",
      nodes: ["tool.external-json-model", "service.harness"],
      evidenceClasses: ["evidence.owner-currentness"],
    },
    graph,
  );
  assert.equal(result.disposition, "AUTHORITY_ADJUDICATION_REQUIRED");
  assert.ok(result.adjudicationRules.includes("adjudication.provider-replacement-authority"));
  assert.ok(result.hardInvariants.includes("constraint.invariant.no-direct-model-world-write"));
  assert.ok(result.authorityBoundaries.includes("constraint.authority.provider-separation"));
});

test("unknown nodes and unknown evidence fail closed", () => {
  assert.throws(
    () => evaluateGameComposition({ operation: "compose", nodes: ["mechanic.missing"], evidenceClasses: [] }, graph),
    /Unknown Game graph node/,
  );
  assert.throws(
    () => evaluateGameComposition({ operation: "compose", nodes: ["mechanic.e03"], evidenceClasses: ["evidence.fake"] }, graph),
    /Unknown evidence class/,
  );
});

test("decision trace binds exact graph identity and never claims live authority", () => {
  const source = readFileSync(new URL("../standards/game_domain_package_graph_r1.json", import.meta.url), "utf8");
  const result = evaluateGameComposition({ operation: "compose", nodes: ["mechanic.e03", "composition.pc02"], evidenceClasses: [] }, graph);
  assert.equal(result.graph.graphId, "ordivon-game-domain-package-graph-r1");
  assert.match(result.graph.sourceDigest, /^sha256:[0-9a-f]{64}$/);
  assert.ok(source.includes(result.graph.graphId));
  assert.equal(result.graph.currentness, "WORKSPACE_GRAPH_ONLY_NOT_LIVE_OWNER_STATE");
  assert.equal(result.semanticAuthorityClaimed, false);
});

test("graph declares operation seeds and evidence requirements rather than hiding policy in evaluator code", () => {
  assert.ok(Array.isArray(graph.decisionOperations));
  for (const operation of ["compose", "promote-shared-core", "claim-human-value", "select-product", "enter-g0", "replace-provider", "replace-engine", "external-effect"]) {
    const definition = graph.decisionOperations.find((candidate) => candidate.id === operation);
    assert.ok(definition, `missing operation definition ${operation}`);
    assert.ok(definition.constraintSeeds.length > 0, `${operation} needs explicit constraint seeds`);
    assert.ok(definition.defaultWhenUnresolved.length > 0, `${operation} needs fail-safe semantics`);
  }
});
