import { readGameKnowledge } from "../src/knowledge-file.ts";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { boundedQueryLimit, cliArgument, normalizeQueryFilter } from "../src/query-input.ts";

const MEMORY_PATH = "knowledge/game_design_counterexample_memory_r1.json";
const EXPERIENCE_PATH = "knowledge/game_mechanism_experience_library_r1.json";

export type DesignCounterexampleQuery = {
  q?: string;
  mechanism?: string;
  game?: string;
  kind?: string;
  limit?: number;
};

export type DesignCounterexampleQueryResult = {
  schemaVersion: 1;
  kind: "ordivon.game.design-counterexample-query";
  query: DesignCounterexampleQuery;
  totalMatched: number;
  returned: number;
  items: any[];
  semanticAuthorityClaimed: false;
  recommendationClaimed: false;
  blacklistClaimed: false;
  notes: string[];
};

function readJson(path: string): any {
  return readGameKnowledge(path);
}

function enrichCounterexamples(): any[] {
  const memory = readJson(MEMORY_PATH);
  const library = readJson(EXPERIENCE_PATH);
  const experiences = new Map(library.experiences.map((experience: any) => [experience.id, experience]));

  return memory.counterexamples.map((counterexample: any) => {
    const resolved = counterexample.experienceRefs.map((ref: string) => {
      const experience = experiences.get(ref) as any;
      if (!experience) throw new Error(`${counterexample.id} references unknown Experience ${ref}`);
      return experience;
    });
    return {
      ...counterexample,
      mechanisms: [...new Set(resolved.flatMap((experience: any) => experience.mechanisms))].sort(),
    };
  });
}

export function queryDesignCounterexamples(query: DesignCounterexampleQuery): DesignCounterexampleQueryResult {
  const q = normalizeQueryFilter(query.q);
  const mechanism = normalizeQueryFilter(query.mechanism);
  const game = normalizeQueryFilter(query.game);
  const kind = normalizeQueryFilter(query.kind);
  const limit = boundedQueryLimit(query.limit, 200);

  const matched = enrichCounterexamples().filter((item: any) => {
    if (q && !JSON.stringify(item).toLowerCase().includes(q)) return false;
    if (mechanism && !item.mechanisms.some((value: string) => value.toLowerCase() === mechanism)) return false;
    if (game && !item.referenceGames.some((value: string) => value.toLowerCase() === game)) return false;
    if (kind && String(item.kind).toLowerCase() !== kind) return false;
    return true;
  });

  return {
    schemaVersion: 1,
    kind: "ordivon.game.design-counterexample-query",
    query: { ...query, limit },
    totalMatched: matched.length,
    returned: Math.min(matched.length, limit),
    items: matched.slice(0, limit),
    semanticAuthorityClaimed: false,
    recommendationClaimed: false,
    blacklistClaimed: false,
    notes: [
      "A counterexample weakens an over-broad assumption under named conditions; it does not become an inverse universal rule.",
      "Mechanisms are resolved through referenced Experience records rather than duplicated into a second ontology.",
      "Matches suggest attack surfaces and cheap discriminators, never rejection, recommendation, ranking, or Human outcome evidence.",
    ],
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const query: DesignCounterexampleQuery = {};
  const q = cliArgument("--q");
  const mechanism = cliArgument("--mechanism");
  const game = cliArgument("--game");
  const kind = cliArgument("--kind");
  const rawLimit = cliArgument("--limit");
  if (q !== undefined) query.q = q;
  if (mechanism !== undefined) query.mechanism = mechanism;
  if (game !== undefined) query.game = game;
  if (kind !== undefined) query.kind = kind;
  if (rawLimit !== undefined) query.limit = Number(rawLimit);
  process.stdout.write(`${JSON.stringify(queryDesignCounterexamples(query), null, 2)}\n`);
}
