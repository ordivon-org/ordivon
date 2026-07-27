import assert from "node:assert/strict";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import { ProviderAdapterError } from "../src/providers/types.ts";
import { ENGINEER_ID } from "../src/scenario.ts";
import { GameStore } from "../src/storage.ts";
import { compileTeamContext } from "../src/team/context.ts";
import type { CompiledTeamContext, TeamProviderDecision } from "../src/team/model.ts";
import {
  admitTeamProviderDecision,
  FixtureTeamProvider,
  parseTeamProviderDecision,
  TeamDecisionAdmissionError,
  validateTeamProviderDecision,
} from "../src/team/providers.ts";
import { actorTaskId, TeamStore } from "../src/team/store.ts";

function context(): { game: GameStore; team: TeamStore; context: CompiledTeamContext } {
  const game = new GameStore(":memory:");
  game.createRun({ runId: "run:team-provider-contract", scenarioVersion: 2, rulesetVersion: 3 });
  game.setActiveRun("run:team-provider-contract");
  const team = new TeamStore(game);
  team.initialize();
  const compiled = compileTeamContext({
    store: game,
    runId: game.activeRunId,
    task: team.getTask(actorTaskId(game.activeRunId, ENGINEER_ID)),
    profile: team.getProfile(ENGINEER_ID),
    goal: team.getGoal(),
    messages: [],
    policyMode: "autonomous",
  });
  return { game, team, context: compiled };
}

function raw(contextId: string, selectedActionCandidateId: string | null): Record<string, unknown> {
  return { contextId, selectedActionCandidateId, confidence: 0.75, rationale: "Exact structured decision." };
}

test("strict Team Provider parser accepts one exact admitted Decision", () => {
  const fixture = context();
  try {
    const selected = fixture.context.allowedActions[0];
    assert.ok(selected);
    const decision = parseTeamProviderDecision(fixture.context, raw(fixture.context.contextId, selected.actionCandidateId), "provider:test");
    assert.equal(decision.providerId, "provider:test");
    assert.equal(decision.selectedActionCandidateId, selected.actionCandidateId);
    validateTeamProviderDecision(decision);
    assert.equal(admitTeamProviderDecision(fixture.context, fixture.game.loadState(), sha256(fixture.game.loadState()), decision)?.actionCandidateId, selected.actionCandidateId);
  } finally { fixture.game.close(); }
});

test("strict Team Provider parser rejects shape, field, type, identity, and value drift", () => {
  const fixture = context();
  try {
    const candidate = fixture.context.allowedActions[0]!;
    const invalid: unknown[] = [
      null,
      [],
      { ...raw(fixture.context.contextId, candidate.actionCandidateId), extra: true },
      { ...raw(fixture.context.contextId, candidate.actionCandidateId), contextId: 1 },
      { ...raw(fixture.context.contextId, candidate.actionCandidateId), selectedActionCandidateId: 1 },
      { ...raw(fixture.context.contextId, candidate.actionCandidateId), confidence: "high" },
      { ...raw(fixture.context.contextId, candidate.actionCandidateId), rationale: 1 },
      { ...raw(fixture.context.contextId, candidate.actionCandidateId), confidence: 2 },
      { ...raw(fixture.context.contextId, candidate.actionCandidateId), rationale: "" },
      raw("team-context:other", candidate.actionCandidateId),
      raw(fixture.context.contextId, "team-action:invented"),
    ];
    for (const value of invalid) {
      assert.throws(
        () => parseTeamProviderDecision(fixture.context, value, "provider:test"),
        (error: unknown) => error instanceof ProviderAdapterError && error.code === "invalid_output",
      );
    }
    assert.throws(
      () => validateTeamProviderDecision({ providerId: "", contextId: fixture.context.contextId, selectedActionCandidateId: null, confidence: 0, rationale: "x" }),
      /providerId and rationale/,
    );
    assert.throws(
      () => validateTeamProviderDecision({ providerId: "p", contextId: fixture.context.contextId, selectedActionCandidateId: null, confidence: -1, rationale: "x" }),
      /confidence/,
    );
  } finally { fixture.game.close(); }
});

