import { sha256 } from "../digest.ts";
import type { JournalEvent } from "../model.ts";
import type { GameStore } from "../storage.ts";
import type {
  ActionProposal,
  AuthorityDecision,
  AuthorityGrant,
  TeamContextReference,
  TeamDispatch,
  TeamEffect,
  TeamMessage,
  TeamObservation,
  TeamRound,
  TeamTickPlan,
} from "../team/model.ts";
import { buildRunEvidenceGraph } from "./evidence.ts";
import { loadReplayTeamData, type ReplayTeamData } from "./team-data.ts";
import type {
  EvidenceNodeKind,
  PointInTimeReplayResult,
  ReplayEvidenceReference,
  ReplayFrame,
  ReplayFramePage,
  ReplaySummary,
  RunEvidenceGraph,
} from "./model.ts";

export const MAX_REPLAY_FRAME_BYTES = 64 * 1024;

interface ReplayFrameSource {
  replays: PointInTimeReplayResult[];
  journal: JournalEvent[];
  rounds: TeamRound[];
  contextsByRound: Map<string, TeamContextReference[]>;
  proposalsByRound: Map<string, ActionProposal[]>;
  tickPlansByRound: Map<string, TeamTickPlan>;
  effectsByRound: Map<string, TeamEffect>;
  dispatchesByRound: Map<string, TeamDispatch>;
  observationsByRound: Map<string, TeamObservation>;
  authorityDecisions: AuthorityDecision[];
  authorityGrants: AuthorityGrant[];
  messages: TeamMessage[];
}

function reference(
  graphNodes: Map<string, RunEvidenceGraph["nodes"][number]>,
  nodeId: string | null,
): ReplayEvidenceReference | null {
  if (!nodeId) return null;
  const node = graphNodes.get(nodeId);
  return node
    ? {
        nodeId: node.nodeId,
        kind: node.kind,
        payloadDigest: node.payloadDigest,
        summary: node.summary,
      }
    : null;
}

function frameRound(rounds: TeamRound[], revision: number): TeamRound | null {
  const advancing = revision === 0
    ? null
    : rounds.find((round) => round.worldRevision === revision - 1) ?? null;
  if (advancing) return advancing;
  return rounds.find(
    (round) => round.worldRevision === revision && round.status !== "completed",
  ) ?? null;
}

function replayStates(
  store: GameStore,
  runId: string,
  terminalRevision: number,
): PointInTimeReplayResult[] {
  return Array.from(
    { length: terminalRevision + 1 },
    (_, revision) => store.stateAtRevision(revision, runId),
  );
}

function loadFrameSource(
  replays: PointInTimeReplayResult[],
  journal: JournalEvent[],
  teamData: ReplayTeamData,
): ReplayFrameSource {
  return {
    replays,
    journal,
    rounds: teamData.rounds,
    contextsByRound: teamData.contextsByRound,
    proposalsByRound: teamData.proposalsByRound,
    tickPlansByRound: teamData.tickPlansByRound,
    effectsByRound: teamData.effectsByRound,
    dispatchesByRound: teamData.dispatchesByRound,
    observationsByRound: teamData.observationsByRound,
    authorityDecisions: teamData.authorityDecisions,
    authorityGrants: teamData.authorityGrants,
    messages: teamData.messages,
  };
}

function createReplayFrame(
  runId: string,
  revision: number,
  graph: RunEvidenceGraph,
  source: ReplayFrameSource,
): ReplayFrame {
  const replay = source.replays[revision];
  if (!replay) throw new TypeError(`revision must be from 0 to ${source.replays.length - 1}`);
  const event = revision === 0
    ? null
    : source.journal.find((record) => record.event.worldRevision === revision)?.event ?? null;
  const round = frameRound(source.rounds, revision);
  const roundId = round?.roundId ?? null;
  const contexts = roundId ? source.contextsByRound.get(roundId) ?? [] : [];
  const proposals = roundId ? source.proposalsByRound.get(roundId) ?? [] : [];
  const tickPlan = roundId ? source.tickPlansByRound.get(roundId) ?? null : null;
  const effect = roundId ? source.effectsByRound.get(roundId) ?? null : null;
  const dispatch = roundId ? source.dispatchesByRound.get(roundId) ?? null : null;
  const observation = roundId ? source.observationsByRound.get(roundId) ?? null : null;
  const proposalIds = new Set(proposals.map((proposal) => proposal.proposalId));
  const decisionIds = new Set(proposals.map((proposal) => proposal.authorityDecisionId));
  const authorityDecisions = source.authorityDecisions.filter(
    (decision) => decisionIds.has(decision.decisionId),
  );
  const authorityGrants = source.authorityGrants.filter(
    (grant) => proposalIds.has(grant.proposalId),
  );
  const messages = source.messages.filter(
    (message) => message.createdTick === revision || message.createdTick === revision - 1,
  );

  const evidenceNodes = graph.nodes.filter((node) =>
    node.nodeId === `world-state:${runId}:${revision}` ||
    node.nodeId === (event ? `world-event:${event.eventId}` : "") ||
    (roundId !== null && node.roundId === roundId) ||
    (node.kind === "team-message" &&
      (node.worldRevision === revision || node.worldRevision === revision - 1)) ||
    (node.kind === "host-event" && node.worldRevision === revision),
  );
  const playerInterventions = evidenceNodes
    .filter((node) => node.kind === "host-event")
    .map((node) => ({
      nodeId: node.nodeId,
      kind: node.kind,
      payloadDigest: node.payloadDigest,
      summary: node.summary,
    }));
  const hostRecords = evidenceNodes
    .filter((node) => node.kind === "host-contract")
    .map((node) => ({
      nodeId: node.nodeId,
      kind: node.kind,
      payloadDigest: node.payloadDigest,
      summary: node.summary,
    }));
  const graphNodes = new Map(graph.nodes.map((node) => [node.nodeId, node]));
  const base = {
    schemaVersion: 1 as const,
    kind: "ordivon.game.replay-frame" as const,
    runId,
    revision,
    previousRevision: revision === 0 ? null : revision - 1,
    state: replay.state,
    digest: replay.digest,
    snapshotRevision: replay.snapshotRevision,
    replayedCommandCount: replay.replayedCommandCount,
    worldEvent: reference(graphNodes, event ? `world-event:${event.eventId}` : null),
    round,
    contexts,
    proposals,
    tickPlan,
    effect,
    dispatch,
    observation,
    authorityDecisions,
    authorityGrants,
    messages,
    playerInterventions,
    hostRecords,
    facts: event?.facts ?? [],
    evidenceNodeIds: evidenceNodes.map((node) => node.nodeId).sort(),
    graphDigest: graph.graphDigest,
    verified: true as const,
  };
  const byteLength = Buffer.byteLength(JSON.stringify(base));
  if (byteLength > MAX_REPLAY_FRAME_BYTES) {
    throw new Error(
      `Replay Frame exceeds ${MAX_REPLAY_FRAME_BYTES} bytes at revision ${revision}: ${byteLength}`,
    );
  }
  return { ...base, byteLength };
}

