import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const PROJECT_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const GRAPH_PATH = "standards/game_domain_package_graph_r1.json";
const EXPERIENCE_PATH = "standards/game_mechanism_experience_library_r1.json";

export type ExploreIntent = "explore" | "claim-human-value" | "external-effect" | "replace-provider";

export type ExploreRequest = {
  intent: ExploreIntent;
  elements: string[];
  mechanisms?: string[];
  evidenceClasses?: string[];
};

type GraphNode = { id: string; kind: string; owner: string; title: string };
type Constraint = { id: string; kind: string; scope: string[]; statement: string; failureDisposition: string; refs: string[] };
type EvidenceClass = { id: string; owner: string; establishes: string; cannotEstablish: string };
type AdvisorySkill = { id: string; path: string; covers: string[]; authority: string; removable: boolean; canBlockCreativeComposition: boolean };
type Pattern = {
  id: string;
  reference: string;
  authority: "ADVISORY_HYPOTHESIS_PATTERN";
  mechanisms: string[];
  hypothesis: string;
  confounds: string[];
  sourceRefs: string[];
  falsifier: string;
  canBlockNovelCombination: boolean;
};
type DecisionOperation = {
  id: string;
  description: string;
  constraintSeeds: string[];
  gateConstraints: string[];
  requiredEvidenceAll?: string[];
  requiredAdjudicationRules: string[];
  requiresAuthorityDecision?: boolean;
  authorityDecisionOwner?: string;
  defaultWhenUnresolved: string;
};

export type CreativeGraph = {
  graphId: string;
  nodes: GraphNode[];
  constraints: Constraint[];
  evidenceClasses: EvidenceClass[];
  creativePolicy: {
    defaultCreativeDisposition: "OPEN_EXPLORATION";
    unmodeledMechanismDisposition: "EXPLORE_NOT_BLOCK";
    componentEvidenceInheritance: "NEVER_AUTOMATIC";
    processModels: "OPTIONAL_SKILLS";
    creativeCombinationRule: string;
    unknownRule: string;
    hardBoundaries: string[];
  };
  advisorySkills: AdvisorySkill[];
  mechanismCombinationPatterns: Pattern[];
  decisionOperations: DecisionOperation[];
  __sourceDigest?: string;
};

type PatternMatch = Pattern & { matchedMechanisms: string[] };

export type MechanismExperience = {
  id: string;
  referenceGame: string;
  kind: string;
  mechanisms: string[];
  designProblem: string;
  interaction: string;
  playerDecisionHypothesis: string;
  observedContext: string;
  confounds: string[];
  transferRisks: string[];
  falsifier: string;
  cheapProbe: string;
  sourceRefs: string[];
  authority: "ADVISORY_HYPOTHESIS";
  inferenceLevel: "SOURCE_GROUNDED_HYPOTHESIS";
  humanOutcomeEstablished: false;
  canBlockNovelCombination: false;
  tags: string[];
};

export type MechanismExperienceLibrary = {
  libraryId: string;
  experiences: MechanismExperience[];
  __sourceDigest?: string;
};

type ExperienceMatch = MechanismExperience & { matchedMechanisms: string[] };

export type CreativeTrace = {
  schemaVersion: 1;
  kind: "ordivon.game.composition-exploration-trace";
  graph: {
    graphId: string;
    sourcePath: string;
    sourceDigest: string;
    currentness: "WORKSPACE_GRAPH_ONLY_NOT_LIVE_OWNER_STATE";
  };
  request: {
    intent: ExploreIntent;
    elements: string[];
    mechanisms: string[];
    evidenceClasses: string[];
  };
  resolvedElements: Array<{ input: string; modeled: boolean; node?: GraphNode }>;
  novelUnmodeledElements: string[];
  advisorySkills: AdvisorySkill[];
  patternMatches: PatternMatch[];
  experienceLibrary: {
    libraryId: string;
    sourcePath: string;
    sourceDigest: string;
  };
  experienceMatches: ExperienceMatch[];
  epistemicFences: string[];
  requiredEvidenceClasses: string[];
  disposition: "OPEN_EXPLORATION" | "EVIDENCE_NOT_TRANSFERABLE" | "EXTERNAL_EFFECT_BLOCKED" | "AUTHORITY_REQUIRED";
  semanticAuthorityClaimed: false;
  compositionEvidenceInherited: false;
  notes: string[];
};

function sha256(value: string): string {
  return `sha256:${createHash("sha256").update(value).digest("hex")}`;
}

function unique(values: string[]): string[] {
  return [...new Set(values)];
}

export function loadGameCreativeGraph(root = PROJECT_ROOT): CreativeGraph {
  const source = readFileSync(resolve(root, GRAPH_PATH), "utf8");
  const graph = JSON.parse(source) as CreativeGraph;
  Object.defineProperty(graph, "__sourceDigest", { value: sha256(source), enumerable: false });
  return graph;
}

export function loadMechanismExperienceLibrary(root = PROJECT_ROOT): MechanismExperienceLibrary {
  const source = readFileSync(resolve(root, EXPERIENCE_PATH), "utf8");
  const library = JSON.parse(source) as MechanismExperienceLibrary;
  Object.defineProperty(library, "__sourceDigest", { value: sha256(source), enumerable: false });
  return library;
}

function validateRequest(request: ExploreRequest, graph: CreativeGraph): void {
  if (request.elements.length === 0) throw new Error("Composition exploration requires at least one element");
  const evidenceIds = new Set(graph.evidenceClasses.map((item) => item.id));
  for (const evidence of request.evidenceClasses ?? []) {
    if (!evidenceIds.has(evidence)) throw new Error(`Unknown evidence class: ${evidence}`);
  }
}

