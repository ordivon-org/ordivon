import fs from 'node:fs';

const data = JSON.parse(fs.readFileSync('evidence/game-post-gpr-domain-coverage-c2/evaluation-comparability-probes.json', 'utf8'));
const checks = [];
const check = (name, cond) => checks.push({name, pass:Boolean(cond)});

check('candidate-c2', data.candidate.includes('Evaluation / Comparability'));
check('gpr8-not-admitted', data.routeAdmission.gpr8 === false);
check('foundation-not-admitted', data.routeAdmission.newNumberedFoundation === false);
check('next-gpr-unknown', data.routeAdmission.nextGpr === 'UNKNOWN');
check('next-practical-unknown', data.routeAdmission.nextPracticalRoute === 'UNKNOWN');
check('next-foundation-unknown', data.routeAdmission.nextFoundation === 'UNKNOWN');
check('eight-candidate-deletions', data.candidateDeletion.length >= 8);
check('score-rejected', data.candidateDeletion.some(x => x.candidate === 'Score' && x.verdict.includes('REJECT')));
check('rating-rejected', data.candidateDeletion.some(x => x.candidate === 'Rating' && x.verdict.includes('REJECT')));
check('rank-rejected', data.candidateDeletion.some(x => x.candidate === 'Rank' && x.verdict.includes('REJECT')));
check('record-rejected', data.candidateDeletion.some(x => x.candidate === 'Record' && x.verdict.includes('REJECT')));
check('comparable-boolean-rejected', data.candidateDeletion.some(x => x.candidate === 'ComparableBoolean' && x.verdict.includes('REJECT')));
check('twelve-probes', data.probes.length >= 12);
check('fide-rank-falsifier', data.probes.some(x => x.id === 'C2-F1' && x.result.includes('RankByIdentity')));
check('rating-model-falsifier', data.probes.some(x => x.id === 'C2-F3' && x.result.includes('intrinsic skill truth')));
check('adaptive-condition-falsifier', data.probes.some(x => x.id === 'C2-F7' && x.result.includes('SamePerformanceConditions')));
check('open-ended-nonnecessity', data.probes.some(x => x.id === 'C2-F10' && x.result.includes('necessary Game condition')));
check('comparison-claim-survives-practically', data.residualPattern.status.includes('PRACTICAL_RESEARCH_PATTERN'));
check('comparison-claim-has-purpose', data.residualPattern.fields.includes('ComparisonPurposeOrQuestion'));
check('comparison-claim-has-conditions', data.residualPattern.fields.includes('ConditionPopulationVersionAssistanceScope'));
check('comparison-claim-has-provenance', data.residualPattern.fields.includes('CurrentnessAndProvenance'));
check('no-game-foundation-survives', data.foundationVerdict === 'NO_INDEPENDENT_GAME_FOUNDATION_RESPONSIBILITY_SURVIVES');
check('no-gpr-admission', data.practicalVerdict.includes('NO_GPR_ADMISSION'));
check('all-reopen-negative', Object.values(data.reopenAudit).every(v => v === 'NOT_TRIGGERED'));
check('classification-cross-cutting', data.finalClassification.startsWith('CROSS_CUTTING'));
check('classification-not-route-selected', data.finalClassification.includes('NOT_ROUTE_SELECTED'));

for (const c of checks) console.log(`${c.pass ? 'PASS' : 'FAIL'} ${c.name}`);
const failed = checks.filter(c => !c.pass);
console.log(`SUMMARY ${checks.length - failed.length}/${checks.length} passed`);
if (failed.length) process.exit(1);
