import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  compareRuns,
  comparisonCompatibility,
  ComparisonError,
} from "../src/comparison/compare.ts";
import { STANDARD_LOADOUT_PROFILE_ID } from "../src/deployment/model.ts";
import { deploymentCatalog, resolveCoordinationProfile } from "../src/deployment/profiles.ts";
import { DeploymentError, DeploymentStore } from "../src/deployment/store.ts";
import {
  MissionControlService,
  type MissionProviderFactory,
} from "../src/mission-control/service.ts";
import { createGameServer } from "../src/server.ts";
import { GameStore } from "../src/storage.ts";
import { TeamHost } from "../src/team/engine.ts";
import { FixtureTeamProvider } from "../src/team/providers.ts";

const factory: MissionProviderFactory = (name, options) => {
  assert.equal(name, "fixture");
  return new FixtureTeamProvider({
    breachStrategy: options?.coordinationProfileId === "engineer-seal"
      ? "engineer-seal"
      : "security-contain",
  });
};

async function finish(service: MissionControlService, runId: string) {
  for (let index = 0; index < 30 && service.state(runId).run.status === "running"; index += 1) {
    const review = await service.advance(runId, "proposal-review");
    if (review.boundary === "terminal") break;
    await service.advance(runId, "tick-verified");
  }
  return service.state(runId);
}

async function listen(game: ReturnType<typeof createGameServer>): Promise<string> {
  await new Promise<void>((resolve) => game.server.listen(0, "127.0.0.1", resolve));
  const address = game.server.address();
  if (!address || typeof address === "string") throw new Error("no address");
  return `http://127.0.0.1:${address.port}`;
}

function fetchFresh(input: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers);
  headers.set("connection", "close");
  return fetch(input, { ...init, headers });
}

test("Deployment Manifest is content-addressed, immutable, and restart-stable", () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-deployment-"));
  const path = join(directory, "world.sqlite3");
  const runId = "run:deployment:stable";
  let store = new GameStore(path);
  try {
    const service = new MissionControlService(store, factory);
    service.initialize({
      runId,
      scenarioCaseId: "baseline",
      coordinationProfileId: "specialist-containment",
      providers: {
        "engineer-01": "fixture",
        "medic-01": "fixture",
        "security-01": "fixture",
      },
    });
    const first = new DeploymentStore(store).get(runId);
    assert.ok(first);
    assert.equal(first.loadoutProfileId, STANDARD_LOADOUT_PROFILE_ID);
    assert.equal(first.coordinationProfileId, "specialist-containment");
    assert.equal(first.actors.length, 3);
    const retained = new DeploymentStore(store).bind({
      runId,
      coordinationProfileId: first.coordinationProfileId,
      authorityPolicyMode: first.authorityPolicyMode,
      actors: first.actors,
    });
    assert.equal(retained.manifestDigest, first.manifestDigest);
    assert.throws(
      () => service.initialize({ runId, coordinationProfileId: "engineer-seal" }),
      (error) => error instanceof DeploymentError && error.code === "deployment_conflict",
    );
    store.close();
    store = new GameStore(path, { activeRunId: runId });
    assert.deepEqual(new DeploymentStore(store).get(runId), first);
  } finally {
    try { store.close(); } catch {}
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Deployment cannot be added after cognition or World execution", async () => {
  const store = new GameStore(":memory:");
  const runId = "run:deployment:late";
  try {
    store.createRun({
      runId,
      scenarioVersion: 2,
      scenarioCaseId: "baseline",
      rulesetVersion: 3,
    });
    const team = new TeamHost(store, new FixtureTeamProvider());
    await team.run(runId, 8);
    assert.ok(store.loadState(runId).revision > 0);
    assert.throws(
      () => new DeploymentStore(store).bind({
        runId,
        authorityPolicyMode: "autonomous",
        actors: team.team.listTasks(runId)
          .filter((task) => task.actorId)
          .map((task) => ({ actorId: task.actorId!, providerOrder: ["fixture"] })),
      }),
      (error) => error instanceof DeploymentError && /before World execution/.test(error.message),
    );
  } finally {
    store.close();
  }
});

test("coordination and compatibility contracts fail closed across unsupported release inputs", () => {
  assert.throws(
    () => resolveCoordinationProfile("generic-coordinator"),
    /unsupported coordination/,
  );
  assert.equal(resolveCoordinationProfile(undefined), "specialist-containment");
  assert.equal(deploymentCatalog().fixedLoadout.profileId, STANDARD_LOADOUT_PROFILE_ID);

  const store = new GameStore(":memory:");
  try {
    new MissionControlService(store, factory).initialize({
      runId: "run:compatibility:base",
      scenarioCaseId: "baseline",
    });
    const base = new DeploymentStore(store).get("run:compatibility:base")!;
    assert.throws(
      () => comparisonCompatibility(base, {
        ...base, runId: "other", scenarioId: "other-scenario",
      }),
      /Scenario contracts/,
    );
    assert.throws(
      () => comparisonCompatibility(base, {
        ...base, runId: "other", scenarioVersion: base.scenarioVersion + 1,
      }),
      /Scenario contracts/,
    );
    assert.throws(
      () => comparisonCompatibility(base, {
        ...base, runId: "other", rulesetId: "other-ruleset",
      }),
      /Ruleset contracts/,
    );
    assert.throws(
      () => comparisonCompatibility(base, {
        ...base, runId: "other", rulesetVersion: base.rulesetVersion + 1,
      }),
      /Ruleset contracts/,
    );
    assert.throws(
      () => comparisonCompatibility(base, {
        ...base, runId: "other", evaluatedInputsDigest: "sha256:other",
      }),
      /Evaluated input contracts/,
    );
  } finally {
    store.close();
  }
});

test("corrupt deployment bindings fail closed before comparison", () => {
  const store = new GameStore(":memory:");
  const runId = "run:deployment:corrupt";
  try {
    new MissionControlService(store, factory).initialize({ runId, scenarioCaseId: "baseline" });
    store.db.prepare(
      "UPDATE host_journal SET payload_json = ? WHERE run_id = ? AND event_type = ?",
    ).run("{}", runId, "game.deployment-bound");
    assert.throws(
      () => new DeploymentStore(store).get(runId),
      (error) =>
        error instanceof DeploymentError &&
        error.code === "deployment_corrupt" &&
        /incomplete/.test(error.message),
    );
  } finally {
    store.close();
  }
});

test("Deployment binding closes at the first retained Team Round before World execution", async () => {
  const store = new GameStore(":memory:");
  const runId = "run:deployment:cognition-only";
  try {
    store.createRun({
      runId,
      scenarioVersion: 2,
      scenarioCaseId: "baseline",
      rulesetVersion: 3,
    });
    const team = new TeamHost(store, new FixtureTeamProvider());
    team.initialize(runId);
    const actors = team.team.listTasks(runId)
      .filter((task) => task.actorId)
      .map((task) => ({ actorId: task.actorId!, providerOrder: ["fixture"] }));
    assert.equal(store.loadState(runId).revision, 0);
    await team.step(runId);
    assert.equal(store.loadState(runId).revision, 0);
    assert.throws(
      () => new DeploymentStore(store).bind({
        runId,
        authorityPolicyMode: "autonomous",
        actors,
      }),
      (error) => error instanceof DeploymentError && /before cognition/.test(error.message),
    );
  } finally {
    store.close();
  }
});