function patternMatches(mechanisms: string[], patterns: Pattern[]): PatternMatch[] {
  const requested = new Set(mechanisms);
  return patterns
    .map((pattern) => ({ ...pattern, matchedMechanisms: pattern.mechanisms.filter((mechanism) => requested.has(mechanism)) }))
    .filter((pattern) => pattern.matchedMechanisms.length > 0)
    .sort((a, b) => b.matchedMechanisms.length - a.matchedMechanisms.length || a.id.localeCompare(b.id));
}

function experienceMatches(mechanisms: string[], experiences: MechanismExperience[]): ExperienceMatch[] {
  const requested = new Set(mechanisms);
  return experiences
    .map((experience) => ({ ...experience, matchedMechanisms: experience.mechanisms.filter((mechanism) => requested.has(mechanism)) }))
    .filter((experience) => experience.matchedMechanisms.length > 0)
    .sort((a, b) => b.matchedMechanisms.length - a.matchedMechanisms.length || a.id.localeCompare(b.id));
}

export function exploreGameComposition(
  request: ExploreRequest,
  graph = loadGameCreativeGraph(),
  experienceLibrary = loadMechanismExperienceLibrary(),
): CreativeTrace {
  validateRequest(request, graph);
  const mechanisms = unique(request.mechanisms ?? []);
  const evidenceClasses = unique(request.evidenceClasses ?? []);
  const evidenceSet = new Set(evidenceClasses);
  const nodeMap = new Map(graph.nodes.map((node) => [node.id, node]));
  const resolvedElements = request.elements.map((input) => {
    const node = nodeMap.get(input);
    return node ? { input, modeled: true, node } : { input, modeled: false };
  });
  const novelUnmodeledElements = resolvedElements.filter((item) => !item.modeled).map((item) => item.input);

  const epistemicFences: string[] = [];
  if (request.elements.length >= 2 && graph.constraints.some((c) => c.id === "constraint.evidence.composition-noninheritance")) {
    epistemicFences.push("constraint.evidence.composition-noninheritance");
  }

  const requiredEvidenceClasses: string[] = [];
  let disposition: CreativeTrace["disposition"] = "OPEN_EXPLORATION";

  if (request.intent === "claim-human-value") {
    if (!evidenceSet.has("evidence.human-participant")) {
      requiredEvidenceClasses.push("evidence.human-participant");
      disposition = "EVIDENCE_NOT_TRANSFERABLE";
    }
  } else if (request.intent === "external-effect") {
    if (!evidenceSet.has("evidence.explicit-effect-authority")) {
      requiredEvidenceClasses.push("evidence.explicit-effect-authority");
    }
    if (!evidenceSet.has("evidence.owner-currentness")) {
      requiredEvidenceClasses.push("evidence.owner-currentness");
    }
    if (requiredEvidenceClasses.length > 0) disposition = "EXTERNAL_EFFECT_BLOCKED";
  } else if (request.intent === "replace-provider") {
    disposition = "AUTHORITY_REQUIRED";
  }

  const notes = [
    graph.creativePolicy.creativeCombinationRule,
    graph.creativePolicy.unknownRule,
    "Pattern matches are broad analogies from prior teardowns; Experience matches are finer source-grounded interaction hypotheses with cheap falsifiers. Neither is a recipe, ranking, recommendation, or rejection rule.",
    "Evidence attached to components or reference games is not inherited by the new composition; emergent behavior may differ in either direction.",
  ];
  if (novelUnmodeledElements.length > 0) {
    notes.push("Unmodeled elements were preserved verbatim as exploration inputs instead of rejected by the graph.");
  }

  return {
    schemaVersion: 1,
    kind: "ordivon.game.composition-exploration-trace",
    graph: {
      graphId: graph.graphId,
      sourcePath: GRAPH_PATH,
      sourceDigest: graph.__sourceDigest ?? sha256(JSON.stringify(graph)),
      currentness: "WORKSPACE_GRAPH_ONLY_NOT_LIVE_OWNER_STATE",
    },
    request: { intent: request.intent, elements: [...request.elements], mechanisms, evidenceClasses },
    resolvedElements,
    novelUnmodeledElements,
    advisorySkills: [...graph.advisorySkills],
    patternMatches: patternMatches(mechanisms, graph.mechanismCombinationPatterns),
    experienceLibrary: {
      libraryId: experienceLibrary.libraryId,
      sourcePath: EXPERIENCE_PATH,
      sourceDigest: experienceLibrary.__sourceDigest ?? sha256(JSON.stringify(experienceLibrary)),
    },
    experienceMatches: experienceMatches(mechanisms, experienceLibrary.experiences),
    epistemicFences,
    requiredEvidenceClasses: unique(requiredEvidenceClasses),
    disposition,
    semanticAuthorityClaimed: false,
    compositionEvidenceInherited: false,
    notes,
  };
}

function argument(name: string): string | undefined {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

function list(value: string | undefined): string[] {
  return value ? value.split(",").map((item) => item.trim()).filter(Boolean) : [];
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const intent = (argument("--intent") ?? "explore") as ExploreIntent;
  const elements = list(argument("--elements"));
  const mechanisms = list(argument("--mechanisms"));
  const evidenceClasses = list(argument("--evidence"));
  if (elements.length === 0) {
    process.stderr.write("Usage: node scripts/composition-explorer.ts --intent <explore|claim-human-value|external-effect|replace-provider> --elements <item,item> [--mechanisms <tag,tag>] [--evidence <class,class>]\n");
    process.exitCode = 2;
  } else {
    process.stdout.write(`${JSON.stringify(exploreGameComposition({ intent, elements, mechanisms, evidenceClasses }), null, 2)}\n`);
  }
}
