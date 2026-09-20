#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const channels = [
  'observe','proposeGameAction','executeGameAction','advise','evaluate','adjudicate','verifyHistory',
  'enforce','generateWorldContent','modifyRules','modifyContent','allocateAccess','adaptGame'
];

const profile = (name, enabled, finalAuthority = []) => ({
  name,
  channels: Object.fromEntries(channels.map((x) => [x, enabled.includes(x)])),
  finalAuthority: Object.fromEntries(channels.map((x) => [x, finalAuthority.includes(x)]))
});

const roles = {
  passiveSpectator: profile('passiveSpectator', ['observe']),
  audienceParticipant: profile('audienceParticipant', ['observe','proposeGameAction']),
  player: profile('player', ['observe','proposeGameAction','executeGameAction'], ['executeGameAction']),
  coach: profile('coach', ['observe','advise']),
  referee: profile('referee', ['observe','evaluate','adjudicate','enforce','verifyHistory'], ['adjudicate']),
  var: profile('VAR', ['observe','evaluate','verifyHistory']),
  gm: profile('gameMaster', ['observe','evaluate','adjudicate','generateWorldContent','modifyContent','executeGameAction'], ['adjudicate','generateWorldContent']),
  moderator: profile('moderator', ['observe','evaluate','enforce','allocateAccess'], ['enforce','allocateAccess']),
  director: profile('experienceManagerDirector', ['observe','evaluate','modifyContent','adaptGame'], ['adaptGame']),
  fusedAgent: profile('fusedPlayerJudgeAgent', ['observe','proposeGameAction','executeGameAction','evaluate','adjudicate'], ['executeGameAction','adjudicate'])
};

const count = (role) => Object.values(role.channels).filter(Boolean).length;
const differs = (a,b,key) => a.channels[key] !== b.channels[key] || a.finalAuthority[key] !== b.finalAuthority[key];

const spectatorToAudience = {
  sameEntity: true,
  before: roles.passiveSpectator.name,
  after: roles.audienceParticipant.name,
  observationHeldFixed: true,
  proposalAuthorityChanged: differs(roles.passiveSpectator, roles.audienceParticipant, 'proposeGameAction')
};

const spectatorVsReferee = {
  sameObservationEvidencePossible: true,
  spectatorFinalRuling: roles.passiveSpectator.finalAuthority.adjudicate,
  refereeFinalRuling: roles.referee.finalAuthority.adjudicate,
  authorityDifferenceSurvives: differs(roles.passiveSpectator, roles.referee, 'adjudicate')
};

const refereeVsVar = {
  bothObserve: roles.referee.channels.observe && roles.var.channels.observe,
  bothCanEvaluate: roles.referee.channels.evaluate && roles.var.channels.evaluate,
  varFinalRuling: roles.var.finalAuthority.adjudicate,
  refereeFinalRuling: roles.referee.finalAuthority.adjudicate,
  evidenceAndFinalRulingSeparated: roles.var.channels.verifyHistory && !roles.var.finalAuthority.adjudicate && roles.referee.finalAuthority.adjudicate
};

const gmBundle = {
  functionCount: count(roles.gm),
  combinesWorldGenerationAndAdjudication: roles.gm.channels.generateWorldContent && roles.gm.channels.adjudicate,
  combinesNpcLikeActionAndConstitutiveAuthority: roles.gm.channels.executeGameAction && roles.gm.finalAuthority.adjudicate,
  namedRoleNotAtomicFunction: count(roles.gm) >= 5
};

const coachIndirect = {
  canAdvise: roles.coach.channels.advise,
  cannotExecuteGameActionByProfile: !roles.coach.channels.executeGameAction,
  causalInfluenceNeedNotBeDirectGameAction: roles.coach.channels.advise && !roles.coach.channels.executeGameAction
};

