import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const packetPath = new URL("../research/player-studies/station-zero-v3-gv7-fresh-player-r1.json", import.meta.url);
const protocolPath = new URL("../research/player-studies/STATION_ZERO_V3_GV7_R1_PROTOCOL.md", import.meta.url);
const packet = JSON.parse(readFileSync(packetPath, "utf8"));
const protocol = readFileSync(protocolPath, "utf8");

const sessionTemplatePath = new URL("../research/player-studies/STATION_ZERO_V3_GV7_R1_SESSION_TEMPLATE.json", import.meta.url);
const sessionTemplate = JSON.parse(readFileSync(sessionTemplatePath, "utf8"));

test("R5 player study maps exactly through the four Research vNext universal roles", () => {
  assert.equal(packet.kind, "ordivon.game-player-study-packet");
  assert.equal(packet.truthRole, "prepared-research-plan-not-human-evidence");
  assert.deepEqual(Object.keys(packet.researchVNext.universalRoles).sort(), [
    "claimBoundary",
    "evaluationLogic",
    "researchIntent",
    "targetOfInquiry",
  ]);
  assert.equal(packet.researchVNext.sourceRevision, "bab965e19dd5ad06bb2427c3b599d775af4b6f6f");
});

test("R5 fresh-player study binds exact Station Zero source and evaluation condition", () => {
  const target = packet.researchVNext.universalRoles.targetOfInquiry;
  assert.equal(target.game, "station-zero-v3");
  assert.equal(target.gameSourceRevision, "fc74ad32a7c03f7c745c1e5ce27985f983ccb6b2");
  assert.equal(target.surface, "/v3");
  assert.equal(target.scenarioCaseId, "fixed-genesis");
  assert.match(target.providerCondition, /fixture\/deterministic/);
  assert.match(target.horizon, /two committed Turns/);
});

test("R5 study cannot launder a prepared protocol into Human evidence", () => {
  assert.equal(packet.status, "PREPARED_NOT_RUN");
  assert.equal(packet.evidenceState.humanSessionsObserved, 0);
  assert.deepEqual(packet.evidenceState.rawHumanEvidenceRefs, []);
  assert.equal(packet.evidenceState.humanEvidenceStanding, "UNKNOWN");
  assert.equal(packet.evidenceState.productDecisionStanding, "HOLD_FOR_HUMAN_EVIDENCE");
  assert.match(protocol, /PREPARED \/ NOT RUN \/ HUMAN EVIDENCE UNKNOWN/);
  assert.match(protocol, /Human sessions observed = 0/);
});

test("R5 study keeps C1/C2 claims separate from experience, market and population claims", () => {
  const boundary = packet.researchVNext.universalRoles.claimBoundary;
  assert.deepEqual(boundary.claimFamilies, ["C1_USABILITY_ACTIONABILITY", "C2_UNDERSTANDING_MENTAL_MODEL"]);
  const forbidden = boundary.mustNotSupport.join("\n");
  for (const term of ["fun or enjoyment", "market appeal", "population prevalence", "retention", "Veilwild Human standing", "Game E2E default-ready standing"]) {
    assert.match(forbidden, new RegExp(term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
  assert.match(protocol, /exploratory only/);
});

test("R5 evaluation logic freezes falsifiers, non-leading observation and version cuts before Human collection", () => {
  const logic = packet.researchVNext.universalRoles.evaluationLogic;
  assert.match(logic.method, /moderated formative qualitative playtest/);
  assert.ok(logic.preStudyFalsifiers.length >= 4);
  assert.equal(logic.canarySamplePlan.noPopulationInference, true);
  assert.equal(logic.canarySamplePlan.initialIndependentFreshParticipants, 3);
  assert.match(logic.decisionRule.repairAndRetest, /new evidence cut/);
  assert.match(logic.decisionRule.inconclusive, /INCONCLUSIVE/);
  assert.match(protocol, /Do \*\*not\*\* explain the delegation model/);
  assert.match(protocol, /Raw observation \/ participant report[\s\S]*coded finding[\s\S]*interpretation[\s\S]*Game repair\/product decision/);
});

test("R5 player study uses external method anchors without creating a method registry", () => {
  assert.equal(packet.methodProfile.family, "formative-human-centred-usability-and-mental-model-evaluation");
  const anchors = packet.methodProfile.externalAnchors.join("\n");
  assert.match(anchors, /ISO 9241-210:2019/);
  assert.match(anchors, /ISO 9241-11:2018/);
  assert.match(anchors, /Games User Research/);
  assert.match(packet.methodProfile.methodBoundary, /does not create a Game or Research method registry/);
});

test("R5 canary minimizes participant data and requires a separate decision before recording/publication", () => {
  const safety = packet.participantSafetyAndPrivacy;
  assert.match(safety.eligibility, /Adults only/);
  assert.match(safety.dataMinimization, /Do not collect demographics, health data, account credentials/);
  assert.match(safety.recording, /No audio\/video recording by default/);
  assert.match(safety.publicationBoundary, /separate ethics\/institutional review decision/);
});


test("R5 apparatus preflight proves only mechanical study readiness, not Human standing", () => {
  assert.equal(packet.apparatusPreflight.standing, "READY_FOR_HUMAN_CANARY");
  assert.equal(packet.apparatusPreflight.gameSourceRevision, "fc74ad32a7c03f7c745c1e5ce27985f983ccb6b2");
  assert.equal(packet.apparatusPreflight.observed.committedTurns, 20);
  assert.deepEqual(packet.apparatusPreflight.observed.browserErrors, []);
  assert.equal(packet.evidenceState.humanEvidenceStanding, "UNKNOWN");
  assert.match(packet.apparatusPreflight.authorityBoundary, /not Human evidence/);
});

test("R5 blank session carrier is structurally incapable of pretending collection already happened", () => {
  assert.equal(sessionTemplate.kind, "ordivon.game-player-session-observation-template");
  assert.equal(sessionTemplate.truthRole, "blank-session-template-not-human-evidence");
  assert.equal(sessionTemplate.collectionStanding, "NOT_OBSERVED");
  assert.equal(sessionTemplate.humanClaimStanding, "UNKNOWN");
  assert.equal(sessionTemplate.sessionIdentity.participantLabel, null);
  assert.equal(sessionTemplate.consent.voluntaryParticipationConfirmed, null);
  assert.equal(sessionTemplate.rawObservation.t0DirectControlMisconception, "UNOBSERVED");
  assert.equal(sessionTemplate.rawObservation.t2ModeratorCorrectionRequired, "UNOBSERVED");
  assert.match(sessionTemplate.authorityBoundary, /cannot itself mint study-level support/);
});
