import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import fc, { type Command } from "fast-check";

import { sha256 } from "../src/digest.ts";
import type { WorldState } from "../src/model.ts";
import { resolveRuleset } from "../src/registry.ts";
import { assertWorldInvariants, initialTeamWorld } from "../src/scenario.ts";
import { GameStore } from "../src/storage.ts";
import { listAvailableActions, materializeAction } from "../src/world.ts";

const ruleset = resolveRuleset("station-zero-core", 3);

test("property: arbitrary legal action sequences preserve all world invariants", () => {
  fc.assert(
    fc.property(fc.array(fc.nat(), { maxLength: 45 }), (choices) => {
      let state = initialTeamWorld();
      for (const [step, choice] of choices.entries()) {
        if (state.mission.status !== "running") break;
        const actions = listAvailableActions(state);
        assert.ok(actions.length > 0);
        for (const candidate of actions) {
          const probe = ruleset.apply(
            state,
            materializeAction(candidate, `probe:${step}:${candidate.actionId}`),
          );
          assert.equal(probe.status, "accepted", candidate.actionId);
        }
        const action = actions[choice % actions.length];
        assert.ok(action);
        const command = materializeAction(action, `property:${step}:${choice}`);
        const beforeDigest = sha256(state);
        const beforeRevision = state.revision;
        const result = ruleset.apply(state, command);
        assert.equal(sha256(state), beforeDigest, "reducer mutated its input");
        if (result.status !== "accepted") throw new Error(`${result.code}: ${result.reason}`);
        assert.equal(result.status, "accepted");
        assert.equal(result.state.revision, beforeRevision + 1);
        assert.equal(result.event.verification?.success, true);
        assertWorldInvariants(result.state);
        state = result.state;
      }
    }),
    { numRuns: 200 },
  );
});

test("property: stale commands are rejected without changing the input", () => {
  fc.assert(
    fc.property(fc.integer({ min: 1, max: 10_000 }), (offset) => {
      const state = initialTeamWorld();
      const before = sha256(state);
      const result = ruleset.apply(state, {
        kind: "move",
        commandId: `stale:${offset}`,
        actorId: "engineer-01",
        targetRoomId: "power-junction",
        expectedRevision: state.revision + offset,
      });
      assert.equal(result.status, "rejected");
      assert.equal(result.status === "rejected" ? result.code : null, "stale_revision");
      assert.equal(sha256(state), before);
    }),
    { numRuns: 100 },
  );
});

test("property: pure, persisted, recovered, and verified executions agree", () => {
  fc.assert(
    fc.property(fc.array(fc.nat(), { maxLength: 18 }), (choices) => {
      const directory = mkdtempSync(join(tmpdir(), "ordivon-game-property-store-"));
      const path = join(directory, "world.sqlite3");
      try {
        const store = new GameStore(path);
        let pure = initialTeamWorld();
        for (const [step, choice] of choices.entries()) {
          if (pure.mission.status !== "running") break;
          const actions = listAvailableActions(pure);
          const action = actions[choice % actions.length];
          assert.ok(action);
          const command = materializeAction(action, `equivalence:${step}:${choice}`);
          const pureResult = ruleset.apply(pure, command);
          if (pureResult.status !== "accepted") throw new Error(`${pureResult.code}: ${pureResult.reason}`);
          assert.equal(pureResult.status, "accepted");
          const persisted = store.apply(command);
          if (persisted.result.status !== "accepted") throw new Error(`${persisted.result.code}: ${persisted.result.reason}`);
          assert.equal(persisted.result.status, "accepted");
          pure = pureResult.state;
          assert.equal(sha256(store.loadState()), sha256(pure));
        }
        const expected = sha256(pure);
        store.close();
        const reopened = new GameStore(path);
        assert.equal(reopened.recover().digest, expected);
        assert.equal(reopened.verifyReplay().digest, expected);
        reopened.close();
      } finally {
        rmSync(directory, { recursive: true, force: true });
      }
    }),
    { numRuns: 35 },
  );
});

interface ModelState {
  location: string;
  revision: number;
  turn: number;
  oxygen: number;
  heat: number;
  crewHealth: number;
  engineerHealth: number;
  status: "running" | "failure";
  reason: string | null;
}

interface RealState {
  state: WorldState;
}

