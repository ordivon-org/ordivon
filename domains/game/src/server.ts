import { readFile } from "node:fs/promises";
import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { sha256 } from "./digest.ts";
import { createMissionControlCatalog, isMissionProviderName } from "./mission-control/catalog.ts";
import { MissionControlService, type MissionControlCommand, type MissionProviderName } from "./mission-control/service.ts";
import { AgentHost } from "./host/engine.ts";
import { admitProviderDecision, compileProviderContext, FixtureProvider, type CognitionProvider } from "./provider.ts";
import { CodexCliProvider } from "./providers/codex-cli.ts";
import { ProviderChain } from "./providers/chain.ts";
import { RecoveryOperationProvider } from "./providers/fixture.ts";
import { HermesCliProvider } from "./providers/hermes-cli.ts";
import type { OperationProvider } from "./providers/types.ts";
import { GameStore, StorageError } from "./storage.ts";
import { authorityTargetId } from "./team/authority.ts";
import { TeamCodexCliProvider } from "./team/codex-cli.ts";
import { TeamHost } from "./team/engine.ts";
import { TeamHermesCliProvider } from "./team/hermes-cli.ts";
import type { AuthorityPolicyMode, MessageChannel, MessageKind } from "./team/model.ts";
import { objectivesForRole, TEAM_OBJECTIVE_GRAPH } from "./team/objectives.ts";
import { TeamProviderChain } from "./team/provider-chain.ts";
import { FixtureTeamProvider, type TeamDecisionProvider } from "./team/providers.ts";
import { TeamStoreError } from "./team/store.ts";
import { listAvailableActions, parseWorldCommand } from "./world.ts";

