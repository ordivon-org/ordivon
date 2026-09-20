#!/usr/bin/env node
import fs from 'node:fs';
const model=JSON.parse(fs.readFileSync(process.argv[2]??'evidence/gdf2-c/identifiability-model.json','utf8'));
const p=JSON.parse(fs.readFileSync(process.argv[3]??'evidence/gdf2-c/identifiability-probes.json','utf8'));
const contractNames=new Set(model.researchContracts.map(x=>x.name));
const requiredContracts=['ChallengeObservationDesign','ChallengeInterventionSet','IdentifiedChallengeClaim','ChallengeEquivalenceClass','IdentificationStatus'];
for(const x of requiredContracts) if(!contractNames.has(x)) throw new Error(`missing ${x}`);
const checks={
  surfaceDemoted:model.surfaceVerdict.CapabilityOutcomeSurface==='demote-to-research-model-family',
  aggregateNonIdentifiability:p.aggregateEquivalence.sameAggregate&&p.aggregateEquivalence.differentSurface,
  populationSelection:p.selection.naiveReversal&&p.selection.standardizedRestoresOrdering,
  gaugeEquivalence:p.gauge.sameProbability,
  repeatedProbeSeparatesRandomness:p.repeatedTrials.repetitionSeparates,
  multidimensionalCompensation:p.compensation.sameOutcome&&p.compensation.directional,
  observedVsAttainableMonotonicity:p.monotonicity.observedCanWorsen&&p.monotonicity.bestAttainableDoesNotWorsen,
  averageAssistInsufficient:p.assist.sameMeanGain&&p.assist.differentProfileShape,
  crossPlayNeeded:p.opponent.sameAggregate&&p.opponent.differentMatchupStructure,
  recoveryNotScalar:p.recovery.transitionsStructurallyDistinct&&p.recovery.noUniversalScalarWithoutWeights,
  enoughProbeFamilies:model.minimumProbeFamilies.length>=8,
  explicitEquivalenceClass:contractNames.has('ChallengeEquivalenceClass'),
  noFoundationReopen:Object.values(model.foundationReopen).filter(x=>typeof x==='boolean').every(x=>x===false)
};
if(Object.values(checks).some(x=>!x)) throw new Error(`C audit failed ${JSON.stringify(checks)}`);
console.log(JSON.stringify({schemaVersion:1,kind:'ordivon.game.gdf2-c-identifiability-audit',reconstructionCount:model.reconstructions.length,probeFamilyCount:model.minimumProbeFamilies.length,lawCount:model.identifiabilityLaws.length,checks,strongestConclusion:'A challenge response surface is not directly identified from aggregate outcomes. GDF2 must freeze epistemic/probe responsibilities rather than a presumed latent surface: observation design, interventions, identified claims, explicit equivalence classes and identification status. Aggregate pass rates, one-shot variance, one average assist effect and one opponent rating are insufficient for unique structural attribution.'},null,2));
