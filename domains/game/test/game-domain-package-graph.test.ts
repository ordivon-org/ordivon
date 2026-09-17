import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const graphPath = new URL("../standards/game_domain_package_graph_r1.json", import.meta.url);
const docPath = new URL("../docs/GAME_DOMAIN_PACKAGE_GRAPH_R1.md", import.meta.url);
const authorityPath = new URL("../docs/authority.md", import.meta.url);
const readmePath = new URL("../README.md", import.meta.url);

type NodeRecord = {
  id: string;
  kind: string;
  owner: string;
  title: string;
  authority?: string;
  refs?: string[];
};

type EdgeRecord = {
  from: string;
  to: string;
  relation: string;
};

type ConstraintRecord = {
  id: string;
  kind: string;
  scope: string[];
  statement: string;
  failureDisposition: string;
  refs: string[];
};

type Graph = {
  schemaVersion: number;
  graphId: string;
  authorityBoundary: string;
  dynamicStandingOwner: string;
  nodeKinds: string[];
  relationKinds: string[];
  constraintKinds: string[];
  nodes: NodeRecord[];
  edges: EdgeRecord[];
  constraints: ConstraintRecord[];
  views: Record<string, string[]>;
};

function loadGraph(): Graph {
  return JSON.parse(readFileSync(graphPath, "utf8")) as Graph;
}

function unique(values: string[], what: string): void {
  assert.equal(new Set(values).size, values.length, `${what} must be unique`);
}

test("Game Domain Package Graph is a machine-readable architecture projection, not a second task authority", () => {
  const graph = loadGraph();
  assert.equal(graph.schemaVersion, 1);
  assert.equal(graph.graphId, "ordivon-game-domain-package-graph-r1");
  assert.equal(graph.authorityBoundary, "game-domain-architecture-projection");
  assert.equal(graph.dynamicStandingOwner, "Host/domain-owner re-entry; never this graph");
  assert.ok(graph.nodes.length >= 35, "graph should cover kernel, foundations, development, products, tools and dependencies");
  assert.ok(graph.edges.length >= 35, "graph should expose real composition/dependency relations");
  assert.ok(graph.constraints.length >= 18, "constraints are first-class graph records, not prose footnotes");
});

test("graph identities and references are closed and machine-checkable", () => {
  const graph = loadGraph();
  unique(graph.nodeKinds, "nodeKinds");
  unique(graph.relationKinds, "relationKinds");
  unique(graph.constraintKinds, "constraintKinds");
  unique(graph.nodes.map((node) => node.id), "node ids");
  unique(graph.constraints.map((constraint) => constraint.id), "constraint ids");

  const nodeIds = new Set(graph.nodes.map((node) => node.id));
  for (const node of graph.nodes) {
    assert.ok(graph.nodeKinds.includes(node.kind), `unknown node kind ${node.kind}`);
    assert.ok(node.owner.length > 0, `${node.id} must name an owner`);
    assert.ok(node.title.length > 0, `${node.id} must have a title`);
  }
  for (const edge of graph.edges) {
    assert.ok(nodeIds.has(edge.from), `edge source missing: ${edge.from}`);
    assert.ok(nodeIds.has(edge.to), `edge target missing: ${edge.to}`);
    assert.ok(graph.relationKinds.includes(edge.relation), `unknown relation ${edge.relation}`);
  }
  for (const constraint of graph.constraints) {
    assert.ok(graph.constraintKinds.includes(constraint.kind), `unknown constraint kind ${constraint.kind}`);
    assert.ok(constraint.statement.length >= 20, `${constraint.id} needs a substantive statement`);
    assert.ok(constraint.failureDisposition.length > 0, `${constraint.id} needs a failure disposition`);
    assert.ok(constraint.refs.length > 0, `${constraint.id} needs source refs`);
    for (const scopedNode of constraint.scope) {
      assert.ok(nodeIds.has(scopedNode), `${constraint.id} scopes unknown node ${scopedNode}`);
    }
  }
});

test("constraint taxonomy separates authority, invariants, admission, evidence, ceilings, currentness and substitution boundaries", () => {
  const graph = loadGraph();
  const required = [
    "authority",
    "invariant",
    "admission",
    "evidence",
    "claim-ceiling",
    "currentness",
    "forbidden-substitution",
    "reopen-condition",
    "replaceability",
  ];
  for (const kind of required) {
    assert.ok(graph.constraintKinds.includes(kind), `missing constraint kind ${kind}`);
    assert.ok(graph.constraints.some((constraint) => constraint.kind === kind), `missing concrete ${kind} constraint`);
  }
});

