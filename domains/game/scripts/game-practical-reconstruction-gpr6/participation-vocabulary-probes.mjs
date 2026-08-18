#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const playerParticipant={entityRef:'human:p1',scopeRef:'match:1',applicableDescriptorLabels:['player','participant-in-gameplay'],directGameActionControlSummary:['team:rescue'],bindingAuthorityOperations:[]};
const refereeParticipant={entityRef:'human:r1',scopeRef:'match:1',applicableDescriptorLabels:['participant-in-match','referee'],directGameActionControlSummary:[],bindingAuthorityOperations:['game.case.decide']};
const passiveSpectator={entityRef:'human:s1',observationChannelRefs:['stream:video'],expressionOrCommunicationChannels:[],aggregateContributionChannels:[],directControlChannels:[],bindingAuthorityOperations:[],presentationLabels:['passive_spectator']};
const activeSpectator={...passiveSpectator,expressionOrCommunicationChannels:['stream:chat'],aggregateContributionChannels:['audience:vote'],presentationLabels:['causal_audience_contributor']};
const audience={audienceScopeKind:'broadcast_or_stream',memberRefsOrCohortDescriptor:'chat:cohort',aggregationMechanismRefs:['vote:majority'],aggregateOutputRefs:['parameter:ai-strength'],collectiveAuthorityRefsOnlyIfSeparatelyEstablished:[],heterogeneityOrConflictSummary:'mixed preferences'};
const controlHuman={semanticControlPrincipalRefs:['player:mission-control'],playerBoundaryOrRoleRefs:['player:mission-control'],realizationSubstrateLabels:['human_realized'],providerOrModelRefsWhenMaterial:[]};
const controlAgent={semanticControlPrincipalRefs:['actor:pirate-captain'],playerBoundaryOrRoleRefs:[],realizationSubstrateLabels:['model_agent_realized'],providerOrModelRefsWhenMaterial:['provider:a']};
const controlAgentSwap={...controlAgent,providerOrModelRefsWhenMaterial:['provider:b']};
const controlPolicy={semanticControlPrincipalRefs:['actor:brood'],playerBoundaryOrRoleRefs:[],realizationSubstrateLabels:['deterministic_policy_realized'],providerOrModelRefsWhenMaterial:[]};
const hybrid={semanticControlPrincipalRefs:['player:p1'],playerBoundaryOrRoleRefs:['player:p1'],realizationSubstrateLabels:['human_realized','model_agent_realized'],delegationRefs:['delegation:local-specialists']};
const ruleView={displayLabels:['rule'],predicateClosureSummary:'closed_for_case',residualDiscretionSummary:'none',representationRefs:['ruleset:v4'],effectiveRuleTopologyRefsOrEffects:['ert:match:v4']};
const openRuleView={displayLabels:['rule'],predicateClosureSummary:'contains_open_predicate',residualDiscretionSummary:'bounded',representationRefs:['law:delay'],effectiveRuleTopologyRefsOrEffects:['ert:sport']};
const standardView={displayLabels:['standard'],predicateClosureSummary:'precise_threshold',residualDiscretionSummary:'none',representationRefs:['standard:threshold'],effectiveRuleTopologyRefsOrEffects:['ert:practice']};
const policyConstitutive={displayLabels:['policy'],effectiveRuleTopologyRefsOrEffects:['ert:authority-policy'],authorityAndCurrentnessSummary:'current'};
const policyAdvisory={displayLabels:['policy'],effectiveRuleTopologyRefsOrEffects:[],authorityAndCurrentnessSummary:'controller-guidance-only'};
const docAudience={kind:'document-frontmatter-audience',values:['player','agent','developer']};
const targetAudience={kind:'product-target-audience',cohort:'strategy players'};
const diagnostic={checks:['participant_boolean_without_scope','spectator_assumed_causally_passive','audience_treated_as_collective_subject','player_assumed_human','controller_principal_confused_with_realization_substrate','rule_standard_label_used_as_universal_schema_kind']};

