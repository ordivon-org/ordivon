import type { GameStore } from "../storage.ts";
import { TeamExecutionStore } from "../team/execution-store.ts";
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
import { TeamStore, teamRunInitialized } from "../team/store.ts";

export interface ReplayContractEntry {
  sequence: number;
  contractKind: string;
  contractDigest: string;
  subjectRef: string;
  relatedDigests: string[];
}

export interface ReplayHostJournalEntry {
  sequence: number;
  eventId: string;
  eventType: string;
  payload: unknown;
}

export interface ReplayTeamData {
  initialized: boolean;
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
  contractTranscript: ReplayContractEntry[];
  hostJournal: ReplayHostJournalEntry[];
}

function emptyReplayTeamData(): ReplayTeamData {
  return {
    initialized: false,
    rounds: [],
    contextsByRound: new Map(),
    proposalsByRound: new Map(),
    tickPlansByRound: new Map(),
    effectsByRound: new Map(),
    dispatchesByRound: new Map(),
    observationsByRound: new Map(),
    authorityDecisions: [],
    authorityGrants: [],
    messages: [],
    contractTranscript: [],
    hostJournal: [],
  };
}

export function loadReplayTeamData(
  store: GameStore,
  runId: string,
): ReplayTeamData {
  if (!teamRunInitialized(store, runId)) return emptyReplayTeamData();

  const team = new TeamStore(store);
  const execution = new TeamExecutionStore(team);
  team.verify(runId);
  execution.authority.verify(runId);
  const projection = team.projection(runId, false);
  const rounds = execution.listRounds(runId);
  const data: ReplayTeamData = {
    initialized: true,
    rounds,
    contextsByRound: new Map(),
    proposalsByRound: new Map(),
    tickPlansByRound: new Map(),
    effectsByRound: new Map(),
    dispatchesByRound: new Map(),
    observationsByRound: new Map(),
    authorityDecisions: projection.authorityDecisions,
    authorityGrants: projection.authorityGrants,
    messages: projection.messages,
    contractTranscript: execution.authority.contracts.transcript(runId),
    hostJournal: team.host.listJournal(runId),
  };

  for (const round of rounds) {
    data.contextsByRound.set(round.roundId, execution.listContexts(round.roundId));
    data.proposalsByRound.set(round.roundId, execution.listProposals(round.roundId));
    if (round.tickPlanId) {
      data.tickPlansByRound.set(round.roundId, execution.getTickPlan(round.tickPlanId));
    }
    if (round.effectId) {
      data.effectsByRound.set(round.roundId, execution.getEffect(round.effectId));
    }
    if (round.dispatchId) {
      data.dispatchesByRound.set(round.roundId, execution.getDispatch(round.dispatchId));
    }
    if (round.observationId) {
      const observation = execution.findObservationForRound(round.roundId);
      if (observation) data.observationsByRound.set(round.roundId, observation);
    }
  }
  return data;
}
