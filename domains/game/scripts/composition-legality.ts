import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const PROJECT_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const GRAPH_PATH = "standards/game_domain_package_graph_r1.json";

export type CompositionOperation =
  | "compose"
  | "promote-shared-core"
  | "claim-human-value"
  | "select-product"
  | "enter-g0"
  | "replace-provider"
  | "replace-engine"
  | "external-effect";

export type CompositionRequest = {
  operation: CompositionOperation;
  nodes: string[];
  evidenceClasses?: string[];
};

type GraphNode = { id: string; kind: string; owner: string; title: string };
type Constraint = {
  id: string;
  kind: string;
  scope: string[];
  statement: string;
  failureDisposition: string;
  refs: string[];
};
type ConstraintProfile = {
  constraintId: string;
  profileKind: string;
  enforcementMode: string;
  authorityOwner: string;
  whenUnknown: string;
  dischargePolicy: string;
};
type ConstraintRelation = {
  from: string;
  to: string;
  relation: string;
  condition: string;
  effect: string;
};
type EvidenceClass = {
  id: string;
  owner: string;
  establishes: string;
  cannotEstablish: string;
};
type DischargeRule = {
  constraintId: string;
  evidenceClass: string;
  effect: string;
  authorityAfterEvidence: string;
  note: string;
};
type AdjudicationRule = {
  id: string;
  whenConstraints: string[];
  authority: string[];
  decision: string;
  defaultWhenUnresolved: string;
  refs: string[];
};
type DecisionOperation = {
  id: CompositionOperation;
  description: string;
  constraintSeeds: string[];
  gateConstraints: string[];
  requiredEvidenceAll?: string[];
  requiredAdjudicationRules: string[];
  requiresAuthorityDecision?: boolean;
  authorityDecisionOwner?: string;
  defaultWhenUnresolved: string;
};

export type GameDomainGraph = {
  schemaVersion: number;
  graphId: string;
  nodes: GraphNode[];
  constraints: Constraint[];
  constraintProfiles: ConstraintProfile[];
  constraintRelations: ConstraintRelation[];
  evidenceClasses: EvidenceClass[];
  evidenceDischargeRules: DischargeRule[];
  authorityAdjudicationRules: AdjudicationRule[];
  decisionOperations: DecisionOperation[];
  __sourceDigest?: string;
};

type TraceEntry = {
  phase: "request" | "constraint" | "relation" | "evidence" | "decision";
  subject: string;
  explanation: string;
};

export type CompositionDecisionTrace = {
  schemaVersion: 1;
  kind: "ordivon.game.composition-legality-trace";
  graph: {
    graphId: string;
    sourcePath: string;
    sourceDigest: string;
    currentness: "WORKSPACE_GRAPH_ONLY_NOT_LIVE_OWNER_STATE";
  };
  request: {
    operation: CompositionOperation;
    nodes: string[];
    evidenceClasses: string[];
  };
  involvedNodes: Array<{ id: string; kind: string; owner: string; title: string }>;
  applicableConstraints: string[];
  hardInvariants: string[];
  authorityBoundaries: string[];
  claimFences: string[];
  unsatisfiedGates: string[];
  requiredEvidenceClasses: string[];
  reopenReviews: string[];
  adjudicationRules: string[];
  authorityDecisionOwners: string[];
  relationEdges: ConstraintRelation[];
  disposition:
    | "NO_GRAPH_BLOCK"
    | "NO_GRAPH_BLOCK_WITH_FENCES"
    | "BLOCKED_PENDING_EVIDENCE_OR_ADJUDICATION"
    | "AUTHORITY_ADJUDICATION_REQUIRED";
  semanticAuthorityClaimed: false;
  productSelected: false;
  g0Entered: false;
  trace: TraceEntry[];
};

function sha256(value: string): string {
  return `sha256:${createHash("sha256").update(value).digest("hex")}`;
}

export function loadGameDomainGraph(root = PROJECT_ROOT): GameDomainGraph {
  const source = readFileSync(resolve(root, GRAPH_PATH), "utf8");
  const graph = JSON.parse(source) as GameDomainGraph;
  Object.defineProperty(graph, "__sourceDigest", { value: sha256(source), enumerable: false });
  return graph;
}

function sortedUnique(values: string[]): string[] {
  return [...new Set(values)].sort();
}

