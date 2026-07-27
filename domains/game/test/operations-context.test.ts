import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { canonicalJson, sha256 } from "../src/digest.ts";
import { AgentContextError, compileAgentContext } from "../src/host/context.ts";
import { HostStore } from "../src/host/store.ts";
import {
  compileOperationFrontier,
  compileSkillPlan,
  materializeSkillStep,
  operationSucceeded,
  OperationCompileError,
  simulateSkillPlan,
} from "../src/host/operations.ts";
import { RecoveryOperationProvider } from "../src/providers/fixture.ts";
import { admitOperationDecision, DecisionAdmissionError } from "../src/providers/types.ts";
import { GameStore } from "../src/storage.ts";

function withStores(run: (game: GameStore, host: HostStore) => Promise<void> | void): Promise<void> | void {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-operations-"));
  const game = new GameStore(join(directory, "world.sqlite3"));
  const cleanup = () => {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  };
  try {
    const result = run(game, new HostStore(game.db));
    if (result instanceof Promise) return result.finally(cleanup);
    cleanup();
  } catch (error) {
    cleanup();
    throw error;
  }
}

test("initial frontier exposes strategic Operations with deterministic Skill plans", () => {
  withStores((game) => {
    const state = game.loadState();
    const frontier = compileOperationFrontier(state);
    assert.ok(frontier.some((candidate) => candidate.kind === "repair_system" && candidate.target.id === "cooling"));
    assert.ok(frontier.some((candidate) => candidate.kind === "seal_hazard"));
    assert.ok(frontier.some((candidate) => candidate.kind === "stabilize_crew"));
    assert.ok(frontier.some((candidate) => candidate.kind === "wait"));
    const cooling = frontier.find((candidate) => candidate.kind === "repair_system" && candidate.target.id === "cooling");
    assert.ok(cooling);
    assert.deepEqual(cooling.planPreview, ["Move to Power Junction", "Move to Reactor Room", "Repair Reactor Cooling"]);
    assert.equal(cooling.estimatedPrimitiveSteps, 3);
    assert.equal(cooling.projected.reactorHeat, 58);
    assert.equal(cooling.projectedTerminalFailure, false);

    for (const candidate of frontier) {
      const plan = compileSkillPlan(state, candidate);
      assert.equal(plan.planId, candidate.planId);
      const simulation = simulateSkillPlan(state, plan);
      if (!candidate.projectedTerminalFailure) {
        assert.equal(operationSucceeded(simulation.state, candidate.successCondition), true, candidate.label);
      }
      assert.deepEqual(
        {
          missionStatus: simulation.state.mission.status,
          missionReason: simulation.state.mission.reason,
          revision: simulation.state.revision,
          turn: simulation.state.turn,
          batteryCharge: simulation.state.resources.batteryCharge,
          oxygen: simulation.state.resources.oxygen,
          reactorHeat: simulation.state.resources.reactorHeat,
          engineerHealth: simulation.state.agents["engineer-01"]?.health ?? 0,
          crewHealth: simulation.state.crew["crew-01"]?.health ?? 0,
        },
        candidate.projected,
      );
    }
  });
});

test("Provider Context is deterministic, bounded, and contains no primitive Command authority", () => {
  withStores((game, host) => {
    const projection = host.initializeRun(game.getRun(), game.loadState(), ["codex", "hermes"]);
    const first = compileAgentContext(game.getRun(), game.loadState(), projection, game.journalEvents());
    const second = compileAgentContext(game.getRun(), game.loadState(), projection, game.journalEvents());
    assert.deepEqual(second, first);
    assert.ok(first.byteLength <= 16 * 1024);
    assert.equal(first.payload.contextId, first.contextId);
    assert.equal(first.payload.allowedOperations.length, compileOperationFrontier(game.loadState()).length);
    const serialized = canonicalJson(first.payload);
    assert.doesNotMatch(serialized, /commandId|expectedRevision|targetRoomId|worldCommand/);
    assert.match(serialized, /operationCandidateId/);
    assert.throws(
      () => compileAgentContext(game.getRun(), game.loadState(), projection, [], 100),
      (error) => error instanceof AgentContextError && error.code === "context_too_large",
    );
    assert.throws(() => compileAgentContext(game.getRun(), game.loadState(), projection, [], 0), /positive integer/);
  });
});

