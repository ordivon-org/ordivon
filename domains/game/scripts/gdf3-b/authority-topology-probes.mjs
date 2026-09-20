#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const grant = ({holder, operation, scope, binding=false, condition='true', source='practice', valid='current'}) => ({holder, operation, scope, binding, condition, source, valid});

const cases = {
  ifabVar: {
    varGrant: grant({holder:'VAR', operation:'recommend_review', scope:'match:reviewable-incidents', binding:false, source:'IFAB'}),
    refereeGrant: grant({holder:'Referee', operation:'decide_case', scope:'match', binding:true, source:'IFAB'})
  },
  ifabReplacement: {
    before: grant({holder:'Referee-A', operation:'decide_case', scope:'match', binding:true, condition:'not-incapacitated', source:'competition-rules'}),
    after: grant({holder:'Replacement-Official', operation:'decide_case', scope:'match', binding:true, condition:'Referee-A-incapacitated && designated-replacement', source:'competition-rules'})
  },
  magicAppeal: {
    floor: grant({holder:'FloorJudge', operation:'first_instance_ruling', scope:'tournament:case', binding:true, source:'MTR'}),
    head: grant({holder:'HeadJudge', operation:'review_override', scope:'tournament:appeal', binding:true, source:'MTR'})
  },
  magicAppointment: {
    adjudicate: grant({holder:'HeadJudge', operation:'decide_case', scope:'tournament', binding:true, source:'MTR'}),
    replace: grant({holder:'TournamentOrganizer', operation:'replace_head_judge', scope:'tournament:exceptional-circumstances', binding:true, source:'MTR'})
  },
  coach: {
    advise: grant({holder:'Coach', operation:'advise_player', scope:'match', binding:false, condition:'coaching-allowed', source:'competition-rules'}),
    player: grant({holder:'Player', operation:'execute_game_action', scope:'player-slot', binding:true, source:'game-practice'})
  },
  audience: {
    member: grant({holder:'AudienceMember', operation:'submit_vote', scope:'audience-channel', binding:false, source:'APG-rules'}),
    aggregator: grant({holder:'AggregationRule', operation:'admit_aggregate_effect', scope:'game-parameter', binding:true, source:'APG-rules'})
  },
  director: {
    manager: grant({holder:'ExperienceManager', operation:'adapt_game', scope:'authorized-dynamics', binding:true, source:'designer-policy'}),
    player: grant({holder:'Player', operation:'execute_game_action', scope:'player-action-space', binding:true, source:'game-rules'})
  },
  fusedAgent: {
    player: grant({holder:'Agent-X', operation:'execute_game_action', scope:'player-slot', binding:true}),
    judge: grant({holder:'Agent-X', operation:'decide_case', scope:'action-legality', binding:true})
  }
};

const sameHolderDifferentAuthority = cases.fusedAgent.player.holder === cases.fusedAgent.judge.holder && cases.fusedAgent.player.operation !== cases.fusedAgent.judge.operation;
const recommendationNotFinal = !cases.ifabVar.varGrant.binding && cases.ifabVar.refereeGrant.binding;
const replacementIsConditionalCurrentness = cases.ifabReplacement.before.condition !== cases.ifabReplacement.after.condition && cases.ifabReplacement.before.operation === cases.ifabReplacement.after.operation;
const reviewNotFirstInstance = cases.magicAppeal.floor.operation !== cases.magicAppeal.head.operation && cases.magicAppeal.head.operation === 'review_override';
const appointmentNotAdjudication = cases.magicAppointment.adjudicate.operation !== cases.magicAppointment.replace.operation;
const adviceNotActionAuthority = !cases.coach.advise.binding && cases.coach.player.binding && cases.coach.advise.operation !== cases.coach.player.operation;
const aggregationLocatesBindingAtRule = !cases.audience.member.binding && cases.audience.aggregator.binding;
const adaptiveAuthorityNotPlayerAuthority = cases.director.manager.operation !== cases.director.player.operation;

const multipleFinalAuthorities = [
  grant({holder:'HeadJudge-A', operation:'decide_case', scope:'flight-A', binding:true, source:'MTR'}),
  grant({holder:'HeadJudge-B', operation:'decide_case', scope:'flight-B', binding:true, source:'MTR'})
];
const noGlobalMaximumRequired = multipleFinalAuthorities.every((x) => x.binding) && new Set(multipleFinalAuthorities.map((x) => x.scope)).size === 2;

