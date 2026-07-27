import { readFile } from "node:fs/promises";
import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { sha256 } from "./digest.ts";
import {
  admitProviderDecision,
  compileProviderContext,
  FixtureProvider,
  type CognitionProvider,
} from "./provider.ts";
import { GameStore } from "./storage.ts";
import { parseWorldCommand } from "./world.ts";

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
    if (length > 64 * 1024) {
      throw new Error("request body exceeds 64 KiB");
    }
    chunks.push(buffer);
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

export interface GameServerOptions {
  dbPath?: string;
  webRoot?: string;
  provider?: CognitionProvider;
}

export interface GameServer {
  server: Server;
  store: GameStore;
  close(): Promise<void>;
}

export function createGameServer(options: GameServerOptions = {}): GameServer {
  const store = new GameStore(options.dbPath ?? defaultDbPath);
  const webRoot = options.webRoot ?? defaultWebRoot;
  const provider = options.provider ?? new FixtureProvider();

  const server = createServer(async (request, response) => {
    try {
      const url = new URL(request.url ?? "/", "http://localhost");

      if (request.method === "GET" && url.pathname === "/api/state") {
        const state = store.loadState();
        sendJson(response, 200, { state, digest: sha256(state), eventCount: store.eventCount() });
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

        const applied = store.apply(command);
        sendJson(response, applied.result.status === "accepted" ? 200 : 409, applied);
        return;
      }

      if (request.method === "GET" && url.pathname === "/api/replay") {
        sendJson(response, 200, store.replay());
        return;
      }

      if (request.method === "GET" && url.pathname === "/api/suggestion") {
        const context = compileProviderContext(store.loadState());
        const decision = await provider.decide(context);
        const admitted = admitProviderDecision(context, decision);
        sendJson(response, 200, { context, decision, admitted });
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
          if (error) {
            reject(error);
            return;
          }
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
    console.log(`Station Zero M0 running at http://127.0.0.1:${port}`);
  });

  const shutdown = () => {
    game.close().finally(() => process.exit(0));
  };
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}
