import { sha256 } from "../digest.ts";
import type { JournalEvent, WorldEvent, WorldState } from "../model.ts";
import type { GameStore } from "../storage.ts";
import type {
  ActionProposal,
  AuthorityDecision,
  AuthorityGrant,
  TeamMessage,
  TeamRound,
} from "../team/model.ts";
import type {
  EvidenceEdge,
  EvidenceEdgeKind,
  EvidenceNode,
  EvidenceNodeKind,
  PointInTimeReplayResult,
  RunEvidenceGraph,
} from "./model.ts";
import { loadReplayTeamData, type ReplayTeamData } from "./team-data.ts";

export class ReplayEvidenceError extends Error {
  readonly code = "replay_evidence_corrupt";
  constructor(message: string) {
    super(message);
    this.name = "ReplayEvidenceError";
  }
}

const timestampKeys = new Set(["createdAt", "updatedAt", "capturedAt", "startedAt", "finishedAt"]);

function semanticValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(semanticValue);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value as Record<string, unknown>)
      .filter(([key, item]) => !timestampKeys.has(key) && item !== undefined)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, item]) => [key, semanticValue(item)]));
  }
  return value;
}

function payloadDigest(value: unknown): string {
  return sha256(semanticValue(value));
}

function proposalRevision(proposal: ActionProposal): number {
  return proposal.worldRevision;
}

function inferHostRevision(payload: unknown, proposals: Map<string, ActionProposal>, rounds: Map<string, TeamRound>): number | null {
  const seen = new Set<unknown>();
  const visit = (value: unknown): number | null => {
    if (!value || typeof value !== "object" || seen.has(value)) return null;
    seen.add(value);
    if (Array.isArray(value)) {
      for (const item of value) { const found = visit(item); if (found !== null) return found; }
      return null;
    }
    const record = value as Record<string, unknown>;
    for (const key of ["worldRevision", "lastWorldRevision"]) {
      if (Number.isSafeInteger(record[key]) && Number(record[key]) >= 0) return Number(record[key]);
    }
    if (typeof record.proposalId === "string") {
      const proposal = proposals.get(record.proposalId);
      if (proposal) return proposal.worldRevision;
    }
    if (typeof record.roundId === "string") {
      const round = rounds.get(record.roundId);
      if (round) return round.worldRevision;
    }
    if (typeof record.createdTick === "number" && Number.isSafeInteger(record.createdTick)) return Number(record.createdTick);
    for (const item of Object.values(record)) { const found = visit(item); if (found !== null) return found; }
    return null;
  };
  return visit(payload);
}


export function assertEvidenceLinkIntegrity(
  nodes: Iterable<Pick<EvidenceNode, "nodeId">>,
  edges: Iterable<EvidenceEdge>,
): void {
  const nodeIds = new Set([...nodes].map((node) => node.nodeId));
  for (const edge of edges) {
    if (edge.required && (!nodeIds.has(edge.fromNodeId) || !nodeIds.has(edge.toNodeId))) {
      throw new ReplayEvidenceError(`Required Evidence edge is dangling: ${edge.edgeId}`);
    }
  }
}

function eventSummary(event: WorldEvent): string {
  if (event.missionStatus !== "running") return `World revision ${event.worldRevision}: ${event.missionStatus} · ${event.missionReason ?? "terminal"}`;
  const intents = event.intentReceipts?.length ?? 1;
  return `World revision ${event.worldRevision}: ${intents} admitted intent${intents === 1 ? "" : "s"}`;
}

function contractSummary(kind: string, subjectRef: string): string {
  const short = kind.replace(/^ordivon\./, "").replaceAll("-", " ");
  return `${short} for ${subjectRef}`;
}

export interface EvidenceBuildInput {
  terminal?: WorldState;
  replays?: PointInTimeReplayResult[];
  journal?: JournalEvent[];
  teamData?: ReplayTeamData;
}