test("core kernel stays minimal and horizontal services stay external owners", () => {
  const graph = loadGraph();
  const ids = new Set(graph.nodes.map((node) => node.id));
  for (const id of [
    "kernel.world-state",
    "kernel.observation",
    "kernel.action",
    "kernel.transition",
    "service.research",
    "service.runtime",
    "service.host",
    "service.harness",
    "service.workstation",
    "service.artifact",
    "service.media",
    "service.distribution",
    "service.network",
    "service.security",
  ]) {
    assert.ok(ids.has(id), `missing required node ${id}`);
  }

  const gameOwnedKernel = graph.nodes.filter((node) => node.kind === "kernel").map((node) => node.id).sort();
  assert.deepEqual(gameOwnedKernel, [
    "kernel.action",
    "kernel.observation",
    "kernel.transition",
    "kernel.world-state",
  ]);

  const externalServices = graph.nodes.filter((node) => node.kind === "service");
  assert.ok(externalServices.every((node) => node.owner !== "Game"), "horizontal services must not be silently re-owned by Game");
});

test("mechanics and compositions are modeled as reusable nodes with mechanical claim ceilings", () => {
  const graph = loadGraph();
  const ids = new Set(graph.nodes.map((node) => node.id));
  for (const id of ["mechanic.e01", "mechanic.e02", "mechanic.e03", "composition.pc01", "composition.pc02", "composition.pc03"]) {
    assert.ok(ids.has(id), `missing reusable node ${id}`);
  }
  assert.ok(
    graph.constraints.some(
      (constraint) =>
        constraint.kind === "claim-ceiling" &&
        constraint.scope.includes("mechanic.e01") &&
        constraint.scope.includes("mechanic.e02") &&
        constraint.scope.includes("mechanic.e03"),
    ),
    "mechanic KEEP results need an explicit mechanical-only ceiling",
  );
});

test("views expose the requested Lego decomposition without creating new authority", () => {
  const graph = loadGraph();
  for (const view of ["semanticKernel", "foundations", "developmentResponsibilities", "commitmentStages", "mechanicLibrary", "compositionLibrary", "gameOwnedTools", "skills", "horizontalServices", "constraints"]) {
    assert.ok(Array.isArray(graph.views[view]), `missing view ${view}`);
    assert.ok(graph.views[view].length > 0, `empty view ${view}`);
  }
});

test("human navigation names the machine graph and its authority/constraint boundary", () => {
  const doc = readFileSync(docPath, "utf8");
  const authority = readFileSync(authorityPath, "utf8");
  const readme = readFileSync(readmePath, "utf8");
  assert.match(doc, /Constraint Taxonomy/);
  assert.match(doc, /Authority/);
  assert.match(doc, /Claim Ceiling/);
  assert.match(doc, /Forbidden Substitution/);
  assert.match(doc, /Reopen Condition/);
  assert.match(doc, /Host.*dynamic.*standing/is);
  assert.match(authority, /GAME_DOMAIN_PACKAGE_GRAPH_R1\.md/);
  assert.match(readme, /GAME_DOMAIN_PACKAGE_GRAPH_R1\.md/);
});


test("every Lego node has an explicit operational contract instead of inferred ownership folklore", () => {
  const graph = loadGraph() as Graph & {
    contracts: Array<{
      nodeId: string;
      contract: string;
      inputs: string[];
      outputs: string[];
      authority: string;
      dependencies: string[];
      evidence: string[];
      replaceability: string;
      consumers: string[];
      currentStanding: string;
    }>;
  };
  assert.ok(Array.isArray(graph.contracts), "contracts must be first-class records");
  assert.equal(graph.contracts.length, graph.nodes.length, "every node must have exactly one operational contract");
  unique(graph.contracts.map((contract) => contract.nodeId), "contract node ids");
  const nodeIds = new Set(graph.nodes.map((node) => node.id));
  for (const contract of graph.contracts) {
    assert.ok(nodeIds.has(contract.nodeId), `contract targets unknown node ${contract.nodeId}`);
    assert.ok(contract.contract.length >= 20, `${contract.nodeId} needs a substantive contract`);
    assert.ok(contract.inputs.length > 0, `${contract.nodeId} needs explicit inputs`);
    assert.ok(contract.outputs.length > 0, `${contract.nodeId} needs explicit outputs`);
    assert.ok(contract.authority.length >= 10, `${contract.nodeId} needs explicit authority`);
    assert.ok(contract.evidence.length > 0, `${contract.nodeId} needs evidence refs/classes`);
    assert.ok(contract.replaceability.length >= 10, `${contract.nodeId} needs replaceability semantics`);
    assert.ok(contract.consumers.length > 0, `${contract.nodeId} needs named consumers`);
    assert.ok(contract.currentStanding.length >= 10, `${contract.nodeId} needs a current-standing rule`);
    for (const dependency of contract.dependencies) {
      assert.ok(nodeIds.has(dependency), `${contract.nodeId} depends on unknown node ${dependency}`);
    }
  }
});