function requireKnownRequest(request: CompositionRequest, graph: GameDomainGraph): void {
  const operation = graph.decisionOperations.find((candidate) => candidate.id === request.operation);
  if (!operation) throw new Error(`Unknown composition operation: ${request.operation}`);
  const nodeIds = new Set(graph.nodes.map((node) => node.id));
  for (const node of request.nodes) {
    if (!nodeIds.has(node)) throw new Error(`Unknown Game graph node: ${node}`);
  }
  const evidenceIds = new Set(graph.evidenceClasses.map((evidence) => evidence.id));
  for (const evidence of request.evidenceClasses ?? []) {
    if (!evidenceIds.has(evidence)) throw new Error(`Unknown evidence class: ${evidence}`);
  }
}

function applicableConstraintIds(request: CompositionRequest, operation: DecisionOperation, graph: GameDomainGraph): string[] {
  const nodes = new Set(request.nodes);
  const direct = graph.constraints
    .filter((constraint) => constraint.scope.some((node) => nodes.has(node)))
    .map((constraint) => constraint.id);
  return sortedUnique([...direct, ...operation.constraintSeeds]);
}

const GATE_PROGRESS_EFFECTS = new Set(["satisfies-gate", "permits-reentry", "permits-reopen-review", "supports-adjudication"]);