export function buildRunEvidenceGraph(
  store: GameStore,
  runId = store.activeRunId,
  retained: EvidenceBuildInput = {},
): RunEvidenceGraph {
  store.getRun(runId);
  store.verifyStream(runId);
  const terminal = retained.terminal ?? store.loadState(runId);
  const replays = retained.replays ?? Array.from(
    { length: terminal.revision + 1 },
    (_, revision) => store.stateAtRevision(revision, runId),
  );
  const nodes = new Map<string, EvidenceNode>();
  const edges = new Map<string, EvidenceEdge>();

  const addNode = (input: Omit<EvidenceNode, "payloadDigest"> & { payload: unknown; payloadDigest?: string }): EvidenceNode => {
    const node: EvidenceNode = {
      nodeId: input.nodeId, kind: input.kind, worldRevision: input.worldRevision, sequence: input.sequence,
      actorId: input.actorId, roundId: input.roundId, subjectId: input.subjectId,
      payloadDigest: input.payloadDigest ?? payloadDigest(input.payload), summary: input.summary,
    };
    const retained = nodes.get(node.nodeId);
    if (retained && payloadDigest(retained) !== payloadDigest(node)) throw new ReplayEvidenceError(`Evidence node identity differs: ${node.nodeId}`);
    nodes.set(node.nodeId, node);
    return node;
  };
  const addEdge = (kind: EvidenceEdgeKind, fromNodeId: string, toNodeId: string, required = true): void => {
    const edgeId = `edge:${kind}:${sha256({ fromNodeId, toNodeId })}`;
    edges.set(edgeId, { edgeId, kind, fromNodeId, toNodeId, required });
  };

  for (const actor of Object.values(replays[0]!.state.agents).sort((a, b) => a.id.localeCompare(b.id))) {
    addNode({ nodeId: `actor:${actor.id}`, kind: "actor", worldRevision: null, sequence: null, actorId: actor.id, roundId: null, subjectId: actor.id, payload: { id: actor.id, name: actor.name, capabilities: [...actor.capabilities].sort() }, summary: `${actor.name} · ${actor.capabilities.join(", ")}` });
  }
  for (const replay of replays) {
    const revision = replay.revision;
    addNode({ nodeId: `world-state:${runId}:${revision}`, kind: "world-state", worldRevision: revision, sequence: revision, actorId: null, roundId: null, subjectId: runId, payload: { digest: replay.digest, mission: replay.state.mission, turn: replay.state.turn }, payloadDigest: replay.digest, summary: revision === 0 ? "Genesis World state" : `World state after revision ${revision}` });
  }
  const journal = retained.journal ?? store.journalEvents(runId);
  const eventByRevision = new Map<number, JournalEvent>();
  for (const record of journal) {
    const event = record.event;
    eventByRevision.set(event.worldRevision, record);
    const nodeId = `world-event:${event.eventId}`;
    addNode({ nodeId, kind: "world-event", worldRevision: event.worldRevision, sequence: record.commandSequence, actorId: event.actorId, roundId: null, subjectId: event.commandId, payload: event, summary: eventSummary(event) });
    addEdge("advances-from", `world-state:${runId}:${event.worldRevision - 1}`, nodeId);
    addEdge("produces-state", nodeId, `world-state:${runId}:${event.worldRevision}`);
    if (nodes.has(`actor:${event.actorId}`)) addEdge("belongs-to", nodeId, `actor:${event.actorId}`, false);
  }

  const teamData = retained.teamData ?? loadReplayTeamData(store, runId);
  if (teamData.initialized) {
    const projection = {
      authorityDecisions: teamData.authorityDecisions,
      authorityGrants: teamData.authorityGrants,
      messages: teamData.messages,
    };
    const rounds = teamData.rounds;
    const roundMap = new Map(rounds.map((round) => [round.roundId, round]));
    const proposalMap = new Map<string, ActionProposal>();

    for (const round of rounds) {
      const roundNode = `team-round:${round.roundId}`;
      addNode({ nodeId: roundNode, kind: "team-round", worldRevision: round.worldRevision, sequence: round.worldRevision, actorId: null, roundId: round.roundId, subjectId: round.roundId, payload: round, summary: `Round ${round.worldRevision} · ${round.status}` });
      addEdge("prepared-from", `world-state:${runId}:${round.worldRevision}`, roundNode);
      const contexts = teamData.contextsByRound.get(round.roundId) ?? [];
      for (const context of contexts) {
        const nodeId = `team-context:${context.contextId}`;
        addNode({ nodeId, kind: "team-context", worldRevision: context.worldRevision, sequence: null, actorId: context.actorId, roundId: round.roundId, subjectId: context.taskId, payload: context, summary: `${context.actorId} Context at revision ${context.worldRevision}` });
        addEdge("belongs-to", nodeId, roundNode);
        addEdge("prepared-from", nodeId, `world-state:${runId}:${context.worldRevision}`);
        addEdge("belongs-to", nodeId, `actor:${context.actorId}`);
      }
      const proposals = teamData.proposalsByRound.get(round.roundId) ?? [];
      for (const proposal of proposals) {
        proposalMap.set(proposal.proposalId, proposal);
        const nodeId = `team-proposal:${proposal.proposalId}`;
        addNode({ nodeId, kind: "team-proposal", worldRevision: proposalRevision(proposal), sequence: null, actorId: proposal.actorId, roundId: round.roundId, subjectId: proposal.proposalId, payload: proposal, summary: `${proposal.actorId}: ${proposal.command.kind} · ${proposal.status}` });
        const contextNode = `team-context:${proposal.contextId}`;
        if (!nodes.has(contextNode)) throw new ReplayEvidenceError(`Proposal references missing Context: ${proposal.proposalId}`);
        addEdge("proposed-from", contextNode, nodeId);
        addEdge("belongs-to", nodeId, roundNode);
        addEdge("belongs-to", nodeId, `actor:${proposal.actorId}`);
      }
      if (round.tickPlanId) {
        const plan = teamData.tickPlansByRound.get(round.roundId)!;
        const planNode = `team-tick-plan:${plan.tickPlanId}`;
        addNode({ nodeId: planNode, kind: "team-tick-plan", worldRevision: plan.worldRevision, sequence: null, actorId: null, roundId: round.roundId, subjectId: plan.tickPlanId, payload: plan, summary: `${plan.selectedProposalIds.length} selected / ${plan.rejectedProposalIds.length} rejected` });
        addEdge("belongs-to", planNode, roundNode);
        for (const proposalId of plan.selectedProposalIds) {
          const proposalNode = `team-proposal:${proposalId}`;
          if (!nodes.has(proposalNode)) throw new ReplayEvidenceError(`TickPlan selects missing Proposal: ${proposalId}`);
          addEdge("selected-by", proposalNode, planNode);
        }
        for (const proposalId of plan.rejectedProposalIds) {
          const proposalNode = `team-proposal:${proposalId}`;
          if (!nodes.has(proposalNode)) throw new ReplayEvidenceError(`TickPlan rejects missing Proposal: ${proposalId}`);
          addEdge("rejected-by", proposalNode, planNode);
        }
      }
      if (round.effectId) {
        const effect = teamData.effectsByRound.get(round.roundId)!;
        const effectNode = `effect:${effect.effectId}`;
        addNode({ nodeId: effectNode, kind: "effect", worldRevision: effect.requiredWorldRevision, sequence: null, actorId: null, roundId: round.roundId, subjectId: effect.effectId, payload: effect, summary: `Team Tick Effect · ${effect.status}` });
        addEdge("materializes", `team-tick-plan:${effect.tickPlanId}`, effectNode);
      }
      if (round.dispatchId) {
        const dispatch = teamData.dispatchesByRound.get(round.roundId)!;
        const dispatchNode = `dispatch:${dispatch.dispatchId}`;
        addNode({ nodeId: dispatchNode, kind: "dispatch", worldRevision: round.worldRevision, sequence: dispatch.commandSequence, actorId: null, roundId: round.roundId, subjectId: dispatch.dispatchId, payload: dispatch, summary: `World Dispatch · ${dispatch.status}` });
        addEdge("dispatches", `effect:${dispatch.effectId}`, dispatchNode);
      }
      if (round.observationId) {
        const observation = teamData.observationsByRound.get(round.roundId) ?? null;
        if (!observation) throw new ReplayEvidenceError(`Round references missing Observation: ${round.roundId}`);
        const observationNode = `observation:${observation.observationId}`;
        addNode({ nodeId: observationNode, kind: "observation", worldRevision: round.worldRevision + 1, sequence: observation.commandSequence, actorId: null, roundId: round.roundId, subjectId: observation.observationId, payload: observation, summary: `${observation.verifiedIntentCommandIds.length} verified intent${observation.verifiedIntentCommandIds.length === 1 ? "" : "s"}` });
        addEdge("observed-as", `dispatch:${observation.dispatchId}`, observationNode);
        const retainedEvent = eventByRevision.get(round.worldRevision + 1)?.event;
        if (!retainedEvent || retainedEvent.eventId !== observation.worldEventId) throw new ReplayEvidenceError(`Observation references missing World Event: ${observation.observationId}`);
        addEdge("records", observationNode, `world-event:${observation.worldEventId}`);
      }
    }

    const decisions = projection.authorityDecisions;
    for (const decision of decisions) {
      const proposal = [...proposalMap.values()].find((candidate) => candidate.authorityDecisionId === decision.decisionId);
      const revision = proposal?.worldRevision ?? null;
      const nodeId = `authority-decision:${decision.decisionId}`;
      addNode({ nodeId, kind: "authority-decision", worldRevision: revision, sequence: null, actorId: decision.actorId, roundId: proposal?.roundId ?? null, subjectId: decision.decisionId, payload: decision, summary: `${decision.actorId} authority · ${decision.outcome}` });
      if (proposal) addEdge("authorized-by", nodeId, `team-proposal:${proposal.proposalId}`);
      addEdge("belongs-to", nodeId, `actor:${decision.actorId}`);
    }
    const grants = projection.authorityGrants;
    for (const grant of grants) {
      const proposal = proposalMap.get(grant.proposalId);
      if (!proposal) throw new ReplayEvidenceError(`Authority Grant references missing Proposal: ${grant.grantId}`);
      const nodeId = `authority-grant:${grant.grantId}`;
      addNode({ nodeId, kind: "authority-grant", worldRevision: proposal.worldRevision, sequence: null, actorId: grant.actorId, roundId: proposal.roundId, subjectId: grant.grantId, payload: grant, summary: `${grant.actorId} grant · ${grant.consumedAtTick === null ? "issued" : "consumed"}` });
      addEdge("granted-for", nodeId, `team-proposal:${grant.proposalId}`);
    }
    for (const message of projection.messages) {
      const nodeId = `team-message:${message.messageId}`;
      addNode({ nodeId, kind: "team-message", worldRevision: Math.min(message.createdTick, terminal.revision), sequence: null, actorId: message.senderActorId, roundId: null, subjectId: message.messageId, payload: message, summary: `${message.kind} · ${message.status}: ${message.boundedSummary}` });
      addEdge("sent-by", `actor:${message.senderActorId}`, nodeId);
      for (const actorId of message.recipientActorIds) addEdge("addressed-to", nodeId, `actor:${actorId}`, false);
    }

    const transcript = teamData.contractTranscript;
    const roundByTaskId = new Map(rounds.map((round) => [`task:team-round:${round.roundId.slice("team-round:".length)}`, round]));
    const previousBySubject = new Map<string, string>();
    for (const entry of transcript) {
      const round = roundByTaskId.get(entry.subjectRef);
      const nodeId = `host-contract:${entry.contractDigest}`;
      addNode({ nodeId, kind: "host-contract", worldRevision: round?.worldRevision ?? null, sequence: entry.sequence, actorId: null, roundId: round?.roundId ?? null, subjectId: entry.subjectRef, payload: { contractKind: entry.contractKind, contractDigest: entry.contractDigest, relatedDigests: entry.relatedDigests }, payloadDigest: entry.contractDigest, summary: contractSummary(entry.contractKind, entry.subjectRef) });
      const previous = previousBySubject.get(entry.subjectRef);
      if (previous) addEdge("records", previous, nodeId, false);
      previousBySubject.set(entry.subjectRef, nodeId);
      for (const digest of entry.relatedDigests) addEdge("references", nodeId, `artifact:${digest}`, false);
    }

    const hostJournal = teamData.hostJournal;
    for (const event of hostJournal.filter((entry) => !entry.eventType.startsWith("host-contract."))) {
      const inferredRevision = inferHostRevision(event.payload, proposalMap, roundMap);
      const playerVisible = /player|configuration-updated|task-provider-updated/.test(event.eventType);
      if (!playerVisible) continue;
      const revision = inferredRevision ?? 0;
      const nodeId = `host-event:${event.eventId}`;
      addNode({ nodeId, kind: "host-event", worldRevision: revision, sequence: event.sequence, actorId: null, roundId: null, subjectId: event.eventId, payload: { eventType: event.eventType, payload: event.payload }, summary: event.eventType.replaceAll(".", " ").replaceAll("-", " ") });
    }
  }

  assertEvidenceLinkIntegrity(nodes.values(), edges.values());
  const orderedNodes = [...nodes.values()].sort((a, b) => a.nodeId.localeCompare(b.nodeId));
  const orderedEdges = [...edges.values()].sort((a, b) => a.edgeId.localeCompare(b.edgeId));
  const graphBase = { schemaVersion: 1, kind: "ordivon.game.run-evidence-graph", runId, terminalRevision: terminal.revision, nodes: orderedNodes, edges: orderedEdges } as const;
  return { ...graphBase, graphDigest: sha256(graphBase) };
}
