import { stationZeroV3PlayerObjectiveViews } from "./mission-control.ts";
import type {
  StationZeroV3OperationDebrief,
  StationZeroV3OperationDebriefObjective,
} from "./p3-model.ts";
import type { StationZeroV3PlanningStore } from "./planning-store.ts";
import type { StationZeroV3Store } from "./persistence.ts";

function terminalReasonLabel(reason: string): string {
  switch (reason) {
    case "turn_limit": return "Turn limit reached";
    case "no_active_combatants": return "No active combatants remain";
    default:
      return reason.split("_").filter(Boolean).map((part) => `${part[0]?.toUpperCase() ?? ""}${part.slice(1)}`).join(" ");
  }
}

export function createStationZeroV3OperationDebrief(
  store: StationZeroV3Store,
  planningStore: StationZeroV3PlanningStore,
  runId: string,
): StationZeroV3OperationDebrief | null {
  const terminal = store.loadState(runId);
  if (terminal.encounter.status !== "terminal") return null;
  if (!terminal.encounter.reason) throw new TypeError("Terminal Station Zero v3 Encounter lacks a reason");

  const committedTurns = store.turnCount(runId);
  if (committedTurns !== terminal.encounter.turn) {
    throw new TypeError("Operation Debrief Turn count differs from terminal World state");
  }

  const initialObjectives = stationZeroV3PlayerObjectiveViews(store.stateAtRevision(runId, 0));
  const terminalObjectives = stationZeroV3PlayerObjectiveViews(terminal);
  const terminalById = new Map(terminalObjectives.map((objective) => [objective.objectiveId, objective]));
  const focusTurns = new Map<string, number>();
  const firstProgressTurn = new Map<string, number>();
  const completedTurn = new Map<string, number>();
  const previousProgress = new Map(initialObjectives.map((objective) => [objective.objectiveId, objective.progress]));

  for (let sequence = 0; sequence < committedTurns; sequence += 1) {
    const receipt = store.turnReceipt(runId, sequence);
    if (!receipt) throw new TypeError(`Operation Debrief lacks retained Turn ${sequence}`);
    const head = planningStore.headOrNull(runId, receipt.planningId);
    const preview = planningStore.currentPreview(runId, receipt.planningId);
    if (!head || !preview || head.committedPreviewId !== preview.previewId) {
      throw new TypeError(`Operation Debrief Turn lacks exact committed Preview: ${receipt.planningId}`);
    }
    const focusId = preview.playerOrder.primaryObjectiveId;
    focusTurns.set(focusId, (focusTurns.get(focusId) ?? 0) + 1);

    const afterObjectives = stationZeroV3PlayerObjectiveViews(receipt.state);
    for (const objective of afterObjectives) {
      const previous = previousProgress.get(objective.objectiveId) ?? 0;
      if (objective.progress > previous && !firstProgressTurn.has(objective.objectiveId)) {
        firstProgressTurn.set(objective.objectiveId, sequence + 1);
      }
      if (objective.status === "completed" && !completedTurn.has(objective.objectiveId)) {
        completedTurn.set(objective.objectiveId, sequence + 1);
      }
      previousProgress.set(objective.objectiveId, objective.progress);
    }
  }

  const exposedIds = new Set(
    initialObjectives
      .filter((objective) => objective.mandatory || (focusTurns.get(objective.objectiveId) ?? 0) > 0)
      .map((objective) => objective.objectiveId),
  );
  const objectives: StationZeroV3OperationDebriefObjective[] = initialObjectives
    .filter((objective) => exposedIds.has(objective.objectiveId))
    .map((objective) => {
      const final = terminalById.get(objective.objectiveId);
      if (!final) throw new TypeError(`Operation Debrief objective left terminal player projection: ${objective.objectiveId}`);
      return {
        objectiveId: objective.objectiveId,
        name: objective.name,
        mandatory: objective.mandatory,
        focusTurns: focusTurns.get(objective.objectiveId) ?? 0,
        finalProgress: final.progress,
        target: final.target,
        finalStatus: final.status,
        firstProgressTurn: firstProgressTurn.get(objective.objectiveId) ?? null,
        completedTurn: completedTurn.get(objective.objectiveId) ?? null,
      };
    });

  const focus = [...focusTurns.entries()]
    .map(([objectiveId, turns]) => {
      const objective = terminalById.get(objectiveId);
      if (!objective) throw new TypeError(`Operation Debrief focus is not player-visible: ${objectiveId}`);
      return { objectiveId, name: objective.name, turns, totalTurns: committedTurns };
    })
    .sort((left, right) => right.turns - left.turns || left.objectiveId.localeCompare(right.objectiveId));

  const required = objectives.filter((objective) => objective.mandatory);
  return {
    committedTurns,
    terminalReason: terminal.encounter.reason,
    terminalReasonLabel: terminalReasonLabel(terminal.encounter.reason),
    requiredCompleted: required.filter((objective) => objective.finalStatus === "completed").length,
    requiredTotal: required.length,
    focus,
    objectives,
  };
}