const graph: Record<string, string[]> = {
  "command-center": ["power-junction"],
  "power-junction": [
    "command-center",
    "storage",
    "medical-bay",
    "reactor",
    "communications",
    "life-support",
  ],
  storage: ["power-junction", "maintenance"],
  maintenance: ["storage", "life-support"],
  "medical-bay": ["power-junction"],
  reactor: ["power-junction"],
  communications: ["power-junction"],
  "life-support": ["power-junction", "maintenance"],
};

function advanceModel(model: ModelState): void {
  model.revision += 1;
  model.turn += 1;
  model.oxygen = Math.max(0, model.oxygen - 4);
  model.heat = Math.min(100, model.heat + 6);
  model.crewHealth = Math.max(0, model.crewHealth - 2 - (model.oxygen < 25 ? 4 : 0));
  if (model.oxygen < 30) model.engineerHealth = Math.max(0, model.engineerHealth - 8);
  else if (model.oxygen < 45) model.engineerHealth = Math.max(0, model.engineerHealth - 3);
  if (model.location === "reactor" && model.heat > 85) {
    model.engineerHealth = Math.max(0, model.engineerHealth - 5);
  }
  if (model.heat >= 100) {
    model.status = "failure";
    model.reason = "reactor_meltdown";
  } else if (model.oxygen <= 0) {
    model.status = "failure";
    model.reason = "station_asphyxiation";
  } else if (model.crewHealth <= 0) {
    model.status = "failure";
    model.reason = "crew_lost";
  } else if (model.engineerHealth <= 0) {
    model.status = "failure";
    model.reason = "engineer_incapacitated";
  }
}

function assertModel(model: ModelState, real: WorldState): void {
  assert.equal(real.agents["engineer-01"]?.location, model.location);
  assert.equal(real.revision, model.revision);
  assert.equal(real.turn, model.turn);
  assert.equal(real.resources.oxygen, model.oxygen);
  assert.equal(real.resources.reactorHeat, model.heat);
  assert.equal(real.crew["crew-01"]?.health, model.crewHealth);
  assert.equal(real.agents["engineer-01"]?.health, model.engineerHealth);
  assert.equal(real.mission.status, model.status);
  assert.equal(real.mission.reason, model.reason);
}

class MoveModelCommand implements Command<ModelState, RealState> {
  readonly target: string;

  constructor(target: string) {
    this.target = target;
  }

  check(model: Readonly<ModelState>): boolean {
    return model.status === "running" && (graph[model.location] ?? []).includes(this.target);
  }

  run(model: ModelState, real: RealState): void {
    const result = ruleset.apply(real.state, {
      kind: "move",
      commandId: `model:move:${model.revision}:${this.target}`,
      actorId: "engineer-01",
      targetRoomId: this.target,
      expectedRevision: model.revision,
    });
    if (result.status !== "accepted") throw new Error(result.reason);
    model.location = this.target;
    advanceModel(model);
    real.state = result.state;
    assertModel(model, real.state);
  }

  toString(): string {
    return `move(${this.target})`;
  }
}

class WaitModelCommand implements Command<ModelState, RealState> {
  check(model: Readonly<ModelState>): boolean {
    return model.status === "running";
  }

  run(model: ModelState, real: RealState): void {
    const result = ruleset.apply(real.state, {
      kind: "wait",
      commandId: `model:wait:${model.revision}`,
      actorId: "engineer-01",
      expectedRevision: model.revision,
    });
    if (result.status !== "accepted") throw new Error(result.reason);
    advanceModel(model);
    real.state = result.state;
    assertModel(model, real.state);
  }

  toString(): string {
    return "wait";
  }
}

test("model-based: movement-only world matches an independent reference model", () => {
  const commandArbitraries = [
    ...Object.keys(graph).map((room) => fc.constant(new MoveModelCommand(room))),
    fc.constant(new WaitModelCommand()),
  ];
  fc.assert(
    fc.property(fc.commands(commandArbitraries, { maxCommands: 25 }), (commands) => {
      fc.modelRun(
        () => ({
          model: {
            location: "command-center",
            revision: 0,
            turn: 0,
            oxygen: 78,
            heat: 40,
            crewHealth: 50,
            engineerHealth: 100,
            status: "running" as const,
            reason: null,
          },
          real: { state: initialTeamWorld() },
        }),
        commands,
      );
    }),
    { numRuns: 100 },
  );
});
