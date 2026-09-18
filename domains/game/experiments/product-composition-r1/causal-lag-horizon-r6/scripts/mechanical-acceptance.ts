import {createHash} from 'node:crypto';
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

// @ts-expect-error Browser-compatible JS module intentionally has no declaration file.
import {FIRST_PRESSURE_RUN} from '../../causal-lag-pressure-r5/pressure-topology.js';
// @ts-expect-error Browser-compatible JS module intentionally has no declaration file.
import {STABLE_HORIZON_WITNESS,VOLATILE_HORIZON_WITNESS,analyzePressureCompositionSaturation,solveHorizonPolicy,solveMyopicPolicy} from '../horizon-policy.js';

const here=dirname(fileURLToPath(import.meta.url));
const root=resolve(here,'..');
const designPath=resolve(root,'../pc01-causal-works-f0/design.json');
const designBytes=readFileSync(designPath);
const design=JSON.parse(designBytes.toString('utf8'));
const sha256=(bytes:Buffer|string)=>'sha256:'+createHash('sha256').update(bytes).digest('hex');

const saturation=analyzePressureCompositionSaturation(design,{maxSequenceLength:5});
const volatileMyopic=solveMyopicPolicy(design,VOLATILE_HORIZON_WITNESS);
const volatile155=solveHorizonPolicy(design,{...VOLATILE_HORIZON_WITNESS,remainingTarget:155});
const volatile160=solveHorizonPolicy(design,{...VOLATILE_HORIZON_WITNESS,remainingTarget:160});
const stable185=solveHorizonPolicy(design,{...STABLE_HORIZON_WITNESS,remainingTarget:185});
const stable190=solveHorizonPolicy(design,{...STABLE_HORIZON_WITNESS,remainingTarget:190});

type Unit={
  sourceCycleIndex:number;
  executionCycleIndex:number;
  pressureProfileId:string;
};

const r5Units=(FIRST_PRESSURE_RUN.units as Unit[]).map(unit=>({
  sourceCycleIndex:unit.sourceCycleIndex,
  executionCycleIndex:unit.executionCycleIndex,
  pressureProfileId:unit.pressureProfileId,
}));

let targetSensitiveWindowStates=0;
let adjacentTargetPolicyTransitions=0;
const sensitiveStates=[] as Array<{
  horizon:number;
  startBeat:number;
  persistence:number;
  previousArchitecture:string;
  transitionCount:number;
}>;

for(const horizon of [2,3]){
  for(let start=0;start<=r5Units.length-horizon;start++){
    const units=r5Units.slice(start,start+horizon);
    for(const persistence of [0.2,0.9]){
      for(const previousArchitecture of design.architectureModes as string[]){
        let previousPolicy='';
        let transitionCount=0;
        for(let remainingTarget=40;remainingTarget<=horizon*100;remainingTarget+=5){
          const result=solveHorizonPolicy(design,{
            units,
            persistence,
            previousArchitecture,
            remainingTarget,
          });
          const currentPolicy=JSON.stringify(result.firstPolicy);
          if(previousPolicy&&currentPolicy!==previousPolicy){
            adjacentTargetPolicyTransitions+=1;
            transitionCount+=1;
          }
          previousPolicy=currentPolicy;
        }
        if(transitionCount>0){
          targetSensitiveWindowStates+=1;
          sensitiveStates.push({
            horizon,
            startBeat:start+1,
            persistence,
            previousArchitecture,
            transitionCount,
          });
        }
      }
    }
  }
}

const pass=
  saturation.localUnitCount===27 &&
  saturation.localEquivalenceClasses===20 &&
  saturation.redundantLocalUnits===7 &&
  saturation.saturationEstablished===false &&
  saturation.sequenceSaturation.length===5 &&
  saturation.sequenceSaturation.every((row:any)=>Math.abs(row.uniqueFraction-20/27)<1e-15) &&
  targetSensitiveWindowStates===96 &&
  adjacentTargetPolicyTransitions===625 &&
  volatileMyopic.expectedImmediateNet===78.8 &&
  volatile155.successProbability===0.68704 &&
  volatile160.successProbability===0.636 &&
  JSON.stringify(volatile155.firstPolicy)!==JSON.stringify(volatile160.firstPolicy) &&
  volatile155.firstPolicyImmediateExpectedNet<volatileMyopic.expectedImmediateNet &&
  stable185.successProbability===0.70846 &&
  stable190.successProbability===0.549 &&
  JSON.stringify(stable185.firstPolicy)!==JSON.stringify(stable190.firstPolicy);