const defaultWebRoot = fileURLToPath(new URL("../web", import.meta.url));
const defaultDbPath = resolve(process.cwd(), "data/station-zero.sqlite3");
const staticFiles: Record<string, { file: string; contentType: string }> = {
  "/": { file: "index.html", contentType: "text/html; charset=utf-8" },
  "/debug.html": { file: "debug.html", contentType: "text/html; charset=utf-8" },
  "/styles.css": { file: "styles.css", contentType: "text/css; charset=utf-8" },
  "/debug.css": { file: "debug.css", contentType: "text/css; charset=utf-8" },
  ...Object.fromEntries([
    "app.js", "api.js", "store.js", "render-utils.js", "render-map.js", "render-actors.js",
    "render-inbox.js", "render-objectives.js", "render-timeline.js", "render-shell.js", "debug.js",
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
export type TeamProviderName = AgentProviderName;
export type TeamProviderFactory = (name: TeamProviderName) => TeamDecisionProvider;

function defaultAgentProviderFactory(name: AgentProviderName): OperationProvider {
  switch (name) {
    case "fixture": return new RecoveryOperationProvider();
    case "codex": return new CodexCliProvider();
    case "hermes": return new HermesCliProvider();
    case "codex-hermes": return new ProviderChain([new CodexCliProvider(), new HermesCliProvider()]);
    case "hermes-codex": return new ProviderChain([new HermesCliProvider(), new CodexCliProvider()]);
  }
}

function defaultTeamProviderFactory(name: TeamProviderName): TeamDecisionProvider {
  switch (name) {
    case "fixture": return new FixtureTeamProvider();
    case "codex": return new TeamCodexCliProvider();
    case "hermes": return new TeamHermesCliProvider();
    case "codex-hermes": return new TeamProviderChain([new TeamCodexCliProvider(), new TeamHermesCliProvider()]);
    case "hermes-codex": return new TeamProviderChain([new TeamHermesCliProvider(), new TeamCodexCliProvider()]);
  }
}

function parseProviderName(value: unknown): AgentProviderName {
  const name = value ?? "fixture";
  if (isMissionProviderName(name)) return name;
  throw new TypeError("unsupported Agent Provider");
}

function parseAuthorityPolicy(value: unknown): AuthorityPolicyMode {
  const policy = value ?? "autonomous";
  if (["autonomous", "supervised", "locked"].includes(String(policy))) return policy as AuthorityPolicyMode;
  throw new TypeError("unsupported Team authority policy");
}

function parseMessageKind(value: unknown): MessageKind {
  const kind = requiredString(value, "message kind");
  if (["fact-share", "help-request", "task-offer", "task-accept", "intent-announce", "blocker-notice", "status-update"].includes(kind)) return kind as MessageKind;
  throw new TypeError("unsupported Team message kind");
}

function parseMessageChannel(value: unknown): MessageChannel {
  const channel = requiredString(value, "message channel");
  if (["local", "station-radio"].includes(channel)) return channel as MessageChannel;
  throw new TypeError("unsupported Team message channel");
}

function requiredString(value: unknown, label: string): string {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} must be a non-empty string`);
  return value;
}

function bodyRecord(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new TypeError("request body must be a JSON object");
  }
  return value as Record<string, unknown>;
}

function parseMissionControlCommand(body: Record<string, unknown>): MissionControlCommand {
  const action = requiredString(body.action, "Mission Control action");
  switch (action) {
    case "approve": return { action, proposalId: requiredString(body.proposalId, "proposalId"), ...(typeof body.issuedBy === "string" ? { issuedBy: body.issuedBy } : {}), ...(body.expiresAtTick === undefined ? {} : { expiresAtTick: Number(body.expiresAtTick) }) };
    case "deny": return { action, proposalId: requiredString(body.proposalId, "proposalId") };
    case "redirect-objective": return { action, actorId: requiredString(body.actorId, "actorId"), objectiveId: requiredString(body.objectiveId, "objectiveId") };
    case "pause":
    case "resume":
    case "cancel": return { action, actorId: requiredString(body.actorId, "actorId") };
    case "set-provider": return { action, actorId: requiredString(body.actorId, "actorId"), provider: parseProviderName(body.provider) as MissionProviderName };
    case "set-authority-policy": return { action, policyMode: parseAuthorityPolicy(body.policyMode) };
    case "send-message": return {
      action, senderActorId: requiredString(body.senderActorId, "senderActorId"),
      recipientActorIds: Array.isArray(body.recipientActorIds) ? body.recipientActorIds.map((value) => requiredString(value, "recipientActorId")) : [],
      kind: parseMessageKind(body.kind), boundedSummary: requiredString(body.boundedSummary, "boundedSummary"),
      channel: parseMessageChannel(body.channel), ...(body.ttlTicks === undefined ? {} : { ttlTicks: Number(body.ttlTicks) }),
    };
    default: throw new TypeError("unsupported Mission Control action");
  }
}

export interface GameServerOptions {
  dbPath?: string;
  webRoot?: string;
  provider?: CognitionProvider;
  agentProviderFactory?: AgentProviderFactory;
  teamProviderFactory?: TeamProviderFactory;
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

function productTimeline(events: ReturnType<AgentHost["host"]["listJournal"]>): ReturnType<AgentHost["host"]["listJournal"]> {
  return events.filter((event) => !event.eventType.startsWith("host-contract."));
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
      timeline: productTimeline(agent.host.listJournal(runId)).slice(-40),
    };
  } catch (error) {
    if (error instanceof Error && /not initialized/.test(error.message)) {
      return { initialized: false, runId, projection: null, effects: [], dispatches: [], timeline: [] };
    }
    throw error;
  }
}

function teamTablesExist(store: GameStore): boolean {
  const row = store.db.prepare("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'team_goals'").get() as { name?: string } | undefined;
  return row?.name === "team_goals";
}

function teamEnvelope(
  store: GameStore,
  provider: TeamDecisionProvider,
  runId: string,
  policyMode: AuthorityPolicyMode,
): unknown {
  if (!teamTablesExist(store)) {
    return { initialized: false, runId, policyMode, projection: null, rounds: [], proposals: [], latestTickPlan: null, timeline: [] };
  }
  const goal = store.db.prepare("SELECT goal_id FROM team_goals WHERE run_id = ?").get(runId) as { goal_id?: string } | undefined;
  if (!goal?.goal_id) {
    return { initialized: false, runId, policyMode, projection: null, rounds: [], proposals: [], latestTickPlan: null, timeline: [] };
  }
  const team = new TeamHost(store, provider, { policyMode });
  const projection = team.team.projection(runId, false);
  const rounds = team.execution.listRounds(runId);
  const proposals = rounds.flatMap((round) => team.execution.listProposals(round.roundId));
  const latestRound = rounds.at(-1) ?? null;
  const latestTickPlan = latestRound?.tickPlanId ? team.execution.getTickPlan(latestRound.tickPlanId) : null;
  return {
    initialized: true,
    runId,
    policyMode,
    projection,
    rounds,
    proposals,
    latestTickPlan,
    timeline: productTimeline(team.team.host.listJournal(runId)).slice(-80),
  };
}

export function createGameServer(options: GameServerOptions = {}): GameServer {
  const store = new GameStore(options.dbPath ?? defaultDbPath);
  const webRoot = options.webRoot ?? defaultWebRoot;
  const provider = options.provider ?? new FixtureProvider();
  const agentProviderFactory = options.agentProviderFactory ?? defaultAgentProviderFactory;
  const teamProviderFactory = options.teamProviderFactory ?? defaultTeamProviderFactory;

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
      if (request.method === "GET" && url.pathname === "/api/replay/state") {
        const rawRevision = url.searchParams.get("revision");
        if (rawRevision === null || !rawRevision.trim()) {
          throw new TypeError("revision is required");
        }
        sendJson(response, 200, store.stateAtRevision(Number(rawRevision), runId));
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
          sendJson(response, 200, { runId, timeline: productTimeline(agent.host.listJournal(runId)) });
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

      if (request.method === "GET" && url.pathname === "/api/mission-control/catalog") {
        sendJson(response, 200, createMissionControlCatalog());
        return;
      }
      if (request.method === "GET" && url.pathname === "/api/mission-control/state") {
        const service = new MissionControlService(store, teamProviderFactory);
        sendJson(response, 200, service.state(runId));
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/mission-control/initialize") {
        const body = bodyRecord(await readJson(request));
        const selectedRunId = typeof body.runId === "string" && body.runId.trim() ? body.runId : runId;
        const rawProviders = body.providers && typeof body.providers === "object" && !Array.isArray(body.providers) ? body.providers as Record<string, unknown> : {};
        const providers = Object.fromEntries(Object.entries(rawProviders).map(([actorId, provider]) => [actorId, parseProviderName(provider)]));
        const service = new MissionControlService(store, teamProviderFactory);
        sendJson(response, 201, service.initialize({
          runId: selectedRunId,
          ...(typeof body.scenarioCaseId === "string" ? { scenarioCaseId: body.scenarioCaseId } : {}),
          authorityPolicyMode: parseAuthorityPolicy(body.authorityPolicyMode),
          providers,
        }));
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/mission-control/advance") {
        const body = bodyRecord(await readJson(request));
        const until = requiredString(body.until, "advance boundary");
        if (until !== "proposal-review" && until !== "tick-verified") throw new TypeError("unsupported advance boundary");
        const maximumInternalSteps = body.maximumInternalSteps === undefined ? 16 : Number(body.maximumInternalSteps);
        const service = new MissionControlService(store, teamProviderFactory);
        sendJson(response, 200, await service.advance(runId, until, maximumInternalSteps));
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/mission-control/command") {
        const body = bodyRecord(await readJson(request));
        const service = new MissionControlService(store, teamProviderFactory);
        const result = service.command(runId, parseMissionControlCommand(body));
        sendJson(response, 200, { result, view: service.state(runId) });
        return;
      }
      if (request.method === "GET" && (url.pathname === "/api/mission-control/timeline" || url.pathname === "/api/replay/timeline")) {
        const limit = url.searchParams.get("limit") === null ? 12 : Number(url.searchParams.get("limit"));
        if (!Number.isSafeInteger(limit) || limit < 1 || limit > 50) throw new TypeError("timeline limit must be an integer from 1 to 50");
        const rawBefore = url.searchParams.get("beforeRevision") ?? url.searchParams.get("before");
        const beforeRevision = rawBefore === null ? null : Number(rawBefore);
        if (beforeRevision !== null && (!Number.isSafeInteger(beforeRevision) || beforeRevision < 0)) {
          throw new TypeError("beforeRevision must be a non-negative integer World revision");
        }
        const service = new MissionControlService(store, teamProviderFactory);
        const page = service.timeline(runId, beforeRevision, limit);
        sendJson(response, 200, { ...page, nextBefore: page.nextBeforeRevision });
        return;
      }

      if (request.method === "GET" && url.pathname === "/api/team/state") {
        const selected = parseProviderName(url.searchParams.get("provider") ?? "fixture");
        const policyMode = parseAuthorityPolicy(url.searchParams.get("policyMode") ?? "autonomous");
        sendJson(response, 200, teamEnvelope(store, teamProviderFactory(selected), runId, policyMode));
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/team/initialize") {
        const body = bodyRecord(await readJson(request));
        const selected = parseProviderName(body.provider);
        const policyMode = parseAuthorityPolicy(body.policyMode);
        const team = new TeamHost(store, teamProviderFactory(selected), { policyMode });
        const projection = team.initialize(runId);
        sendJson(response, 201, { runId, provider: selected, policyMode, projection, team: teamEnvelope(store, teamProviderFactory(selected), runId, policyMode) });
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/team/step") {
        const body = bodyRecord(await readJson(request));
        const selected = parseProviderName(body.provider);
        const policyMode = parseAuthorityPolicy(body.policyMode);
        const team = new TeamHost(store, teamProviderFactory(selected), { policyMode });
        const receipt = await team.step(runId);
        sendJson(response, 200, {
          provider: selected,
          policyMode,
          receipt,
          team: teamEnvelope(store, teamProviderFactory(selected), runId, policyMode),
          world: stateEnvelope(store, runId),
        });
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/team/run") {
        const body = bodyRecord(await readJson(request));
        const selected = parseProviderName(body.provider);
        const policyMode = parseAuthorityPolicy(body.policyMode);
        const maximumSteps = body.maximumSteps === undefined ? 512 : Number(body.maximumSteps);
        if (!Number.isSafeInteger(maximumSteps) || maximumSteps < 1 || maximumSteps > 1024) {
          sendJson(response, 400, { error: "invalid_step_budget", message: "maximumSteps must be an integer from 1 to 1024" });
          return;
        }
        const team = new TeamHost(store, teamProviderFactory(selected), { policyMode });
        const receipt = await team.run(runId, maximumSteps);
        sendJson(response, 200, {
          provider: selected,
          policyMode,
          receipt,
          team: teamEnvelope(store, teamProviderFactory(selected), runId, policyMode),
          world: stateEnvelope(store, runId),
        });
        return;
      }
      if (request.method === "POST" && url.pathname === "/api/team/input") {
        const body = bodyRecord(await readJson(request));
        const selected = parseProviderName(body.provider);
        const policyMode = parseAuthorityPolicy(body.policyMode);
        const action = requiredString(body.action, "Team input action");
        const team = new TeamHost(store, teamProviderFactory(selected), { policyMode });
        team.initialize(runId);
        let result: unknown;
        if (action === "approve") {
          const proposalId = requiredString(body.proposalId, "proposalId");
          const proposal = team.execution.getProposal(proposalId);
          if (proposal.runId !== runId || proposal.authorityOutcome !== "require-human") throw new TeamStoreError("team_conflict", "Proposal is not awaiting human authority");
          const state = store.loadState(runId);
          const expiresAtTick = body.expiresAtTick === undefined ? state.turn + 2 : Number(body.expiresAtTick);
          if (!Number.isSafeInteger(expiresAtTick) || expiresAtTick < state.turn) throw new TypeError("expiresAtTick must be a current or future integer Tick");
          result = team.team.issueGrant({
            actorId: proposal.actorId,
            proposalId: proposal.proposalId,
            actionCandidateId: proposal.actionCandidateId,
            contextDigest: proposal.contextId,
            worldDigest: proposal.worldDigest,
            policyRevision: 1,
            operationKind: proposal.command.kind,
            targetId: authorityTargetId(proposal.command),
            expiresAtTick,
            issuedBy: typeof body.issuedBy === "string" && body.issuedBy.trim() ? body.issuedBy : "player:http",
          }, runId);
        } else if (action === "deny") {
          const proposalId = requiredString(body.proposalId, "proposalId");
          const proposal = team.execution.getProposal(proposalId);
          if (proposal.runId !== runId) throw new TeamStoreError("team_conflict", "Proposal belongs to another Run");
          const updatedAt = new Date().toISOString();
          result = team.execution.saveProposal({ ...proposal, status: "rejected", rejectionReason: "player_denied", updatedAt }, "team.proposal-player-denied");
          team.team.transitionTask(proposal.actorTaskId, {
            state: "blocked",
            admittedProposalId: proposal.proposalId,
            wait: { kind: "authority", subjectId: proposal.proposalId, reason: "Player denied authority", sinceTick: store.loadState(runId).turn },
          }, "team.task-player-denied", { proposalId });
        } else if (action === "send-message") {
          result = team.team.sendMessage({
            senderActorId: requiredString(body.senderActorId, "senderActorId"),
            recipientActorIds: Array.isArray(body.recipientActorIds) ? body.recipientActorIds.map((value) => requiredString(value, "recipientActorId")) : [],
            kind: parseMessageKind(body.kind),
            referencedFactIds: Array.isArray(body.referencedFactIds) ? body.referencedFactIds.map((value) => requiredString(value, "Fact identity")) : [],
            referencedArtifactDigests: Array.isArray(body.referencedArtifactDigests) ? body.referencedArtifactDigests.map((value) => requiredString(value, "Artifact digest")) : [],
            boundedSummary: requiredString(body.boundedSummary, "boundedSummary"),
            channel: parseMessageChannel(body.channel),
            ...(body.ttlTicks === undefined ? {} : { ttlTicks: Number(body.ttlTicks) }),
          }, runId);
        } else if (action === "redirect-objective") {
          const actorId = requiredString(body.actorId, "actorId");
          const objectiveId = requiredString(body.objectiveId, "objectiveId");
          const profile = team.team.getProfile(actorId, runId);
          if (!TEAM_OBJECTIVE_GRAPH.nodes.some((node) => node.objectiveId === objectiveId)) throw new TypeError("unknown Objective");
          if (!objectivesForRole(profile.role).includes(objectiveId)) throw new TeamStoreError("team_conflict", "Objective is outside the Actor role mandate");
          const task = team.team.listTasks(runId).find((candidate) => candidate.actorId === actorId);
          if (!task) throw new Error(`Actor Task missing: ${actorId}`);
          result = team.team.transitionTask(task.taskId, {
            state: "ready",
            activeObjectiveId: objectiveId,
            preparedContextDigest: null,
            admittedProposalId: null,
            wait: null,
            lastWorldRevision: store.loadState(runId).revision,
          }, "team.task-player-redirected", { actorId, objectiveId });
        } else if (action === "pause" || action === "resume" || action === "cancel") {
          const actorId = typeof body.actorId === "string" && body.actorId.trim() ? body.actorId : null;
          const tasks = team.team.listTasks(runId).filter((task) => task.actorId && (!actorId || task.actorId === actorId));
          if (tasks.length === 0) throw new TypeError("no matching Actor Task");
          const tick = store.loadState(runId).turn;
          result = tasks.map((task) => {
            if (task.control.mode === "cancelled" && action !== "cancel") throw new TeamStoreError("team_conflict", "Cancelled Actor Task cannot resume");
            const mode = action === "pause" ? "paused" : action === "cancel" ? "cancelled" : "active";
            return team.team.transitionTask(task.taskId, {
              state: mode === "cancelled" ? "cancelled" : mode === "paused" ? "waiting" : "ready",
              control: { mode, reason: mode === "active" ? null : `Player ${action}d Actor`, issuedBy: "player:http", issuedAtTick: tick },
              preparedContextDigest: null,
              admittedProposalId: null,
              wait: mode === "paused" ? { kind: "replan", subjectId: "player:http", reason: "Player paused Actor", sinceTick: tick } : null,
            }, `team.task-player-${action}d`, { actorId: task.actorId });
          });
        } else if (action === "set-provider") {
          const actorId = requiredString(body.actorId, "actorId");
          const provider = parseProviderName(body.provider);
          const task = team.team.listTasks(runId).find((candidate) => candidate.actorId === actorId);
          if (!task) throw new TypeError("no matching Actor Task");
          result = team.team.transitionTask(task.taskId, { providerOrder: [provider] }, "team.task-provider-updated", { actorId, provider });
        } else if (action === "set-authority-policy") {
          result = team.team.saveConfiguration(parseAuthorityPolicy(body.policyMode), runId);
        } else {
          throw new TypeError("unsupported Team input action");
        }
        sendJson(response, 200, {
          action,
          result,
          team: teamEnvelope(store, teamProviderFactory(selected), runId, policyMode),
          world: stateEnvelope(store, runId),
        });
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
      if (error instanceof TeamStoreError) {
        sendJson(response, error.code === "team_corrupt" ? 500 : 409, { error: error.code, message: error.message });
        return;
      }
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
    console.log(`Station Zero M3 running at http://127.0.0.1:${port}`);
  });
  const shutdown = () => game.close().finally(() => process.exit(0));
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}
