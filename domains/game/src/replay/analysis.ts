import { sha256 } from "../digest.ts";
import type { ItemId, WorldState } from "../model.ts";
import type { GameStore } from "../storage.ts";
import { TEAM_OBJECTIVE_GRAPH, objectiveSatisfied } from "../team/objectives.ts";
import { buildRunEvidenceGraph } from "./evidence.ts";
import { buildReplayFrames } from "./frames.ts";
import type {
  ItemLocationCurvePoint,
  ReplayCurves,
  ReplayFrame,
  ReplayKeyTurn,
  RunEvidenceGraph,
} from "./model.ts";

const CRITICAL_ITEMS: ItemId[] = [
  "sealant",
  "spare-parts",
  "medkit",
  "breaker-key",
  "toolkit",
];

function itemPoint(state: WorldState, itemId: ItemId): ItemLocationCurvePoint {
  const rooms = Object.fromEntries(
    Object.values(state.rooms)
      .sort((left, right) => left.id.localeCompare(right.id))
      .map((room) => [room.id, room.inventory[itemId] ?? 0]),
  );
  const actors = Object.fromEntries(
    Object.values(state.agents)
      .sort((left, right) => left.id.localeCompare(right.id))
      .map((actor) => [actor.id, actor.inventory[itemId] ?? 0]),
  );
  const consumed = state.resources.consumedItems[itemId] ?? 0;
  return {
    revision: state.revision,
    rooms,
    actors,
    consumed,
    total:
      Object.values(rooms).reduce((sum, quantity) => sum + quantity, 0) +
      Object.values(actors).reduce((sum, quantity) => sum + quantity, 0) +
      consumed,
  };
}

export function replayCurvesFromFrames(
  runId: string,
  graph: RunEvidenceGraph,
  frames: ReplayFrame[],
): ReplayCurves {
  const first = frames[0]?.state;
  if (!first) throw new TypeError("Replay projection requires a Genesis frame");

  const actorIds = Object.keys(first.agents).sort();
  const crewIds = Object.keys(first.crew).sort();
  const systemIds = Object.keys(first.systems).sort();
  const itemIds = Object.keys(first.resources.consumedItems).sort() as ItemId[];
  const objectiveIds = TEAM_OBJECTIVE_GRAPH.nodes.map((node) => node.objectiveId);

  const base = {
    schemaVersion: 1 as const,
    kind: "ordivon.game.replay-curves" as const,
    runId,
    graphDigest: graph.graphDigest,
    revisions: frames.map((frame) => frame.revision),
    battery: frames.map((frame) => ({
      revision: frame.revision,
      value: frame.state.resources.batteryCharge,
    })),
    oxygen: frames.map((frame) => ({
      revision: frame.revision,
      value: frame.state.resources.oxygen,
    })),
    reactorHeat: frames.map((frame) => ({
      revision: frame.revision,
      value: frame.state.resources.reactorHeat,
    })),
    actorHealth: Object.fromEntries(
      actorIds.map((actorId) => [
        actorId,
        frames.map((frame) => ({
          revision: frame.revision,
          value: frame.state.agents[actorId]?.health ?? 0,
        })),
      ]),
    ),
    crewHealth: Object.fromEntries(
      crewIds.map((crewId) => [
        crewId,
        frames.map((frame) => ({
          revision: frame.revision,
          value: frame.state.crew[crewId]?.health ?? 0,
        })),
      ]),
    ),
    systems: Object.fromEntries(
      systemIds.map((systemId) => [
        systemId,
        frames.map((frame) => ({
          revision: frame.revision,
          integrity: frame.state.systems[systemId]?.integrity ?? 0,
          powered: frame.state.systems[systemId]?.powered ?? false,
        })),
      ]),
    ),
    items: Object.fromEntries(
      itemIds.map((itemId) => [
        itemId,
        frames.map((frame) => itemPoint(frame.state, itemId)),
      ]),
    ),
    objectives: Object.fromEntries(
      objectiveIds.map((objectiveId) => [
        objectiveId,
        frames.map((frame) => ({
          revision: frame.revision,
          value: objectiveSatisfied(frame.state, objectiveId),
        })),
      ]),
    ),
  };

  return { ...base, curvesDigest: sha256(base) };
}

export function buildReplayCurves(
  store: GameStore,
  runId = store.activeRunId,
  graph = buildRunEvidenceGraph(store, runId),
): ReplayCurves {
  return replayCurvesFromFrames(runId, graph, buildReplayFrames(store, runId, graph));
}

function frameEvidence(frame: ReplayFrame): string[] {
  return frame.worldEvent
    ? [frame.worldEvent.nodeId]
    : frame.evidenceNodeIds.filter((nodeId) => nodeId.startsWith("world-state:"));
}

function addKeyTurn(
  output: ReplayKeyTurn[],
  input: Omit<ReplayKeyTurn, "keyTurnId">,
): void {
  const evidenceNodeIds = [...input.evidenceNodeIds].sort();
  const identity = {
    revision: input.revision,
    kind: input.kind,
    title: input.title,
    evidenceNodeIds,
  };
  output.push({
    keyTurnId: `key-turn:${sha256(identity)}`,
    ...input,
    evidenceNodeIds,
  });
}

function firstThreshold(
  points: Array<{ revision: number; value: number }>,
  predicate: (value: number) => boolean,
): number | null {
  return points.find((point, index) =>
    predicate(point.value) && (index === 0 || !predicate(points[index - 1]!.value)),
  )?.revision ?? null;
}