export function buildReplayFrames(
  store: GameStore,
  runId: string,
  graph = buildRunEvidenceGraph(store, runId),
  retainedReplays?: PointInTimeReplayResult[],
  retainedJournal?: JournalEvent[],
  retainedTeamData?: ReplayTeamData,
): ReplayFrame[] {
  const terminalRevision = graph.terminalRevision;
  const replays = retainedReplays ?? replayStates(store, runId, terminalRevision);
  const journal = retainedJournal ?? store.journalEvents(runId);
  const teamData = retainedTeamData ?? loadReplayTeamData(store, runId);
  const source = loadFrameSource(replays, journal, teamData);
  return replays.map((_, revision) => createReplayFrame(runId, revision, graph, source));
}

export function replayFrame(
  store: GameStore,
  runId: string,
  revision: number,
  graph = buildRunEvidenceGraph(store, runId),
): ReplayFrame {
  if (!Number.isSafeInteger(revision) || revision < 0) {
    throw new TypeError("revision must be a non-negative integer");
  }
  const frames = buildReplayFrames(store, runId, graph);
  const retained = frames[revision];
  if (!retained) throw new TypeError(`revision must be from 0 to ${frames.length - 1}`);
  return retained;
}

export function replayFramesPage(
  store: GameStore,
  runId: string,
  fromRevision = 0,
  limit = 20,
): ReplayFramePage {
  if (!Number.isSafeInteger(fromRevision) || fromRevision < 0) {
    throw new TypeError("fromRevision must be a non-negative integer");
  }
  if (!Number.isSafeInteger(limit) || limit < 1 || limit > 50) {
    throw new TypeError("frame limit must be an integer from 1 to 50");
  }
  const graph = buildRunEvidenceGraph(store, runId);
  const frames = buildReplayFrames(store, runId, graph);
  const terminalRevision = frames.length - 1;
  if (fromRevision > terminalRevision) {
    throw new TypeError(`fromRevision must be from 0 to ${terminalRevision}`);
  }
  const selected = frames.slice(fromRevision, fromRevision + limit);
  const nextFromRevision = fromRevision + selected.length <= terminalRevision
    ? fromRevision + selected.length
    : null;
  return {
    runId,
    fromRevision,
    limit,
    frames: selected,
    nextFromRevision,
    graphDigest: graph.graphDigest,
  };
}

export function replaySummaryFromGraph(
  terminal: PointInTimeReplayResult["state"],
  graph: RunEvidenceGraph,
): ReplaySummary {
  const nodeKinds: EvidenceNodeKind[] = [
    "actor",
    "world-state",
    "world-event",
    "team-round",
    "team-context",
    "team-proposal",
    "team-tick-plan",
    "team-message",
    "authority-decision",
    "authority-grant",
    "host-contract",
    "host-event",
    "effect",
    "dispatch",
    "observation",
  ];
  const nodeCounts = Object.fromEntries(
    nodeKinds.map((kind) => [
      kind,
      graph.nodes.filter((node) => node.kind === kind).length,
    ]),
  ) as Record<EvidenceNodeKind, number>;
  return {
    schemaVersion: 1,
    kind: "ordivon.game.replay-summary",
    runId: graph.runId,
    terminalRevision: terminal.revision,
    terminalStatus: terminal.mission.status,
    terminalReason: terminal.mission.reason,
    terminalDigest: sha256(terminal),
    graphDigest: graph.graphDigest,
    frameCount: terminal.revision + 1,
    nodeCounts,
    edgeCount: graph.edges.length,
  };
}

export function replaySummary(
  store: GameStore,
  runId = store.activeRunId,
): ReplaySummary {
  const graph = buildRunEvidenceGraph(store, runId);
  return replaySummaryFromGraph(store.loadState(runId), graph);
}
