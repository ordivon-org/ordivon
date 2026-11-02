import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { boundedQueryLimit, cliArgument, normalizeQueryFilter } from "../src/query-input.ts";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const LIBRARY_PATH = "standards/game_mechanism_experience_library_r1.json";

export type MechanismExperienceQuery = {
  q?: string;
  mechanism?: string;
  reference?: string;
  kind?: string;
  tag?: string;
  limit?: number;
};

export type MechanismExperienceQueryResult = {
  schemaVersion: 1;
  kind: "ordivon.game.mechanism-experience-query";
  query: MechanismExperienceQuery;
  totalMatched: number;
  returned: number;
  items: any[];
  semanticAuthorityClaimed: false;
  recommendationClaimed: false;
  notes: string[];
};

function library(): any {
  return JSON.parse(readFileSync(resolve(ROOT, LIBRARY_PATH), "utf8"));
}

export function queryMechanismExperiences(query: MechanismExperienceQuery): MechanismExperienceQueryResult {
  const q = normalizeQueryFilter(query.q);
  const mechanism = normalizeQueryFilter(query.mechanism);
  const reference = normalizeQueryFilter(query.reference);
  const kind = normalizeQueryFilter(query.kind);
  const tag = normalizeQueryFilter(query.tag);
  const limit = boundedQueryLimit(query.limit, 200);

  const matched = library().experiences.filter((experience: any) => {
    if (q && !JSON.stringify(experience).toLowerCase().includes(q)) return false;
    if (mechanism && !experience.mechanisms.some((item: string) => item.toLowerCase() === mechanism)) return false;
    if (reference && String(experience.referenceGame).toLowerCase() !== reference) return false;
    if (kind && String(experience.kind).toLowerCase() !== kind) return false;
    if (tag && !(experience.tags ?? []).some((item: string) => item.toLowerCase() === tag)) return false;
    return true;
  });

  return {
    schemaVersion: 1,
    kind: "ordivon.game.mechanism-experience-query",
    query: { ...query, limit },
    totalMatched: matched.length,
    returned: Math.min(matched.length, limit),
    items: matched.slice(0, limit),
    semanticAuthorityClaimed: false,
    recommendationClaimed: false,
    notes: [
      "Matches are source-grounded advisory hypotheses, not scores, recipes, recommendations, or rejection rules.",
      "Use each record's confounds, transfer risks, falsifier, and cheap probe before transferring a relationship.",
      "No Human outcome evidence transfers from a reference project into a new composition.",
    ],
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const query: MechanismExperienceQuery = {};
  const q = cliArgument("--q");
  const mechanism = cliArgument("--mechanism");
  const reference = cliArgument("--reference");
  const kind = cliArgument("--kind");
  const tag = cliArgument("--tag");
  const rawLimit = cliArgument("--limit");
  if (q !== undefined) query.q = q;
  if (mechanism !== undefined) query.mechanism = mechanism;
  if (reference !== undefined) query.reference = reference;
  if (kind !== undefined) query.kind = kind;
  if (tag !== undefined) query.tag = tag;
  if (rawLimit !== undefined) query.limit = Number(rawLimit);
  process.stdout.write(`${JSON.stringify(queryMechanismExperiences(query), null, 2)}\n`);
}
