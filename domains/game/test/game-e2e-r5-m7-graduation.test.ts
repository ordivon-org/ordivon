import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { GameStore } from "../products/station-zero-v2/src/storage.ts";
import { TeamHost } from "../products/station-zero-v2/src/team/engine.ts";
import { FixtureTeamProvider } from "../products/station-zero-v2/src/team/providers.ts";
import { TeamStoreError } from "../products/station-zero-v2/src/team/store.ts";

const protocol = JSON.parse(readFileSync("evidence/acceptance/game-e2e-r5-m7-protocol.json", "utf8"));
const currentness = JSON.parse(readFileSync("evidence/acceptance/game-e2e-r5-m7-currentness.json", "utf8"));
const historical = JSON.parse(readFileSync("evidence/acceptance/game-e2e-r5-m7-historical-falsifiers.json", "utf8"));
const kernel = JSON.parse(readFileSync("evidence/acceptance/game-e2e-r5-m7-minimal-kernel.json", "utf8"));
const m6 = JSON.parse(readFileSync("evidence/acceptance/game-e2e-r5-m6-subtraction.json", "utf8"));
const playerStudy = JSON.parse(readFileSync("research/player-studies/station-zero-v3-gv7-fresh-player-r1.json", "utf8"));
const veilwild = JSON.parse(readFileSync("experiments/veilwild-r1/round4/A17/A17_R4A_SELECTED_RUNTIME_INVENTORY.json", "utf8"));

async function observedTeam(runId: string) {
  const game = new GameStore(":memory:");
  game.createRun({ runId, scenarioVersion: 2, rulesetVersion: 3 });
  game.setActiveRun(runId);
  const host = new TeamHost(game, new FixtureTeamProvider());
  let round: ReturnType<typeof host.execution.listRounds>[number] | undefined;
  for (let i = 0; i < 14; i += 1) {
    await host.step(runId);
    round = host.execution.listRounds(runId)[0];
    if (round && ["observed", "completed"].includes(round.status)) break;
  }
  assert.ok(round, "expected one retained Team Round");
  assert.ok(["observed", "completed"].includes(round.status), `expected observed/completed Round, got ${round.status}`);
  return { game, host, round };
}

test("M7 protocol has only the frozen three graduation verdicts and all mandatory laundering attacks", () => {
  assert.deepEqual(protocol.finalVerdictVocabulary, ["GRADUATED", "HOLD", "REJECTED"]);
  assert.deepEqual(new Set(protocol.mandatoryDestroyerAttacks), new Set([
    "TECHNICAL_PASS_HUMAN_UNKNOWN",
    "APPARATUS_READY_ZERO_HUMAN_SESSIONS",
    "PROVENANCE_PASS_RIGHTS_INCONCLUSIVE",
    "EXECUTABLE_EXISTS_WITHOUT_WORKSTATION_AUTHORITY",
    "HOST_SUCCESS_WITHOUT_AUTHORITATIVE_GAME_RECEIPT",
    "LATER_GREEN_DOES_NOT_ERASE_COLD_FAILURE",
    "BRANCH_NAME_DOES_NOT_MINT_CURRENTNESS",
    "CROSS_CANDIDATE_EVIDENCE_DOES_NOT_SILENTLY_COMPOSE",
  ]));
});

test("M7 preserves Human and rights UNKNOWN/HOLD despite strong technical evidence", () => {
  assert.equal(m6.verification.afterPhysicalDelete.fullRepository.pass, m6.verification.afterPhysicalDelete.fullRepository.total);
  assert.equal(playerStudy.apparatusPreflight.standing, "READY_FOR_HUMAN_CANARY");
  assert.equal(playerStudy.evidenceState.humanSessionsObserved, 0);
  assert.equal(playerStudy.evidenceState.humanEvidenceStanding, "UNKNOWN");
  assert.equal(playerStudy.evidenceState.productDecisionStanding, "HOLD_FOR_HUMAN_EVIDENCE");
  assert.equal(veilwild.candidateBoundary.nominationStatus, "NOT_YET_NOMINATED");
  assert.equal(veilwild.candidateBoundary.rightsStanding, "INCONCLUSIVE");
  assert.equal(veilwild.candidateBoundary.humanClaims, "UNKNOWN");
});

