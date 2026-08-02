import { sha256 } from "../digest.ts";
import type { GameStore } from "../storage.ts";
import { actorCanClaimMissionItem } from "../team/context.ts";
import { TEAM_OBJECTIVE_GRAPH, objectiveSatisfied } from "../team/objectives.ts";
import { applyWorldTick, listAvailableActions, materializeAction } from "../world.ts";
import type {
  DiagnosisClaim,
  DiagnosisEvidenceClass,
  ReplayProjection,
  RunDiagnosis,
} from "./model.ts";
import { buildReplayProjection } from "./projection.ts";

function addClaim(
  output: DiagnosisClaim[],
  input: Omit<DiagnosisClaim, "claimId">,
): void {
  const base = {
    evidenceClass: input.evidenceClass,
    revision: input.revision,
    title: input.title,
    explanation: input.explanation,
    evidenceNodeIds: [...new Set(input.evidenceNodeIds)].sort(),
  };
  output.push({ claimId: `diagnosis:${sha256(base)}`, ...base });
}

function evidence(runId: string, revision: number, nodeId?: string | null): string[] {
  return nodeId ? [nodeId] : [`world-state:${runId}:${revision}`];
}

export function diagnosisDirectExplanation(reason: string | null): [string, string] {
  switch (reason) {
    case "power_exhausted":
      return [
        "Battery reserve reached zero",
        "The terminal mission predicate was triggered by exhausted battery charge.",
      ];
    case "engineer_incapacitated":
      return [
        "The Engineer was incapacitated",
        "The terminal predicate was triggered when Engineer health reached zero.",
      ];
    case "team_incapacitated":
      return [
        "The specialist Team was incapacitated",
        "The terminal predicate was triggered when no active specialist retained health.",
      ];
    case "crew_lost":
      return [
        "The injured crew member was lost",
        "The terminal predicate was triggered when crew health reached zero.",
      ];
    case "reactor_meltdown":
      return [
        "Reactor heat reached the terminal limit",
        "The terminal predicate was triggered by reactor meltdown.",
      ];
    case "mission_timeout":
      return [
        "The mission reached its turn limit",
        "The terminal predicate was triggered before every rescue requirement was satisfied.",
      ];
    case "rescue_signal_verified":
      return [
        "Rescue conditions were verified",
        "The distress signal and all required stabilization conditions were satisfied.",
      ];
    default:
      return [
        "Terminal World state was verified",
        `The retained World ended with reason ${reason ?? "unknown"}.`,
      ];
  }
}

function previousValue(
  points: Array<{ revision: number; value: number }>,
  revision: number,
): number | null {
  return points.find((point) => point.revision === revision - 1)?.value ?? null;
}

export function boundedFinalRoundSensitivity(
  store: GameStore,
  runId = store.activeRunId,
  retainedProjection?: ReplayProjection,
): DiagnosisClaim[] {
  const projection = retainedProjection ?? buildReplayProjection(store, runId);
  const terminal = projection.frames.at(-1)!;
  if (terminal.state.mission.status !== "failure" || terminal.revision < 1) return [];
  const plan = terminal.tickPlan;
  if (!terminal.round || !plan) return [];

  const selected = plan.selectedProposalIds
    .map((proposalId) =>
      terminal.proposals.find((proposal) => proposal.proposalId === proposalId),
    )
    .filter((proposal): proposal is NonNullable<typeof proposal> => Boolean(proposal));
  if (selected.length === 0) return [];

  const before = projection.frames[terminal.revision - 1]!.state;
  for (const proposal of [...selected].sort((left, right) =>
    left.actorId.localeCompare(right.actorId),
  )) {
    const alternatives = listAvailableActions(before, proposal.actorId)
      .sort((left, right) => left.actionId.localeCompare(right.actionId));
    for (const alternative of alternatives) {
      const intents = selected.map((candidate, index) => ({
        commandSequence: index,
        command: candidate.proposalId === proposal.proposalId
          ? materializeAction(
              alternative,
              `counterfactual:${proposal.proposalId}:${alternative.actionId}`,
            )
          : {
              ...candidate.command,
              commandId: `counterfactual:retained:${candidate.proposalId}`,
            },
      }));
      const result = applyWorldTick(before, {
        tickId: `counterfactual:${terminal.round.roundId}:${proposal.actorId}`,
        expectedWorldRevision: before.revision,
        intents,
      });
      if (
        result.status === "accepted" &&
        result.state.mission.status !== terminal.state.mission.status
      ) {
        const base = {
          evidenceClass: "COUNTERFACTUAL_SENSITIVE" as const,
          revision: terminal.revision,
          title: `${proposal.actorId} final-Round alternative changed the terminal status`,
          explanation:
            `Replacing retained candidate ${proposal.actionCandidateId} with legal action ` +
            `${alternative.actionId}, while keeping the other selected intents fixed, changes ` +
            `the one-Tick simulation from ${terminal.state.mission.status} to ` +
            `${result.state.mission.status}. This is bounded sensitivity, not proof of a unique cause.`,
          evidenceNodeIds: [
            `team-proposal:${proposal.proposalId}`,
            ...(terminal.worldEvent ? [terminal.worldEvent.nodeId] : []),
          ],
        };
        return [{ claimId: `diagnosis:${sha256(base)}`, ...base }];
      }
    }
  }
  return [];
}

