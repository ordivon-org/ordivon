import { readFile } from "node:fs/promises";
import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { sha256 } from "./digest.ts";
import { AgentHost } from "./host/engine.ts";
import { admitProviderDecision, compileProviderContext, FixtureProvider, type CognitionProvider } from "./provider.ts";
import { CodexCliProvider } from "./providers/codex-cli.ts";
import { ProviderChain } from "./providers/chain.ts";
import { RecoveryOperationProvider } from "./providers/fixture.ts";
import { HermesCliProvider } from "./providers/hermes-cli.ts";
import type { OperationProvider } from "./providers/types.ts";
import { GameStore, StorageError } from "./storage.ts";
import { listAvailableActions, parseWorldCommand } from "./world.ts";

const defaultWebRoot = fileURLToPath(new URL("../web", import.meta.url));
const defaultDbPath = resolve(process.cwd(), "data/station-zero.sqlite3");
const staticFiles: Record<string, { file: string; contentType: string }> = {
  "/": { file: "index.html", contentType: "text/html; charset=utf-8" },
  "/app.js": { file: "app.js", contentType: "text/javascript; charset=utf-8" },
  "/styles.css": { file: "styles.css", contentType: "text/css; charset=utf-8" },
};

function sendJson(response: ServerResponse, statusCode: number, value: unknown): void {
  const body = JSON.stringify(value);
  response.writeHead(statusCode, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(body),
  });
  response.end(body);
}

async function readJson(request: IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = [];
  let length = 0;
  for await (const chunk of request) {
    const buffer = Buffer.from(chunk);
    length += buffer.length;
    if (length > 64 * 1024) throw new Error("request body exceeds 64 KiB");
    chunks.push(buffer);
  }
  const text = Buffer.concat(chunks).toString("utf8");
  return text ? JSON.parse(text) : {};
}

export type AgentProviderName = "fixture" | "codex" | "hermes" | "codex-hermes" | "hermes-codex";
export type AgentProviderFactory = (name: AgentProviderName) => OperationProvider;

function defaultAgentProviderFactory(name: AgentProviderName): OperationProvider {
  switch (name) {
    case "fixture": return new RecoveryOperationProvider();
    case "codex": return new CodexCliProvider();
    case "hermes": return new HermesCliProvider();
    case "codex-hermes": return new ProviderChain([new CodexCliProvider(), new HermesCliProvider()]);
    case "hermes-codex": return new ProviderChain([new HermesCliProvider(), new CodexCliProvider()]);
  }
}

function parseProviderName(value: unknown): AgentProviderName {
  const name = value ?? "fixture";
  if (["fixture", "codex", "hermes", "codex-hermes", "hermes-codex"].includes(String(name))) {
    return name as AgentProviderName;
  }
  throw new TypeError("unsupported Agent Provider");
}

function bodyRecord(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new TypeError("request body must be a JSON object");
  }
  return value as Record<string, unknown>;
}

export interface GameServerOptions {
  dbPath?: string;
  webRoot?: string;
  provider?: CognitionProvider;
  agentProviderFactory?: AgentProviderFactory;
}

export interface GameServer {
  server: Server;
  store: GameStore;
  close(): Promise<void>;
}

function requestedRunId(url: URL, store: GameStore): string {
  return url.searchParams.get("runId") ?? store.activeRunId;
}

function stateEnvelope(store: GameStore, runId: string): unknown {
  const state = store.loadState(runId);
  return {
    run: store.getRun(runId),
    state,
    digest: sha256(state),
    eventCount: store.eventCount(runId),
    availableActions: listAvailableActions(state),
    recentEvents: store.recentJournalEvents(8, runId).map((record) => record.event),
  };
}

function agentEnvelope(store: GameStore, provider: OperationProvider, runId: string): unknown {
  const agent = new AgentHost(store, provider);
  try {
    const projection = agent.projection(runId);
    return {
      initialized: true,
      runId,
      projection,
      effects: agent.execution.listEffects(runId),
      dispatches: agent.execution.listDispatches(runId),
      timeline: agent.host.listJournal(runId).slice(-40),
    };
  } catch (error) {
    if (error instanceof Error && /not initialized/.test(error.message)) {
      return { initialized: false, runId, projection: null, effects: [], dispatches: [], timeline: [] };
    }
    throw error;
  }
}

