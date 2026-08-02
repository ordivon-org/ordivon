import { readFile } from "node:fs/promises";
import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { compareRuns, ComparisonError } from "./comparison/compare.ts";
import type { DeploymentProviderOptions } from "./deployment/model.ts";
import { DeploymentError, DeploymentStore } from "./deployment/store.ts";
import { createMissionControlCatalog, isMissionProviderName } from "./mission-control/catalog.ts";
import {
  MissionControlService,
  type MissionControlCommand,
  type MissionProviderFactory,
  type MissionProviderName,
} from "./mission-control/service.ts";
import type { DoctrineId, MissionAdvanceMode } from "./mission-control/model.ts";
import { buildReplayReport } from "./replay/report.ts";
import { replayFrame } from "./replay/frames.ts";
import { GameStore, StorageError } from "./storage.ts";
import { TeamCodexCliProvider } from "./team/codex-cli.ts";
import { TeamHermesCliProvider } from "./team/hermes-cli.ts";
import type { AuthorityPolicyMode, MessageChannel, MessageKind } from "./team/model.ts";
import { providerPreflight } from "./team/provider-preflight.ts";
import { TeamProviderChain } from "./team/provider-chain.ts";
import { FixtureTeamProvider, type TeamDecisionProvider } from "./team/providers.ts";
import { TeamStoreError } from "./team/store.ts";

const defaultWebRoot = fileURLToPath(new URL("../web", import.meta.url));
const defaultDbPath = resolve(process.cwd(), "data/station-zero.sqlite3");
const staticFiles: Record<string, { file: string; contentType: string }> = {
  "/": { file: "index.html", contentType: "text/html; charset=utf-8" },
  "/styles.css": { file: "styles.css", contentType: "text/css; charset=utf-8" },
  ...Object.fromEntries([
    "app.js", "api.js", "store.js", "render-utils.js", "render-map.js", "render-actors.js",
    "render-inbox.js", "render-objectives.js", "render-fronts.js", "render-timeline.js",
    "render-shell.js", "render-navigation.js", "render-curves.js", "render-replay.js",
    "render-diagnosis.js", "render-compare.js",
  ].map((file) => [`/${file}`, { file, contentType: "text/javascript; charset=utf-8" }])),
};

function sendJson(response: ServerResponse, statusCode: number, value: unknown): void {
  const body = JSON.stringify(value);
  response.writeHead(statusCode, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(body),
  });
  response.end(body);
}

class HttpRequestError extends Error {
  readonly statusCode: number;
  readonly code: string;

  constructor(statusCode: number, code: string, message: string) {
    super(message);
    this.name = "HttpRequestError";
    this.statusCode = statusCode;
    this.code = code;
  }
}

async function readJson(request: IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = [];
  let length = 0;
  for await (const chunk of request) {
    const buffer = Buffer.from(chunk);
    length += buffer.length;
    if (length > 64 * 1024) throw new HttpRequestError(413, "request_too_large", "request body exceeds 64 KiB");
    chunks.push(buffer);
  }
  const text = Buffer.concat(chunks).toString("utf8");
  return text ? JSON.parse(text) : {};
}

function defaultProviderFactory(name: MissionProviderName, options?: DeploymentProviderOptions): TeamDecisionProvider {
  switch (name) {
    case "fixture":
      return new FixtureTeamProvider({
        breachStrategy: options?.coordinationProfileId === "engineer-seal" ? "engineer-seal" : "security-contain",
      });
    case "codex": return new TeamCodexCliProvider();
    case "hermes": return new TeamHermesCliProvider();
    case "codex-hermes": return new TeamProviderChain([new TeamCodexCliProvider(), new TeamHermesCliProvider()]);
    case "hermes-codex": return new TeamProviderChain([new TeamHermesCliProvider(), new TeamCodexCliProvider()]);
  }
}

