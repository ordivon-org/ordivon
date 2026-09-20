import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

// @ts-expect-error Historical JS experiment intentionally has no declaration file; this falsifier consumes its runtime witness contract.
import { runWitnesses as runE01Witnesses } from "../mechanic-prototype-wave-r1/e01-counterfactual-probe/core.js";
// @ts-expect-error Historical JS experiment intentionally has no declaration file; this falsifier consumes its runtime witness contract.
import { runWitnesses as runE02Witnesses } from "../mechanic-prototype-wave-r1/e02-transfer-route/core.js";
// @ts-expect-error Historical JS experiment intentionally has no declaration file; this falsifier consumes its runtime witness contract.
import { SCENARIO as E03_SCENARIO, advanceTarget, anticipatoryActions, forecastTarget, initialTarget, reactiveActions, simulateSequence } from "../mechanic-prototype-wave-r1/e03-commitment-lag/core.js";
// @ts-expect-error Historical JS experiment intentionally has no declaration file; this falsifier consumes its runtime witness contract.
import { runWitnesses as runPc03Witnesses } from "../pc03-f0/web/core.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const PC01_DESIGN = "experiments/product-composition-r1/pc01-causal-works-f0/design.json";
const PC01_EVIDENCE = "experiments/product-composition-r1/pc01-causal-works-f0/evidence/structural-falsifier-r1.json";
const PC02_EVIDENCE = "experiments/product-composition-r1/pc02-persistent-workshop-f0/evidence/structural-acceptance-r1.json";
const PC02_CARRIER = "experiments/product-composition-r1/pc02-persistent-workshop-f0/carrier.py";
const WAVE_PATH = "standards/game_self_attack_wave_r1.json";

function readJson(path: string): any {
  return JSON.parse(readFileSync(resolve(ROOT, path), "utf8"));
}

function observation(diag: string, cause: string): string {
  if (diag === "none") return "none";
  return diag === cause ? "fault" : "ok";
}

function pc01ImmediatePolicy(
  design: any,
  sourceCycle: any,
  rewardCycle: any,
  previous: string | null,
  allowDiagnostics: boolean,
): { diagnostic: string; architectureByObservation: Record<string, string>; total: number } {
  const architectures: string[] = design.architectureModes;
  const diagnostics: string[] = allowDiagnostics ? design.diagnostics : ["none"];
  let best: { diagnostic: string; architectureByObservation: Record<string, string>; total: number } | null = null;

  for (const diagnostic of diagnostics) {
    const groups = new Map<string, Array<[string, number]>>();
    for (const [cause, rawPrior] of Object.entries(sourceCycle.causePrior)) {
      const obs = observation(diagnostic, cause);
      const members = groups.get(obs) ?? [];
      members.push([cause, Number(rawPrior)]);
      groups.set(obs, members);
    }

    let total = diagnostic === "none" ? 0 : -Number(design.diagnosticCost);
    const architectureByObservation: Record<string, string> = {};
    for (const [obs, members] of groups.entries()) {
      const pObs = members.reduce((sum, [, p]) => sum + p, 0);
      let branch: { architecture: string; value: number } | null = null;
      for (const architecture of architectures) {
        let value = members.reduce(
          (sum, [cause, p]) => sum + (p / pObs) * Number(rewardCycle.rewardByCauseAndArchitecture[cause][architecture]),
          0,
        );
        if (previous !== null && architecture !== previous) value -= Number(design.switchCost);
        if (branch === null || value > branch.value) branch = { architecture, value };
      }
      if (branch === null) throw new Error("PC01 policy branch has no architecture");
      total += pObs * branch.value;
      architectureByObservation[obs] = branch.architecture;
    }

    const candidate = { diagnostic, architectureByObservation, total };
    if (best === null || candidate.total > best.total) best = candidate;
  }
  if (best === null) throw new Error("PC01 policy search produced no candidate");
  return best;
}

function samePolicy(a: any, b: any): boolean {
  return a.diagnostic === b.diagnostic && JSON.stringify(a.architectureByObservation) === JSON.stringify(b.architectureByObservation);
}

