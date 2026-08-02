import type { WorldState } from "../model.ts";
import { applyWorldTick } from "../world.ts";
import { candidateAllowed } from "./authority.ts";
import type { ActionProposal, TeamRound } from "./model.ts";

/**
 * Station Zero has exactly three specialist actors. This is a versioned Game
 * policy, not a general-purpose multi-Agent scheduler.
 */
export const STATION_ZERO_COORDINATION_POLICY_ID =
  "station-zero-compatible-max-productivity-v1";
export const STATION_ZERO_SPECIALIST_LIMIT = 3;

export interface StationZeroCoordinationCandidate {
  proposal: ActionProposal;
  authorityGrantAvailable: boolean;
}

export interface StationZeroCoordinationDecision {
  policyId: typeof STATION_ZERO_COORDINATION_POLICY_ID;
  legalSubsets: ActionProposal[][];
  selected: ActionProposal[] | null;
}

function assertBoundedCandidates(
  candidates: StationZeroCoordinationCandidate[],
): void {
  if (candidates.length > STATION_ZERO_SPECIALIST_LIMIT) {
    throw new RangeError(
      `Station Zero coordination admits at most ${STATION_ZERO_SPECIALIST_LIMIT} specialist Proposals`,
    );
  }
  const actorIds = candidates.map(({ proposal }) => proposal.actorId);
  if (new Set(actorIds).size !== actorIds.length) {
    throw new TypeError("Station Zero coordination requires at most one Proposal per Actor");
  }
}

export function evaluateStationZeroCoordination(
  state: WorldState,
  round: Pick<TeamRound, "roundId" | "worldRevision">,
  candidates: StationZeroCoordinationCandidate[],
): StationZeroCoordinationDecision {
  assertBoundedCandidates(candidates);
  const eligible = candidates
    .filter(({ proposal, authorityGrantAvailable }) =>
      proposal.status === "proposed" &&
      candidateAllowed(
        { authorityOutcome: proposal.authorityOutcome },
        authorityGrantAvailable,
      )
    )
    .map(({ proposal }) => proposal);

  const legalSubsets: ActionProposal[][] = [];
  for (let mask = 1; mask < (1 << eligible.length); mask += 1) {
    const subset = eligible.filter((_, index) => (mask & (1 << index)) !== 0);
    const result = applyWorldTick(state, {
      tickId: `probe:${round.roundId}:${mask}`,
      expectedWorldRevision: round.worldRevision,
      intents: subset.map((proposal, index) => ({
        commandSequence: index,
        command: proposal.command,
      })),
    });
    if (result.status === "accepted") legalSubsets.push(subset);
  }

  legalSubsets.sort((left, right) =>
    right.filter((proposal) => proposal.command.kind !== "wait").length -
      left.filter((proposal) => proposal.command.kind !== "wait").length ||
    right.length - left.length ||
    left.map((proposal) => proposal.proposalId).sort().join("|").localeCompare(
      right.map((proposal) => proposal.proposalId).sort().join("|"),
    )
  );
  return {
    policyId: STATION_ZERO_COORDINATION_POLICY_ID,
    legalSubsets,
    selected: legalSubsets[0] ?? null,
  };
}
