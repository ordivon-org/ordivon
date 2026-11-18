import { readGameKnowledge } from "../src/knowledge-file.ts";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { boundedQueryLimit, normalizeQueryFilter } from "../src/query-input.ts";
import { cliArgument, cliQueryArguments } from "./cli-argument.ts";


type QueryType = "sources" | "teardowns" | "skills";

export type ExternalKnowledgeQuery = {
  type: QueryType;
  q?: string;
  category?: string;
  authority?: string;
  status?: string;
  limit?: number;
};

export type ExternalKnowledgeQueryResult = {
  schemaVersion: 1;
  kind: "ordivon.game.external-knowledge-query";
  query: ExternalKnowledgeQuery;
  totalMatched: number;
  returned: number;
  items: any[];
  semanticAuthorityClaimed: false;
  notes: string[];
};

function json(path: string): any {
  return readGameKnowledge(path);
}

function text(value: unknown): string {
  return JSON.stringify(value).toLowerCase();
}

export function queryExternalKnowledge(query: ExternalKnowledgeQuery): ExternalKnowledgeQueryResult {
  const q = normalizeQueryFilter(query.q);
  const category = normalizeQueryFilter(query.category);
  const authority = normalizeQueryFilter(query.authority);
  const status = normalizeQueryFilter(query.status);
  const limit = boundedQueryLimit(query.limit, 200);

  let items: any[];
  if (query.type === "sources") {
    items = json("knowledge/game_external_knowledge_base_r1.json").sources;
  } else if (query.type === "teardowns") {
    items = json("knowledge/game_teardown_queue_r1.json").targets;
  } else if (query.type === "skills") {
    items = json("knowledge/game_external_skill_watchlist_r1.json").skills;
  } else {
    throw new Error(`Unknown knowledge query type: ${String(query.type)}`);
  }

  const matched = items.filter((item) => {
    if (q && !text(item).includes(q)) return false;
    if (category && String(item.category ?? "").toLowerCase() !== category) return false;
    if (authority && String(item.authorityClass ?? item.instructionAuthority ?? "").toLowerCase() !== authority) return false;
    if (status && String(item.status ?? "").toLowerCase() !== status) return false;
    return true;
  });

  return {
    schemaVersion: 1,
    kind: "ordivon.game.external-knowledge-query",
    query: { ...query, limit },
    totalMatched: matched.length,
    returned: Math.min(matched.length, limit),
    items: matched.slice(0, limit),
    semanticAuthorityClaimed: false,
    notes: [
      "This surface retrieves source-grounded knowledge; it does not rank, recommend, approve, reject, or select game ideas.",
      "Source authority remains bounded to each record's declared native scope and evidence limit.",
    ],
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const query: ExternalKnowledgeQuery = {
    type: (cliArgument("--type") ?? "sources") as QueryType,
    ...cliQueryArguments(["q", "category", "authority", "status"]),
  };
  const result = queryExternalKnowledge(query);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}
