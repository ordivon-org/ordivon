/** Source-grounded Game relationship projection, independent of file and CLI I/O.

Input source text remains canonical for digest provenance; the returned graph is
an advisory retrieval view, not a ranking, causal claim, or closed ontology.
*/
import { createHash } from "node:crypto";

export const LIBRARY_PATH = "knowledge/game_mechanism_experience_library_r1.json";
export const SPEC_PATH = "knowledge/game_mechanism_relationship_spec_r1.json";

type JsonSource = { raw: string; value: any };

function digest(raw: string): string {
  return `sha256:${createHash("sha256").update(raw).digest("hex")}`;
}

function unique<T>(items: T[]): T[] {
  return [...new Set(items)];
}

type MechanismNodeAccumulator = {
  id: string;
  experienceRefs: string[];
  referenceGames: string[];
  relationKinds: string[];
};

export function buildMechanismRelationshipGraphFromSources(libraryFile: JsonSource, specFile: JsonSource): any {
  const library = libraryFile.value;
  const spec = specFile.value;
  const experienceMap = new Map(library.experiences.map((experience: any) => [experience.id, experience]));

  const resolveExperiences = (refs: string[], owner: string): any[] => refs.map((ref) => {
    const experience = experienceMap.get(ref);
    if (!experience) throw new Error(`${owner} references unknown experience ${ref}`);
    return experience;
  });

  const mechanismMap = new Map<string, MechanismNodeAccumulator>();
  const withinExperienceEdges: any[] = [];

  for (const experience of library.experiences) {
    for (const mechanism of experience.mechanisms) {
      const node: MechanismNodeAccumulator = mechanismMap.get(mechanism) ?? { id: mechanism, experienceRefs: [], referenceGames: [], relationKinds: [] };
      node.experienceRefs.push(experience.id);
      node.referenceGames.push(experience.referenceGame);
      node.relationKinds.push(experience.kind);
      mechanismMap.set(mechanism, node);
    }
    for (let i = 0; i < experience.mechanisms.length; i++) {
      for (let j = i + 1; j < experience.mechanisms.length; j++) {
        const pair = [experience.mechanisms[i], experience.mechanisms[j]].sort();
        withinExperienceEdges.push({
          id: `edge.${experience.id}.${pair[0]}::${pair[1]}`,
          a: pair[0],
          b: pair[1],
          experienceRef: experience.id,
          referenceGame: experience.referenceGame,
          relationKind: experience.kind,
          authority: "OBSERVED_WITHIN_SOURCE_GROUNDED_EXPERIENCE",
          causalRelationEstablished: false,
          canBlockNovelCombination: false,
        });
      }
    }
  }

  const mechanismNodes = [...mechanismMap.values()].map((node) => ({
    id: node.id,
    experienceRefs: unique(node.experienceRefs).sort(),
    referenceGames: unique(node.referenceGames).sort(),
    relationKinds: unique(node.relationKinds).sort(),
    appearanceCount: node.experienceRefs.length,
    authority: "RETRIEVAL_INDEX_ONLY",
    closedVocabulary: false,
  })).sort((a, b) => a.id.localeCompare(b.id));

  const retrievalFacets = spec.retrievalFacets.map((facet: any) => {
    const experiences = resolveExperiences(facet.experienceRefs, facet.id);
    const availableMechanisms = new Set(experiences.flatMap((experience: any) => experience.mechanisms));
    for (const mechanism of facet.mechanismTags) {
      if (!availableMechanisms.has(mechanism)) throw new Error(`${facet.id} mechanism ${mechanism} is not present in its experience refs`);
    }
    return {
      ...facet,
      referenceGames: unique(experiences.map((experience: any) => experience.referenceGame)).sort(),
      relationKinds: unique(experiences.map((experience: any) => experience.kind)).sort(),
      sourceRefs: unique(experiences.flatMap((experience: any) => experience.sourceRefs)).sort(),
      authority: "ADVISORY_RETRIEVAL_ALIAS",
      exhaustive: false,
      canRejectUnmatchedMechanism: false,
    };
  });

  const facetIds = new Set(retrievalFacets.map((facet: any) => facet.id));
  const conditionalities = spec.conditionalities.map((item: any) => {
    const experiences = resolveExperiences(item.experienceRefs, item.id);
    for (const facetId of item.facetIds) if (!facetIds.has(facetId)) throw new Error(`${item.id} references unknown facet ${facetId}`);
    const availableMechanisms = new Set(experiences.flatMap((experience: any) => experience.mechanisms));
    for (const mechanism of item.triggerMechanisms) {
      if (!availableMechanisms.has(mechanism)) throw new Error(`${item.id} trigger ${mechanism} is not present in its experience refs`);
    }
    return {
      ...item,
      referenceGames: unique(experiences.map((experience: any) => experience.referenceGame)).sort(),
      relationKinds: unique(experiences.map((experience: any) => experience.kind)).sort(),
      sourceRefs: unique(experiences.flatMap((experience: any) => experience.sourceRefs)).sort(),
      authority: "ADVISORY_CONDITIONAL_HYPOTHESIS",
      inferenceLevel: "CROSS_GAME_SOURCE_GROUNDED_CONDITIONAL",
      humanOutcomeEstablished: false,
      canBlockNovelCombination: false,
    };
  });

  return {
    schemaVersion: 1,
    graphId: "ordivon-game-mechanism-relationship-graph-r1",
    generatedOn: "2026-09-18",
    sourceLibrary: { path: LIBRARY_PATH, digest: digest(libraryFile.raw), libraryId: library.libraryId },
    sourceSpec: { path: SPEC_PATH, digest: digest(specFile.raw), specId: spec.specId },
    policy: {
      closedOntology: false,
      canBlockNovelCombination: false,
      recommendationAuthority: "NONE",
      humanEvidenceInherited: false,
      edgeSemantics: "Within-experience edges mean co-presence inside one source-grounded hypothesis only; they do not establish causal effect or universal compatibility.",
      facetSemantics: "Retrieval facets are authored semantic aliases for cross-game recall; they are incomplete and non-exclusive.",
      conditionalitySemantics: "Conditionalities preserve apparent conflicts and context distinctions; they suggest discriminating experiments rather than verdicts.",
    },
    mechanismNodes,
    withinExperienceEdges,
    retrievalFacets,
    conditionalities,
  };
}
