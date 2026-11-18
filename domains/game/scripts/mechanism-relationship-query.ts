import { readFileSync } from "node:fs";
import { buildMechanismRelationshipGraphFromSources, LIBRARY_PATH, SPEC_PATH } from "../src/mechanism-relationship-graph.ts";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { boundedQueryLimit, normalizeQueryFilter } from "../src/query-input.ts";
import { cliArgument, cliQueryArguments } from "./cli-argument.ts";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

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
  // Filesystem ownership remains in this CLI; derivation remains pure.
  function source(path: string): { raw: string; value: any } {
    const raw = readFileSync(resolve(ROOT, path), "utf8");
    return { raw, value: JSON.parse(raw) };
  }
  return buildMechanismRelationshipGraphFromSources(source(LIBRARY_PATH), source(SPEC_PATH));
}

export function queryMechanismRelationships(query: MechanismRelationshipQuery): MechanismRelationshipQueryResult {
  const g = graph();
  const q = normalizeQueryFilter(query.q);
  const mechanism = normalizeQueryFilter(query.mechanism);
  const game = normalizeQueryFilter(query.game);
  const facet = normalizeQueryFilter(query.facet);
  const limit = boundedQueryLimit(query.limit, 200);

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

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const query: MechanismRelationshipQuery = {
    type: (cliArgument("--type") ?? "conditionalities") as MechanismRelationshipQueryType,
    ...cliQueryArguments(["q", "mechanism", "game", "facet"]),
  };
  process.stdout.write(`${JSON.stringify(queryMechanismRelationships(query), null, 2)}\n`);
}
