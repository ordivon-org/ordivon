import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { runWholeProductRecompositionR1 } from "../experiments/whole-product-recomposition-r1/run.ts";

const wave = JSON.parse(readFileSync(new URL("../standards/game_self_attack_wave_r1.json", import.meta.url), "utf8")) as any;
const synthesis = JSON.parse(readFileSync(new URL("../standards/game_counterexample_synthesis_r1.json", import.meta.url), "utf8")) as any;
const memory = JSON.parse(readFileSync(new URL("../standards/game_design_counterexample_memory_r1.json", import.meta.url), "utf8")) as any;
const library = JSON.parse(readFileSync(new URL("../standards/game_mechanism_experience_library_r1.json", import.meta.url), "utf8")) as any;
const pkg = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8")) as any;

test("R1 self-attack wave is bounded to four recomposition falsifiers plus two stress probes", () => {
  assert.equal(wave.schemaVersion, 1);
  assert.equal(wave.kind, "ordivon.game.self-attack-wave-r1");
  assert.equal(wave.recompositionProbes.length, 4);
  assert.equal(wave.stressProbes.length, 2);
  assert.equal(wave.productSelected, false);
  assert.equal(wave.g0Entered, false);
  assert.equal(wave.canBlockNovelComposition, false);
  assert.equal(wave.humanOutcomeEstablished, false);
});

test("all self-attack retrieval references close over synthesis, counterexamples and Experiences", () => {
  const themeIds = new Set(synthesis.themes.map((x: any) => x.id));
  const counters = new Map(memory.counterexamples.map((x: any) => [x.id, x]));
  const experienceIds = new Set(library.experiences.map((x: any) => x.id));
  for (const probe of [...wave.recompositionProbes, ...wave.stressProbes]) {
    assert.ok(probe.themeRefs.length >= 1, `${probe.id} lacks synthesis theme`);
    assert.ok(probe.counterexampleRefs.length >= 1, `${probe.id} lacks counterexample`);
    for (const ref of probe.themeRefs) assert.ok(themeIds.has(ref), `${probe.id} unknown theme ${ref}`);
    for (const ref of probe.counterexampleRefs) {
      const counter = counters.get(ref) as any;
      assert.ok(counter, `${probe.id} unknown counterexample ${ref}`);
      for (const expRef of counter.experienceRefs) assert.ok(experienceIds.has(expRef), `${probe.id} unresolved Experience ${expRef}`);
    }
    assert.equal(probe.canSelectProduct, false);
    assert.equal(probe.canEstablishHumanValue, false);
  }
});

test("R01 mechanically treats E01 as subsumed by PC01 rather than additive novelty", () => {
  const result = runWholeProductRecompositionR1();
  assert.equal(result.r01.disposition, "SUBSUMED_NO_INTEGRATION");
  assert.equal(result.r01.e01WitnessPass, true);
  assert.equal(result.r01.pc01DiagnosticCausalityPass, true);
  assert.equal(result.r01.e01MechanicalSignatureSubsetOfPc01, true);
  assert.ok(result.r01.pc01ExtraDimensions.includes("persistence-switch-cost"));
  assert.ok(result.r01.pc01ExtraDimensions.includes("changing-operating-context"));
});

test("R02 mechanically treats E02 as subsumed by PC03 stable-rule transfer", () => {
  const result = runWholeProductRecompositionR1();
  assert.equal(result.r02.disposition, "SUBSUMED_NO_INTEGRATION");
  assert.equal(result.r02.e02WitnessPass, true);
  assert.equal(result.r02.pc03TimingAwareComplete, true);
  assert.equal(result.r02.pc03TimingInsensitiveFails, true);
  assert.ok(result.r02.pc03StableRuleUses >= 4);
  assert.equal(result.r02.e02MechanicalSignatureSubsetOfPc03, true);
});

test("R03 lag changes PC01 commit policy while diagnosis remains mechanically useful", () => {
  const result = runWholeProductRecompositionR1();
  assert.equal(result.r03.disposition, "SURVIVES_MINIMAL_ADDITIVITY_FALSIFIER");
  assert.equal(result.r03.coupling.hiddenCausePersistsAcrossLag, true);
  assert.equal(result.r03.coupling.nextOperatingContextForecastable, true);
  assert.ok(result.r03.policyChangeCases.length >= 3);
  assert.ok(result.r03.diagnosisPositiveUpliftCases.length >= 1);
  assert.ok(result.r03.maxLaggedDiagnosisUplift > 0);
  assert.equal(result.r03.pc01OriginalDesignHasCauseTransitionModel, false);
  assert.equal(result.r03.requiresNewProductCouplingAssumption, true);
});

test("R04 delayed PC02 feedback stays exactly attributable and adds no mechanical authority", () => {
  const result = runWholeProductRecompositionR1();
  assert.equal(result.r04.disposition, "DROP_NO_FIT");
  assert.equal(result.r04.delayedAttributionRemainsExact, true);
  assert.equal(result.r04.feedbackRemainsNonAuthoritative, true);
  assert.equal(result.r04.preferenceDoesNotGateProgression, true);
  assert.equal(result.r04.nonRedundantMechanicalEffectDemonstrated, false);
});

test("stress probes expose PC02 intent-gate and E03 forecast-model transfer boundaries", () => {
  const result = runWholeProductRecompositionR1();
  assert.equal(result.s01.intentAffectsCommitAdmissibility, true);
  assert.equal(result.s01.contextFeedbackConsumesIntent, false);
  assert.equal(result.s01.affordanceDerivationConsumesIntent, false);
  assert.equal(result.s01.boundary, "INTENT_CURRENTLY_CAUSAL_THROUGH_COMMIT_GATE_NOT_CONTEXT_OR_AFFORDANCE_SEMANTICS");
  assert.deepEqual(result.s02.costs, { perfect: 0, reactive: 8, wrongDirection: 4, alwaysCenter: 4 });
  assert.equal(result.s02.boundary, "E03_ANTICIPATION_VALUE_DEPENDS_ON_EXPLOITABLE_TRANSITION_MODEL");
});

test("R1 recomposition exposes evaluation command but no product-selection command", () => {
  assert.equal(pkg.scripts["eval:recomposition:r1"], "node experiments/whole-product-recomposition-r1/run.ts");
  assert.equal(pkg.scripts["select:recomposition:r1"], undefined);
});

test("R1 recomposition is documented as mechanical attack evidence only", () => {
  const doc = readFileSync(new URL("../docs/GAME_WHOLE_PRODUCT_RECOMPOSITION_R1_20260918.md", import.meta.url), "utf8");
  const project = readFileSync(new URL("../.ordivon/project.yaml", import.meta.url), "utf8");
  assert.match(doc, /SUBSUMED_NO_INTEGRATION/);
  assert.match(doc, /SURVIVES_MINIMAL_ADDITIVITY_FALSIFIER/);
  assert.match(doc, /DROP_NO_FIT/);
  assert.match(doc, /productSelected=false/);
  assert.match(doc, /G0=false/);
  assert.match(doc, /Human/i);
  for (const path of [
    "docs/GAME_WHOLE_PRODUCT_RECOMPOSITION_R1_20260918.md",
    "standards/game_self_attack_wave_r1.json",
    "experiments/whole-product-recomposition-r1/run.ts",
  ]) assert.match(project, new RegExp(path.replaceAll("/", "\\/")));
});
