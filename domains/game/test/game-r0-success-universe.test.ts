import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const doc = readFileSync(new URL("../docs/GAME_R0_SUCCESS_UNIVERSE_20260911.md", import.meta.url), "utf8");
const universe = JSON.parse(readFileSync(new URL("../evidence/acceptance/game-r0-success-universe-20260911.json", import.meta.url), "utf8"));
const xbox = JSON.parse(readFileSync(new URL("../evidence/acceptance/game-r0-xbox-most-played-20260911.json", import.meta.url), "utf8"));
const annualPs = JSON.parse(readFileSync(new URL("../evidence/acceptance/game-r0-playstation-2025-annual.json", import.meta.url), "utf8"));
const stacks = JSON.parse(readFileSync(new URL("../evidence/acceptance/game-r0-reference-stacks-20260911.json", import.meta.url), "utf8"));
const stackDoc = readFileSync(new URL("../docs/GAME_R0_REFERENCE_STACKS_20260911.md", import.meta.url), "utf8");
const oldR0 = JSON.parse(readFileSync(new URL("../evidence/acceptance/game-r0-external-reference-class-20260911.json", import.meta.url), "utf8"));
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const agents = readFileSync(new URL("../AGENTS.md", import.meta.url), "utf8");
const project = readFileSync(new URL("../.ordivon/project.yaml", import.meta.url), "utf8");
const authority = readFileSync(new URL("../docs/authority.md", import.meta.url), "utf8");

test("R0 success universe is upstream of feasibility and keeps clone implementation closed", () => {
  assert.equal(universe.productSelected, false);
  assert.equal(universe.g0Entered, false);
  assert.equal(universe.r1Admitted, false);
  assert.equal(universe.r1ReferenceTeardownAdmitted, true);
  assert.equal(universe.r1CloneImplementationAdmitted, false);
  assert.equal(universe.previousFirstR1SetSuperseded, true);
  assert.deepEqual(universe.cheapBaselineSet, ["Balatro", "Vampire Survivors", "Mini Metro"]);
  for (const law of [
    "UniverseMembership != LearningOrder",
    "PopularityMetric != DesignCause",
    "CrossPlatformCharts != OneGlobalRank",
    "CheapBaselineSet != RepresentativeSuccessUniverse",
  ]) assert.ok(universe.laws.includes(law));
  assert.match(doc, /R1 Reference Teardown\s+ADMITTED_WAVE1/);
  assert.match(doc, /R1 Clone Implementation\s+NOT_ADMITTED/);
  assert.match(doc, /Only the \*\*cheap causal baseline\*\* is filtered by implementation cost/);
});

test("complete Steam surfaces are retained before archetype inference", () => {
  assert.equal(universe.surfaces.steamTopSellersUS.coverage, "complete top 100");
  assert.equal(universe.surfaces.steamTopSellersUS.items.length, 100);
  assert.equal(universe.surfaces.steamMostPlayed.coverage, "complete top 100");
  assert.equal(universe.surfaces.steamMostPlayed.items.length, 100);
  assert.equal(universe.surfaces.steamMostPlayed.items[0].title, "Counter-Strike 2");
  assert.ok(universe.surfaces.steamMostPlayed.items.some((row: any) => row.title === "Factorio"));
  assert.ok(universe.surfaces.steamMostPlayed.items.some((row: any) => row.title === "RimWorld"));
});

test("Xbox delimiter corruption is invalidated and corrected source preserves exactly fifty titles", () => {
  assert.equal(universe.surfaces.xboxMostPlayedUS.valid, false);
  assert.equal(universe.surfaces.xboxMostPlayedUS.standing, "INVALIDATED_DELIMITER_CORRUPTION");
  assert.equal(universe.surfaces.xboxMostPlayedUS.supersededBy, "game-r0-xbox-most-played-20260911.json");
  assert.equal(xbox.valid, true);
  assert.equal(xbox.items.length, 50);
  assert.equal(xbox.items[8].title, "EA SPORTS FC 26 XBOX Series X|S");
  assert.equal(xbox.items[9].title, "Grand Theft Auto Online (Xbox Series X|S)");
  assert.equal(xbox.items[12].title, "NBA 2K26 for Xbox Series X|S");
  assert.equal(xbox.items[49].title, "theHunter: Call of the Wild");
  assert.ok(!xbox.items.some((row: any) => row.title === "S" || row.title === "S)"));
});

