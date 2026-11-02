import { readGameKnowledge } from "../src/knowledge-file.ts";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { boundedQueryLimit, normalizeQueryFilter } from "../src/query-input.ts";
import { cliArgument } from "./cli-argument.ts";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const COUNTEREXAMPLE_SYNTHESIS_PATH = "knowledge/game_counterexample_synthesis_r1.json";
const MEMORY_PATH = "knowledge/game_design_counterexample_memory_r1.json";
const EXPERIENCE_PATH = "knowledge/game_mechanism_experience_library_r1.json";

export type { CounterexampleTheme, EnrichedCounterexampleTheme } from "../src/counterexample-projection.ts";
import {
  projectCounterexampleThemes,
  type EnrichedCounterexampleTheme,
} from "../src/counterexample-projection.ts";

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
  return readGameKnowledge(path, root);
}

export function loadCounterexampleSynthesis(root = ROOT): any {
  return readJson(root, COUNTEREXAMPLE_SYNTHESIS_PATH);
}

export function enrichCounterexampleThemes(root = ROOT): EnrichedCounterexampleTheme[] {
  return projectCounterexampleThemes(
    loadCounterexampleSynthesis(root).themes,
    readJson(root, MEMORY_PATH).counterexamples,
    readJson(root, EXPERIENCE_PATH).experiences,
  );
}

export function queryCounterexampleSynthesis(query: CounterexampleSynthesisQuery): CounterexampleSynthesisQueryResult {
  const q = normalizeQueryFilter(query.q);
  const theme = normalizeQueryFilter(query.theme);
  const mechanism = normalizeQueryFilter(query.mechanism);
  const counterexample = normalizeQueryFilter(query.counterexample);
  const limit = boundedQueryLimit(query.limit, 100);

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

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const query: CounterexampleSynthesisQuery = {};
  const q = cliArgument("--q");
  const theme = cliArgument("--theme");
  const mechanism = cliArgument("--mechanism");
  const counterexample = cliArgument("--counterexample");
  const rawLimit = cliArgument("--limit");
  if (q !== undefined) query.q = q;
  if (theme !== undefined) query.theme = theme;
  if (mechanism !== undefined) query.mechanism = mechanism;
  if (counterexample !== undefined) query.counterexample = counterexample;
  if (rawLimit !== undefined) query.limit = Number(rawLimit);
  process.stdout.write(`${JSON.stringify(queryCounterexampleSynthesis(query), null, 2)}\n`);
}