function requiredString(value: unknown, label: string): string {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} must be a non-empty string`);
  return value;
}

function bodyRecord(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new TypeError("request body must be a JSON object");
  return value as Record<string, unknown>;
}

function parseProviderName(value: unknown): MissionProviderName {
  if (isMissionProviderName(value ?? "fixture")) return (value ?? "fixture") as MissionProviderName;
  throw new TypeError("unsupported Mission Provider");
}

function parseDoctrineId(value: unknown): DoctrineId {
  if (["delegated-response", "critical-approval", "strict-control"].includes(String(value))) return value as DoctrineId;
  throw new TypeError("unsupported Mission Control doctrine");
}

function parseMissionAdvanceMode(value: unknown): MissionAdvanceMode {
  const mode = requiredString(value, "mission advance mode");
  if (["one-tick", "three-ticks", "until-intervention"].includes(mode)) return mode as MissionAdvanceMode;
  throw new TypeError("unsupported mission advance mode");
}

function parseAuthorityPolicy(value: unknown): AuthorityPolicyMode {
  const policy = String(value ?? "autonomous");
  if (["autonomous", "supervised", "locked"].includes(policy)) return policy as AuthorityPolicyMode;
  throw new TypeError("unsupported Team authority policy");
}

function parseMessageKind(value: unknown): MessageKind {
  const kind = requiredString(value, "message kind");
  if (["fact-share", "help-request", "task-offer", "task-accept", "intent-announce", "blocker-notice", "status-update"].includes(kind)) return kind as MessageKind;
  throw new TypeError("unsupported Team message kind");
}

function parseMessageChannel(value: unknown): MessageChannel {
  const channel = requiredString(value, "message channel");
  if (channel === "local" || channel === "station-radio") return channel;
  throw new TypeError("unsupported Team message channel");
}

function parseCommand(body: Record<string, unknown>): MissionControlCommand {
  const action = requiredString(body.action, "Mission Control action");
  switch (action) {
    case "approve": return {
      action, proposalId: requiredString(body.proposalId, "proposalId"),
      ...(typeof body.issuedBy === "string" ? { issuedBy: body.issuedBy } : {}),
      ...(body.expiresAtTick === undefined ? {} : { expiresAtTick: Number(body.expiresAtTick) }),
    };
    case "deny": return { action, proposalId: requiredString(body.proposalId, "proposalId") };
    case "redirect-objective": return {
      action, actorId: requiredString(body.actorId, "actorId"),
      objectiveId: requiredString(body.objectiveId, "objectiveId"),
    };
    case "pause":
    case "resume":
    case "cancel": return { action, actorId: requiredString(body.actorId, "actorId") };
    case "set-provider": return {
      action, actorId: requiredString(body.actorId, "actorId"), provider: parseProviderName(body.provider),
    };
    case "set-authority-policy": return { action, policyMode: parseAuthorityPolicy(body.policyMode) };
    case "send-message": return {
      action,
      senderActorId: requiredString(body.senderActorId, "senderActorId"),
      recipientActorIds: Array.isArray(body.recipientActorIds)
        ? body.recipientActorIds.map((item) => requiredString(item, "recipientActorId")) : [],
      kind: parseMessageKind(body.kind),
      boundedSummary: requiredString(body.boundedSummary, "boundedSummary"),
      channel: parseMessageChannel(body.channel),
      ...(body.ttlTicks === undefined ? {} : { ttlTicks: Number(body.ttlTicks) }),
    };
    default: throw new TypeError("unsupported Mission Control action");
  }
}

export interface GameServerOptions {
  dbPath?: string;
  webRoot?: string;
  providerFactory?: MissionProviderFactory;
}

export interface GameServer {
  server: Server;
  store: GameStore;
  close(): Promise<void>;
}

export function createGameServer(options: GameServerOptions = {}): GameServer {
  const store = new GameStore(options.dbPath ?? defaultDbPath);
  const webRoot = options.webRoot ?? defaultWebRoot;
  const providerFactory = options.providerFactory ?? defaultProviderFactory;
  const service = (): MissionControlService => new MissionControlService(store, providerFactory);

  const server = createServer(async (request, response) => {
    try {
      const url = new URL(request.url ?? "/", "http://localhost");
      const runId = url.searchParams.get("runId") ?? store.activeRunId;

      if (request.method === "GET" && url.pathname === "/api/runs") {
        sendJson(response, 200, { activeRunId: store.activeRunId, runs: store.listRuns() });
        return;
      }
      if (request.method === "GET" && url.pathname === "/api/providers/preflight") {
        sendJson(response, 200, providerPreflight());
        return;
      }
      if (request.method === "GET" && url.pathname === "/api/mission-control/catalog") {
        sendJson(response, 200, createMissionControlCatalog());
        return;
      }
      if (request.method === "GET" && url.pathname === "/api/mission-control/state") {
        sendJson(response, 200, service().state(runId));
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/mission-control/initialize") {
        const body = bodyRecord(await readJson(request));
        const rawProviders = body.providers && typeof body.providers === "object" && !Array.isArray(body.providers)
          ? body.providers as Record<string, unknown> : {};
        sendJson(response, 201, service().initialize({
          runId: typeof body.runId === "string" && body.runId.trim() ? body.runId : runId,
          ...(typeof body.scenarioCaseId === "string" ? { scenarioCaseId: body.scenarioCaseId } : {}),
          ...(body.authorityPolicyMode === undefined ? {} : { authorityPolicyMode: parseAuthorityPolicy(body.authorityPolicyMode) }),
          ...(body.doctrineId === undefined ? {} : { doctrineId: parseDoctrineId(body.doctrineId) }),
          providers: Object.fromEntries(Object.entries(rawProviders).map(([id, provider]) => [id, parseProviderName(provider)])),
          ...(typeof body.coordinationProfileId === "string" ? { coordinationProfileId: body.coordinationProfileId } : {}),
        }));
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/mission-control/advance") {
        const body = bodyRecord(await readJson(request));
        sendJson(response, 200, await service().advancePlay(
          runId,
          parseMissionAdvanceMode(body.mode),
          body.maximumWorldTicks === undefined ? undefined : Number(body.maximumWorldTicks),
          body.maximumInternalSteps === undefined ? undefined : Number(body.maximumInternalSteps),
        ));
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/mission-control/command") {
        const result = service().command(runId, parseCommand(bodyRecord(await readJson(request))));
        sendJson(response, 200, { result, view: service().state(runId) });
        return;
      }
      if (request.method === "GET" && (url.pathname === "/api/mission-control/timeline" || url.pathname === "/api/replay/timeline")) {
        const limit = url.searchParams.get("limit") === null ? 12 : Number(url.searchParams.get("limit"));
        const rawBefore = url.searchParams.get("beforeRevision") ?? url.searchParams.get("before");
        const beforeRevision = rawBefore === null ? null : Number(rawBefore);
        if (!Number.isSafeInteger(limit) || limit < 1 || limit > 50) throw new TypeError("timeline limit must be an integer from 1 to 50");
        if (beforeRevision !== null && (!Number.isSafeInteger(beforeRevision) || beforeRevision < 0)) {
          throw new TypeError("beforeRevision must be a non-negative integer World revision");
        }
        const page = service().timeline(runId, beforeRevision, limit);
        sendJson(response, 200, { ...page, nextBefore: page.nextBeforeRevision });
        return;
      }
      if (request.method === "GET" && url.pathname === "/api/replay/report") {
        sendJson(response, 200, buildReplayReport(store, runId));
        return;
      }
      if (request.method === "GET" && url.pathname === "/api/replay/frame") {
        const revision = url.searchParams.get("revision");
        if (revision === null || !revision.trim()) throw new TypeError("revision is required");
        sendJson(response, 200, replayFrame(store, runId, Number(revision)));
        return;
      }
      if (request.method === "GET" && url.pathname === "/api/deployments/manifest") {
        const manifest = new DeploymentStore(store).get(runId);
        sendJson(response, manifest ? 200 : 404, manifest ?? { error: "deployment_not_found" });
        return;
      }
      if (request.method === "GET" && url.pathname === "/api/compare") {
        sendJson(response, 200, compareRuns(
          store,
          requiredString(url.searchParams.get("leftRunId"), "leftRunId"),
          requiredString(url.searchParams.get("rightRunId"), "rightRunId"),
        ));
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
      if (error instanceof HttpRequestError) sendJson(response, error.statusCode, { error: error.code, message: error.message });
      else if (error instanceof DeploymentError) sendJson(response, error.code === "deployment_corrupt" ? 500 : 409, { error: error.code, message: error.message });
      else if (error instanceof ComparisonError) sendJson(response, 409, { error: error.code, message: error.message });
      else if (error instanceof TeamStoreError) sendJson(response, error.code === "team_corrupt" ? 500 : 409, { error: error.code, message: error.message });
      else if (error instanceof StorageError) sendJson(response, error.code === "storage_busy" ? 503 : 500, { error: error.code, message: error.message });
      else if (error instanceof TypeError || error instanceof SyntaxError || error instanceof URIError) sendJson(response, 400, { error: "invalid_request", message: error.message });
      else sendJson(response, 500, { error: "internal_error", message: error instanceof Error ? error.message : String(error) });
    }
  });

  return {
    server,
    store,
    close: () => new Promise<void>((resolveClose, reject) => {
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
  game.server.listen(port, "127.0.0.1", () => console.log(`Station Zero running at http://127.0.0.1:${port}`));
  const shutdown = () => game.close().finally(() => process.exit(0));
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}
