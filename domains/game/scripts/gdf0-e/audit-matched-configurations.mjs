#!/usr/bin/env node
import fs from 'node:fs';

const input = process.argv[2] ?? 'evidence/gdf0-e/matched-configuration-evidence.json';
const data = JSON.parse(fs.readFileSync(input, 'utf8'));

const required = ['id', 'evidenceClass', 'source', 'heldFixed', 'changed', 'outcomes', 'supports', 'limits', 'predictionStatus'];
const allowedClasses = new Set(['M1', 'M2', 'M3', 'M4']);

for (const item of data.interventions) {
  for (const field of required) {
    if (!(field in item)) throw new Error(`${item.id ?? '<unknown>'} missing ${field}`);
  }
  if (!allowedClasses.has(item.evidenceClass)) throw new Error(`${item.id} invalid evidenceClass ${item.evidenceClass}`);
  if (item.heldFixed.length === 0) throw new Error(`${item.id} has no heldFixed variables`);
  if (item.changed.length === 0) throw new Error(`${item.id} has no changed variables`);
  if (item.evidenceClass !== 'M4' && item.outcomes.length === 0) throw new Error(`${item.id} empirical/quasi evidence missing outcomes`);
  if (item.limits.length === 0) throw new Error(`${item.id} missing limits`);
}

const counts = Object.fromEntries([...allowedClasses].map((c) => [c, data.interventions.filter((x) => x.evidenceClass === c).length]));
const empirical = data.interventions.filter((x) => x.evidenceClass !== 'M4');
const genericGamificationFalsifier = empirical.some((x) => x.predictionStatus === 'falsifies-monotonic-more-game-elements-more-play');
const sameStructureConfigCausality = empirical.some((x) => x.predictionStatus.includes('configuration-causality'));
const sameArtifactStructureChange = empirical.some((x) => x.predictionStatus === 'supports-same-artifact-different-effective-structure');

const output = {
  schemaVersion: 1,
  kind: 'ordivon.game.gdf0-e-matched-configuration-audit',
  interventionCount: data.interventions.length,
  evidenceClassCounts: counts,
  admittedEmpiricalOrQuasiMatchedCount: empirical.length,
  tests: {
    sameStructureConfigCausality,
    genericMoreGameElementsMorePlayFalsified: genericGamificationFalsifier,
    sameArtifactCanSupportDifferentEffectiveStructure: sameArtifactStructureChange,
  },
  c12Disposition: data.c12Audit.disposition,
  strongConclusion:
    'configuration variables have causal/constitutive effects, but effects are outcome- and mediator-specific; no monotonic gameness/playfulness transformation is supported, so C12 remains a disciplined factorized causal framework rather than a novel Game essence',
  epistemicBoundary:
    'the audit validates research bookkeeping and prediction coverage; causal claims come from the admitted primary studies or explicit structural analysis, not from this script itself',
};

console.log(JSON.stringify(output, null, 2));
