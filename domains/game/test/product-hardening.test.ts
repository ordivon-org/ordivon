import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { DatabaseSync } from "node:sqlite";
import test from "node:test";

import { canonicalJson, sha256 } from "../src/digest.ts";
import { createMissionControlCatalog } from "../src/mission-control/catalog.ts";
import { missionControlEncodedSize } from "../src/mission-control/projection.ts";
import { MissionControlService } from "../src/mission-control/service.ts";
import { listRulesetContracts, listScenarioContracts, resolveScenario } from "../src/registry.ts";
import { applyScenarioGenesisSpec, createScenarioCaseWorld, listScenarioCases, resolveScenarioCase } from "../src/scenario-cases.ts";
import { initialTeamWorld } from "../src/scenario.ts";
import { createGameServer } from "../src/server.ts";
import { GameStore } from "../src/storage.ts";
import { objectivesForRole } from "../src/team/objectives.ts";
import { FixtureTeamProvider } from "../src/team/providers.ts";

async function finish(
  scenarioCaseId: string,
  breachStrategy: "security-contain" | "engineer-seal",
): Promise<{ store: GameStore; service: MissionControlService; runId: string }> {
  const store = new GameStore(":memory:");
  const runId = `run:case:${scenarioCaseId}:${breachStrategy}`;
  const service = new MissionControlService(
    store,
    () => new FixtureTeamProvider({ breachStrategy }),
  );
  service.initialize({ runId, scenarioCaseId });
  for (let tick = 0; tick < 24 && service.state(runId).run.status === "running"; tick += 1) {
    const review = await service.advance(runId, "proposal-review");
    if (review.boundary === "terminal") break;
    await service.advance(runId, "tick-verified");
  }
  return { store, service, runId };
}

async function listen(game: ReturnType<typeof createGameServer>): Promise<string> {
  await new Promise<void>((resolve) => game.server.listen(0, "127.0.0.1", resolve));
  const address = game.server.address();
  if (!address || typeof address === "string") throw new Error("server did not expose a TCP address");
  return `http://127.0.0.1:${address.port}`;
}

test("Scenario Cases replace label-only seed semantics with distinct deterministic Genesis inputs", () => {
  const cases = listScenarioCases();
  assert.deepEqual(cases.map((entry) => entry.caseId), ["baseline", "power-constrained", "oxygen-constrained"]);
  assert.equal(new Set(cases.map((entry) => entry.genesisSpecDigest)).size, 3);

  const baseline = createScenarioCaseWorld("station-zero", 2, "baseline");
  const power = createScenarioCaseWorld("station-zero", 2, "power-constrained");
  const oxygen = createScenarioCaseWorld("station-zero", 2, "oxygen-constrained");
  assert.deepEqual(baseline.state, initialTeamWorld());
  assert.equal(baseline.genesisDigest, sha256(initialTeamWorld()));
  assert.equal(power.state.resources.batteryInitial, 50);
  assert.equal(power.state.resources.batteryCharge, 50);
  assert.equal(oxygen.state.resources.oxygen, 62);
  assert.equal(new Set([baseline.genesisDigest, power.genesisDigest, oxygen.genesisDigest]).size, 3);

  const seedA = createScenarioCaseWorld("station-zero", 2, "baseline", "seed-a").state;
  const seedB = createScenarioCaseWorld("station-zero", 2, "baseline", "seed-b").state;
  assert.equal(seedA.seed, "seed-a");
  assert.equal(seedB.seed, "seed-b");
  assert.deepEqual({ ...seedA, seed: "compatibility" }, { ...seedB, seed: "compatibility" });
  assert.equal(resolveScenario("station-zero", 2).defaultCaseId, "baseline");
  assert.deepEqual(resolveScenario("station-zero", 2).caseIds, cases.map((entry) => entry.caseId));
  assert.throws(() => resolveScenarioCase("station-zero", 2, "missing"), /unsupported Scenario Case/);
});

