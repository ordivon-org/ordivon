import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

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

function normalize(value?: string): string | undefined {
  const result = value?.trim().toLowerCase();
  return result || undefined;
}

export function queryMechanismExperiences(query: MechanismExperienceQuery): MechanismExperienceQueryResult {
  const q = normalize(query.q);
  const mechanism = normalize(query.mechanism);
  const reference = normalize(query.reference);
  const kind = normalize(query.kind);
  const tag = normalize(query.tag);
  const limit = Number.isInteger(query.limit) && (query.limit ?? 0) > 0 ? Math.min(query.limit!, 200) : 50;

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

function arg(name: string): string | undefined {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const query: MechanismExperienceQuery = {};
  const q = arg("--q");
  const mechanism = arg("--mechanism");
  const reference = arg("--reference");
  const kind = arg("--kind");
  const tag = arg("--tag");
  const rawLimit = arg("--limit");
  if (q !== undefined) query.q = q;
  if (mechanism !== undefined) query.mechanism = mechanism;
  if (reference !== undefined) query.reference = reference;
  if (kind !== undefined) query.kind = kind;
  if (tag !== undefined) query.tag = tag;
  if (rawLimit !== undefined) query.limit = Number(rawLimit);
  process.stdout.write(`${JSON.stringify(queryMechanismExperiences(query), null, 2)}\n`);
}
