import { sha256 } from "./digest.ts";
import type { WorldState } from "./world.ts";

export interface AllowedAction {
  actionId: string;
  kind: "restore_power";
  actorId: string;
  targetId: string;
  expectedRevision: number;
  summary: string;
}

export interface ProviderContext {
  contextId: string;
  worldDigest: string;
  worldRevision: number;
  goal: string;
  allowedActions: AllowedAction[];
}

export interface ProviderDecision {
  provider: string;
  contextId: string;
  selectedActionId: string | null;
  rationale: string;
}

export interface CognitionProvider {
  decide(context: ProviderContext): Promise<ProviderDecision>;
}

export function compileProviderContext(state: WorldState): ProviderContext {
  const room = state.rooms["life-support"];
  const engineer = state.agents["engineer-01"];
  const allowedActions: AllowedAction[] = [];

  if (
    room &&
    engineer &&
    !room.powered &&
    engineer.capabilities.includes("restore_power") &&
    engineer.inventory.includes("breaker-key")
  ) {
    allowedActions.push({
      actionId: "restore-life-support-power",
      kind: "restore_power",
      actorId: engineer.id,
      targetId: room.id,
      expectedRevision: state.revision,
      summary: "Use the breaker key to restore power to Life Support.",
    });
  }

  const payload = {
    worldDigest: sha256(state),
    worldRevision: state.revision,
    goal: "Restore stable life-support operation.",
    allowedActions,
  };

  return { contextId: sha256(payload), ...payload };
}

export class FixtureProvider implements CognitionProvider {
  async decide(context: ProviderContext): Promise<ProviderDecision> {
    const selected = context.allowedActions[0] ?? null;
    return {
      provider: "fixture-v0",
      contextId: context.contextId,
      selectedActionId: selected?.actionId ?? null,
      rationale: selected
        ? "Life Support is unpowered and the Engineer has the required capability and tool."
        : "No admitted action is currently available.",
    };
  }
}

export function admitProviderDecision(
  context: ProviderContext,
  decision: ProviderDecision,
): AllowedAction | null {
  if (decision.contextId !== context.contextId) {
    throw new Error("provider decision targets a different context");
  }
  if (decision.selectedActionId === null) {
    return null;
  }

  const action = context.allowedActions.find(
    (candidate) => candidate.actionId === decision.selectedActionId,
  );
  if (!action) {
    throw new Error("provider selected an action outside the admitted candidate set");
  }
  return action;
}