test("stale Operations and invented Decisions fail without world effects", async () => {
  await withStores(async (game, host) => {
    const projection = host.initializeRun(game.getRun(), game.loadState());
    const context = compileAgentContext(game.getRun(), game.loadState(), projection);
    const provider = new RecoveryOperationProvider();
    const decision = await provider.decide(context);
    const admitted = admitOperationDecision(context, game.loadState(), decision);
    assert.equal(admitted?.kind, "repair_system");
    assert.equal(admitted?.target.id, "cooling");

    const beforeEvents = game.eventCount();
    const firstAction = game.loadState();
    const wait = compileOperationFrontier(firstAction).find((candidate) => candidate.kind === "wait");
    assert.ok(wait);
    const step = compileSkillPlan(firstAction, wait).steps[0];
    assert.ok(step);
    game.apply(materializeSkillStep(firstAction, step, "manual-world-drift"));
    assert.throws(
      () => admitOperationDecision(context, game.loadState(), decision),
      (error) => error instanceof DecisionAdmissionError && error.code === "stale_world",
    );
    assert.throws(
      () => compileSkillPlan(game.loadState(), admitted!),
      (error) => error instanceof OperationCompileError,
    );
    assert.equal(game.eventCount(), beforeEvents + 1);

    const fresh = compileAgentContext(game.getRun(), game.loadState(), projection, game.journalEvents());
    assert.throws(
      () => admitOperationDecision(fresh, game.loadState(), {
        providerId: "hostile",
        contextId: fresh.contextId,
        selectedOperationCandidateId: "operation:invented",
        riskLevel: "low",
        confidence: 1,
        rationale: "Invent an operation.",
      }),
      (error) => error instanceof DecisionAdmissionError && error.code === "invented_operation",
    );
  });
});

test("ten strategic fixture decisions reproduce the 25-Tick verified victory", async () => {
  await withStores(async (game, host) => {
    const provider = new RecoveryOperationProvider();
    const projection = host.initializeRun(game.getRun(), game.loadState());
    let decisions = 0;
    while (game.loadState().mission.status === "running" && decisions < 16) {
      const state = game.loadState();
      const context = compileAgentContext(game.getRun(), state, projection, game.journalEvents());
      const decision = await provider.decide(context);
      const candidate = admitOperationDecision(context, state, decision);
      assert.ok(candidate);
      const plan = compileSkillPlan(state, candidate);
      for (const [index, step] of plan.steps.entries()) {
        const current = game.loadState();
        if (current.mission.status !== "running") break;
        const applied = game.apply(
          materializeSkillStep(current, step, `operation-loop:${decisions}:${index}:${candidate.operationCandidateId}`),
        );
        if (applied.result.status !== "accepted") throw new Error(applied.result.reason);
      }
      const after = game.loadState();
      if (after.mission.status === "running") {
        assert.equal(operationSucceeded(after, candidate.successCondition), true, candidate.label);
      }
      decisions += 1;
    }
    const terminal = game.loadState();
    assert.equal(terminal.mission.status, "victory");
    assert.equal(terminal.mission.reason, "rescue_signal_verified");
    assert.equal(terminal.turn, 25);
    assert.equal(game.eventCount(), 25);
    assert.equal(decisions, 10);
    assert.equal(sha256(terminal), "41d7bfd4c1b36f0a8e38533be7f7e9b48b1625608c76c5ced1ddd3d0952d02d2");
  });
});

