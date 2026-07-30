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
import { createEvaluatedInputManifest, listEvaluatedInputFiles } from "../src/release/inputs.ts";
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
  const runId = `run:m5:${scenarioCaseId}:${breachStrategy}`;
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

function createManifestFixture(): string {
  const root = mkdtempSync(join(tmpdir(), "ordivon-m5-inputs-"));
  for (const directory of [".github/workflows", "scripts", "src", "test", "web", "docs", "data"]) {
    mkdirSync(join(root, directory), { recursive: true });
  }
  writeFileSync(join(root, ".github/workflows/ci.yml"), "name: verify\n");
  writeFileSync(join(root, "scripts/a.ts"), "export const script = 1;\n");
  writeFileSync(join(root, "src/a.ts"), "export const source = 1;\n");
  writeFileSync(join(root, "test/a.test.ts"), "export const testValue = 1;\n");
  writeFileSync(join(root, "web/a.js"), "export const web = 1;\n");
  writeFileSync(join(root, "package.json"), JSON.stringify({ name: "fixture", version: "1.2.3" }));
  writeFileSync(join(root, "pnpm-lock.yaml"), "lockfileVersion: '9.0'\n");
  writeFileSync(join(root, "tsconfig.json"), "{}\n");
  writeFileSync(join(root, "docs/generated.json"), "ignored\n");
  writeFileSync(join(root, "data/local.sqlite3"), "ignored\n");
  return root;
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

  const legacy = createScenarioCaseWorld("station-zero", 1);
  assert.equal(legacy.definition.caseId, "legacy-fixed");
  assert.equal(Object.keys(legacy.state.agents).length, 1);
});

test("constrained Cases retain measured strategy sensitivity without changing World rules", async () => {
  const expectations = [
    ["power-constrained", "security-contain", "victory", "rescue_signal_verified", 18, 2],
    ["power-constrained", "engineer-seal", "failure", "power_exhausted", 21, 0],
    ["oxygen-constrained", "security-contain", "victory", "rescue_signal_verified", 18, 55],
    ["oxygen-constrained", "engineer-seal", "failure", "team_incapacitated", 19, 26],
  ] as const;
  for (const [scenarioCaseId, strategy, status, reason, turn, terminalResource] of expectations) {
    const result = await finish(scenarioCaseId, strategy);
    try {
      const state = result.store.loadState(result.runId);
      assert.equal(state.mission.status, status, `${scenarioCaseId}/${strategy}`);
      assert.equal(state.mission.reason, reason, `${scenarioCaseId}/${strategy}`);
      assert.equal(state.turn, turn, `${scenarioCaseId}/${strategy}`);
      assert.equal(
        scenarioCaseId === "power-constrained" ? state.resources.batteryCharge : state.resources.oxygen,
        terminalResource,
        `${scenarioCaseId}/${strategy}`,
      );
      assert.equal(result.store.verifyReplay(result.runId).digest, sha256(state));
    } finally {
      result.store.close();
    }
  }
});