export function diagnoseProjection(
  store: GameStore,
  projection: ReplayProjection,
): RunDiagnosis {
  const { runId, graph, curves, keyTurns, frames } = projection;
  const terminal = frames.at(-1)!;
  const claims: DiagnosisClaim[] = [];
  const terminalEvidence = evidence(
    runId,
    terminal.revision,
    terminal.worldEvent?.nodeId,
  );

  if (terminal.state.mission.status !== "running") {
    const [title, explanation] = diagnosisDirectExplanation(terminal.state.mission.reason);
    addClaim(claims, {
      evidenceClass: "VERIFIED_DIRECT",
      revision: terminal.revision,
      title,
      explanation,
      evidenceNodeIds: terminalEvidence,
    });
  } else {
    addClaim(claims, {
      evidenceClass: "CONTEXT_ONLY",
      revision: terminal.revision,
      title: "Mission remains active",
      explanation: "No terminal Game predicate has been retained for this Run.",
      evidenceNodeIds: [`world-state:${runId}:${terminal.revision}`],
    });
  }

  const oxygenLoss = curves.oxygen.find((point, index) =>
    index > 0 && point.value < curves.oxygen[index - 1]!.value,
  );
  if (
    oxygenLoss &&
    terminal.state.mission.status === "failure" &&
    terminal.state.resources.oxygen < 45
  ) {
    const frame = frames[oxygenLoss.revision]!;
    addClaim(claims, {
      evidenceClass: "VERIFIED_CONTRIBUTOR",
      revision: oxygenLoss.revision,
      title: "Oxygen loss reduced the health margin",
      explanation:
        `Oxygen fell from ${previousValue(curves.oxygen, oxygenLoss.revision) ?? "unknown"}% ` +
        `to ${oxygenLoss.value}% and ended below the retained health-damage boundary. ` +
        "This is a verified contributor, not the unique cause.",
      evidenceNodeIds: evidence(runId, oxygenLoss.revision, frame.worldEvent?.nodeId),
    });
  }

  const battery = curves.battery.find((point, index) =>
    point.value <= 10 && (index === 0 || curves.battery[index - 1]!.value > 10),
  );
  if (battery && terminal.state.mission.status === "failure") {
    const frame = frames[battery.revision]!;
    addClaim(claims, {
      evidenceClass: "VERIFIED_CONTRIBUTOR",
      revision: battery.revision,
      title: "Battery reserve entered the critical band",
      explanation:
        `Battery charge reached ${battery.value}. ` +
        "The retained trajectory had little remaining power margin.",
      evidenceNodeIds: evidence(runId, battery.revision, frame.worldEvent?.nodeId),
    });
  }

  const healthCurves = [
    ...Object.entries(curves.actorHealth),
    ...Object.entries(curves.crewHealth),
  ];
  for (const [subjectId, points] of healthCurves) {
    const loss = points.find((point, index) =>
      index > 0 && point.value < points[index - 1]!.value,
    );
    if (
      !loss ||
      terminal.state.mission.status !== "failure" ||
      points.at(-1)!.value > 25
    ) continue;
    const frame = frames[loss.revision]!;
    addClaim(claims, {
      evidenceClass: "VERIFIED_CONTRIBUTOR",
      revision: loss.revision,
      title: `${subjectId} lost health during the mission`,
      explanation:
        `Retained World state shows health loss and a terminal value of ` +
        `${points.at(-1)!.value}.`,
      evidenceNodeIds: evidence(runId, loss.revision, frame.worldEvent?.nodeId),
    });
  }

  if (terminal.state.mission.reason === "mission_timeout") {
    const incomplete = TEAM_OBJECTIVE_GRAPH.nodes
      .filter((node) => !objectiveSatisfied(terminal.state, node.objectiveId))
      .map((node) => node.label);
    addClaim(claims, {
      evidenceClass: "VERIFIED_CONTRIBUTOR",
      revision: terminal.revision,
      title: "Rescue requirements remained incomplete",
      explanation: `At timeout, these retained requirements were unsatisfied: ${incomplete.join(", ")}.`,
      evidenceNodeIds: terminalEvidence,
    });
  }

  for (const itemId of ["sealant", "spare-parts"] as const) {
    const blocked = Object.values(terminal.state.agents).filter((actor) =>
      (actor.inventory[itemId] ?? 0) > 0 &&
      !actorCanClaimMissionItem(terminal.state, actor.id, itemId),
    );
    if (blocked.length === 0 || terminal.state.mission.status !== "failure") continue;
    addClaim(claims, {
      evidenceClass: "VERIFIED_CONTRIBUTOR",
      revision: terminal.revision,
      title: `${itemId} remained with an Actor unable to consume it`,
      explanation:
        `${blocked.map((actor) => actor.name).join(", ")} retained ${itemId} while ` +
        "rescue work remained incomplete. Ownership is verified; this is not asserted as the sole cause.",
      evidenceNodeIds: terminalEvidence,
    });
  }

  const sensitive = boundedFinalRoundSensitivity(store, runId, projection);
  claims.push(...sensitive);
  if (sensitive.length === 0) {
    addClaim(claims, {
      evidenceClass: "CONTEXT_ONLY",
      revision: terminal.revision,
      title: "No bounded one-step counterfactual was certified",
      explanation:
        "The retained trace does not prove that replacing one legal primitive action in the " +
        "final Team Tick would change the terminal result. No counterfactual cause is asserted.",
      evidenceNodeIds: [`world-state:${runId}:${terminal.revision}`],
    });
  }

  const rank: Record<DiagnosisEvidenceClass, number> = {
    VERIFIED_DIRECT: 0,
    VERIFIED_CONTRIBUTOR: 1,
    COUNTERFACTUAL_SENSITIVE: 2,
    CONTEXT_ONLY: 3,
  };
  claims.sort((left, right) =>
    rank[left.evidenceClass] - rank[right.evidenceClass] ||
    left.revision - right.revision ||
    left.claimId.localeCompare(right.claimId),
  );

  const base = {
    schemaVersion: 1 as const,
    kind: "ordivon.game.run-diagnosis" as const,
    runId,
    terminal: {
      status: terminal.state.mission.status,
      reason: terminal.state.mission.reason,
      revision: terminal.revision,
      digest: terminal.digest,
    },
    graphDigest: graph.graphDigest,
    curvesDigest: curves.curvesDigest,
    keyTurns,
    claims,
    unsupportedCounterfactualReason: sensitive.length === 0
      ? "No retained final-Round one-Actor alternative changed the terminal status."
      : null,
  };
  return { ...base, diagnosisDigest: sha256(base) };
}

export function diagnoseRun(
  store: GameStore,
  runId = store.activeRunId,
): RunDiagnosis {
  return diagnoseProjection(store, buildReplayProjection(store, runId));
}