test("typed Genesis Specs validate every bounded mutation and preserve invariants", () => {
  const patched = applyScenarioGenesisSpec(initialTeamWorld(), {
    resources: { batteryInitial: 60, oxygen: 70, reactorHeat: 55 },
    mission: { turnLimit: 30 },
    crew: { "crew-01": { health: 65 } },
    systems: { cooling: { integrity: 1, powered: true } },
  });
  assert.equal(patched.resources.batteryInitial, 60);
  assert.equal(patched.resources.batteryCharge, 60);
  assert.equal(patched.resources.energyConsumed, 0);
  assert.equal(patched.resources.oxygen, 70);
  assert.equal(patched.resources.reactorHeat, 55);
  assert.equal(patched.mission.turnLimit, 30);
  assert.equal(patched.crew["crew-01"]?.health, 65);
  assert.equal(patched.systems.cooling?.integrity, 1);
  assert.equal(patched.systems.cooling?.powered, true);
  assert.notEqual(patched, initialTeamWorld());

  assert.throws(() => applyScenarioGenesisSpec(initialTeamWorld(), { resources: { batteryInitial: 0 } }), /batteryInitial/);
  assert.throws(() => applyScenarioGenesisSpec(initialTeamWorld(), { resources: { oxygen: 101 } }), /oxygen/);
  assert.throws(() => applyScenarioGenesisSpec(initialTeamWorld(), { resources: { reactorHeat: Number.NaN } }), /reactorHeat/);
  assert.throws(() => applyScenarioGenesisSpec(initialTeamWorld(), { mission: { turnLimit: 1.5 } }), /turnLimit/);
  assert.throws(() => applyScenarioGenesisSpec(initialTeamWorld(), { crew: { missing: { health: 50 } } }), /unknown crew/);
  assert.throws(() => applyScenarioGenesisSpec(initialTeamWorld(), { crew: { "crew-01": { health: -1 } } }), /crew-01.health/);
  assert.throws(() => applyScenarioGenesisSpec(initialTeamWorld(), { systems: { missing: { integrity: 1 } } }), /unknown system/);
  assert.throws(() => applyScenarioGenesisSpec(initialTeamWorld(), { systems: { cooling: { integrity: 2 } } }), /cooling.integrity/);
  assert.throws(() => applyScenarioGenesisSpec(initialTeamWorld(), { systems: { cooling: { powered: true } } }), /damaged system is powered/);

});

test("new Runs retain truthful Case, Genesis, build, and evaluated-input identity", () => {
  const store = new GameStore(":memory:");
  try {
    const run = store.createRun({
      runId: "run:product-identity",
      scenarioVersion: 2,
      scenarioCaseId: "power-constrained",
      rulesetVersion: 3,
    });
    assert.equal(run.scenarioCaseId, "power-constrained");
    assert.equal(run.genesisDigest, sha256(store.loadState(run.runId)));
    assert.match(run.evaluatedInputsDigest, /^[a-f0-9]{64}$/);
    assert.equal(run.createdWithBuild, "ordivon-game@0.1.0-alpha.1");
    assert.doesNotMatch(run.createdWithBuild, /\+m2/);
    assert.throws(() => store.createRun({
      runId: "run:product-false-case",
      scenarioVersion: 2,
      scenarioCaseId: "baseline",
      rulesetVersion: 3,
      genesis: initialTeamWorld(),
    }), /custom Genesis/);
  } finally {
    store.close();
  }

});

test("Mission Control catalog is the single product contract for Cases, Providers, Actors, and evidence ordering", () => {
  const catalog = createMissionControlCatalog();
  assert.equal(catalog.scenario.seedSemantics, "compatibility-label");
  assert.deepEqual(catalog.cases.map((entry) => entry.caseId), ["baseline", "power-constrained", "oxygen-constrained"]);
  assert.deepEqual(catalog.providers.map((entry) => entry.providerId), ["fixture", "codex", "hermes", "codex-hermes", "hermes-codex"]);
  assert.deepEqual(catalog.evidenceOrdering.authoritative, ["world-revision", "host-sequence", "projection-revision"]);
  assert.equal(catalog.evidenceOrdering.timestamp, "metadata-only");
  for (const actor of catalog.actors) assert.deepEqual(actor.objectiveIds, objectivesForRole(actor.role));
  const browserStore = readFileSync(new URL("../web/store.js", import.meta.url), "utf8");
  assert.doesNotMatch(browserStore, /codex|hermes|engineer-01|breach-contained/);
});
