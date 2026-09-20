import type { StationZeroV3MissionControlView } from "./p2-model.ts";
import type {
  StationZeroV3AgentCandidate,
  StationZeroV3PlanImpactObjective,
  StationZeroV3PlanPreview,
} from "./p3-model.ts";

const POSITIONING_ROUTE_TAGS: Record<string, string[]> = {
  "recover-research-core": ["route:reactor-console"],
  "eliminate-hive-alpha": ["route:maintenance-nest"],
};

function selectedRescueCandidates(preview: StationZeroV3PlanPreview): Array<{
  candidate: StationZeroV3AgentCandidate;
  actorName: string;
  responsibilityObjectiveId: string | null;
}> {
  const rescueExplanations = new Map(preview.explanations.rescue.actorIntents.map((entry) => [entry.actorId, entry]));
  const rescueContexts = new Map(preview.contexts.filter((context) => context.factionId === "rescue").map((context) => [context.actor.actorId, context]));
  const rows: Array<{ candidate: StationZeroV3AgentCandidate; actorName: string; responsibilityObjectiveId: string | null }> = [];
  for (const decision of preview.agentDecisions.filter((entry) => entry.factionId === "rescue")) {
    const context = rescueContexts.get(decision.actorId);
    const candidate = context?.candidates.find((entry) => entry.candidateId === decision.candidateId);
    if (!context || !candidate) throw new TypeError(`Preview Rescue Decision lacks its admitted Candidate: ${decision.actorId}`);
    rows.push({
      candidate,
      actorName: rescueExplanations.get(decision.actorId)?.actorName ?? context.actor.name,
      responsibilityObjectiveId: context.responsibility && candidate.tags.includes("responsibility:advance")
        ? context.responsibility.objectiveId
        : null,
    });
  }
  return rows.sort((left, right) => left.candidate.actorId.localeCompare(right.candidate.actorId));
}

export function createStationZeroV3PlanImpact(
  preview: StationZeroV3PlanPreview,
  objectives: StationZeroV3MissionControlView["objectives"],
): StationZeroV3PlanImpactObjective[] {
  const exposedObjectives = objectives.filter((objective) =>
    objective.mandatory || objective.objectiveId === preview.playerOrder.primaryObjectiveId);
  const objectiveIds = new Set(exposedObjectives.map((objective) => objective.objectiveId));
  const direct = new Map<string, Map<string, string>>();
  const positioning = new Map<string, Map<string, string>>();
  const add = (target: Map<string, Map<string, string>>, objectiveId: string, actorId: string, actorName: string) => {
    if (!objectiveIds.has(objectiveId)) return;
    const actors = target.get(objectiveId) ?? new Map<string, string>();
    actors.set(actorId, actorName);
    target.set(objectiveId, actors);
  };

  for (const row of selectedRescueCandidates(preview)) {
    const { candidate, actorName, responsibilityObjectiveId } = row;
    for (const tag of candidate.tags) {
      if (tag.startsWith("objective:")) add(direct, tag.slice("objective:".length), candidate.actorId, actorName);
    }
    if (responsibilityObjectiveId) add(direct, responsibilityObjectiveId, candidate.actorId, actorName);
    if (candidate.intent.kind === "extract") add(direct, "rescue-team-survives", candidate.actorId, actorName);
    for (const [objectiveId, routeTags] of Object.entries(POSITIONING_ROUTE_TAGS)) {
      if (routeTags.some((tag) => candidate.tags.includes(tag))) add(positioning, objectiveId, candidate.actorId, actorName);
    }
  }

  return exposedObjectives.map((objective) => {
    const directActors = direct.get(objective.objectiveId) ?? new Map<string, string>();
    const positioningActors = positioning.get(objective.objectiveId) ?? new Map<string, string>();
    const selected = directActors.size > 0 ? directActors : positioningActors;
    return {
      objectiveId: objective.objectiveId,
      name: objective.name,
      mandatory: objective.mandatory,
      status: objective.status,
      progress: objective.progress,
      target: objective.target,
      selectedPriority: preview.playerOrder.primaryObjectiveId === objective.objectiveId,
      impact: directActors.size > 0 ? "direct" : positioningActors.size > 0 ? "positioning" : "none",
      actorIds: [...selected.keys()].sort(),
      actorNames: [...selected.entries()].sort(([left], [right]) => left.localeCompare(right)).map(([, name]) => name),
    };
  });
}
