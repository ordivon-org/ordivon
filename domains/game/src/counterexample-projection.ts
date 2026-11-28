/** Pure source-bound Counterexample projections.
 *
 * The records are evidence, never universal Game laws. This module owns only
 * reference resolution and derived fields; dataset I/O, filtering, and CLI
 * behavior remain with their existing consumers.
 */
export type MechanismExperience = {
  id: string;
  mechanisms: string[];
};

export type CounterexampleRecord = {
  id: string;
  experienceRefs: string[];
  referenceGames: string[];
  sourceRefs: string[];
  [field: string]: unknown;
};

export type CounterexampleTheme = {
  id: string;
  label: string;
  summary: string;
  counterexampleRefs: string[];
  retrievalQuestions: string[];
  falseUniversalizations: string[];
  authority: "ADVISORY_RETRIEVAL_THEME";
  exhaustive: false;
  canRankDesigns: false;
  canBlockNovelCombination: false;
  canMintRecommendation: false;
};

export type EnrichedCounterexample = CounterexampleRecord & { mechanisms: string[] };
export type EnrichedCounterexampleTheme = CounterexampleTheme & {
  mechanisms: string[];
  referenceGames: string[];
  sourceRefs: string[];
  counterexampleMechanisms: Array<{ counterexampleRef: string; mechanisms: string[] }>;
};

function sortedUnique(values: string[]): string[] {
  return [...new Set(values)].sort();
}

export function projectCounterexamples(
  counterexamples: readonly CounterexampleRecord[],
  experiences: readonly MechanismExperience[],
): EnrichedCounterexample[] {
  const byId = new Map(experiences.map((experience) => [experience.id, experience]));
  return counterexamples.map((counterexample) => ({
    ...counterexample,
    mechanisms: sortedUnique(counterexample.experienceRefs.flatMap((ref) => {
      const experience = byId.get(ref);
      if (!experience) throw new Error(`${counterexample.id} references unknown Experience ${ref}`);
      return experience.mechanisms;
    })),
  }));
}

export function projectCounterexampleThemes(
  themes: readonly CounterexampleTheme[],
  counterexamples: readonly CounterexampleRecord[],
  experiences: readonly MechanismExperience[],
): EnrichedCounterexampleTheme[] {
  const byId = new Map(projectCounterexamples(counterexamples, experiences).map((item) => [item.id, item]));
  return themes.map((theme) => {
    const resolved = theme.counterexampleRefs.map((ref) => {
      const item = byId.get(ref);
      if (!item) throw new Error(`${theme.id} references unknown Counterexample ${ref}`);
      return item;
    });
    const counterexampleMechanisms = resolved.map((item) => ({
      counterexampleRef: item.id,
      mechanisms: item.mechanisms,
    }));
    return {
      ...theme,
      mechanisms: sortedUnique(counterexampleMechanisms.flatMap((item) => item.mechanisms)),
      referenceGames: sortedUnique(resolved.flatMap((item) => item.referenceGames)),
      sourceRefs: sortedUnique(resolved.flatMap((item) => item.sourceRefs)),
      counterexampleMechanisms,
    };
  });
}
