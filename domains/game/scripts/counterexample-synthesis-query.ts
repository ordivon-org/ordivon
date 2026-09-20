import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const COUNTEREXAMPLE_SYNTHESIS_PATH = "standards/game_counterexample_synthesis_r1.json";
const MEMORY_PATH = "standards/game_design_counterexample_memory_r1.json";
const EXPERIENCE_PATH = "standards/game_mechanism_experience_library_r1.json";

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

export type EnrichedCounterexampleTheme = CounterexampleTheme & {
  mechanisms: string[];
  referenceGames: string[];
  sourceRefs: string[];
  counterexampleMechanisms: Array<{ counterexampleRef: string; mechanisms: string[] }>;
};

export type CounterexampleSynthesisQuery = {
  q?: string;
  theme?: string;
  mechanism?: string;
  counterexample?: string;
  limit?: number;
};

export type CounterexampleSynthesisQueryResult = {
  schemaVersion: 1;
  kind: "ordivon.game.counterexample-synthesis-query";
  query: CounterexampleSynthesisQuery;
  totalMatched: number;
  returned: number;
  items: Array<EnrichedCounterexampleTheme & { matchedMechanisms: string[]; matchedCounterexampleRefs: string[] }>;
  semanticAuthorityClaimed: false;
  recommendationClaimed: false;
  rankingClaimed: false;
  blacklistClaimed: false;
  notes: string[];
};

function readJson(root: string, path: string): any {
  return JSON.parse(readFileSync(resolve(root, path), "utf8"));
}

function normalize(value?: string): string | undefined {
  const result = value?.trim().toLowerCase();
  return result || undefined;
}

export function loadCounterexampleSynthesis(root = ROOT): any {
  return readJson(root, COUNTEREXAMPLE_SYNTHESIS_PATH);
}

export function enrichCounterexampleThemes(root = ROOT): EnrichedCounterexampleTheme[] {
  const synthesis = loadCounterexampleSynthesis(root);
  const memory = readJson(root, MEMORY_PATH);
  const library = readJson(root, EXPERIENCE_PATH);
  const counterexamples = new Map(memory.counterexamples.map((item: any) => [item.id, item]));
  const experiences = new Map(library.experiences.map((item: any) => [item.id, item]));

  return synthesis.themes.map((theme: CounterexampleTheme) => {
    const resolvedCounterexamples = theme.counterexampleRefs.map((ref) => {
      const item = counterexamples.get(ref) as any;
      if (!item) throw new Error(`${theme.id} references unknown Counterexample ${ref}`);
      return item;
    });
    const counterexampleMechanisms = resolvedCounterexamples.map((counterexample: any) => {
      const resolvedExperiences = counterexample.experienceRefs.map((ref: string) => {
        const item = experiences.get(ref) as any;
        if (!item) throw new Error(`${counterexample.id} references unknown Experience ${ref}`);
        return item;
      });
      return {
        counterexampleRef: counterexample.id,
        mechanisms: [...new Set(resolvedExperiences.flatMap((item: any) => item.mechanisms))].sort() as string[],
      };
    });
    return {
      ...theme,
      mechanisms: [...new Set(counterexampleMechanisms.flatMap((item) => item.mechanisms))].sort(),
      referenceGames: [...new Set(resolvedCounterexamples.flatMap((item: any) => item.referenceGames))].sort() as string[],
      sourceRefs: [...new Set(resolvedCounterexamples.flatMap((item: any) => item.sourceRefs))].sort() as string[],
      counterexampleMechanisms,
    };
  });
}

export function queryCounterexampleSynthesis(query: CounterexampleSynthesisQuery): CounterexampleSynthesisQueryResult {
  const q = normalize(query.q);
  const theme = normalize(query.theme);
  const mechanism = normalize(query.mechanism);
  const counterexample = normalize(query.counterexample);
  const limit = Number.isInteger(query.limit) && (query.limit ?? 0) > 0 ? Math.min(query.limit!, 100) : 50;

  const matched = enrichCounterexampleThemes()
    .map((item) => ({
      ...item,
      matchedMechanisms: mechanism ? item.mechanisms.filter((value) => value.toLowerCase() === mechanism) : [],
      matchedCounterexampleRefs: counterexample
        ? item.counterexampleRefs.filter((value) => value.toLowerCase() === counterexample)
        : mechanism
          ? item.counterexampleMechanisms
              .filter((entry) => entry.mechanisms.some((value) => value.toLowerCase() === mechanism))
              .map((entry) => entry.counterexampleRef)
          : [],
    }))
    .filter((item) => {
      if (q && !JSON.stringify(item).toLowerCase().includes(q)) return false;
      if (theme && item.id.toLowerCase() !== theme) return false;
      if (mechanism && item.matchedMechanisms.length === 0) return false;
      if (counterexample && item.matchedCounterexampleRefs.length === 0) return false;
      return true;
    });

  return {
    schemaVersion: 1,
    kind: "ordivon.game.counterexample-synthesis-query",
    query: { ...query, limit },
    totalMatched: matched.length,
    returned: Math.min(matched.length, limit),
    items: matched.slice(0, limit),
    semanticAuthorityClaimed: false,
    recommendationClaimed: false,
    rankingClaimed: false,
    blacklistClaimed: false,
    notes: [
      "Counterexample themes are overlapping retrieval aliases over source-grounded Counterexamples, not a failure ontology or exhaustive taxonomy.",
      "Theme membership does not rank severity, probability, design quality, or transferability.",
      "A theme match suggests related attack surfaces and retrieval questions only; it cannot reject, recommend, rank, or block a novel composition.",
    ],
  };
}

function arg(name: string): string | undefined {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const query: CounterexampleSynthesisQuery = {};
  const q = arg("--q");
  const theme = arg("--theme");
  const mechanism = arg("--mechanism");
  const counterexample = arg("--counterexample");
  const rawLimit = arg("--limit");
  if (q !== undefined) query.q = q;
  if (theme !== undefined) query.theme = theme;
  if (mechanism !== undefined) query.mechanism = mechanism;
  if (counterexample !== undefined) query.counterexample = counterexample;
  if (rawLimit !== undefined) query.limit = Number(rawLimit);
  process.stdout.write(`${JSON.stringify(queryCounterexampleSynthesis(query), null, 2)}\n`);
}