test("Context trims retained Facts before failing its hard byte limit", () => {
  withStores((game, host) => {
    const projection = host.initializeRun(game.getRun(), game.loadState());
    const state = game.loadState();
    const base = compileAgentContext(game.getRun(), state, projection, []);
    const event = {
      tickId: "tick:large",
      commandSequence: 0,
      simulationTick: 1,
      worldRevision: 1,
      event: {
        eventId: "event:large",
        commandId: "command:large",
        commandKind: "wait" as const,
        actorId: "engineer-01",
        worldRevision: 1,
        turn: 1,
        beforeDigest: "before",
        afterDigest: "after",
        changes: [],
        missionStatus: "running" as const,
        missionReason: null,
        facts: Array.from({ length: 8 }, (_, index) => ({
          kind: "oxygen_changed" as const,
          before: index,
          after: index + 1,
          causes: ["x".repeat(2_000)],
        })),
      },
    };
    const trimmed = compileAgentContext(
      game.getRun(), state, projection, [event], base.byteLength + 500,
    );
    assert.ok(trimmed.payload.recentFacts.length < event.event.facts.length);
    assert.ok(trimmed.byteLength <= base.byteLength + 500);
    assert.throws(
      () => compileAgentContext(game.getRun(), state, projection, [], 1.5),
      /positive integer/,
    );
  });
});

test("Context projects missing and terminal world objects conservatively", () => {
  withStores((game, host) => {
    const projection = host.initializeRun(game.getRun(), game.loadState());
    const state = game.loadState();
    delete state.systems.cooling;
    delete state.systems["life-support"];
    delete state.systems.communications;
    delete state.hazards["maintenance-breach"];
    delete state.crew["crew-01"];
    state.turn = 30;
    state.revision = 30;
    state.mission.status = "failure";
    state.mission.reason = "test";
    const context = compileAgentContext(game.getRun(), state, projection);
    assert.deepEqual(context.payload.objectives, {
      coolingOperational: false,
      coolingPowered: false,
      breachSealed: false,
      lifeSupportOperational: false,
      lifeSupportPowered: false,
      crewStabilized: false,
      communicationsOperational: false,
      communicationsPowered: false,
      distressSent: false,
    });
    assert.equal(context.payload.mission.turnsRemaining, 0);
    assert.deepEqual(context.payload.allowedOperations, []);
    delete state.agents["engineer-01"];
    assert.throws(
      () => compileAgentContext(game.getRun(), state, projection),
      (error) => error instanceof AgentContextError && error.code === "missing_engineer",
    );
  });
});

test("Operation compiler omits unavailable work and fails malformed or stale plans closed", () => {
  withStores((game) => {
    const state = game.loadState();
    state.agents["engineer-01"]!.inventory["spare-parts"] = 0;
    state.rooms.storage!.inventory["spare-parts"] = 0;
    state.resources.consumedItems["spare-parts"] = 3;
    state.agents["engineer-01"]!.inventory.sealant = 0;
    state.rooms.storage!.inventory.sealant = 0;
    state.resources.consumedItems.sealant = 1;
    state.agents["engineer-01"]!.inventory.medkit = 0;
    state.rooms["medical-bay"]!.inventory.medkit = 0;
    state.resources.consumedItems.medkit = 1;
    const frontier = compileOperationFrontier(state);
    assert.ok(!frontier.some((candidate) => candidate.kind === "repair_system"));
    assert.ok(!frontier.some((candidate) => candidate.kind === "seal_hazard"));
    assert.ok(!frontier.some((candidate) => candidate.kind === "stabilize_crew"));
    assert.ok(frontier.some((candidate) => candidate.kind === "wait"));

    const normal = game.loadState();
    const candidate = compileOperationFrontier(normal).find((item) => item.kind === "repair_system");
    assert.ok(candidate);
    assert.throws(
      () => compileSkillPlan(normal, { ...candidate, planId: "plan:tampered" }),
      /no longer compiles identically/,
    );
    const plan = compileSkillPlan(normal, candidate);
    assert.throws(
      () => simulateSkillPlan(normal, { ...plan, requiredWorldDigest: "stale" }),
      /skill plan is stale/,
    );
    const invalidPlan = {
      ...plan,
      steps: [{ kind: "move" as const, targetRoomId: "missing", label: "Invalid" }],
    };
    assert.throws(() => simulateSkillPlan(normal, invalidPlan), /unknown room/);

    const malformed = {
      ...candidate,
      target: { type: "hazard" as const, id: "maintenance-breach" },
    };
    assert.throws(() => compileSkillPlan(normal, malformed), /repair target must be a system/);
  });
});

