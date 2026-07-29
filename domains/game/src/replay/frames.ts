import { sha256 } from "../digest.ts";
import type { GameStore } from "../storage.ts";
import { TeamExecutionStore } from "../team/execution-store.ts";
import type { TeamRound } from "../team/model.ts";
import { TeamStore } from "../team/store.ts";
import { buildRunEvidenceGraph } from "./evidence.ts";
import type {
  EvidenceNodeKind,
  ReplayEvidenceReference,
  ReplayFrame,
  ReplayFramePage,
  ReplaySummary,
  RunEvidenceGraph,
} from "./model.ts";

export const MAX_REPLAY_FRAME_BYTES = 64 * 1024;

function teamInitialized(store: GameStore, runId: string): boolean {
  const table = store.db.prepare("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'team_actor_sessions'").get() as { name?: string } | undefined;
  if (!table?.name) return false;
  const row = store.db.prepare("SELECT 1 AS present FROM team_actor_sessions WHERE run_id = ? LIMIT 1").get(runId) as { present?: number } | undefined;
  return row?.present === 1;
}

function reference(graph: RunEvidenceGraph, nodeId: string | null): ReplayEvidenceReference | null {
  if (!nodeId) return null;
  const node = graph.nodes.find((candidate) => candidate.nodeId === nodeId);
  return node ? { nodeId: node.nodeId, kind: node.kind, payloadDigest: node.payloadDigest, summary: node.summary } : null;
}

function frameRound(rounds: TeamRound[], revision: number): TeamRound | null {
  const advancing = revision === 0
    ? null
    : rounds.find((round) => round.worldRevision === revision - 1) ?? null;
  if (advancing) return advancing;
  return rounds.find((round) => round.worldRevision === revision && round.status !== "completed") ?? null;
}

export function replayFrame(store: GameStore, runId: string, revision: number, graph = buildRunEvidenceGraph(store, runId)): ReplayFrame {
  const replay = store.stateAtRevision(revision, runId);
  const event = revision === 0 ? null : store.journalEvents(runId).find((record) => record.event.worldRevision === revision)?.event ?? null;
  let round: TeamRound | null = null;
  let contexts: ReplayFrame["contexts"] = [];
  let proposals: ReplayFrame["proposals"] = [];
  let tickPlan: ReplayFrame["tickPlan"] = null;
  let effect: ReplayFrame["effect"] = null;
  let dispatch: ReplayFrame["dispatch"] = null;
  let observation: ReplayFrame["observation"] = null;
  let authorityDecisions: ReplayFrame["authorityDecisions"] = [];
  let authorityGrants: ReplayFrame["authorityGrants"] = [];
  let messages: ReplayFrame["messages"] = [];

  if (teamInitialized(store, runId)) {
    const team = new TeamStore(store);
    const execution = new TeamExecutionStore(team);
    const rounds = execution.listRounds(runId);
    round = frameRound(rounds, revision);
    if (round) {
      contexts = execution.listContexts(round.roundId);
      proposals = execution.listProposals(round.roundId);
      tickPlan = round.tickPlanId ? execution.getTickPlan(round.tickPlanId) : null;
      effect = round.effectId ? execution.getEffect(round.effectId) : null;
      dispatch = round.dispatchId ? execution.getDispatch(round.dispatchId) : null;
      observation = round.observationId ? execution.findObservationForRound(round.roundId) : null;
      const proposalIds = new Set(proposals.map((proposal) => proposal.proposalId));
      const decisionIds = new Set(proposals.map((proposal) => proposal.authorityDecisionId));
      authorityDecisions = team.listAuthorityDecisions(runId).filter((decision) => decisionIds.has(decision.decisionId));
      authorityGrants = team.listAuthorityGrants(runId).filter((grant) => proposalIds.has(grant.proposalId));
    }
    messages = team.listMessages(runId).filter((message) => message.createdTick === revision || message.createdTick === revision - 1);
  }

  const roundId = round?.roundId ?? null;
  const evidenceNodes = graph.nodes.filter((node) =>
    node.nodeId === `world-state:${runId}:${revision}` ||
    node.nodeId === (event ? `world-event:${event.eventId}` : "") ||
    (roundId !== null && node.roundId === roundId) ||
    (node.kind === "team-message" && (node.worldRevision === revision || node.worldRevision === revision - 1)) ||
    (node.kind === "host-event" && node.worldRevision === revision));
  const playerInterventions = evidenceNodes.filter((node) => node.kind === "host-event").map((node) => ({ nodeId: node.nodeId, kind: node.kind, payloadDigest: node.payloadDigest, summary: node.summary }));
  const hostRecords = evidenceNodes.filter((node) => node.kind === "host-contract").map((node) => ({ nodeId: node.nodeId, kind: node.kind, payloadDigest: node.payloadDigest, summary: node.summary }));
  const base = {
    schemaVersion: 1 as const, kind: "ordivon.game.replay-frame" as const, runId, revision,
    previousRevision: revision === 0 ? null : revision - 1, state: replay.state, digest: replay.digest,
    snapshotRevision: replay.snapshotRevision, replayedCommandCount: replay.replayedCommandCount,
    worldEvent: reference(graph, event ? `world-event:${event.eventId}` : null),
    round, contexts, proposals, tickPlan, effect, dispatch, observation, authorityDecisions, authorityGrants, messages,
    playerInterventions, hostRecords, facts: event?.facts ?? [],
    evidenceNodeIds: evidenceNodes.map((node) => node.nodeId).sort(), graphDigest: graph.graphDigest, verified: true as const,
  };
  const byteLength = Buffer.byteLength(JSON.stringify(base));
  if (byteLength > MAX_REPLAY_FRAME_BYTES) throw new Error(`Replay Frame exceeds ${MAX_REPLAY_FRAME_BYTES} bytes at revision ${revision}: ${byteLength}`);
  return { ...base, byteLength };
}