const out={
  schemaVersion:1,
  kind:'ordivon.game.causal-lag-horizon-r6-mechanical-acceptance',
  designId:design.id,
  designDigest:sha256(designBytes),
  parentR5EvidenceDigest:'sha256:194486746b494487c899ed11607d283a7241d9a39ba83a011031fa4ad5592a37',
  sourceBaseRevision:'bb742432e1ac9b73a259492e0020757fe7e04793',
  methodSnapshot:{
    ordivonNextRevision:'2231438e8f293742c1f5f1a2622b3e567003f5e0',
    authority:'ANALYSIS_METHOD_PROVENANCE_ONLY',
  },
  lensRouting:{
    target:'Choose between composition saturation and horizon-aware contract planning.',
    selectedLegoLens:'lego-ck-design',
    domainMethods:[
      'exact-combinatorial-enumeration',
      'finite-horizon-dynamic-programming',
    ],
    rejectedOrDeferred:[
      {
        lens:'lego-exploration-policy',
        reason:'deterministic exhaustive search remains cheaper and exactly attributable',
      },
      {
        lens:'lego-feedback-control',
        reason:'no new durable controller/runtime responsibility is required by this oracle-only slice',
      },
      {
        lens:'lego-information-flow',
        reason:'oracle privacy remains an existing evidence boundary; no new information-flow architecture decision is introduced',
      },
    ],
    routingStanding:'DOMAIN_METHOD_PLUS_ONE_GENERATIVE_LENS',
  },
  branchCompetition:{
    saturation,
    horizon:{
      testedHorizons:[2,3],
      persistences:[0.2,0.9],
      previousArchitectures:[...design.architectureModes],
      targetGrid:{
        minimum:40,
        step:5,
        maximumRule:'100 × horizon',
      },
      targetSensitiveWindowStates,
      adjacentTargetPolicyTransitions,
      sensitiveStates,
      horizonRelationEstablished:true,
      interpretation:'REMAINING_CONTRACT_TARGET_CAN_CHANGE_CURRENT_POLICY_UNDER_FIXED_LOCAL_STATE',
    },
    selectedBranch:'HORIZON_AWARE_CONTRACT_PLANNING',
    saturationBranchStanding:'DEFER_NEW_AXIS_FROM_SATURATION',
  },
  volatileWitness:{
    definition:VOLATILE_HORIZON_WITNESS,
    myopic:volatileMyopic,
    target155:volatile155,
    target160:volatile160,
    interpretation:'LOCALLY_LOWER_IMMEDIATE_EV_INFORMATION_CAN_INCREASE_CONTRACT_SUCCESS_PROBABILITY',
  },
  stableWitness:{
    definition:STABLE_HORIZON_WITNESS,
    target185:stable185,
    target190:stable190,
    interpretation:'TARGET_SENSITIVITY_IS_NOT_LIMITED_TO_THE_VOLATILE_REGIME',
  },
  browserCarrierCreated:false,
  browserCarrierReason:'The exact oracle consumes persistence probabilities and success-model information that are not player observations; a browser carrier would risk confusing falsification truth with player-visible game state.',
  runtimeKernelChanged:false,
  projectNodeAdded:false,
  newPlayerVerbsAdded:0,
  pass,
  productSelected:false,
  g0Entered:false,
  humanOutcomeEstablished:false,
  gameCoreChanged:false,
  claimBoundary:'FINITE_HORIZON_MECHANICAL_POLICY_SENSITIVITY_ONLY_NO_HUMAN_STRATEGY_OR_PRODUCT_VALUE_CLAIM',
};

const evidencePath=resolve(root,'evidence/mechanical-acceptance-r6.json');
mkdirSync(dirname(evidencePath),{recursive:true});
writeFileSync(evidencePath,JSON.stringify(out,null,2)+'\n');
process.stdout.write(JSON.stringify(out,null,2)+'\n');
if(!pass)process.exitCode=3;