export function evaluateGameComposition(request: CompositionRequest, graph = loadGameDomainGraph()): CompositionDecisionTrace {
  requireKnownRequest(request, graph);
  const operation = graph.decisionOperations.find((candidate) => candidate.id === request.operation)!;
  const evidence = sortedUnique(request.evidenceClasses ?? []);
  const evidenceSet = new Set(evidence);
  const constraintIds = applicableConstraintIds(request, operation, graph);
  const constraintSet = new Set(constraintIds);
  const constraintsById = new Map(graph.constraints.map((constraint) => [constraint.id, constraint]));
  const profilesById = new Map(graph.constraintProfiles.map((profile) => [profile.constraintId, profile]));

  for (const id of constraintIds) {
    if (!constraintsById.has(id)) throw new Error(`Decision operation ${operation.id} references unknown constraint: ${id}`);
    if (!profilesById.has(id)) throw new Error(`Constraint has no enforcement profile: ${id}`);
  }

  const hardInvariants = constraintIds.filter((id) => profilesById.get(id)?.profileKind === "hard-invariant");
  const authorityBoundaries = constraintIds.filter((id) => profilesById.get(id)?.profileKind === "authority-boundary");
  const claimFences = constraintIds.filter((id) => profilesById.get(id)?.profileKind === "claim-fence");

  const matchingRules = graph.evidenceDischargeRules.filter(
    (rule) => constraintSet.has(rule.constraintId) && evidenceSet.has(rule.evidenceClass),
  );

  const unsatisfiedGates = operation.gateConstraints.filter((constraintId) => {
    const progress = matchingRules.some(
      (rule) => rule.constraintId === constraintId && GATE_PROGRESS_EFFECTS.has(rule.effect),
    );
    return !progress;
  });

  const missingOperationEvidence = (operation.requiredEvidenceAll ?? []).filter((evidenceId) => !evidenceSet.has(evidenceId));
  const possibleGateEvidence = graph.evidenceDischargeRules
    .filter((rule) => unsatisfiedGates.includes(rule.constraintId) && GATE_PROGRESS_EFFECTS.has(rule.effect))
    .map((rule) => rule.evidenceClass);
  const requiredEvidenceClasses = sortedUnique([...possibleGateEvidence, ...missingOperationEvidence]);

  const reopenReviews = sortedUnique(
    matchingRules.filter((rule) => rule.effect === "permits-reopen-review").map((rule) => {
      const profile = profilesById.get(rule.constraintId);
      if (profile?.profileKind === "reopen-trigger") return rule.constraintId;
      const relation = graph.constraintRelations.find(
        (edge) => edge.from === rule.constraintId && edge.relation === "preconditions" && profilesById.get(edge.to)?.profileKind === "reopen-trigger",
      );
      return relation?.to ?? rule.constraintId;
    }),
  );

  const relationEdges = graph.constraintRelations.filter((edge) => constraintSet.has(edge.from) && constraintSet.has(edge.to));
  const adjudicationIds = sortedUnique(operation.requiredAdjudicationRules);
  for (const id of adjudicationIds) {
    if (!graph.authorityAdjudicationRules.some((rule) => rule.id === id)) {
      throw new Error(`Decision operation ${operation.id} references unknown adjudication rule: ${id}`);
    }
  }
  const authorityDecisionOwners = sortedUnique([
    ...(operation.authorityDecisionOwner ? [operation.authorityDecisionOwner] : []),
    ...graph.authorityAdjudicationRules
      .filter((rule) => adjudicationIds.includes(rule.id))
      .flatMap((rule) => rule.authority),
  ]);

  const blocked = unsatisfiedGates.length > 0 || missingOperationEvidence.length > 0;
  const adjudicationRequired = !blocked && (adjudicationIds.length > 0 || operation.requiresAuthorityDecision === true);
  const disposition: CompositionDecisionTrace["disposition"] = blocked
    ? "BLOCKED_PENDING_EVIDENCE_OR_ADJUDICATION"
    : adjudicationRequired
      ? "AUTHORITY_ADJUDICATION_REQUIRED"
      : claimFences.length > 0
        ? "NO_GRAPH_BLOCK_WITH_FENCES"
        : "NO_GRAPH_BLOCK";

  const trace: TraceEntry[] = [
    {
      phase: "request",
      subject: operation.id,
      explanation: `${operation.description} The evaluator projects graph constraints only and claims no semantic decision authority.`,
    },
  ];
  for (const id of constraintIds) {
    const constraint = constraintsById.get(id)!;
    const profile = profilesById.get(id)!;
    trace.push({
      phase: "constraint",
      subject: id,
      explanation: `${profile.profileKind}: ${constraint.statement} When unresolved: ${profile.whenUnknown}.`,
    });
  }
  for (const edge of relationEdges) {
    trace.push({
      phase: "relation",
      subject: `${edge.from} -> ${edge.to}`,
      explanation: `${edge.relation}: ${edge.condition}; ${edge.effect}.`,
    });
  }
  for (const evidenceId of evidence) {
    const evidenceClass = graph.evidenceClasses.find((candidate) => candidate.id === evidenceId)!;
    trace.push({
      phase: "evidence",
      subject: evidenceId,
      explanation: `Establishes ${evidenceClass.establishes}; cannot establish ${evidenceClass.cannotEstablish}.`,
    });
  }
  for (const rule of matchingRules) {
    trace.push({
      phase: "evidence",
      subject: `${rule.evidenceClass} -> ${rule.constraintId}`,
      explanation: `${rule.effect}: ${rule.note} Evidence changes review/gate standing but does not auto-transfer authority.`,
    });
  }
  if (adjudicationRequired) {
    trace.push({
      phase: "decision",
      subject: "authority-adjudication",
      explanation: `Evidence/replaceability does not auto-decide the request. Named authority must adjudicate: ${authorityDecisionOwners.join(", ")}.`,
    });
  } else if (blocked) {
    trace.push({
      phase: "decision",
      subject: "blocked",
      explanation: `Graph gate remains unresolved. Required evidence/re-entry: ${requiredEvidenceClasses.join(", ") || "owner-specific basis"}.`,
    });
  } else {
    trace.push({
      phase: "decision",
      subject: "graph-projection",
      explanation: `No graph-level block was found for this bounded operation; claim fences remain explicit and this does not auto-select a product, enter G0, or mint semantic authority.`,
    });
  }

  return {
    schemaVersion: 1,
    kind: "ordivon.game.composition-legality-trace",
    graph: {
      graphId: graph.graphId,
      sourcePath: GRAPH_PATH,
      sourceDigest: graph.__sourceDigest ?? sha256(JSON.stringify(graph)),
      currentness: "WORKSPACE_GRAPH_ONLY_NOT_LIVE_OWNER_STATE",
    },
    request: { operation: request.operation, nodes: [...request.nodes], evidenceClasses: evidence },
    involvedNodes: request.nodes.map((id) => {
      const node = graph.nodes.find((candidate) => candidate.id === id)!;
      return { id: node.id, kind: node.kind, owner: node.owner, title: node.title };
    }),
    applicableConstraints: constraintIds,
    hardInvariants,
    authorityBoundaries,
    claimFences,
    unsatisfiedGates,
    requiredEvidenceClasses,
    reopenReviews,
    adjudicationRules: adjudicationIds,
    authorityDecisionOwners,
    relationEdges,
    disposition,
    semanticAuthorityClaimed: false,
    productSelected: false,
    g0Entered: false,
    trace,
  };
}

function parseList(value: string | undefined): string[] {
  if (!value) return [];
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function argument(name: string): string | undefined {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const operation = argument("--operation") as CompositionOperation | undefined;
  const nodes = parseList(argument("--nodes"));
  const evidenceClasses = parseList(argument("--evidence"));
  if (!operation || nodes.length === 0) {
    process.stderr.write("Usage: node scripts/composition-legality.ts --operation <operation> --nodes <id,id> [--evidence <class,class>]\n");
    process.exitCode = 2;
  } else {
    process.stdout.write(`${JSON.stringify(evaluateGameComposition({ operation, nodes, evidenceClasses }), null, 2)}\n`);
  }
}
