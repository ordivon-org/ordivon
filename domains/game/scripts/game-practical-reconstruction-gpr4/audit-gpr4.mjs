#!/usr/bin/env node
import fs from 'node:fs';
const matrix=JSON.parse(fs.readFileSync(process.argv[2]??'evidence/game-practical-reconstruction-gpr4/enforcement-remedy-contracts.json','utf8'));
const probes=JSON.parse(fs.readFileSync(process.argv[3]??'evidence/game-practical-reconstruction-gpr4/enforcement-remedy-probes.json','utf8'));
const c=matrix.contracts;
const checks={
  foundationsFrozen:Object.values(matrix.foundationStatus).slice(0,4).every(x=>x==='FROZEN') && matrix.foundationStatus.reopenTriggered===false,
  sevenContracts:Object.keys(c).length===7,
  directiveConditional:c.ConsequenceDirectiveRecord.status==='STABILIZE_CONDITIONAL_SOURCE_WORKFLOW',
  directiveAdmissionBoundary:c.ConsequenceDirectiveRecord.admissionRule.includes('independent workflow identity'),
  attemptConditional:c.EnforcementAttemptRecord.status==='STABILIZE_CONDITIONAL_EXECUTION_LINK_RECORD',
  attemptNoDuplicateExecutor:c.EnforcementAttemptRecord.resultDerivation.includes('ordinary dispatch/action/World/observation/verification'),
  enforcementDerived:c.EnforcementStatusView.status==='STABILIZE_DERIVED_WORKFLOW_VIEW',
  partialState:c.EnforcementStatusView.states.includes('partially_realized'),
  realizationDerived:c.RealizedConsequenceView.status==='STABILIZE_DERIVED_WORLD_EFFECT_COMPARISON',
  worldTruthGuard:c.RealizedConsequenceView.laws.some(x=>x.includes('World history/effects remain source truth')),
  remedyConditional:c.RemedyPlanRecord.status==='STABILIZE_CONDITIONAL_CORRECTIVE_WORKFLOW',
  remedyNotRollback:c.RemedyPlanRecord.laws.includes('RemedyPlan != Rollback'),
  remedyCanCompensate:c.RemedyPlanRecord.laws.some(x=>x.includes('compensatory')),
  remedyStatusDerived:c.RemedyStatusView.status==='STABILIZE_DERIVED_CORRECTIVE_STATUS_VIEW',
  substituteState:c.RemedyStatusView.states.includes('satisfied_by_substitute_or_compensation'),
  timelineDerived:c.EnforcementRemedyTimeline.status==='STABILIZE_DERIVED_AUDIT_TIMELINE',
  sixtyCases:matrix.stressCases.length>=60,
  nineEngineeringFindings:Object.keys(matrix.currentEngineeringAudit).length>=9,
  teamEffectSeparated:matrix.currentEngineeringAudit.TeamEffect.classification==='GENERIC_EXECUTION_EFFECT_PREPARATION_NOT_ENFORCEMENT_DIRECTIVE',
  dispatchSeparated:matrix.currentEngineeringAudit.TeamDispatch.classification==='GENERIC_EXECUTION_DISPATCH_NOT_ENFORCEMENT_ATTEMPT_BY_IDENTITY',
  observationReusable:matrix.currentEngineeringAudit.TeamObservation.classification==='GENERIC_REALIZED_EFFECT_EVIDENCE',
  rollbackSeparated:matrix.currentEngineeringAudit.StorageTransactionRollback.classification==='TECHNICAL_ATOMICITY_NOT_GAME_REMEDY',
  repairSeparated:matrix.currentEngineeringAudit.StationZeroRepairOperation.classification==='ORDINARY_GAMEPLAY_REPAIR_NOT_REMEDY',
  directConsumerNotProven:matrix.implementationDecision.currentDirectEnforcementConsumerNeed==='NOT_PROVEN',
  strongExecutionSubstrate:matrix.implementationDecision.existingReusableExecutionSubstrate==='STRONG',
  noBroadImplementation:matrix.implementationDecision.broadImplementationNow===false,
  gpr5Selected:matrix.nextRound.name.startsWith('GPR5'),
  probesPass:Object.values(probes.probes).every(x=>x===true),
  lawDetEnf:matrix.crossCuttingLaws.includes('AuthoritativeDetermination != Enforcement'),
  lawAttemptEffect:matrix.crossCuttingLaws.includes('EnforcementAttempt != RealizedWorldEffect'),
  lawFailed:matrix.crossCuttingLaws.includes('FailedEnforcement != InvalidDetermination'),
  lawRetry:matrix.crossCuttingLaws.includes('IdempotentRecovery != RepeatedEnforcementByIdentity'),
  lawOrdinary:matrix.crossCuttingLaws.includes('OrdinaryExecution != EnforcementByOperationName'),
  lawTechRollback:matrix.crossCuttingLaws.includes('TechnicalRollback != GameRemedyByIdentity'),
  lawRemedy:matrix.crossCuttingLaws.includes('Remedy != Rollback'),
  lawComp:matrix.crossCuttingLaws.includes('CompensationCanBeRemedyWithoutRestoration'),
  lawWorld:matrix.crossCuttingLaws.includes('WorldHistoryRemainsSourceOfRealizedEffectTruth')
};
if(Object.values(checks).some(x=>!x)) throw new Error(`GPR4 audit failed\n${JSON.stringify(checks,null,2)}`);
console.log(JSON.stringify({schemaVersion:1,kind:'ordivon.game.gpr4-audit',contractCount:Object.keys(c).length,stressCaseCount:matrix.stressCases.length,lawCount:matrix.crossCuttingLaws.length,probeCount:Object.keys(probes.probes).length,checkCount:Object.keys(checks).length,checks,decision:'GPR4 reconstructs enforcement as a conditional directive/attempt workflow layered over existing ordinary execution, with realized consequence and status kept derived from World/observation/verification. Remedy is a forward corrective plan/status workflow, never automatic rollback or history erasure. Current Game has strong reusable execution substrate but no proven generic enforcement/remedy consumer.'},null,2));