function r01Pc01E01Subsumption() {
  const e01 = runE01Witnesses();
  const design = readJson(PC01_DESIGN);
  const evidence = readJson(PC01_EVIDENCE);
  const pc01DiagnosticCausalityPass = Boolean(
    evidence.checks?.diagnosisAddsExpectedValue &&
      evidence.checks?.negativeDiagnosticObservationRemainsAmbiguous &&
      evidence.checks?.uniqueBestArchitecturePerCause &&
      Number(evidence.metrics?.diagnosisExpectedValueUplift) > 0 &&
      design.hiddenCauseStates.length >= 2 &&
      design.diagnostics.filter((x: string) => x !== "none").length >= 1 &&
      Number(design.diagnosticCost) > 0,
  );
  const e01MechanicalSignatureSubsetOfPc01 = Boolean(
    e01.pass &&
      e01.initialViewsMatch &&
      e01.fixedRepairCannotSolveBoth &&
      e01.inspectionSeparatesFaults &&
      e01.informedSolvesBoth &&
      e01.boundedInspection &&
      pc01DiagnosticCausalityPass,
  );
  const pc01ExtraDimensions: string[] = [];
  if (Number(design.switchCost) > 0 && evidence.checks?.persistenceChangesAtLeastOneDecision) pc01ExtraDimensions.push("persistence-switch-cost");
  if (design.cycles.length > 1 && new Set(design.cycles.map((x: any) => x.operatingContext)).size > 1) pc01ExtraDimensions.push("changing-operating-context");
  if (new Set(evidence.metrics?.noScanArchitectureChoicesAcrossCycles ?? []).size > 1) pc01ExtraDimensions.push("cross-cycle-objective-revaluation");
  return {
    id: "R01",
    targets: ["composition.pc01", "mechanic.e01"],
    e01WitnessPass: e01.pass,
    pc01DiagnosticCausalityPass,
    sharedMechanicalSignature: [
      "initially-ambiguous-hidden-cause",
      "bounded-information-action",
      "observation-changes-corrective-choice",
      "cause-specific-successful-correction",
    ],
    pc01ExtraDimensions,
    e01MechanicalSignatureSubsetOfPc01,
    disposition: e01MechanicalSignatureSubsetOfPc01 ? "SUBSUMED_NO_INTEGRATION" : "REOPEN_SUBSUMPTION_TEST",
    claimBoundary: "MECHANICAL_SUBSUMPTION_ONLY_NO_PRODUCT_OR_HUMAN_CLAIM",
  } as const;
}

function r02Pc03E02Subsumption() {
  const e02 = runE02Witnesses();
  const pc03 = runPc03Witnesses();
  const pc03TimingAwareComplete = Boolean(pc03.aware.complete);
  const pc03TimingInsensitiveFails = Boolean(!pc03.insensitive.complete && pc03.insensitive.failures > 0);
  const pc03StableRuleUses = Number(pc03.aware.ruleUses);
  const invariantSame = pc03.uninformed.worldInvariant === pc03.aware.worldInvariant && pc03.insensitive.worldInvariant === pc03.aware.worldInvariant;
  const e02MechanicalSignatureSubsetOfPc03 = Boolean(
    e02.pass &&
      e02.transferSucceeds &&
      e02.timingMattersOnRoute2 &&
      e02.absoluteScheduleDoesNotTransfer &&
      e02.noKnowledgeAuthorizationState &&
      pc03TimingAwareComplete &&
      pc03TimingInsensitiveFails &&
      pc03StableRuleUses >= 4 &&
      pc03.stableRule.authoritativeKnowledgeState === false &&
      pc03.stableRule.instances.length >= 2 &&
      invariantSame,
  );
  return {
    id: "R02",
    targets: ["composition.pc03", "mechanic.e02"],
    e02WitnessPass: e02.pass,
    pc03TimingAwareComplete,
    pc03TimingInsensitiveFails,
    pc03StableRuleUses,
    pc03StableRuleInstances: pc03.stableRule.instances,
    worldInvariantSameAcrossPolicies: invariantSame,
    e02MechanicalSignatureSubsetOfPc03,
    disposition: e02MechanicalSignatureSubsetOfPc03 ? "SUBSUMED_NO_INTEGRATION" : "REOPEN_SUBSUMPTION_TEST",
    claimBoundary: "MECHANICAL_SUBSUMPTION_ONLY_NO_HUMAN_LEARNING_OR_PRODUCT_CLAIM",
  } as const;
}