test("current annual lifetime and mobile surfaces prevent one PC snapshot from defining the universe", () => {
  assert.equal(universe.surfaces.playstationAugust2026.ps5USCanada.length, 20);
  assert.equal(universe.surfaces.playstationAugust2026.ps5EU.length, 20);
  assert.equal(universe.surfaces.playstationAugust2026.freeToPlay.length, 10);
  assert.equal(annualPs.ps5USCanada.length, 20);
  assert.equal(annualPs.ps5EU.length, 20);
  assert.equal(annualPs.ps4USCanada.length, 20);
  assert.equal(annualPs.ps4EU.length, 20);
  assert.equal(annualPs.psvr2USCanada[0], "Beat Saber");
  assert.equal(annualPs.freeToPlayUSCanada[0], "Fortnite");
  assert.equal(universe.surfaces.nintendoSwitchLifetime.items[0].title, "Mario Kart 8 Deluxe");
  assert.equal(universe.surfaces.nintendoSwitchLifetime.items[0].millionUnits, 71.53);
  assert.equal(universe.surfaces.mobileAugust2026.revenueTop5.length, 5);
  assert.equal(universe.surfaces.mobileAugust2026.downloadsTop5.length, 5);
  assert.match(universe.surfaces.mobileAugust2026.metric, /third-party Android markets excluded/);
});

test("archetype map spans major successful forms and retains coverage debt", () => {
  const map = universe.archetypeMap;
  assert.ok(Object.keys(map).length >= 35);
  for (const key of [
    "competitive_tactical_fps",
    "ugc_social_platform",
    "action_rpg_souls_hunt",
    "survival_craft",
    "automation_factory",
    "racing_vehicle_sim",
    "sports_competitive",
    "party_local_social",
    "mobile_liveops_strategy",
    "mobile_merge_match_casual",
    "fighting_brawler",
    "survival_horror",
    "real_time_strategy",
    "cooperative_adventure",
    "vr_rhythm_embodied",
    "cinematic_action_adventure",
    "live_service_gacha_action",
  ]) assert.ok(Array.isArray(map[key]) && map[key].length > 0, key);
  assert.ok(Array.isArray(universe.coverageDebt) && universe.coverageDebt.length >= 5);
});

test("reference stacks admit broad teardown without admitting clone implementation or product selection", () => {
  assert.equal(stacks.productSelected, false);
  assert.equal(stacks.g0Entered, false);
  assert.equal(stacks.firstR1Wave.length, 12);
  for (const title of ["Counter-Strike 2", "Dota 2", "Fortnite", "Minecraft", "Grand Theft Auto V", "ELDEN RING", "Baldur's Gate 3", "Factorio", "Mario Kart 8 Deluxe", "Animal Crossing: New Horizons", "Candy Crush Saga", "Beat Saber"]) assert.ok(stacks.firstR1Wave.includes(title), title);
  assert.equal(stacks.r1Admission.standing, "ADMIT_REFERENCE_TEARDOWN_ONLY");
  assert.equal(stacks.r1Admission.cloneImplementation, false);
  assert.equal(stacks.r1Admission.accessLimitationDoesNotDeleteReference, true);
  assert.match(stackDoc, /ReferenceImportance != ReproductionCost/);
  assert.match(stackDoc, /R1 Clone Implementation\s+NOT_ADMITTED/);
});

test("current repository authority points to success universe and reference stacks while demoting old R0", () => {
  for (const carrier of [readme, agents, project, authority]) {
    assert.match(carrier, /GAME_R0_SUCCESS_UNIVERSE_20260911\.md/);
    assert.match(carrier, /GAME_R0_REFERENCE_STACKS_20260911\.md/);
  }
  assert.equal(oldR0.standing, "SUPERSEDED_AS_R1_ADMISSION");
  assert.equal(oldR0.r1Admitted, false);
  assert.deepEqual(oldR0.cheapBaselineSet, ["Balatro", "Vampire Survivors", "Mini Metro"]);
  assert.match(readme, /first broad R1 \*\*reference-teardown-only\*\* wave/);
});
