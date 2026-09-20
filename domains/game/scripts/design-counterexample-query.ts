import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const MEMORY_PATH = "standards/game_design_counterexample_memory_r1.json";
const EXPERIENCE_PATH = "standards/game_mechanism_experience_library_r1.json";

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
  return JSON.parse(readFileSync(resolve(ROOT, path), "utf8"));
}

function normalize(value?: string): string | undefined {
  const result = value?.trim().toLowerCase();
  return result || undefined;
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
  const q = normalize(query.q);
  const mechanism = normalize(query.mechanism);
  const game = normalize(query.game);
  const kind = normalize(query.kind);
  const limit = Number.isInteger(query.limit) && (query.limit ?? 0) > 0 ? Math.min(query.limit!, 200) : 50;

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

function arg(name: string): string | undefined {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const query: DesignCounterexampleQuery = {};
  const q = arg("--q");
  const mechanism = arg("--mechanism");
  const game = arg("--game");
  const kind = arg("--kind");
  const rawLimit = arg("--limit");
  if (q !== undefined) query.q = q;
  if (mechanism !== undefined) query.mechanism = mechanism;
  if (game !== undefined) query.game = game;
  if (kind !== undefined) query.kind = kind;
  if (rawLimit !== undefined) query.limit = Number(rawLimit);
  process.stdout.write(`${JSON.stringify(queryDesignCounterexamples(query), null, 2)}\n`);
}