function r03Pc01E03Additivity() {
  const design = readJson(PC01_DESIGN);
  const previousStates: Array<string | null> = [null, ...design.architectureModes];
  const policyChangeCases: any[] = [];
  const diagnosisPositiveUpliftCases: any[] = [];
  let maxLaggedDiagnosisUplift = 0;

  for (let i = 0; i < design.cycles.length - 1; i += 1) {
    const source = design.cycles[i];
    const target = design.cycles[i + 1];
    for (const previous of previousStates) {
      const reactive = pc01ImmediatePolicy(design, source, source, previous, true);
      const anticipatory = pc01ImmediatePolicy(design, source, target, previous, true);
      const laggedNoDiagnosis = pc01ImmediatePolicy(design, source, target, previous, false);
      const uplift = anticipatory.total - laggedNoDiagnosis.total;
      if (!samePolicy(reactive, anticipatory)) {
        policyChangeCases.push({ fromCycle: source.id, executionContext: target.id, previousArchitecture: previous, reactive, anticipatory });
      }
      if (uplift > 1e-9) {
        diagnosisPositiveUpliftCases.push({ fromCycle: source.id, executionContext: target.id, previousArchitecture: previous, uplift });
        maxLaggedDiagnosisUplift = Math.max(maxLaggedDiagnosisUplift, uplift);
      }
    }
  }

  const topLevelKeys = new Set(Object.keys(design));
  const cycleKeys = new Set(design.cycles.flatMap((cycle: any) => Object.keys(cycle)));
  const pc01OriginalDesignHasCauseTransitionModel = ["causeTransition", "causeTransitions", "transitionModel", "causeDynamics"].some(
    (key) => topLevelKeys.has(key) || cycleKeys.has(key),
  );
  const coupling = {
    lagSteps: 1,
    hiddenCausePersistsAcrossLag: true,
    nextOperatingContextForecastable: true,
    executionRewardContextAdvancesOneCycle: true,
    diagnosticObservationUsesCurrentPersistingCause: true,
  };
  const survives = policyChangeCases.length > 0 && diagnosisPositiveUpliftCases.length > 0 && maxLaggedDiagnosisUplift > 0;
  return {
    id: "R03",
    targets: ["composition.pc01", "mechanic.e03"],
    coupling,
    policyChangeCases,
    diagnosisPositiveUpliftCases,
    maxLaggedDiagnosisUplift,
    pc01OriginalDesignHasCauseTransitionModel,
    requiresNewProductCouplingAssumption: !pc01OriginalDesignHasCauseTransitionModel,
    disposition: survives ? "SURVIVES_MINIMAL_ADDITIVITY_FALSIFIER" : "DROP_NO_ADDITIVE_POLICY_CHANGE",
    claimBoundary: "SYNTHETIC_MECHANICAL_COUPLING_ONLY_NO_HUMAN_VALUE_OR_PRODUCT_SELECTION_CLAIM",
  } as const;
}

function r04Pc02E03NoFit() {
  const evidence = readJson(PC02_EVIDENCE);
  const rounds = evidence.rounds ?? [];
  const delayedPairs = [];
  for (let i = 0; i < rounds.length - 1; i += 1) {
    const sourceRevision = rounds[i].revision;
    const sourceContext = rounds[i].context;
    const laterRevision = rounds[i + 1].revision;
    delayedPairs.push({
      sourceRevisionId: sourceRevision.id,
      sourceArtifactDigest: sourceRevision.artifactDigest,
      delayedUntilAfterRevisionId: laterRevision.id,
      delayedUntilAfterArtifactDigest: laterRevision.artifactDigest,
      contextRevisionId: sourceContext.revisionId,
      contextArtifactDigest: sourceContext.artifactDigest,
      exactSourceIdentityPreserved:
        sourceContext.revisionId === sourceRevision.id &&
        sourceContext.artifactDigest === sourceRevision.artifactDigest &&
        sourceContext.artifactDigest !== laterRevision.artifactDigest,
    });
  }
  const delayedAttributionRemainsExact = delayedPairs.length > 0 && delayedPairs.every((x) => x.exactSourceIdentityPreserved);
  const feedbackRemainsNonAuthoritative = rounds.every((round: any) => round.context?.feedback?.authority === "advisory-context-observation");
  const preferenceDoesNotGateProgression = Boolean(evidence.checks?.rejectedAudiencePreferenceStillProgresses);
  const nonRedundantMechanicalEffectDemonstrated = false;
  const noFit = delayedAttributionRemainsExact && feedbackRemainsNonAuthoritative && preferenceDoesNotGateProgression;
  return {
    id: "R04",
    targets: ["composition.pc02", "mechanic.e03"],
    delayedPairs,
    delayedAttributionRemainsExact,
    feedbackRemainsNonAuthoritative,
    preferenceDoesNotGateProgression,
    nonRedundantMechanicalEffectDemonstrated,
    disposition: noFit ? "DROP_NO_FIT" : "REOPEN_ATTRIBUTION_ATTACK",
    claimBoundary: "MECHANICAL_ATTRIBUTION_AND_AUTHORITY_ONLY_NO_HUMAN_RESPONSIVENESS_CLAIM",
  } as const;
}