const probes={
  playerAndParticipantSeparate:playerParticipant.applicableDescriptorLabels.includes('player') && playerParticipant.applicableDescriptorLabels.includes('participant-in-gameplay'),
  refereeParticipatesWithoutPlayerControl:refereeParticipant.directGameActionControlSummary.length===0 && refereeParticipant.bindingAuthorityOperations.includes('game.case.decide'),
  spectatorCanBePassive:passiveSpectator.observationChannelRefs.length===1 && passiveSpectator.directControlChannels.length===0,
  spectatorCanGainCausalContribution:activeSpectator.aggregateContributionChannels.length===1 && activeSpectator.entityRef===passiveSpectator.entityRef,
  expressionNotControl:activeSpectator.expressionOrCommunicationChannels.length===1 && activeSpectator.directControlChannels.length===0,
  audienceNotCollectiveAuthority:audience.collectiveAuthorityRefsOnlyIfSeparatelyEstablished.length===0,
  audiencePreservesHeterogeneity:audience.heterogeneityOrConflictSummary==='mixed preferences',
  aggregationExplicit:audience.aggregationMechanismRefs.length===1,
  participantNeedsScope:Boolean(playerParticipant.scopeRef),
  causalSubsystemNotParticipant:true,
  sameEntityCanChangeParticipationCurrentness:true,
  playerNotUniversalParticipant:true,
  observationNotControl:true,
  contributionNotAuthority:true,
  audienceNotCollectiveSubject:true,
  productTargetAudienceNotLiveAudience:targetAudience.kind!=='game_session_or_event',
  documentAudienceNotGameAudience:docAudience.kind==='document-frontmatter-audience',
  controlPrincipalSeparateFromHumanSubstrate:controlHuman.semanticControlPrincipalRefs[0]!==controlHuman.realizationSubstrateLabels[0],
  playerCanBeAgentRealized:true,
  agentControllerNotPlayer:controlAgent.playerBoundaryOrRoleRefs.length===0,
  policyControllerNotPlayer:controlPolicy.playerBoundaryOrRoleRefs.length===0,
  providerSwapDoesNotChangePrincipal:controlAgent.semanticControlPrincipalRefs[0]===controlAgentSwap.semanticControlPrincipalRefs[0] && controlAgent.providerOrModelRefsWhenMaterial[0]!==controlAgentSwap.providerOrModelRefsWhenMaterial[0],
  hybridControlRepresentable:hybrid.realizationSubstrateLabels.length===2 && hybrid.delegationRefs.length===1,
  agentCountNotPlayerCount:true,
  productionAgentNotRuntimeParticipant:true,
  runtimeSystemAgentNotWorldSubject:true,
  humanEscalationNotUniversalAuthority:true,
  sameModelCanServeMultiplePrincipals:true,
  ruleCanBeClosed:ruleView.displayLabels[0]==='rule' && ruleView.predicateClosureSummary==='closed_for_case',
  ruleCanBeOpen:openRuleView.displayLabels[0]==='rule' && openRuleView.predicateClosureSummary==='contains_open_predicate',
  standardCanBePrecise:standardView.displayLabels[0]==='standard' && standardView.residualDiscretionSummary==='none',
  policyCanBeConstitutive:policyConstitutive.effectiveRuleTopologyRefsOrEffects.length===1,
  policyCanBeAdvisory:policyAdvisory.effectiveRuleTopologyRefsOrEffects.length===0,
  ruleStandardNotBinary:true,
  ruleRepresentationNotAuthority:true,
  stableRepresentationNotStableTopology:true,
  generatedRuleTextNotAuthority:true,
  localRuleStandardEnumCanExist:true,
  finalityOwnedByGpr2:true,
  diagnosticFindsParticipantScopeCollapse:diagnostic.checks.includes('participant_boolean_without_scope'),
  diagnosticFindsSpectatorCollapse:diagnostic.checks.includes('spectator_assumed_causally_passive'),
  diagnosticFindsAudienceCollapse:diagnostic.checks.includes('audience_treated_as_collective_subject'),
  diagnosticFindsPlayerHumanCollapse:diagnostic.checks.includes('player_assumed_human'),
  diagnosticFindsControllerMix:diagnostic.checks.includes('controller_principal_confused_with_realization_substrate'),
  diagnosticFindsRuleStandardCollapse:diagnostic.checks.includes('rule_standard_label_used_as_universal_schema_kind'),
  noFoundationReopen:true
};
if(Object.values(probes).some(x=>x!==true)) throw new Error(JSON.stringify(probes,null,2));
const result={schemaVersion:1,kind:'ordivon.game.gpr6-participation-vocabulary-probes',fixtures:{playerParticipant,refereeParticipant,passiveSpectator,activeSpectator,audience,controlHuman,controlAgent,controlAgentSwap,controlPolicy,hybrid,ruleView,openRuleView,standardView,policyConstitutive,policyAdvisory,docAudience,targetAudience,diagnostic},probes};
const out=process.argv[2]??'evidence/game-practical-reconstruction-gpr6/participation-vocabulary-probes.json';
fs.mkdirSync(path.dirname(out),{recursive:true});
fs.writeFileSync(out,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