test("new and migrated Runs retain truthful Case, Genesis, build, and evaluated-input identity", () => {
  const store = new GameStore(":memory:");
  try {
    const run = store.createRun({
      runId: "run:m5-identity",
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
      runId: "run:m5-false-case",
      scenarioVersion: 2,
      scenarioCaseId: "baseline",
      rulesetVersion: 3,
      genesis: initialTeamWorld(),
    }), /custom Genesis/);
  } finally {
    store.close();
  }

  const directory = mkdtempSync(join(tmpdir(), "ordivon-m5-legacy-run-"));
  const path = join(directory, "world.sqlite3");
  try {
    const state = initialTeamWorld();
    const db = new DatabaseSync(path);
    db.exec(`
      CREATE TABLE runs (
        run_id TEXT PRIMARY KEY, scenario_id TEXT NOT NULL, scenario_version INTEGER NOT NULL,
        ruleset_id TEXT NOT NULL, ruleset_version INTEGER NOT NULL, state_schema_version INTEGER NOT NULL,
        seed TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, created_with_build TEXT NOT NULL
      );
      CREATE TABLE snapshots (
        run_id TEXT NOT NULL, revision INTEGER NOT NULL, state_json TEXT NOT NULL,
        digest TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (run_id, revision)
      );
    `);
    db.prepare("INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)").run(
      "run:legacy", "station-zero", 2, "station-zero-core", 3, state.schemaVersion,
      state.seed, "running", "2026-07-28T00:00:00.000Z", "ordivon-game@legacy",
    );
    db.prepare("INSERT INTO snapshots (run_id, revision, state_json, digest) VALUES (?, ?, ?, ?)")
      .run("run:legacy", 0, canonicalJson(state), sha256(state));
    const customState = initialTeamWorld();
    customState.resources.oxygen = 77;
    db.prepare("INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)").run(
      "run:legacy-custom", "station-zero", 2, "station-zero-core", 3, customState.schemaVersion,
      customState.seed, "running", "2026-07-28T00:00:01.000Z", "ordivon-game@legacy",
    );
    db.prepare("INSERT INTO snapshots (run_id, revision, state_json, digest) VALUES (?, ?, ?, ?)")
      .run("run:legacy-custom", 0, canonicalJson(customState), sha256(customState));
    db.close();

    const migrated = new GameStore(path, { activeRunId: "run:legacy" });
    try {
      const run = migrated.getRun("run:legacy");
      assert.equal(run.scenarioCaseId, "baseline");
      assert.equal(run.genesisDigest, sha256(state));
      assert.equal(run.evaluatedInputsDigest, "legacy:unbound");
      assert.equal(migrated.verifyReplay("run:legacy").digest, sha256(state));
      const custom = migrated.getRun("run:legacy-custom");
      assert.equal(custom.scenarioCaseId, "legacy-custom-genesis");
      assert.equal(custom.genesisDigest, sha256(customState));
    } finally {
      migrated.close();
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("evaluated-input manifests are canonical, source-sensitive, and ignore generated outputs", () => {
  const root = createManifestFixture();
  try {
    const options = {
      root,
      scenarioContracts: [{ id: "z", version: 2 }, { id: "a", version: 1 }],
      rulesetContracts: [{ id: "core", version: 3 }],
      sourceCommit: "commit:test",
      sourceTree: "tree:test",
    };
    const first = createEvaluatedInputManifest(options);
    const second = createEvaluatedInputManifest({
      ...options,
      scenarioContracts: [...options.scenarioContracts].reverse(),
    });
    assert.equal(first.evaluatedInputsDigest, second.evaluatedInputsDigest);
    assert.equal(
      createEvaluatedInputManifest({ ...options, sourceCommit: "another-commit", sourceTree: "another-tree" }).evaluatedInputsDigest,
      first.evaluatedInputsDigest,
    );
    assert.deepEqual(first.scenarioContracts, [{ id: "a", version: 1 }, { id: "z", version: 2 }]);
    assert.deepEqual(listEvaluatedInputFiles(root), first.files.map((file) => file.path));
    assert.ok(!first.files.some((file) => file.path.startsWith("docs/") || file.path.startsWith("data/")));
    const sourceFile = first.files.find((file) => file.path === "src/a.ts");
    assert.equal(
      sourceFile?.sha256,
      createHash("sha256").update(readFileSync(join(root, "src/a.ts"))).digest("hex"),
    );

    writeFileSync(join(root, "docs/generated.json"), "changed but ignored\n");
    assert.equal(createEvaluatedInputManifest(options).evaluatedInputsDigest, first.evaluatedInputsDigest);
    writeFileSync(join(root, "src/a.ts"), "export const source = 2;\n");
    assert.notEqual(createEvaluatedInputManifest(options).evaluatedInputsDigest, first.evaluatedInputsDigest);
  } finally {
    rmSync(root, { recursive: true, force: true });
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

test("the 22-Tick route remains bounded and true revision paging reaches the complete retained history", async () => {
  const result = await finish("baseline", "engineer-seal");
  try {
    const terminal = result.service.state(result.runId);
    assert.equal(terminal.run.status, "victory");
    assert.equal(terminal.run.turn, 22);
    assert.ok(missionControlEncodedSize(terminal) <= 64 * 1024, String(missionControlEncodedSize(terminal)));
    assert.equal(terminal.timeline.length, 12);

    const journalBefore = Number((result.store.db.prepare("SELECT COUNT(*) AS count FROM host_journal WHERE run_id = ?")
      .get(result.runId) as { count: number }).count);
    const revisions: number[] = [];
    let beforeRevision: number | null = null;
    do {
      const page = result.service.timeline(result.runId, beforeRevision, 5);
      revisions.push(...page.items.map((item) => item.worldRevision));
      beforeRevision = page.nextBeforeRevision;
    } while (beforeRevision !== null);
    assert.deepEqual(revisions, Array.from({ length: 22 }, (_, index) => 21 - index));
    assert.equal(new Set(revisions).size, 22);
    assert.ok(revisions.some((revision) => revision < 10));
    const journalAfter = Number((result.store.db.prepare("SELECT COUNT(*) AS count FROM host_journal WHERE run_id = ?")
      .get(result.runId) as { count: number }).count);
    assert.equal(journalAfter, journalBefore);

    const beforeTimestampChange = result.service.timeline(result.runId, null, 50);
    result.store.db.prepare("UPDATE host_journal SET created_at = ? WHERE run_id = ?")
      .run("1900-01-01T00:00:00.000Z", result.runId);
    assert.deepEqual(result.service.timeline(result.runId, null, 50), beforeTimestampChange);
    assert.throws(() => result.service.timeline(result.runId, -1, 5), /beforeRevision/);
    assert.throws(() => result.service.timeline(result.runId, null, 51), /timeline limit/);
  } finally {
    result.store.close();
  }
});

test("catalog and replay timeline HTTP routes expose the hardened contracts", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-m5-http-"));
  const game = createGameServer({
    dbPath: join(directory, "world.sqlite3"),
    teamProviderFactory: () => new FixtureTeamProvider(),
  });
  try {
    const base = await listen(game);
    const catalog = await fetch(`${base}/api/mission-control/catalog`);
    assert.equal(catalog.status, 200);
    assert.equal((await catalog.json() as { scenario: { seedSemantics: string } }).scenario.seedSemantics, "compatibility-label");

    const initialized = await fetch(`${base}/api/mission-control/initialize`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ runId: "run:m5-http", scenarioCaseId: "power-constrained" }),
    });
    assert.equal(initialized.status, 201);
    const view = await initialized.json() as { run: { scenarioCaseId: string; genesisDigest: string } };
    assert.equal(view.run.scenarioCaseId, "power-constrained");
    assert.match(view.run.genesisDigest, /^[a-f0-9]{64}$/);

    await fetch(`${base}/api/mission-control/advance?runId=run:m5-http`, {
      method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ until: "proposal-review" }),
    });
    await fetch(`${base}/api/mission-control/advance?runId=run:m5-http`, {
      method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ until: "tick-verified" }),
    });
    const timeline = await fetch(`${base}/api/replay/timeline?runId=run:m5-http&limit=1`);
    assert.equal(timeline.status, 200);
    const page = await timeline.json() as { items: Array<{ worldRevision: number }>; nextBeforeRevision: number | null };
    assert.equal(page.items.length, 1);
    assert.equal(page.items[0]?.worldRevision, 0);
    assert.equal(page.nextBeforeRevision, null);
    assert.equal((await fetch(`${base}/api/replay/timeline?runId=run:m5-http&beforeRevision=-1`)).status, 400);

    const mismatched = await fetch(`${base}/api/mission-control/initialize`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ runId: "run:m5-http", scenarioCaseId: "baseline" }),
    });
    assert.equal(mismatched.status, 409);
  } finally {
    await game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("release input contracts enumerate all registered Scenario and Ruleset versions", () => {
  const manifest = createEvaluatedInputManifest({
    scenarioContracts: listScenarioContracts(),
    rulesetContracts: listRulesetContracts(),
  });
  assert.deepEqual(manifest.scenarioContracts, [{ id: "station-zero", version: 1 }, { id: "station-zero", version: 2 }]);
  assert.deepEqual(manifest.rulesetContracts, [
    { id: "station-zero-core", version: 1 },
    { id: "station-zero-core", version: 2 },
    { id: "station-zero-core", version: 3 },
  ]);
  assert.ok(manifest.files.some((file) => file.path === "src/scenario-cases.ts"));
  assert.ok(manifest.files.some((file) => file.path === "scripts/release-inputs.ts"));
});
