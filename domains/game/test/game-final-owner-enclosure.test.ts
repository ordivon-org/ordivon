import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";

const receipt = JSON.parse(readFileSync("evidence/acceptance/game-final-owner-enclosure-20260912.json", "utf8"));

test("final owner enclosure records bounded anti-framework evidence", () => {
  assert.equal(receipt.kind, "ordivon.game-final-owner-enclosure-acceptance");
  assert.equal(receipt.frozenRevision, "ef12c82");
  assert.equal(receipt.standing, "PASS_IN_SCOPE");
  assert.deepEqual(receipt.verification.fullRepositoryAndBrowser.unitAndStructural, { pass: 424, total: 424, standing: "PASS" });
  assert.ok(Object.values(receipt.verification.fullRepositoryAndBrowser.browserSurfaces).every((value) => value === "PASS"));
  assert.equal(receipt.verification.productDeletionFalsifier.pass, 121);
  assert.equal(receipt.verification.productDeletionFalsifier.total, 121);
  assert.equal(receipt.verification.productDeletionFalsifier.terminalMarker, "PRODUCTLESS_BIG_GAME=PASS");
  assert.deepEqual(receipt.verification.receiptIncludedRepositoryCheck, {
    jobId: "job-01a09495-7550-7e43-b195-abe1b72caa77",
    pass: 428,
    total: 428,
    standing: "PASS",
    note: "Full typecheck, web syntax, and repository tests including the four final owner-enclosure guard tests.",
  });
});

test("final owner enclosure cannot launder product or Human standing", () => {
  assert.equal(receipt.doNotInherit.stationZeroFreshPlayerHuman, "UNKNOWN");
  assert.equal(receipt.doNotInherit.veilwildHuman, "UNKNOWN");
  assert.equal(receipt.doNotInherit.preG0C0, "UNOBSERVED");
  assert.equal(receipt.doNotInherit.preG0C1, "UNOBSERVED");
  assert.equal(receipt.doNotInherit.productReleaseStanding, "NOT_EVALUATED_BY_THIS_RECEIPT");
  assert.equal(receipt.doNotInherit.distributionRightsStanding, "NOT_EVALUATED_BY_THIS_RECEIPT");
  assert.equal(receipt.doNotInherit.liveRemoteCurrentness, "NOT_EVALUATED_NO_FETCH");
});

test("final owner enclosure preserves the no-framework physical boundary", () => {
  assert.equal(receipt.ownershipResult.bigGameRuntimeSource, "NONE");
  assert.equal(receipt.antiFrameworkFalsifier.stationZeroDeletionPreservesBigGame, "PASS");
  assert.equal(existsSync("src/server.ts"), false);
  assert.equal(existsSync("src/build.ts"), false);
  assert.equal(existsSync("src/digest.ts"), false);
  assert.equal(existsSync("products/station-zero-v2/src/server.ts"), true);
  assert.equal(existsSync("experiments/research-preview/server.ts"), true);
  assert.equal(existsSync("tools/canonical-digest.ts"), true);
});

test("retained Host vocabulary is compatibility debt rather than subsystem authority", () => {
  assert.deepEqual(receipt.compatibilityDebt.retainedVocabulary, ["host_artifacts", "host_journal", "host-event:*", "host-contract"]);
  assert.match(receipt.compatibilityDebt.meaning, /no generic Host subsystem authority/);
  assert.match(receipt.compatibilityDebt.migrationRule, /versioned lossless persistence migration/);
});