test("Team Decision admission distinguishes wrong Context, stale World, invented Action, and null selection", () => {
  const fixture = context();
  try {
    const candidate = fixture.context.allowedActions[0]!;
    const base: TeamProviderDecision = {
      providerId: "provider:test",
      contextId: fixture.context.contextId,
      selectedActionCandidateId: candidate.actionCandidateId,
      confidence: 0.5,
      rationale: "test",
    };
    assert.throws(
      () => admitTeamProviderDecision(fixture.context, fixture.game.loadState(), sha256(fixture.game.loadState()), { ...base, contextId: "team-context:wrong" }),
      (error: unknown) => error instanceof TeamDecisionAdmissionError && error.code === "wrong_context",
    );
    const stale = structuredClone(fixture.game.loadState());
    stale.revision += 1;
    assert.throws(
      () => admitTeamProviderDecision(fixture.context, stale, sha256(stale), base),
      (error: unknown) => error instanceof TeamDecisionAdmissionError && error.code === "stale_world",
    );
    assert.throws(
      () => admitTeamProviderDecision(fixture.context, fixture.game.loadState(), sha256(fixture.game.loadState()), { ...base, selectedActionCandidateId: "team-action:invented" }),
      (error: unknown) => error instanceof TeamDecisionAdmissionError && error.code === "invented_action",
    );
    assert.equal(admitTeamProviderDecision(fixture.context, fixture.game.loadState(), sha256(fixture.game.loadState()), { ...base, selectedActionCandidateId: null }), null);
  } finally { fixture.game.close(); }
});

test("Fixture Team Provider covers scheduled, failed, waiting, fallback, and alternative breach choices", async () => {
  const fixture = context();
  try {
    const provider = new FixtureTeamProvider();
    const first = await provider.decide(fixture.context);
    assert.equal(first.selectedActionCandidateId, fixture.context.allowedActions.find((entry) => entry.actionId === "move:power-junction")?.actionCandidateId);

    const failed = new FixtureTeamProvider({ failActors: [ENGINEER_ID] });
    await assert.rejects(() => failed.decide(fixture.context), (error: unknown) => error instanceof ProviderAdapterError && error.code === "process_failed");

    const waitContext: CompiledTeamContext = { ...fixture.context, worldRevision: 99 };
    const waiting = await provider.decide(waitContext);
    assert.equal(waiting.selectedActionCandidateId, waitContext.allowedActions.find((entry) => entry.actionId === "wait")?.actionCandidateId);

    const firstOnly: CompiledTeamContext = { ...fixture.context, worldRevision: 99, allowedActions: [fixture.context.allowedActions[0]!] };
    assert.equal((await provider.decide(firstOnly)).selectedActionCandidateId, firstOnly.allowedActions[0]?.actionCandidateId);

    const empty: CompiledTeamContext = { ...fixture.context, actorId: "unknown-actor", worldRevision: 99, allowedActions: [] };
    const none = await provider.decide(empty);
    assert.equal(none.selectedActionCandidateId, null);
    assert.equal(none.confidence, 0);
    assert.match(none.rationale, /No admitted action/);

    const sealProvider = new FixtureTeamProvider({ breachStrategy: "engineer-seal" });
    const moveMaintenance = { ...fixture.context.allowedActions[0]!, actionCandidateId: "team-action:move-maintenance", actionId: "move:maintenance" };
    const seal = { ...fixture.context.allowedActions[0]!, actionCandidateId: "team-action:seal", actionId: "seal:maintenance-breach" };
    assert.equal((await sealProvider.decide({ ...fixture.context, worldRevision: 7, allowedActions: [moveMaintenance] })).selectedActionCandidateId, moveMaintenance.actionCandidateId);
    assert.equal((await sealProvider.decide({ ...fixture.context, worldRevision: 8, allowedActions: [seal] })).selectedActionCandidateId, seal.actionCandidateId);
    assert.equal((await sealProvider.decide({ ...fixture.context, actorId: "medic-01", worldRevision: 50 })).selectedActionCandidateId,
      fixture.context.allowedActions.find((entry) => entry.actionId === "wait")?.actionCandidateId);
    assert.equal((await sealProvider.decide({ ...fixture.context, actorId: "security-01", worldRevision: 3 })).selectedActionCandidateId,
      fixture.context.allowedActions.find((entry) => entry.actionId === "wait")?.actionCandidateId);
    assert.equal((await sealProvider.decide({ ...fixture.context, actorId: "coordinator", worldRevision: 0 })).selectedActionCandidateId,
      fixture.context.allowedActions.find((entry) => entry.actionId === "wait")?.actionCandidateId);
  } finally { fixture.game.close(); }
});
