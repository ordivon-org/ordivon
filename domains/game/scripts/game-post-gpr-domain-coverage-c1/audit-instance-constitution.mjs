import fs from 'node:fs';

const path = 'evidence/game-post-gpr-domain-coverage-c1/instance-constitution-probes.json';
const data = JSON.parse(fs.readFileSync(path, 'utf8'));
const checks = [];
const check = (name, cond) => checks.push({ name, pass: Boolean(cond) });

check('candidate-is-c1-instance-constitution', data.candidate.includes('GameInstance Constitution'));
check('gpr8-not-admitted', data.routeAdmission.gpr8 === false);
check('new-numbered-foundation-not-admitted', data.routeAdmission.newNumberedFoundation === false);
check('next-gpr-unknown', data.routeAdmission.nextGpr === 'UNKNOWN');
check('next-practical-route-unknown', data.routeAdmission.nextPracticalRoute === 'UNKNOWN');
check('next-foundation-unknown', data.routeAdmission.nextFoundation === 'UNKNOWN');
check('all-four-gdfs-frozen', ['GDF0','GDF1','GDF2','GDF3'].every(k => data.frozenStatus[k] === 'FROZEN_NOT_REOPENED'));
check('candidate-deletion-broad', data.candidateDeletion.length >= 8);
check('twelve-cross-regime-probes', data.probes.length >= 12);
check('presence-collapse-rejected', data.candidateDeletion.some(x => x.candidate === 'Presence' && x.verdict.includes('REJECT')));
check('participant-set-collapse-rejected', data.candidateDeletion.some(x => x.candidate === 'ParticipantSet' && x.verdict.includes('REJECT')));
check('runtime-instance-collapse-rejected', data.candidateDeletion.some(x => x.candidate === 'RuntimeSession' && x.verdict.includes('REJECT')));
check('material-instance-collapse-rejected', data.candidateDeletion.some(x => x.candidate === 'MaterialContinuity' && x.verdict.includes('REJECT')));
check('survivor-not-admitted', data.survivingResponsibility.status === 'STRONG_FOUNDATION_UNCLOSED_CANDIDATE_NOT_ADMITTED');
check('three-surviving-obligations', data.survivingResponsibility.obligations.length === 3);
check('constitution-obligation', data.survivingResponsibility.obligations.some(x => x.name === 'ConstitutionBasisAndCurrentness'));
check('composition-obligation', data.survivingResponsibility.obligations.some(x => x.name === 'ParticipationCompositionAndTransition'));
check('continuity-obligation', data.survivingResponsibility.obligations.some(x => x.name === 'InstanceContinuityBoundary'));
check('ownership-game-present', Array.isArray(data.ownership.Game) && data.ownership.Game.length >= 3);
check('runtime-network-boundary-present', Array.isArray(data.ownership.RuntimeNetwork) && data.ownership.RuntimeNetwork.length >= 3);
check('all-reopen-audits-negative', Object.values(data.reopenAudit).every(v => v === 'NOT_TRIGGERED'));
check('final-classification-not-route-selection', data.finalClassification.includes('NOT_ROUTE_SELECTED'));

for (const c of checks) console.log(`${c.pass ? 'PASS' : 'FAIL'} ${c.name}`);
const failed = checks.filter(c => !c.pass);
console.log(`SUMMARY ${checks.length - failed.length}/${checks.length} passed`);
if (failed.length) process.exit(1);
