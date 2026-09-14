import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const policy = readFileSync(new URL("../docs/GAME_EXTERNAL_MATURE_PRACTICE_ADOPTION_R1.md", import.meta.url), "utf8");
const matrix = JSON.parse(readFileSync(new URL("../evidence/acceptance/game-external-mature-practice-adoption-r1.json", import.meta.url), "utf8"));
const composition = JSON.parse(readFileSync(new URL("../evidence/acceptance/game-external-mature-practice-composition-r1.json", import.meta.url), "utf8"));
const adjudication = JSON.parse(readFileSync(new URL("../evidence/acceptance/game-external-mature-practice-adjudication-r1.json", import.meta.url), "utf8"));
const core = readFileSync(new URL("../docs/GAME_DEVELOPMENT_CORE.md", import.meta.url), "utf8");
const playerEvidence = readFileSync(new URL("../docs/GAME_PLAYER_EVIDENCE_PROGRAMME.md", import.meta.url), "utf8");
const paradigm = readFileSync(new URL("../docs/GAME_DEVELOPMENT_PARADIGM_RESEARCH.md", import.meta.url), "utf8");
const authority = readFileSync(new URL("../docs/authority.md", import.meta.url), "utf8");
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const frontHalf = readFileSync(new URL("../docs/GAME_FRONT_HALF_EXTERNAL_REFERENCE_PROFILE.md", import.meta.url), "utf8");

test("external mature mechanism is the default and local extension requires falsification", () => {
  assert.equal(matrix.defaultPolicy, "DIRECT_ADOPT_EXTERNAL_WITHIN_NATIVE_SCOPE");
  assert.equal(matrix.localExtensionRule, "ADAPT_ONLY_IF_FALSIFIED");
  assert.match(policy, /Default = DIRECTLY ADOPT mature external mechanism/);
  assert.match(policy, /Local extension requires falsifier/);
  assert.match(paradigm, /external-first/i);
});


test("front-half product discovery observes the success universe before feasibility or internal novelty filtering", () => {
  assert.match(policy, /Product discovery: external reference before internal direction search/);
  assert.match(policy, /External successful mature games\s+PRIMARY REFERENCE MATERIAL/);
  assert.match(policy, /Implementation feasibility\s+LEARNING-ORDER \/ CHEAP-BASELINE FILTER ONLY/);
  assert.match(frontHalf, /Steamworks.*similar titles/is);
  assert.match(frontHalf, /Nintendo.*Echoes of Wisdom/is);
  assert.match(frontHalf, /Human play \/ evidence/);
  assert.match(frontHalf, /Runtime Agents remain `none` by default/);
});

test("authoritative external standards cover requirements quality Human research lifecycle accessibility provenance and compliance", () => {
  for (const mechanism of [
    "ISO/IEC/IEEE 29148:2018",
    "ISO/IEC 25010:2023",
    "ISO/IEC 25019:2023",
    "ISO 9241-210:2019",
    "ISO 9241-11:2018",
    "ISO 20252:2026",
    "ISO/IEC/IEEE 12207:2026",
    "SLSA",
    "SPDX",
    "ISO/IEC 5230:2020 OpenChain",
    "Xbox Accessibility Guidelines",
    "WCAG 2.2",
  ]) assert.ok(matrix.mechanisms.some((row: any) => row.mechanism.includes(mechanism)), mechanism);
});

test("platform-native playtest experimentation and release are consumed rather than reimplemented", () => {
  for (const area of ["playtest-delivery", "controlled-experiments", "distribution-release"]) {
    const row = matrix.mechanisms.find((entry: any) => entry.area === area);
    assert.equal(row.disposition, "PLATFORM_NATIVE");
  }
  assert.match(policy, /Steam Playtest/);
  assert.match(policy, /PlayFab Experiments/);
  const release = matrix.mechanisms.find((entry: any) => entry.area === "distribution-release");
  assert.equal(release.mechanism, "Steamworks Release/Review Process");
  assert.match(policy, /platform review\/checklists\/permissions\/release/);
});

test("Game retains only irreducible semantic and product-interpretation ownership", () => {
  for (const kept of ["ExperienceIntent", "PlayableSemantics", "ContentProgressionGrammar", "ProductValueInterpretation", "ProductDirectionDecision"]) {
    assert.ok(matrix.gameOwnedResidual.includes(kept));
  }
  for (const forbidden of ["GenericABExperimentPlatform", "GenericTelemetryWarehouse", "GenericSoftwareLifecycleStandard", "PlatformReleaseWorkflow", "UniversalAccessibilityChecklist"]) {
    assert.ok(matrix.gameMustNotOwn.includes(forbidden));
  }
});

test("D1-D8 and Player Evidence are routing/profile views over external practice, not competing standards", () => {
  assert.match(core, /D1–D8 is a \*\*routing\/profile view\*\*/i);
  assert.match(playerEvidence, /GamePlayerEvidenceProfile/);
  assert.match(playerEvidence, /ISO 9241-210/);
  assert.match(playerEvidence, /ISO 20252:2026/);
  assert.match(playerEvidence, /does not replace the external research\/HCD\/experiment mechanisms/i);
});

test("adoption policy is discoverable and has bounded authority", () => {
  assert.match(authority, /GAME_EXTERNAL_MATURE_PRACTICE_ADOPTION_R1\.md/);
  assert.match(authority, /direct-adoption policy/i);
  assert.match(readme, /GAME_EXTERNAL_MATURE_PRACTICE_ADOPTION_R1\.md/);
  assert.match(policy, /No synthetic compliance/i);
  assert.match(policy, /Game does NOT own/);
});


test("independent adjudication binds external-first composition without claiming compliance", () => {
  assert.equal(composition.standing, "PASS_BOUNDED");
  assert.equal(composition.independentVerification.focused.pass, 28);
  assert.equal(composition.independentVerification.fullRepository.pass, 402);
  assert.equal(adjudication.verdict, "ADOPT_EXTERNAL_FIRST");
  assert.equal(adjudication.activationContract.noForceUpdate, true);
  assert.match(adjudication.truthRole, /not-standards-compliance-certificate/);
  assert.ok(adjudication.doNotInfer.some((row: string) => /not ISO\/XAG\/WCAG\/SLSA\/OpenChain compliance/.test(row)));
});
