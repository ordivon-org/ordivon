import { readGameKnowledge } from "../src/knowledge-file.ts";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { boundedQueryLimit, normalizeQueryFilter } from "../src/query-input.ts";
import { cliQueryArguments } from "./cli-argument.ts";

const LIBRARY_PATH = "knowledge/game_mechanism_experience_library_r1.json";

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
  return readGameKnowledge(LIBRARY_PATH);
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
  const query: MechanismExperienceQuery = cliQueryArguments(["q", "mechanism", "reference", "kind", "tag"]);
  process.stdout.write(`${JSON.stringify(queryMechanismExperiences(query), null, 2)}\n`);
}