const timedReview = {
  beforeRestart: grant({holder:'Referee', operation:'revise_decision', scope:'incident', binding:true, condition:'review-permitted-before-cutoff', source:'IFAB'}),
  afterRestart: grant({holder:'Referee', operation:'revise_decision', scope:'incident', binding:true, condition:'normally-not-permitted-after-restart-except-specified-cases', source:'IFAB'})
};
const authorityNeedsConditionAndTime = timedReview.beforeRestart.condition !== timedReview.afterRestart.condition;

const ruleVsCase = {
  ruleAuthor: grant({holder:'RulesAuthority', operation:'change_general_rule', scope:'ruleset-version', binding:true}),
  adjudicator: grant({holder:'CaseJudge', operation:'decide_case', scope:'instance-case', binding:true})
};
const ruleAuthorityNotCaseAuthority = ruleVsCase.ruleAuthor.operation !== ruleVsCase.adjudicator.operation && ruleVsCase.ruleAuthor.scope !== ruleVsCase.adjudicator.scope;

const rulingVsEnforcement = {
  ruling: grant({holder:'Judge', operation:'decide_case', scope:'case', binding:true}),
  enforcement: grant({holder:'ScorekeeperOrSystem', operation:'apply_record_or_sanction', scope:'official-record', binding:true})
};
const rulingNotEnforcement = rulingVsEnforcement.ruling.operation !== rulingVsEnforcement.enforcement.operation;

const postHocVerification = {
  originalHistoryDigest:'H1',
  certificationBefore:null,
  certificationAfter:'VALID_RECORD',
  originalHistoryChanged:false
};
const verificationNotWorldHistoryRewrite = postHocVerification.certificationBefore !== postHocVerification.certificationAfter && !postHocVerification.originalHistoryChanged;

const result = {
  schemaVersion:1,
  kind:'ordivon.game.gdf3-b-authority-topology-probes',
  epistemicBoundary:{
    proves:[
      'the constructed authority cases can be represented using scoped typed grants rather than role identity or a global authority scalar',
      'recommendation/evidence, first-instance ruling, review/override, appointment/replacement, advice, player action and game adaptation can be separated by operation and scope',
      'binding authority can move between occupants through condition/currentness without changing role ontology',
      'multiple equally binding authorities can coexist on disjoint scopes without a single global maximum',
      'aggregation can bind at the aggregation/admission rule while individual contributions remain nonbinding',
      'one entity can hold multiple authority grants, making conflict constraints separable from identity',
      'post-hoc certification can change practice-record validity without changing original game history'
    ],
    doesNotProve:[
      'that the tested operation vocabulary is exhaustive',
      'that every authority system should use explicit Role objects',
      'that adjudication is fully explained by this topology',
      'that social legitimacy equals formal authority',
      'that co-located authority is always undesirable',
      'that a new semantic primitive is required'
    ]
  },
  cases,
  multipleFinalAuthorities,
  timedReview,
  ruleVsCase,
  rulingVsEnforcement,
  postHocVerification,
  strongestFalsifiers:{
    finalAuthorityNotGlobalScalar: noGlobalMaximumRequired,
    recommendationNotFinalAuthority: recommendationNotFinal,
    roleOccupantCanChangeByCondition: replacementIsConditionalCurrentness,
    reviewAuthorityNotFirstInstanceAuthority: reviewNotFirstInstance,
    appointmentAuthorityNotAdjudicationAuthority: appointmentNotAdjudication,
    adviceNotActionAuthority: adviceNotActionAuthority,
    aggregateEffectNotMemberAuthority: aggregationLocatesBindingAtRule,
    adaptiveGameAuthorityNotPlayerAuthority: adaptiveAuthorityNotPlayerAuthority,
    entityIdentityNotAuthorityIdentity: sameHolderDifferentAuthority,
    authorityRequiresScopeConditionCurrentness: authorityNeedsConditionAndTime,
    ruleChangeAuthorityNotCaseRulingAuthority: ruleAuthorityNotCaseAuthority,
    rulingNotEnforcement: rulingNotEnforcement,
    verificationNotWorldHistoryRewrite: verificationNotWorldHistoryRewrite
  }
};

const output = process.argv[2] ?? 'evidence/gdf3-b/authority-topology-probes.json';
fs.mkdirSync(path.dirname(output), {recursive:true});
fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