test("Operation frontier handles terminal, missing Agent, unreachable rooms, and terminal projections", () => {
  withStores((game) => {
    const terminal = game.loadState();
    terminal.mission.status = "failure";
    terminal.mission.reason = "test";
    assert.deepEqual(compileOperationFrontier(terminal), []);

    const noEngineer = game.loadState();
    delete noEngineer.agents["engineer-01"];
    assert.deepEqual(compileOperationFrontier(noEngineer), []);

    const disconnected = game.loadState();
    disconnected.rooms["command-center"]!.neighbors = [];
    disconnected.rooms["power-junction"]!.neighbors = disconnected.rooms["power-junction"]!.neighbors
      .filter((room) => room !== "command-center");
    const disconnectedFrontier = compileOperationFrontier(disconnected);
    assert.ok(disconnectedFrontier.some((candidate) => candidate.kind === "wait"));
    assert.ok(!disconnectedFrontier.some((candidate) => candidate.kind === "repair_system"));

    const nearMeltdown = game.loadState();
    nearMeltdown.resources.reactorHeat = 94;
    const candidate = compileOperationFrontier(nearMeltdown)
      .find((operation) => operation.kind === "repair_system" && operation.target.id === "communications");
    assert.ok(candidate);
    assert.equal(candidate.projectedTerminalFailure, true);
    const simulation = simulateSkillPlan(nearMeltdown, compileSkillPlan(nearMeltdown, candidate));
    assert.equal(simulation.state.mission.status, "failure");
    assert.equal(simulation.state.mission.reason, "reactor_meltdown");
  });
});

test("all Operation success conditions have true and false semantics", () => {
  withStores((game) => {
    const state = game.loadState();
    assert.equal(operationSucceeded(state, { kind: "system_integrity", systemId: "missing", minimum: 0.8 }), false);
    assert.equal(operationSucceeded(state, { kind: "system_power", systemId: "missing", powered: true }), false);
    assert.equal(operationSucceeded(state, { kind: "hazard_sealed", hazardId: "missing" }), false);
    assert.equal(operationSucceeded(state, { kind: "crew_stabilized", crewId: "missing" }), false);
    assert.equal(operationSucceeded(state, { kind: "distress_sent" }), false);
    assert.equal(operationSucceeded(state, { kind: "tick_advanced", minimumRevision: 1 }), false);
  });
});

test("Decision validation covers null selection, wrong Context, and malformed confidence", async () => {
  await withStores(async (game, host) => {
    const projection = host.initializeRun(game.getRun(), game.loadState());
    const context = compileAgentContext(game.getRun(), game.loadState(), projection);
    const base = {
      providerId: "test",
      contextId: context.contextId,
      selectedOperationCandidateId: null,
      riskLevel: "low" as const,
      confidence: 0,
      rationale: "No operation.",
    };
    assert.equal(admitOperationDecision(context, game.loadState(), base), null);
    assert.throws(
      () => admitOperationDecision(context, game.loadState(), { ...base, contextId: "wrong" }),
      (error) => error instanceof DecisionAdmissionError && error.code === "wrong_context",
    );
    for (const decision of [
      { ...base, providerId: "" },
      { ...base, rationale: " " },
      { ...base, confidence: Number.NaN },
      { ...base, confidence: -0.1 },
      { ...base, confidence: 1.1 },
    ]) {
      assert.throws(
        () => admitOperationDecision(context, game.loadState(), decision),
        (error) => error instanceof DecisionAdmissionError && error.code === "invalid_decision",
      );
    }

    const terminal = structuredClone(game.loadState());
    terminal.mission.status = "failure";
    terminal.mission.reason = "test";
    const terminalContext = compileAgentContext(game.getRun(), terminal, projection);
    const provider = new RecoveryOperationProvider();
    const terminalDecision = await provider.decide(terminalContext);
    assert.equal(terminalDecision.selectedOperationCandidateId, null);
    assert.equal(terminalDecision.confidence, 0);
  });
});