export function replayKeyTurnsFromFrames(
  runId: string,
  curves: ReplayCurves,
  frames: ReplayFrame[],
): ReplayKeyTurn[] {
  const output: ReplayKeyTurn[] = [];
  const framesByRevision = new Map(frames.map((frame) => [frame.revision, frame]));
  const frame = (revision: number): ReplayFrame => {
    const retained = framesByRevision.get(revision);
    if (!retained) throw new TypeError(`Missing Replay Frame ${revision}`);
    return retained;
  };

  addKeyTurn(output, {
    revision: 0,
    priority: 10,
    kind: "genesis",
    title: "Mission deployed",
    detail: "Station Zero Genesis state was verified.",
    evidenceNodeIds: [`world-state:${runId}:0`],
  });

  const resourceThresholds: Array<[
    string,
    Array<{ revision: number; value: number }>,
    (value: number) => boolean,
    string,
  ]> = [
    [
      "Battery reserve became critical",
      curves.battery,
      (value) => value <= 10,
      "Battery crossed the 10-unit warning boundary.",
    ],
    [
      "Oxygen reserve became critical",
      curves.oxygen,
      (value) => value < 45,
      "Oxygen crossed the 45% health-damage boundary.",
    ],
    [
      "Reactor heat became critical",
      curves.reactorHeat,
      (value) => value >= 85,
      "Reactor heat crossed the 85-unit exposure boundary.",
    ],
  ];

  for (const [title, points, predicate, detail] of resourceThresholds) {
    const revision = firstThreshold(points, predicate);
    if (revision !== null) {
      addKeyTurn(output, {
        revision,
        priority: 70,
        kind: "resource-threshold",
        title,
        detail,
        evidenceNodeIds: frameEvidence(frame(revision)),
      });
    }
  }

  const healthCurves = [
    ...Object.entries(curves.actorHealth),
    ...Object.entries(curves.crewHealth),
  ];
  for (const [subjectId, points] of healthCurves) {
    const revision = firstThreshold(points, (value) => value <= 25);
    if (revision !== null) {
      addKeyTurn(output, {
        revision,
        priority: 75,
        kind: "health-threshold",
        title: `${subjectId} entered critical health`,
        detail: "Health crossed the 25-point critical boundary.",
        evidenceNodeIds: frameEvidence(frame(revision)),
      });
    }
  }

  for (const [objectiveId, points] of Object.entries(curves.objectives)) {
    const transition = points.find((point, index) =>
      point.value && index > 0 && !points[index - 1]!.value,
    );
    if (!transition) continue;
    const definition = TEAM_OBJECTIVE_GRAPH.nodes.find(
      (node) => node.objectiveId === objectiveId,
    );
    addKeyTurn(output, {
      revision: transition.revision,
      priority: objectiveId === "verified-rescue" ? 95 : 55,
      kind: "objective",
      title: definition?.label ?? objectiveId,
      detail: "Objective changed from unsatisfied to satisfied.",
      evidenceNodeIds: frameEvidence(frame(transition.revision)),
    });
  }

  for (const itemId of CRITICAL_ITEMS) {
    const points = curves.items[itemId] ?? [];
    for (let index = 1; index < points.length; index += 1) {
      const before = points[index - 1]!;
      const after = points[index]!;
      const gained = Object.entries(after.actors).find(
        ([actorId, quantity]) => quantity > (before.actors[actorId] ?? 0),
      );
      if (!gained) continue;
      addKeyTurn(output, {
        revision: after.revision,
        priority: 50,
        kind: "critical-item",
        title: `${gained[0]} acquired ${itemId}`,
        detail: "A mission-critical item changed ownership.",
        evidenceNodeIds: frameEvidence(frame(after.revision)),
      });
    }
  }

  for (const current of frames) {
    if (
      current.authorityGrants.length > 0 ||
      current.authorityDecisions.some((decision) => decision.outcome === "require-human")
    ) {
      addKeyTurn(output, {
        revision: current.revision,
        priority: 65,
        kind: "authority",
        title: "Human authority affected the Round",
        detail: "The retained Round required or consumed a human authority decision.",
        evidenceNodeIds: current.evidenceNodeIds.filter((nodeId) =>
          nodeId.startsWith("authority-"),
        ),
      });
    }
    if (current.playerInterventions.length > 0) {
      addKeyTurn(output, {
        revision: current.revision,
        priority: 60,
        kind: "player",
        title: "Player changed mission control",
        detail: current.playerInterventions.map((entry) => entry.summary).join("; "),
        evidenceNodeIds: current.playerInterventions.map((entry) => entry.nodeId),
      });
    }
  }

  const terminal = frames.at(-1)!;
  if (terminal.state.mission.status !== "running") {
    addKeyTurn(output, {
      revision: terminal.revision,
      priority: 100,
      kind: "terminal",
      title: terminal.state.mission.status === "victory"
        ? "Rescue verified"
        : `Mission failed: ${terminal.state.mission.reason}`,
      detail: "The terminal World state and reason were replay-verified.",
      evidenceNodeIds: frameEvidence(terminal),
    });
  }

  return output
    .sort((left, right) =>
      right.priority - left.priority ||
      left.revision - right.revision ||
      left.keyTurnId.localeCompare(right.keyTurnId),
    )
    .filter((turn, index, all) =>
      all.findIndex((candidate) =>
        candidate.revision === turn.revision &&
        candidate.kind === turn.kind &&
        candidate.title === turn.title,
      ) === index,
    )
    .slice(0, 12)
    .sort((left, right) =>
      left.revision - right.revision || right.priority - left.priority,
    );
}

export function buildKeyTurns(
  store: GameStore,
  runId = store.activeRunId,
  graph = buildRunEvidenceGraph(store, runId),
  curves?: ReplayCurves,
  frames = buildReplayFrames(store, runId, graph),
): ReplayKeyTurn[] {
  const retainedCurves = curves ?? replayCurvesFromFrames(runId, graph, frames);
  return replayKeyTurnsFromFrames(runId, retainedCurves, frames);
}
