import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { boundedQueryLimit, cliArgument, normalizeQueryFilter } from "../src/query-input.ts";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

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
  return JSON.parse(readFileSync(resolve(ROOT, path), "utf8"));
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
    items = json("standards/game_external_knowledge_base_r1.json").sources;
  } else if (query.type === "teardowns") {
    items = json("standards/game_teardown_queue_r1.json").targets;
  } else if (query.type === "skills") {
    items = json("standards/game_external_skill_watchlist_r1.json").skills;
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
  };
  const q = cliArgument("--q");
  const category = cliArgument("--category");
  const authority = cliArgument("--authority");
  const status = cliArgument("--status");
  const rawLimit = cliArgument("--limit");
  if (q !== undefined) query.q = q;
  if (category !== undefined) query.category = category;
  if (authority !== undefined) query.authority = authority;
  if (status !== undefined) query.status = status;
  if (rawLimit !== undefined) query.limit = Number(rawLimit);
  const result = queryExternalKnowledge(query);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}
