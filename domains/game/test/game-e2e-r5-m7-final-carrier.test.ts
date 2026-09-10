import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const carrier = JSON.parse(readFileSync(".ordivon/game-e2e-current.json", "utf8"));
const adjudication = JSON.parse(readFileSync("evidence/acceptance/game-e2e-r5-m7-adjudication.json", "utf8"));

test("M7 independent adjudication graduates only the Game E2E infrastructure boundary", () => {
  assert.equal(adjudication.verdict, "GRADUATED");
  assert.equal(adjudication.evaluatedCandidate.revision, "18f40e456ff22afe350fcf5ac45bc2582903d305");
  assert.equal(adjudication.independentVerification.focusedDestroyer.pass, 23);
  assert.equal(adjudication.independentVerification.focusedDestroyer.total, 23);
  assert.equal(adjudication.independentVerification.fullRepository.pass, 393);
  assert.equal(adjudication.independentVerification.fullRepository.total, 393);
  assert.equal(adjudication.mandatoryAttackEvidence.length, 8);
  assert.ok(adjudication.mandatoryAttackEvidence.every((row: any) => String(row.standing).startsWith("PASS")));
});

test("M7 current carrier is main by explicit contract and older/remote refs cannot mint currentness", () => {
  assert.equal(carrier.standing, "GRADUATED");
  assert.equal(carrier.currentCarrier.ref, "refs/heads/main");
  assert.equal(carrier.currentCarrier.evaluatedCandidate, adjudication.evaluatedCandidate.revision);
  const candidate = carrier.competingRefs.find((row: any) => row.ref === "refs/heads/game-e2e-r5-candidate");
  const remote = carrier.competingRefs.find((row: any) => row.ref === "refs/remotes/origin/main");
  assert.equal(candidate.classification, "SUPERSEDED_M6_CANDIDATE");
  assert.equal(remote.classification, "REMOTE_TRACKING_OBSERVATION_NOT_LOCAL_CURRENTNESS_AUTHORITY");
  assert.match(adjudication.activationContract.failureRule, /GRADUATED verdict is not active/);
});

test("M7 graduation cannot upgrade Veilwild, Human, rights, or external substitution standing", () => {
  const expected = {
    veilwildCandidateNomination: "NOT_YET_NOMINATED",
    veilwildDistributionRights: "INCONCLUSIVE",
    veilwildHuman: "UNKNOWN",
    stationZeroFreshPlayerHuman: "UNKNOWN",
    fullExternalEvidenceSubstitution: "NOT_ADMITTED",
  };
  assert.deepEqual(carrier.doNotInherit, expected);
  assert.deepEqual(adjudication.doNotInherit, expected);
});
