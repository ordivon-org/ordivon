import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const GRAPH_PATH = "standards/game_mechanism_relationship_graph_r1.json";

export type MechanismRelationshipQueryType = "mechanisms" | "edges" | "facets" | "conditionalities";

export type MechanismRelationshipQuery = {
  type: MechanismRelationshipQueryType;
  q?: string;
  mechanism?: string;
  game?: string;
  facet?: string;
  limit?: number;
};

export type MechanismRelationshipQueryResult = {
  schemaVersion: 1;
  kind: "ordivon.game.mechanism-relationship-query";
  query: MechanismRelationshipQuery;
  totalMatched: number;
  returned: number;
  items: any[];
  semanticAuthorityClaimed: false;
  recommendationClaimed: false;
  compatibilityVerdictClaimed: false;
  notes: string[];
};

function graph(): any {
  return JSON.parse(readFileSync(resolve(ROOT, GRAPH_PATH), "utf8"));
}

function normalize(value?: string): string | undefined {
  const result = value?.trim().toLowerCase();
  return result || undefined;
}

export function queryMechanismRelationships(query: MechanismRelationshipQuery): MechanismRelationshipQueryResult {
  const g = graph();
  const q = normalize(query.q);
  const mechanism = normalize(query.mechanism);
  const game = normalize(query.game);
  const facet = normalize(query.facet);
  const limit = Number.isInteger(query.limit) && (query.limit ?? 0) > 0 ? Math.min(query.limit!, 200) : 50;

  let items: any[];
  if (query.type === "mechanisms") items = g.mechanismNodes;
  else if (query.type === "edges") items = g.withinExperienceEdges;
  else if (query.type === "facets") items = g.retrievalFacets;
  else if (query.type === "conditionalities") items = g.conditionalities;
  else throw new Error(`Unknown relationship query type: ${String(query.type)}`);

  const matched = items.filter((item) => {
    if (q && !JSON.stringify(item).toLowerCase().includes(q)) return false;
    if (mechanism) {
      const mechanisms = query.type === "mechanisms"
        ? [item.id]
        : query.type === "edges"
          ? [item.a, item.b]
          : query.type === "facets"
            ? item.mechanismTags
            : item.triggerMechanisms;
      if (!mechanisms.some((value: string) => value.toLowerCase() === mechanism)) return false;
    }
    if (game) {
      const games = query.type === "edges" ? [item.referenceGame] : item.referenceGames ?? [];
      if (!games.some((value: string) => value.toLowerCase() === game)) return false;
    }
    if (facet) {
      if (query.type === "facets") {
        if (String(item.id).toLowerCase() !== facet) return false;
      } else if (query.type === "conditionalities") {
        if (!(item.facetIds ?? []).some((value: string) => value.toLowerCase() === facet)) return false;
      } else {
        return false;
      }
    }
    return true;
  });

  return {
    schemaVersion: 1,
    kind: "ordivon.game.mechanism-relationship-query",
    query: { ...query, limit },
    totalMatched: matched.length,
    returned: Math.min(matched.length, limit),
    items: matched.slice(0, limit),
    semanticAuthorityClaimed: false,
    recommendationClaimed: false,
    compatibilityVerdictClaimed: false,
    notes: [
      "Within-experience edges are co-occurrence evidence only, not causal or compatibility proof.",
      "Retrieval facets are incomplete semantic aliases, not an ontology or exhaustive mechanism classification.",
      "Conditionalities preserve apparent conflicts and transfer conditions; they suggest discriminating probes rather than verdicts.",
    ],
  };
}

function arg(name: string): string | undefined {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const query: MechanismRelationshipQuery = {
    type: (arg("--type") ?? "conditionalities") as MechanismRelationshipQueryType,
  };
  const q = arg("--q");
  const mechanism = arg("--mechanism");
  const game = arg("--game");
  const facet = arg("--facet");
  const rawLimit = arg("--limit");
  if (q !== undefined) query.q = q;
  if (mechanism !== undefined) query.mechanism = mechanism;
  if (game !== undefined) query.game = game;
  if (facet !== undefined) query.facet = facet;
  if (rawLimit !== undefined) query.limit = Number(rawLimit);
  process.stdout.write(`${JSON.stringify(queryMechanismRelationships(query), null, 2)}\n`);
}
