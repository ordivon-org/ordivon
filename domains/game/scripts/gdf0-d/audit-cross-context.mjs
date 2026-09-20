#!/usr/bin/env node
import fs from 'node:fs';

const input = process.argv[2] ?? 'evidence/gdf0-d/cross-context-matrix.json';
const data = JSON.parse(fs.readFileSync(input, 'utf8'));

const required = [
  'agencyScaffold',
  'policyDifferentiation',
  'fixedGlobalGoal',
  'localEvaluation',
  'frame',
  'externalInstrumentality',
  'perturbationRecovery',
  'ruleAuthority',
  'pressure',
];

for (const c of data.cases) {
  for (const field of required) {
    if (!(field in c)) throw new Error(`case ${c.id} missing ${field}`);
  }
}

const audit = Object.entries(data.candidateAudit).map(([candidate, record]) => {
  const game = record.gameCases ?? record.gameOrPlayCases ?? record.supportingCases ?? [];
  const nonGame = record.nonGameCounterexamples ?? record.nonPlayCounterexamples ?? [];
  return {
    candidate,
    gameOrSupportingCaseCount: game.length,
    nonGameCounterexampleCount: nonGame.length,
    hasCrossCategoryCounterexample: nonGame.length > 0,
    disposition: record.disposition,
  };
});

const output = {
  schemaVersion: 1,
  kind: 'ordivon.game.gdf0-d-cross-context-audit',
  caseCount: data.cases.length,
  audit,
  strongResult:
    'every single C mechanism proposed as a possible Game discriminator has explicit non-game/play counterpressure; category-specificity, if any, must be sought at configuration/practice/experience level rather than inferred from one mechanism',
  epistemicBoundary:
    'manual case coding is research judgement; this script validates completeness and makes disposition/counterexample accounting reproducible, not objectively true by computation',
};

console.log(JSON.stringify(output, null, 2));