export function createGameServer(options: GameServerOptions = {}): GameServer {
  const store = new GameStore(options.dbPath ?? defaultDbPath);
  const webRoot = options.webRoot ?? defaultWebRoot;
  const provider = options.provider ?? new FixtureProvider();
  const agentProviderFactory = options.agentProviderFactory ?? defaultAgentProviderFactory;

  const server = createServer(async (request, response) => {
    try {
      const url = new URL(request.url ?? "/", "http://localhost");
      const runId = requestedRunId(url, store);

      if (request.method === "GET" && url.pathname === "/api/runs") {
        sendJson(response, 200, { activeRunId: store.activeRunId, runs: store.listRuns() });
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/runs") {
        const input = await readJson(request);
        if (input !== null && typeof input !== "object") {
          sendJson(response, 400, { error: "invalid_run", message: "run input must be an object" });
          return;
        }
        const run = store.createRun((input ?? {}) as Record<string, never>);
        sendJson(response, 201, { run, state: store.loadState(run.runId) });
        return;
      }
      if (request.method === "GET" && url.pathname === "/api/state") {
        sendJson(response, 200, stateEnvelope(store, runId));
        return;
      }
      if (request.method === "GET" && url.pathname === "/api/events") {
        sendJson(response, 200, { runId, events: store.events(runId) });
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/actions") {
        let command;
        try {
          command = parseWorldCommand(await readJson(request));
        } catch (error) {
          sendJson(response, 400, {
            error: "invalid_command",
            message: error instanceof Error ? error.message : String(error),
          });
          return;
        }
        const applied = store.apply(command, runId);
        sendJson(response, applied.result.status === "accepted" ? 200 : 409, applied);
        return;
      }
      if (request.method === "GET" && url.pathname === "/api/replay") {
        sendJson(response, 200, store.replay(runId));
        return;
      }
      if (request.method === "GET" && url.pathname === "/api/suggestion") {
        const context = compileProviderContext(store.loadState(runId));
        const decision = await provider.decide(context);
        const admitted = admitProviderDecision(context, decision);
        sendJson(response, 200, { runId, context, decision, admitted });
        return;
      }

      if (request.method === "GET" && url.pathname === "/api/agent/state") {
        const selected = parseProviderName(url.searchParams.get("provider") ?? "fixture");
        sendJson(response, 200, agentEnvelope(store, agentProviderFactory(selected), runId));
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/agent/initialize") {
        const body = bodyRecord(await readJson(request));
        const selected = parseProviderName(body.provider);
        const operationProvider = agentProviderFactory(selected);
        const agent = new AgentHost(store, operationProvider);
        const projection = agent.initialize(runId, [operationProvider.providerId]);
        sendJson(response, 201, { runId, provider: selected, projection });
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/agent/step") {
        const body = bodyRecord(await readJson(request));
        const selected = parseProviderName(body.provider);
        const operationProvider = agentProviderFactory(selected);
        const agent = new AgentHost(store, operationProvider);
        const receipt = await agent.step(runId);
        sendJson(response, 200, {
          provider: selected,
          receipt,
          agent: agentEnvelope(store, operationProvider, runId),
          world: stateEnvelope(store, runId),
        });
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/agent/run") {
        const body = bodyRecord(await readJson(request));
        const selected = parseProviderName(body.provider);
        const maximumSteps = body.maximumSteps === undefined ? 256 : Number(body.maximumSteps);
        if (!Number.isSafeInteger(maximumSteps) || maximumSteps < 1 || maximumSteps > 512) {
          sendJson(response, 400, { error: "invalid_step_budget", message: "maximumSteps must be an integer from 1 to 512" });
          return;
        }
        const operationProvider = agentProviderFactory(selected);
        const agent = new AgentHost(store, operationProvider);
        const receipt = await agent.run(runId, maximumSteps);
        sendJson(response, 200, {
          provider: selected,
          receipt,
          agent: agentEnvelope(store, operationProvider, runId),
          world: stateEnvelope(store, runId),
        });
        return;
      }
      if (request.method === "GET" && url.pathname === "/api/agent/timeline") {
        const operationProvider = agentProviderFactory("fixture");
        const agent = new AgentHost(store, operationProvider);
        try {
          sendJson(response, 200, { runId, timeline: agent.host.listJournal(runId) });
        } catch (error) {
          if (error instanceof Error && /not initialized/.test(error.message)) {
            sendJson(response, 200, { runId, timeline: [] });
          } else throw error;
        }
        return;
      }
      if (request.method === "GET" && url.pathname.startsWith("/api/agent/artifacts/")) {
        const digest = decodeURIComponent(url.pathname.slice("/api/agent/artifacts/".length));
        const agent = new AgentHost(store, agentProviderFactory("fixture"));
        try {
          sendJson(response, 200, agent.host.getArtifact(digest));
        } catch (error) {
          if (error instanceof Error && /unknown Host Artifact/.test(error.message)) {
            sendJson(response, 404, { error: "artifact_not_found", message: error.message });
          } else throw error;
        }
        return;
      }

      const staticFile = staticFiles[url.pathname];
      if (request.method === "GET" && staticFile) {
        const body = await readFile(resolve(webRoot, staticFile.file));
        response.writeHead(200, {
          "content-type": staticFile.contentType,
          "content-length": body.length,
          "cache-control": "no-store",
        });
        response.end(body);
        return;
      }
      sendJson(response, 404, { error: "not_found" });
    } catch (error) {
      if (error instanceof StorageError) {
        sendJson(response, error.code === "storage_busy" ? 503 : 500, {
          error: error.code,
          message: error.message,
        });
        return;
      }
      if (error instanceof TypeError || error instanceof SyntaxError) {
        sendJson(response, 400, { error: "invalid_request", message: error.message });
        return;
      }
      sendJson(response, 500, {
        error: "internal_error",
        message: error instanceof Error ? error.message : String(error),
      });
    }
  });

  return {
    server,
    store,
    close: () =>
      new Promise<void>((resolveClose, reject) => {
        server.close((error) => {
          if (error) return reject(error);
          store.close();
          resolveClose();
        });
      }),
  };
}

if (process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href) {
  const port = Number(process.env.PORT ?? 4173);
  const game = createGameServer({ dbPath: process.env.ORDIVON_GAME_DB ?? defaultDbPath });
  game.server.listen(port, "127.0.0.1", () => {
    console.log(`Station Zero M2 running at http://127.0.0.1:${port}`);
  });
  const shutdown = () => game.close().finally(() => process.exit(0));
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}