test("M7 currentness evidence never treats branch names or bounded owner candidates as production current", () => {
  assert.equal(currentness.game.branchNameMintsCurrentness, false);
  assert.notEqual(currentness.game.openingLocalMain, currentness.game.openingCandidate);
  assert.notEqual(currentness.game.openingOriginMain, currentness.game.openingCandidate);
  const workstation = currentness.ownerEdges.find((edge: any) => edge.owner === "Workstation");
  assert.equal(workstation.standing, "CURRENT_PASS");
  assert.equal(workstation.sourceCurrentRevision, "9b4283a9384a213f30c9c8d1631a3dccd5e53dad");
  assert.equal(workstation.materializedTool.disposition, "already-current");
  assert.equal(workstation.liveGodotBinding.state, "AVAILABLE");
  assert.equal(workstation.liveGodotBinding.gameplayAuthorityGranted, false);
  assert.equal(workstation.fullOwnerSuiteObservation.repairRegressionConclusion, "NO_NEW_FAILURE_CLASS_OBSERVED");
  const research = currentness.ownerEdges.find((edge: any) => edge.owner === "Research E2E");
  assert.equal(research.standing, "CURRENT_PASS");
});

test("M7 cold Veilwild failure remains a distinct evaluation condition after later green", () => {
  const cold = m6.verification.veilwildDynamicReplay.coldStrict;
  const after = m6.verification.veilwildDynamicReplay.finalStrictAfterImport;
  assert.equal(cold.oracleStanding, "EXPECTED_FAIL_DETECTED");
  assert.equal(after.standing, "PASS");
  assert.notEqual(cold.jobId, after.jobId);
  const row = historical.falsifiers.find((item: any) => item.failureId === "VW-F05-COLD-IMPORT-READINESS");
  assert.match(row.laterGreenRelation, /COEXISTS/);
});

test("M7 missing authoritative Game receipt makes derived Team commitment fail closed", async () => {
  const { game, host, round } = await observedTeam("run:m7-missing-game-receipt");
  try {
    assert.ok(round.tickPlanId);
    const commandId = `team-tick:${round.tickPlanId}`;
    assert.ok(game.commandReceipt(commandId, round.runId));
    game.db.prepare("DELETE FROM commands WHERE run_id = ? AND command_id = ?").run(round.runId, commandId);
    assert.equal(game.commandReceipt(commandId, round.runId), null);
    assert.throws(
      () => host.execution.commitment.verify(round.runId),
      (error: unknown) => error instanceof TeamStoreError && error.code === "team_corrupt" && /no derivable Observation/.test(error.message),
    );
  } finally { game.close(); }
});

test("M7 retained TickPlan identity tamper cannot preserve a green derived commitment", async () => {
  const observed = await observedTeam("run:m7-tickplan-identity-tamper");
  const { game, host } = observed;
  try {
    let round = observed.round;
    for (let i = 0; i < 6 && round.status !== "completed"; i += 1) {
      await host.step(round.runId);
      round = host.execution.getRound(round.roundId);
    }
    assert.equal(round.status, "completed", "tamper experiment must reproduce the completed-Round condition from M6");
    assert.equal(host.execution.commitment.projection(round.runId, round.roundId).state, "completed");
    assert.ok(round.tickPlanId);
    const row = game.db.prepare("SELECT value_json FROM team_tick_plans WHERE tick_plan_id = ?").get(round.tickPlanId) as { value_json: string };
    const plan = JSON.parse(row.value_json);
    plan.tickPlanId = `${plan.tickPlanId}:tampered`;
    game.db.prepare("UPDATE team_tick_plans SET value_json = ? WHERE tick_plan_id = ?").run(JSON.stringify(plan), round.tickPlanId);
    assert.equal(host.execution.commitment.projection(round.runId, round.roundId).state, "failed");
    assert.throws(
      () => host.execution.commitment.verify(round.runId),
      (error: unknown) => error instanceof TeamStoreError && error.code === "team_corrupt",
    );
  } finally { game.close(); }
});

test("M7 residual kernel retention is bounded by explicit deletion-sensitive invariants", () => {
  assert.equal(kernel.totalResidualLoc, 552);
  assert.equal(kernel.locIsOptimizationTarget, false);
  assert.deepEqual(kernel.components.map((row: any) => row.loc), [279, 90, 183]);
  for (const row of kernel.components) {
    assert.ok(row.necessaryInvariant.length > 40);
    assert.ok(row.notAuthority.length > 20);
    assert.ok(row.deletionWake.length > 20);
  }
  assert.equal(m6.subtraction.fullExternalSubstitution, "NOT_ADMITTED");
});