test("every constraint has an enforcement profile rather than a prose-only kind", () => {
  const graph = loadGraph() as Graph & {
    constraintProfileKinds: string[];
    constraintProfiles: Array<{
      constraintId: string;
      profileKind: string;
      enforcementMode: string;
      authorityOwner: string;
      whenUnknown: string;
      dischargePolicy: string;
    }>;
  };
  const requiredKinds = [
    "hard-invariant",
    "authority-boundary",
    "admission-gate",
    "evidence-gate",
    "claim-fence",
    "currentness-fence",
    "substitution-ban",
    "reopen-trigger",
    "replaceability-boundary",
  ];
  assert.deepEqual([...graph.constraintProfileKinds].sort(), [...requiredKinds].sort());
  assert.equal(graph.constraintProfiles.length, graph.constraints.length, "every constraint needs exactly one enforcement profile");
  unique(graph.constraintProfiles.map((profile) => profile.constraintId), "constraint profile ids");
  const constraintIds = new Set(graph.constraints.map((constraint) => constraint.id));
  for (const profile of graph.constraintProfiles) {
    assert.ok(constraintIds.has(profile.constraintId), `profile targets unknown constraint ${profile.constraintId}`);
    assert.ok(graph.constraintProfileKinds.includes(profile.profileKind), `unknown profile kind ${profile.profileKind}`);
    assert.ok(profile.enforcementMode.length >= 8, `${profile.constraintId} needs enforcement semantics`);
    assert.ok(profile.authorityOwner.length >= 3, `${profile.constraintId} needs an authority owner`);
    assert.ok(profile.whenUnknown.length >= 5, `${profile.constraintId} needs unknown-state semantics`);
    assert.ok(profile.dischargePolicy.length >= 5, `${profile.constraintId} needs discharge semantics`);
  }
  assert.ok(graph.constraintProfiles.some((profile) => profile.profileKind === "hard-invariant"));
  assert.ok(graph.constraintProfiles.some((profile) => profile.profileKind === "evidence-gate"));
  assert.ok(graph.constraintProfiles.some((profile) => profile.profileKind === "claim-fence"));
});

test("constraint-to-constraint relations are closed, typed, and directional", () => {
  const graph = loadGraph() as Graph & {
    constraintRelationKinds: string[];
    constraintRelations: Array<{
      from: string;
      to: string;
      relation: string;
      condition: string;
      effect: string;
    }>;
  };
  const requiredRelations = [
    "preconditions",
    "strengthens",
    "narrows",
    "triggers",
    "blocks",
    "reopen-enables",
    "potential-conflict",
    "requires-adjudication-after",
  ];
  for (const relation of requiredRelations) {
    assert.ok(graph.constraintRelationKinds.includes(relation), `missing constraint relation kind ${relation}`);
  }
  assert.ok(graph.constraintRelations.length >= 20, "constraint graph needs enough relations to expose real interaction");
  const ids = new Set(graph.constraints.map((constraint) => constraint.id));
  for (const edge of graph.constraintRelations) {
    assert.ok(ids.has(edge.from), `constraint edge source missing: ${edge.from}`);
    assert.ok(ids.has(edge.to), `constraint edge target missing: ${edge.to}`);
    assert.notEqual(edge.from, edge.to, "constraint relation may not self-loop");
    assert.ok(graph.constraintRelationKinds.includes(edge.relation), `unknown constraint relation ${edge.relation}`);
    assert.ok(edge.condition.length >= 8, "constraint edge needs an explicit condition");
    assert.ok(edge.effect.length >= 8, "constraint edge needs an explicit effect");
  }
  assert.ok(graph.constraintRelations.some((edge) => edge.relation === "potential-conflict"));
  assert.ok(graph.constraintRelations.some((edge) => edge.relation === "requires-adjudication-after"));
});

