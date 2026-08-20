import { readFile } from "node:fs/promises";
import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { compareRuns, ComparisonError } from "./comparison/compare.ts";
import { CasefileService, CasefileStore, CasefileStoreError } from "./casefile/index.ts";
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
import { ProviderAdapterError } from "./team/provider-runtime.ts";
import { FixtureTeamProvider, type TeamDecisionProvider } from "./team/providers.ts";
import { TeamStoreError } from "./team/store.ts";
import {
  StationZeroV3DeepSeekProviderPool,
  StationZeroV3PlanningStoreError,
  StationZeroV3PlayService,
  StationZeroV3StorageError,
  StationZeroV3Store,
  stationZeroV3DeepSeekCredentialSources,
  type StationZeroV3AgentProviderFactory,
  type StationZeroV3CommanderOrderPatch,
  type StationZeroV3DeepSeekThinkingMode,
} from "./station-zero-v3/index.ts";

const defaultWebRoot = fileURLToPath(new URL("../web", import.meta.url));
const defaultV3WebRoot = fileURLToPath(new URL("../web-v3", import.meta.url));
const defaultLabWebRoot = fileURLToPath(new URL("../web-lab", import.meta.url));
const defaultPreG0WebRoot = fileURLToPath(new URL("../web-pre-g0", import.meta.url));
const defaultCasefileWebRoot = fileURLToPath(new URL("../web-casefile", import.meta.url));
const defaultDbPath = resolve(process.cwd(), "data/station-zero.sqlite3");
const defaultV3DbPath = resolve(process.cwd(), "data/station-zero-v3.sqlite3");
const defaultCasefileDbPath = resolve(process.cwd(), "data/casefile.sqlite3");
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

const casefileStaticFiles: Record<string, { file: string; contentType: string }> = {
  "/casefile": { file: "index.html", contentType: "text/html; charset=utf-8" },
  "/casefile/": { file: "index.html", contentType: "text/html; charset=utf-8" },
  "/casefile/styles.css": { file: "styles.css", contentType: "text/css; charset=utf-8" },
  "/casefile/app.js": { file: "app.js", contentType: "text/javascript; charset=utf-8" },
};

const labStaticFiles: Record<string, { file: string; contentType: string }> = {
  "/lab": { file: "index.html", contentType: "text/html; charset=utf-8" },
  "/lab/": { file: "index.html", contentType: "text/html; charset=utf-8" },
  "/lab/styles.css": { file: "styles.css", contentType: "text/css; charset=utf-8" },
  "/lab/app.js": { file: "app.js", contentType: "text/javascript; charset=utf-8" },
};

const preG0StaticFiles: Record<string, { file: string; contentType: string }> = {
  "/pre-g0": { file: "index.html", contentType: "text/html; charset=utf-8" },
  "/pre-g0/": { file: "index.html", contentType: "text/html; charset=utf-8" },
  "/pre-g0/styles.css": { file: "styles.css", contentType: "text/css; charset=utf-8" },
  "/pre-g0/app.js": { file: "app.js", contentType: "text/javascript; charset=utf-8" },
};

