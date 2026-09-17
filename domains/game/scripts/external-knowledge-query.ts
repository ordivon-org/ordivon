import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

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

function normalize(value?: string): string | undefined {
  const result = value?.trim();
  return result ? result.toLowerCase() : undefined;
}

export function queryExternalKnowledge(query: ExternalKnowledgeQuery): ExternalKnowledgeQueryResult {
  const q = normalize(query.q);
  const category = normalize(query.category);
  const authority = normalize(query.authority);
  const status = normalize(query.status);
  const limit = Number.isInteger(query.limit) && (query.limit ?? 0) > 0 ? Math.min(query.limit!, 200) : 50;

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

function arg(name: string): string | undefined {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : undefined;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const query: ExternalKnowledgeQuery = {
    type: (arg("--type") ?? "sources") as QueryType,
  };
  const q = arg("--q");
  const category = arg("--category");
  const authority = arg("--authority");
  const status = arg("--status");
  const rawLimit = arg("--limit");
  if (q !== undefined) query.q = q;
  if (category !== undefined) query.category = category;
  if (authority !== undefined) query.authority = authority;
  if (status !== undefined) query.status = status;
  if (rawLimit !== undefined) query.limit = Number(rawLimit);
  const result = queryExternalKnowledge(query);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}