function s01Pc02IntentBoundary() {
  const evidence = readJson(PC02_EVIDENCE);
  const carrierSource = readFileSync(resolve(ROOT, PC02_CARRIER), "utf8");
  const deriveSignatureOnlyPieces = /def derive_affordances\(pieces: list\[dict\]\)/.test(carrierSource);
  const feedbackSignatureOnlyPieces = /def profile_feedback\(profile_id: str, pieces: list\[dict\]\)/.test(carrierSource);
  const commitUsesIntentGate = /if not intent_satisfied\(self\.intent, snapshot\):/.test(carrierSource);
  const commitDerivesAffordancesFromSnapshotOnly = /"derivedAffordances": derive_affordances\(snapshot\)/.test(carrierSource);
  return {
    id: "S01",
    target: "composition.pc02",
    intentAffectsCommitAdmissibility: Boolean(evidence.checks?.intentAxisChangesNonAudienceCommitConstraint && commitUsesIntentGate),
    contextFeedbackConsumesIntent: !(evidence.checks?.contextFeedbackDoesNotConsumeIntentMetadata && feedbackSignatureOnlyPieces),
    affordanceDerivationConsumesIntent: !(deriveSignatureOnlyPieces && commitDerivesAffordancesFromSnapshotOnly),
    boundary: "INTENT_CURRENTLY_CAUSAL_THROUGH_COMMIT_GATE_NOT_CONTEXT_OR_AFFORDANCE_SEMANTICS",
    claimBoundary: "STRUCTURAL_CARRIER_BOUNDARY_ONLY_NO_AUTHORSHIP_OR_EXPRESSIVE_INTENT_CLAIM",
  } as const;
}

function e03WrongDirectionActions(): number[] {
  let target = initialTarget();
  const actions: number[] = [];
  for (let tick = 0; tick < E03_SCENARIO.horizon; tick += 1) {
    const wrongModel = { lane: target.lane, direction: -target.direction };
    actions.push(forecastTarget(wrongModel, 1).lane);
    target = advanceTarget(target);
  }
  return actions;
}

function s02E03ForecastSensitivity() {
  const perfect = simulateSequence(anticipatoryActions(1), 1);
  const reactive = simulateSequence(reactiveActions(), 1);
  const wrongDirection = simulateSequence(e03WrongDirectionActions(), 1);
  const alwaysCenter = simulateSequence(Array(E03_SCENARIO.horizon).fill(1), 1);
  return {
    id: "S02",
    target: "mechanic.e03",
    costs: {
      perfect: perfect.recoveryCost,
      reactive: reactive.recoveryCost,
      wrongDirection: wrongDirection.recoveryCost,
      alwaysCenter: alwaysCenter.recoveryCost,
    },
    misses: {
      perfect: perfect.misses,
      reactive: reactive.misses,
      wrongDirection: wrongDirection.misses,
      alwaysCenter: alwaysCenter.misses,
    },
    boundary: "E03_ANTICIPATION_VALUE_DEPENDS_ON_EXPLOITABLE_TRANSITION_MODEL",
    claimBoundary: "MECHANICAL_TRANSFER_BOUNDARY_ONLY_NO_HUMAN_PLANNING_OR_FUN_CLAIM",
  } as const;
}

export function runWholeProductRecompositionR1() {
  const wave = readJson(WAVE_PATH);
  const r01 = r01Pc01E01Subsumption();
  const r02 = r02Pc03E02Subsumption();
  const r03 = r03Pc01E03Additivity();
  const r04 = r04Pc02E03NoFit();
  const s01 = s01Pc02IntentBoundary();
  const s02 = s02E03ForecastSensitivity();
  return {
    schemaVersion: 1,
    kind: "ordivon.game.whole-product-recomposition-r1-evidence",
    waveId: wave.waveId,
    sourceRevision: wave.sourceRevision,
    hostTaskId: wave.hostTaskId,
    r01,
    r02,
    r03,
    r04,
    s01,
    s02,
    finiteRecompositionStanding: {
      r01: r01.disposition,
      r02: r02.disposition,
      r03: r03.disposition,
      r04: r04.disposition,
      mechanicalSurvivors: r03.disposition === "SURVIVES_MINIMAL_ADDITIVITY_FALSIFIER" ? ["PC01+E03@R03-coupling"] : [],
    },
    productSelected: false,
    g0Entered: false,
    humanOutcomeEstablished: false,
    gameCoreChanged: false,
    claimBoundary: wave.claimBoundary,
  } as const;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const result = runWholeProductRecompositionR1();
  const evidencePath = resolve(dirname(fileURLToPath(import.meta.url)), "evidence/recomposition-r1.json");
  mkdirSync(dirname(evidencePath), { recursive: true });
  writeFileSync(evidencePath, `${JSON.stringify(result, null, 2)}\n`);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}
