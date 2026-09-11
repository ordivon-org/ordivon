import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const access = JSON.parse(readFileSync(new URL("../evidence/acceptance/game-r1-direct-play-access-20260911.json", import.meta.url), "utf8"));
const doc = readFileSync(new URL("../docs/GAME_R1_DIRECT_PLAY_ACCESS_20260911.md", import.meta.url), "utf8");
const sheet = readFileSync(new URL("../docs/GAME_R1_DIRECT_PLAY_OBSERVATION_SHEET.md", import.meta.url), "utf8");
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const agents = readFileSync(new URL("../AGENTS.md", import.meta.url), "utf8");
const project = readFileSync(new URL("../.ordivon/project.yaml", import.meta.url), "utf8");
const authority = readFileSync(new URL("../docs/authority.md", import.meta.url), "utf8");

test("access census does not launder installation absence into ownership or access claims", () => {
  assert.equal(access.ownershipStanding, "UNKNOWN_UNLESS_EXPLICITLY_PROVEN");
  assert.equal(access.localScan.targetInstalledEvidenceCount, 0);
  assert.equal(access.localScan.vrRuntimeMarkersPresent, false);
  assert.ok(access.localScan.doNotInfer.includes("not detected != not owned"));
  assert.match(doc, /Not installed here\s*!= not owned/);
});

test("direct-play access classes cover all twelve references exactly once", () => {
  const titles = access.accessClasses.flatMap((x: any) => x.titles);
  assert.equal(titles.length, 12);
  assert.equal(new Set(titles).size, 12);
  for (const title of ["Factorio","Minecraft","Counter-Strike 2","Dota 2","Fortnite","Candy Crush Saga","Grand Theft Auto V","ELDEN RING","Baldur's Gate 3","Mario Kart 8 Deluxe","Animal Crossing: New Horizons","Beat Saber"]) assert.ok(titles.includes(title), title);
  assert.equal(access.recommendedFirstCarrier.title, "Factorio");
  assert.equal(access.recommendedFirstCarrier.notYetAuthorized, true);
});

test("downloads purchases sign-in and synthetic Human evidence stay closed without user authority", () => {
  assert.equal(access.safetyAndAuthority.automaticPurchase, false);
  assert.equal(access.safetyAndAuthority.automaticAccountSignin, false);
  assert.equal(access.safetyAndAuthority.automaticCredentialUse, false);
  assert.equal(access.safetyAndAuthority.automaticDownloadInstall, false);
  assert.equal(access.safetyAndAuthority.humanExperienceCanBeSynthesized, false);
  assert.equal(access.safetyAndAuthority.r2ImplementationAdmitted, false);
  assert.match(doc, /No purchase, account sign-in, credential use, large download or device pairing is authorized/);
});

test("observation sheet is blank and cannot claim Human evidence before a real session", () => {
  assert.match(sheet, /BLANK TEMPLATE — NO HUMAN EVIDENCE HAS BEEN COLLECTED/);
  assert.match(sheet, /SURVIVES_DIRECT_PLAY/);
  assert.match(sheet, /REVISE_CAUSAL_HYPOTHESIS/);
  assert.match(sheet, /REJECT_TRANSFER/);
  assert.match(sheet, /INCONCLUSIVE/);
  assert.doesNotMatch(sheet, /Participant name:/i);
});

test("repository navigation exposes the direct-play gate", () => {
  for (const carrier of [readme, agents, project, authority]) {
    assert.match(carrier, /GAME_R1_DIRECT_PLAY_ACCESS_20260911\.md/);
    assert.match(carrier, /GAME_R1_DIRECT_PLAY_OBSERVATION_SHEET\.md/);
  }
});