const directorBoundary = {
  changesRunningGame: roles.director.channels.adaptGame,
  noPlayerGameActionByProfile: !roles.director.channels.executeGameAction,
  causalGameComponentNeedNotBePlayer: roles.director.channels.adaptGame && !roles.director.channels.executeGameAction
};

const fusedRoleConflict = {
  sameEntityCanHoldPlayerAndJudgeChannels: roles.fusedAgent.channels.executeGameAction && roles.fusedAgent.channels.adjudicate,
  authorityCompositionVisible: roles.fusedAgent.finalAuthority.executeGameAction && roles.fusedAgent.finalAuthority.adjudicate,
  entityIdentityInsufficientToInferRoleSeparation: true
};

const collectiveAudience = {
  members: 100,
  memberVotes: 100,
  aggregationRule: 'majority-to-candidate-action',
  requiresCollectiveSubject: false,
  representableAsMultiEntityContributionPlusAggregation: true
};

const roleAssignmentChange = {
  entityId: 'E1',
  time0Role: 'passiveSpectator',
  time1Role: 'audienceParticipant',
  entityIdentityChanged: false,
  roleAssignmentChanged: true,
  newCausalChannelWithoutIdentityBreak: spectatorToAudience.proposalAuthorityChanged
};

const actionVsAdjudication = {
  playerActionContractStillDistinct: true,
  adjudicatorMayClassifyOrRuleOnCandidateOrEvent: true,
  adjudicationIsNotThePlayerGameActionByIdentity: true
};

const result = {
  schemaVersion: 1,
  kind: 'ordivon.game.gdf3-a-participation-role-probes',
  epistemicBoundary: {
    proves: [
      'within the constructed profiles, observation, action, advice, adjudication, verification, governance and adaptive-game channels can dissociate',
      'the same Entity can change Game-relative role/channels without identity change',
      'a named GM role can bundle several separable functions',
      'evidence/recommendation can be separated from final ruling authority',
      'causal influence on Game/player policy need not be direct GameAction authority',
      'a game-adapting system function need not be modeled as a Player',
      'collective audience control can be represented without postulating one collective Subject',
      'one Entity can hold player and adjudicator authority simultaneously, making role/authority composition explicit'
    ],
    doesNotProve: [
      'a universal taxonomy of all game participation roles',
      'that every spectator is a participant in every scope',
      'that Player has one culturally universal definition',
      'that adjudication requires a new semantic primitive',
      'human subjective play experience',
      'that the proposed channel set is complete'
    ]
  },
  roles,
  cases: { spectatorToAudience, spectatorVsReferee, refereeVsVar, gmBundle, coachIndirect, directorBoundary, fusedRoleConflict, collectiveAudience, roleAssignmentChange, actionVsAdjudication },
  strongestFalsifiers: {
    participantCannotBeEntityKind: roleAssignmentChange.roleAssignmentChanged && !roleAssignmentChange.entityIdentityChanged,
    spectatorNotCausallyIrrelevantByIdentity: spectatorToAudience.proposalAuthorityChanged,
    observationDoesNotDetermineRole: spectatorVsReferee.authorityDifferenceSurvives,
    adjudicationAuthorityNotObservationOrEvidenceAlone: refereeVsVar.evidenceAndFinalRulingSeparated,
    namedRoleNotAtomicFunction: gmBundle.namedRoleNotAtomicFunction,
    causalInfluenceNotDirectActionIdentity: coachIndirect.causalInfluenceNeedNotBeDirectGameAction,
    causalSystemComponentNotPlayerIdentity: directorBoundary.causalGameComponentNeedNotBePlayer,
    entityIdentityNotEnoughForRoleConflict: fusedRoleConflict.sameEntityCanHoldPlayerAndJudgeChannels,
    audienceDoesNotRequireCollectiveSubject: collectiveAudience.representableAsMultiEntityContributionPlusAggregation && !collectiveAudience.requiresCollectiveSubject
  }
};

const output = process.argv[2] ?? 'evidence/gdf3-a/participation-role-probes.json';
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