export function replayFramesPage(store: GameStore, runId: string, fromRevision = 0, limit = 20): ReplayFramePage {
  if (!Number.isSafeInteger(fromRevision) || fromRevision < 0) throw new TypeError("fromRevision must be a non-negative integer");
  if (!Number.isSafeInteger(limit) || limit < 1 || limit > 50) throw new TypeError("frame limit must be an integer from 1 to 50");
  const terminalRevision = store.loadState(runId).revision;
  if (fromRevision > terminalRevision) throw new TypeError(`fromRevision must be from 0 to ${terminalRevision}`);
  const graph = buildRunEvidenceGraph(store, runId);
  const end = Math.min(terminalRevision, fromRevision + limit - 1);
  const frames = Array.from({ length: end - fromRevision + 1 }, (_, index) => replayFrame(store, runId, fromRevision + index, graph));
  return { runId, fromRevision, limit, frames, nextFromRevision: end < terminalRevision ? end + 1 : null, graphDigest: graph.graphDigest };
}

export function replaySummary(store: GameStore, runId = store.activeRunId): ReplaySummary {
  const graph = buildRunEvidenceGraph(store, runId);
  const terminal = store.loadState(runId);
  const nodeKinds: EvidenceNodeKind[] = ["actor", "world-state", "world-event", "team-round", "team-context", "team-proposal", "team-tick-plan", "team-message", "authority-decision", "authority-grant", "host-contract", "host-event", "effect", "dispatch", "observation"];
  const nodeCounts = Object.fromEntries(nodeKinds.map((kind) => [kind, graph.nodes.filter((node) => node.kind === kind).length])) as Record<EvidenceNodeKind, number>;
  return { schemaVersion: 1, kind: "ordivon.game.replay-summary", runId, terminalRevision: terminal.revision, terminalStatus: terminal.mission.status, terminalReason: terminal.mission.reason, terminalDigest: sha256(terminal), graphDigest: graph.graphDigest, frameCount: terminal.revision + 1, nodeCounts, edgeCount: graph.edges.length };
}