test("evidence discharge rules never turn evidence into authority", () => {
  const graph = loadGraph() as Graph & {
    evidenceClasses: Array<{ id: string; owner: string; establishes: string; cannotEstablish: string }>;
    dischargeEffects: string[];
    evidenceDischargeRules: Array<{
      constraintId: string;
      evidenceClass: string;
      effect: string;
      authorityAfterEvidence: string;
      note: string;
    }>;
    constraintProfiles: Array<{ constraintId: string; profileKind: string }>;
  };
  assert.ok(graph.evidenceClasses.length >= 7, "graph should name reusable evidence classes");
  unique(graph.evidenceClasses.map((evidence) => evidence.id), "evidence class ids");
  const evidenceIds = new Set(graph.evidenceClasses.map((evidence) => evidence.id));
  const constraintIds = new Set(graph.constraints.map((constraint) => constraint.id));
  const allowedEffects = new Set(["satisfies-gate", "permits-reentry", "permits-reopen-review", "narrows-claim", "supports-adjudication", "does-not-discharge"]);
  assert.deepEqual([...graph.dischargeEffects].sort(), [...allowedEffects].sort());
  assert.ok(graph.evidenceDischargeRules.length >= 8);
  for (const rule of graph.evidenceDischargeRules) {
    assert.ok(constraintIds.has(rule.constraintId), `discharge rule targets unknown constraint ${rule.constraintId}`);
    assert.ok(evidenceIds.has(rule.evidenceClass), `unknown evidence class ${rule.evidenceClass}`);
    assert.ok(allowedEffects.has(rule.effect), `unknown discharge effect ${rule.effect}`);
    assert.ok(rule.authorityAfterEvidence.length >= 3, "evidence must still name post-evidence authority");
    assert.ok(rule.note.length >= 12, "discharge semantics need explanation");
  }
  const hardIds = new Set(graph.constraintProfiles.filter((profile) => profile.profileKind === "hard-invariant").map((profile) => profile.constraintId));
  assert.ok(
    graph.evidenceDischargeRules
      .filter((rule) => hardIds.has(rule.constraintId))
      .every((rule) => rule.effect === "does-not-discharge" || rule.effect === "supports-adjudication"),
    "evidence may not silently discharge a hard invariant",
  );
});

test("authority adjudication is explicit for conditional constraint conflicts and gate completion", () => {
  const graph = loadGraph() as Graph & {
    authorityAdjudicationRules: Array<{
      id: string;
      whenConstraints: string[];
      authority: string[];
      decision: string;
      defaultWhenUnresolved: string;
      refs: string[];
    }>;
  };
  assert.ok(graph.authorityAdjudicationRules.length >= 3);
  unique(graph.authorityAdjudicationRules.map((rule) => rule.id), "adjudication rule ids");
  const constraintIds = new Set(graph.constraints.map((constraint) => constraint.id));
  for (const rule of graph.authorityAdjudicationRules) {
    assert.ok(rule.whenConstraints.length >= 2, `${rule.id} must bind multiple interacting constraints`);
    for (const constraintId of rule.whenConstraints) {
      assert.ok(constraintIds.has(constraintId), `${rule.id} references unknown constraint ${constraintId}`);
    }
    assert.ok(rule.authority.length > 0, `${rule.id} needs named authority`);
    assert.ok(rule.decision.length >= 12, `${rule.id} needs a bounded decision contract`);
    assert.ok(rule.defaultWhenUnresolved.length >= 5, `${rule.id} needs a fail-safe default`);
    assert.ok(rule.refs.length > 0, `${rule.id} needs authority refs`);
  }
});

test("human documentation explains interaction semantics, discharge, and adjudication", () => {
  const doc = readFileSync(docPath, "utf8");
  assert.match(doc, /Constraint Interaction Graph/);
  assert.match(doc, /Hard Invariant/);
  assert.match(doc, /Evidence Gate/);
  assert.match(doc, /Claim Fence/);
  assert.match(doc, /Evidence Discharge/);
  assert.match(doc, /Authority Adjudication/);
  assert.match(doc, /evidence.*does not.*authority/is);
});
