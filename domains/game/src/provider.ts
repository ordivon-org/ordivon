import { sha256 } from "./digest.ts";
import type { AvailableAction, WorldState } from "./model.ts";
import { listAvailableActions } from "./world.ts";

export interface ProviderContext {
  contextId: string;
  worldDigest: string;
  worldRevision: number;
  goal: string;
  allowedActions: AvailableAction[];
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
  const payload = {
    worldDigest: sha256(state),
    worldRevision: state.revision,
    goal: "Stabilize Station Zero and transmit a verified rescue signal.",
    allowedActions: listAvailableActions(state),
  };
  return { contextId: sha256(payload), ...payload };
}

export class FixtureProvider implements CognitionProvider {
  async decide(context: ProviderContext): Promise<ProviderDecision> {
    const selected = context.allowedActions.find((action) => action.command.kind !== "wait") ?? context.allowedActions[0] ?? null;
    return {
      provider: "fixture-v1",
      contextId: context.contextId,
      selectedActionId: selected?.actionId ?? null,
      rationale: selected
        ? `Choose admitted action: ${selected.label}`
        : "No admitted action is currently available.",
    };
  }
}

export function admitProviderDecision(
  context: ProviderContext,
  decision: ProviderDecision,
): AvailableAction | null {
  if (decision.contextId !== context.contextId) {
    throw new Error("provider decision targets a different context");
  }
  if (decision.selectedActionId === null) return null;
  const action = context.allowedActions.find((candidate) => candidate.actionId === decision.selectedActionId);
  if (!action) throw new Error("provider selected an action outside the admitted candidate set");
  return action;
}
