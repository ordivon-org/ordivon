import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { createMissionControlCatalog } from "../src/mission-control/catalog.ts";
import { MissionControlService } from "../src/mission-control/service.ts";
import { GameStore } from "../src/storage.ts";
import { FixtureTeamProvider } from "../src/team/providers.ts";
import { renderDeployment, renderMission } from "../web/render-shell.js";
import { compatibleRuns, createRunId, runIdFromUrl, urlForRun } from "../web/store.js";

const directory = mkdtempSync(join(tmpdir(), "ordivon-m4-web-check-"));
const game = new GameStore(join(directory, "world.sqlite3"));
try {
  const service = new MissionControlService(game, () => new FixtureTeamProvider());
  const runId = "run:web-smoke";
  service.initialize({ runId, authorityPolicyMode: "autonomous" });
  const review = await service.advance(runId, "proposal-review");
  const catalog = createMissionControlCatalog();
  const mission = renderMission(review.view, { catalog });
  assert.match(mission, /Station Zero/);
  assert.match(mission, /Engineer Imani/);
  assert.match(mission, /Medic Reyes/);
  assert.match(mission, /Security Chen/);
  assert.match(mission, /Prepare proposals/);
  assert.match(mission, /Commit one verified Tick/);
  assert.match(mission, /Observed/);
  assert.match(mission, /Assessed · unverified/);
  assert.doesNotMatch(mission, /MANUAL COMMAND|PERSISTENT AGENT|Latest receipt/);

  const terminalView = structuredClone(review.view);
  terminalView.run.status = "victory";
  terminalView.mission.reason = "rescue_signal_verified";
  terminalView.mission.score = 2200;
  terminalView.mission.scoreComponents = { verifiedVictory: 1000, objectiveProgress: 700 };
  assert.match(renderMission(terminalView, { catalog }), /Verified terminal outcome/i);
  assert.match(renderMission(terminalView, { catalog }), /Score 2200/);

  const runs = compatibleRuns(game.listRuns());
  const deployment = renderDeployment(runs, null, null, catalog);
  assert.match(deployment, /Team configuration/);
  assert.match(deployment, /Engineer Imani/);
  assert.match(deployment, /Power constrained/);
  assert.match(deployment, /Resume mission/);

  assert.equal(runIdFromUrl("https://example.test/?runId=run%3Aone"), "run:one");
  assert.equal(urlForRun("https://example.test/game?x=1", "run:two"), "/game?x=1&runId=run%3Atwo");
  assert.equal(urlForRun("https://example.test/game?runId=run%3Aone", null), "/game");
  assert.equal(createRunId(123, "fixed"), "run:web:123:fixed");
} finally {
  game.close();
  rmSync(directory, { recursive: true, force: true });
}