const v3StaticFiles: Record<string, { file: string; contentType: string }> = {
  "/v3": { file: "index.html", contentType: "text/html; charset=utf-8" },
  "/v3/": { file: "index.html", contentType: "text/html; charset=utf-8" },
  "/v3/styles.css": { file: "styles.css", contentType: "text/css; charset=utf-8" },
  "/v3/app.js": { file: "app.js", contentType: "text/javascript; charset=utf-8" },
  "/v3/api.js": { file: "api.js", contentType: "text/javascript; charset=utf-8" },
  "/v3/render.js": { file: "render.js", contentType: "text/javascript; charset=utf-8" },
  "/v3/assets/rescue-expression.png": { file: "assets/rescue-expression.png", contentType: "image/png" },
  "/v3/assets/rescue-specialists.png": { file: "assets/rescue-specialists.png", contentType: "image/png" },
  "/v3/assets/audio/plan-ready.ogg": { file: "assets/audio/plan-ready.ogg", contentType: "audio/ogg" },
  "/v3/assets/audio/commit.ogg": { file: "assets/audio/commit.ogg", contentType: "audio/ogg" },
  "/v3/assets/audio/aftermath.ogg": { file: "assets/audio/aftermath.ogg", contentType: "audio/ogg" },
  "/v3/assets/system-signal.svg": { file: "assets/system-signal.svg", contentType: "image/svg+xml; charset=utf-8" },
  "/v3/assets/hazard-signal.svg": { file: "assets/hazard-signal.svg", contentType: "image/svg+xml; charset=utf-8" },
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

function parseV3OrderPatch(body: Record<string, unknown>): StationZeroV3CommanderOrderPatch {
  const patch: StationZeroV3CommanderOrderPatch = {};
  if (body.primaryObjectiveId !== undefined) {
    const value = requiredString(body.primaryObjectiveId, "primaryObjectiveId");
    if (!["rescue-two-civilians", "recover-research-core", "eliminate-hive-alpha"].includes(value)) {
      throw new TypeError("unsupported Station Zero v3 primary Objective");
    }
    patch.primaryObjectiveId = value as NonNullable<StationZeroV3CommanderOrderPatch["primaryObjectiveId"]>;
  }
  if (body.posture !== undefined) {
    const value = requiredString(body.posture, "posture");
    if (!["cautious", "balanced", "aggressive"].includes(value)) throw new TypeError("unsupported Station Zero v3 posture");
    patch.posture = value as NonNullable<StationZeroV3CommanderOrderPatch["posture"]>;
  }
  if (body.formation !== undefined) {
    const value = requiredString(body.formation, "formation");
    if (!["cohesive", "split"].includes(value)) throw new TypeError("unsupported Station Zero v3 formation");
    patch.formation = value as NonNullable<StationZeroV3CommanderOrderPatch["formation"]>;
  }
  if (body.retreatHealthThreshold !== undefined) patch.retreatHealthThreshold = Number(body.retreatHealthThreshold);
  if (body.lethalForce !== undefined) {
    const value = requiredString(body.lethalForce, "lethalForce");
    if (!["forbidden", "permitted", "preferred"].includes(value)) throw new TypeError("unsupported lethal-force policy");
    patch.lethalForce = value as NonNullable<StationZeroV3CommanderOrderPatch["lethalForce"]>;
  }
  if (body.collateralPolicy !== undefined) {
    const value = requiredString(body.collateralPolicy, "collateralPolicy");
    if (!["forbidden", "limited", "permitted"].includes(value)) throw new TypeError("unsupported collateral policy");
    patch.collateralPolicy = value as NonNullable<StationZeroV3CommanderOrderPatch["collateralPolicy"]>;
  }
  if (body.lootPolicy !== undefined) {
    const value = requiredString(body.lootPolicy, "lootPolicy");
    if (!["ignore", "mission-only", "opportunistic"].includes(value)) throw new TypeError("unsupported loot policy");
    patch.lootPolicy = value as NonNullable<StationZeroV3CommanderOrderPatch["lootPolicy"]>;
  }
  for (const key of ["protectedActorId", "priorityTargetActorId"] as const) {
    const value = body[key];
    if (value !== undefined) {
      if (value !== null && typeof value !== "string") throw new TypeError(`${key} must be a string or null`);
      patch[key] = value as string | null;
    }
  }
  if (body.commanderDirectiveId !== undefined) {
    const value = requiredString(body.commanderDirectiveId, "commanderDirectiveId");
    if (![
      "hold-command", "scan-reactor", "scan-maintenance", "scan-life-support", "reroute-cooling",
      "lock-maintenance", "emergency-uplink", "call-extraction",
    ].includes(value)) throw new TypeError("unsupported Commander directive");
    patch.commanderDirectiveId = value as NonNullable<StationZeroV3CommanderOrderPatch["commanderDirectiveId"]>;
  }
  return patch;
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
  v3DbPath?: string;
  v3WebRoot?: string;
  labWebRoot?: string;
  preG0WebRoot?: string;
  casefileDbPath?: string;
  casefileWebRoot?: string;
  v3ProviderFactory?: StationZeroV3AgentProviderFactory;
}

export interface GameServer {
  server: Server;
  store: GameStore;
  v3Store: StationZeroV3Store;
  v3Play: StationZeroV3PlayService;
  casefileStore: CasefileStore;
  casefile: CasefileService;
  close(): Promise<void>;
}

export function createGameServer(options: GameServerOptions = {}): GameServer {
  const store = new GameStore(options.dbPath ?? defaultDbPath);
  const v3DbPath = options.v3DbPath ?? (options.dbPath
    ? options.dbPath === ":memory:" ? ":memory:" : `${options.dbPath}.v3`
    : defaultV3DbPath);
  const v3Store = new StationZeroV3Store(v3DbPath);
  const casefileDbPath = options.casefileDbPath ?? (options.dbPath
    ? options.dbPath === ":memory:" ? ":memory:" : `${options.dbPath}.casefile`
    : defaultCasefileDbPath);
  const casefileStore = new CasefileStore(casefileDbPath);
  const casefile = new CasefileService(casefileStore);
  const v3Play = new StationZeroV3PlayService(v3Store, {
    ...(options.v3ProviderFactory ? { providerFactory: options.v3ProviderFactory } : {}),
  });
  const webRoot = options.webRoot ?? defaultWebRoot;
  const v3WebRoot = options.v3WebRoot ?? defaultV3WebRoot;
  const labWebRoot = options.labWebRoot ?? defaultLabWebRoot;
  const preG0WebRoot = options.preG0WebRoot ?? defaultPreG0WebRoot;
  const casefileWebRoot = options.casefileWebRoot ?? defaultCasefileWebRoot;
  const providerFactory = options.providerFactory ?? defaultProviderFactory;
  const service = (): MissionControlService => new MissionControlService(store, providerFactory);

  const server = createServer(async (request, response) => {
    try {
      const url = new URL(request.url ?? "/", "http://localhost");
      const runId = url.searchParams.get("runId") ?? store.activeRunId;

      if (request.method === "GET" && url.pathname === "/api/casefile/catalog") {
        sendJson(response, 200, casefile.catalog());
        return;
      }
      if (request.method === "GET" && url.pathname === "/api/casefile/runs") {
        sendJson(response, 200, { runs: casefile.listRuns() });
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/casefile/runs") {
        const body = bodyRecord(await readJson(request));
        sendJson(response, 201, casefile.initialize(
          requiredString(body.runId, "runId"),
          typeof body.scenarioId === "string" && body.scenarioId.trim() ? body.scenarioId : undefined,
        ));
        return;
      }
      if (request.method === "GET" && url.pathname === "/api/casefile/state") {
        sendJson(response, 200, casefile.state(requiredString(url.searchParams.get("runId"), "runId")));
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/casefile/action") {
        const body = bodyRecord(await readJson(request));
        sendJson(response, 200, casefile.act(
          requiredString(url.searchParams.get("runId"), "runId"),
          requiredString(body.actionId, "actionId"),
        ));
        return;
      }

      if (request.method === "GET" && url.pathname === "/api/station-zero-v3/catalog") {
        sendJson(response, 200, v3Play.catalog());
        return;
      }
      if (request.method === "GET" && url.pathname === "/api/station-zero-v3/runs") {
        sendJson(response, 200, { runs: v3Play.listRuns() });
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/station-zero-v3/runs") {
        const body = bodyRecord(await readJson(request));
        const v3RunId = requiredString(body.runId, "runId");
        sendJson(response, 201, v3Play.initialize({
          runId: v3RunId,
          ...(typeof body.seed === "string" && body.seed.trim() ? { seed: body.seed } : {}),
          ...(typeof body.scenarioCaseId === "string" && body.scenarioCaseId.trim() ? { scenarioCaseId: body.scenarioCaseId } : {}),
        }));
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/station-zero-v3/resume") {
        const v3RunId = requiredString(url.searchParams.get("runId"), "runId");
        sendJson(response, 200, v3Play.resume(v3RunId));
        return;
      }
      if (request.method === "GET" && url.pathname === "/api/station-zero-v3/state") {
        const v3RunId = requiredString(url.searchParams.get("runId"), "runId");
        sendJson(response, 200, v3Play.state(v3RunId));
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/station-zero-v3/order") {
        const v3RunId = requiredString(url.searchParams.get("runId"), "runId");
        sendJson(response, 200, v3Play.saveOrder(v3RunId, parseV3OrderPatch(bodyRecord(await readJson(request)))));
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/station-zero-v3/preview") {
        const v3RunId = requiredString(url.searchParams.get("runId"), "runId");
        const generated = await v3Play.generatePreview(v3RunId);
        sendJson(response, 200, {
          idempotent: generated.idempotent,
          previewId: generated.preview.previewId,
          previewDigest: generated.preview.previewDigest,
          view: generated.view,
        });
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/station-zero-v3/commit") {
        const v3RunId = requiredString(url.searchParams.get("runId"), "runId");
        const body = bodyRecord(await readJson(request));
        sendJson(response, 200, await v3Play.commitPreview(
          v3RunId,
          typeof body.previewId === "string" && body.previewId.trim() ? body.previewId : undefined,
        ));
        return;
      }

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

      const casefileStaticFile = casefileStaticFiles[url.pathname];
      if (request.method === "GET" && casefileStaticFile) {
        const body = await readFile(resolve(casefileWebRoot, casefileStaticFile.file));
        response.writeHead(200, {
          "content-type": casefileStaticFile.contentType,
          "content-length": body.length,
          "cache-control": "no-store",
        });
        response.end(body);
        return;
      }
      const labStaticFile = labStaticFiles[url.pathname];
      if (request.method === "GET" && labStaticFile) {
        const body = await readFile(resolve(labWebRoot, labStaticFile.file));
        response.writeHead(200, {
          "content-type": labStaticFile.contentType,
          "content-length": body.length,
          "cache-control": "no-store",
        });
        response.end(body);
        return;
      }
      const preG0StaticFile = preG0StaticFiles[url.pathname];
      if (request.method === "GET" && preG0StaticFile) {
        const body = await readFile(resolve(preG0WebRoot, preG0StaticFile.file));
        response.writeHead(200, {
          "content-type": preG0StaticFile.contentType,
          "content-length": body.length,
          "cache-control": "no-store",
        });
        response.end(body);
        return;
      }
      const v3StaticFile = v3StaticFiles[url.pathname];
      if (request.method === "GET" && v3StaticFile) {
        const body = await readFile(resolve(v3WebRoot, v3StaticFile.file));
        response.writeHead(200, {
          "content-type": v3StaticFile.contentType,
          "content-length": body.length,
          "cache-control": "no-store",
        });
        response.end(body);
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
      else if (error instanceof StationZeroV3PlanningStoreError) sendJson(response, error.code === "station_zero_v3_planning_corrupt" ? 500 : 409, { error: error.code, message: error.message });
      else if (error instanceof CasefileStoreError) sendJson(response, error.code === "casefile_not_found" ? 404 : error.code === "casefile_conflict" ? 409 : 500, { error: error.code, message: error.message });
      else if (error instanceof StationZeroV3StorageError) sendJson(response,
        error.code === "station_zero_v3_busy" ? 503 : error.code === "station_zero_v3_constraint" ? 409 : 500,
        { error: error.code, message: error.message });
      else if (error instanceof StorageError) sendJson(response, error.code === "storage_busy" ? 503 : 500, { error: error.code, message: error.message });
      else if (error instanceof ProviderAdapterError) sendJson(response,
        error.code === "timeout" ? 504 : ["unavailable", "process_failed"].includes(error.code) ? 503 : 502,
        { error: `provider_${error.code}`, message: error.message });
      else if (error instanceof TypeError || error instanceof SyntaxError || error instanceof URIError) sendJson(response, 400, { error: "invalid_request", message: error.message });
      else sendJson(response, 500, { error: "internal_error", message: error instanceof Error ? error.message : String(error) });
    }
  });

  return {
    server,
    store,
    v3Store,
    v3Play,
    casefileStore,
    casefile,
    close: () => new Promise<void>((resolveClose, reject) => {
      server.close((error) => {
        if (error) return reject(error);
        store.close();
        v3Store.close();
        casefileStore.close();
        resolveClose();
      });
    }),
  };
}

if (process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href) {
  const port = Number(process.env.PORT ?? 4173);
  const v3ProviderMode = process.env.ORDIVON_GAME_V3_PROVIDER ?? "fixture";
  if (!["fixture", "deepseek"].includes(v3ProviderMode)) throw new TypeError(`unsupported ORDIVON_GAME_V3_PROVIDER: ${v3ProviderMode}`);
  const thinkingMode = (process.env.ORDIVON_GAME_V3_DEEPSEEK_THINKING ?? "disabled") as StationZeroV3DeepSeekThinkingMode;
  if (!["disabled", "enabled"].includes(thinkingMode)) throw new TypeError(`unsupported DeepSeek thinking mode: ${thinkingMode}`);
  const v3Pool = v3ProviderMode === "deepseek" ? new StationZeroV3DeepSeekProviderPool({
    credentialSources: stationZeroV3DeepSeekCredentialSources(process.env.ORDIVON_GAME_V3_DEEPSEEK_SOURCES ?? process.env.ORDIVON_GAME_V3_DEEPSEEK_SECRETS),
    thinkingMode,
    timeoutMs: Number(process.env.ORDIVON_GAME_V3_DEEPSEEK_TIMEOUT_MS ?? 30_000),
    maxTokens: Number(process.env.ORDIVON_GAME_V3_DEEPSEEK_MAX_TOKENS ?? (thinkingMode === "enabled" ? 2_048 : 512)),
    temperature: Number(process.env.ORDIVON_GAME_V3_DEEPSEEK_TEMPERATURE ?? 0.1),
    maximumConcurrencyPerCredential: Number(process.env.ORDIVON_GAME_V3_DEEPSEEK_CONCURRENCY ?? 4),
    retryBaseDelayMs: Number(process.env.ORDIVON_GAME_V3_DEEPSEEK_RETRY_BASE_DELAY_MS ?? 1_000),
    credentialReloadIntervalMs: Number(process.env.ORDIVON_GAME_V3_DEEPSEEK_RELOAD_INTERVAL_MS ?? 15_000),
    credentialCooldownMaximumMs: Number(process.env.ORDIVON_GAME_V3_DEEPSEEK_COOLDOWN_MAXIMUM_MS ?? 30_000),
    ...(process.env.ORDIVON_GAME_V3_DEEPSEEK_MAX_ATTEMPTS
      ? { maximumAttempts: Number(process.env.ORDIVON_GAME_V3_DEEPSEEK_MAX_ATTEMPTS) }
      : {}),
  }) : null;
  const game = createGameServer({
    dbPath: process.env.ORDIVON_GAME_DB ?? defaultDbPath,
    v3DbPath: process.env.ORDIVON_GAME_V3_DB ?? defaultV3DbPath,
    casefileDbPath: process.env.ORDIVON_GAME_CASEFILE_DB ?? defaultCasefileDbPath,
    ...(v3Pool ? { v3ProviderFactory: v3Pool.providerFactory() } : {}),
  });
  const v3ProviderDescription = (() => {
    if (!v3Pool) return "fixture";
    const snapshot = v3Pool.evidenceSnapshot();
    const totalConcurrency = snapshot.credentials.reduce((sum, credential) => sum + credential.maximumConcurrency, 0);
    return `${v3Pool.providerId} (${snapshot.credentials.length} credentials, ${totalConcurrency} configured concurrent calls)`;
  })();
  game.server.listen(port, "127.0.0.1", () => console.log(`Station Zero running at http://127.0.0.1:${port} with v3 Provider ${v3ProviderDescription}`));
  const shutdown = () => game.close().finally(() => process.exit(0));
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}
