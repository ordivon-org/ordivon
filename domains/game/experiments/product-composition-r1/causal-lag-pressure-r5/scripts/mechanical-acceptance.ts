import {createHash} from 'node:crypto';
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

// @ts-expect-error Browser-compatible JS core intentionally has no declaration file.
import {commitRound,createSessionRun,nextRound,publicView,selectArchitecture} from '../../causal-lag-session-r3/web/core.js';
// @ts-expect-error Browser-compatible JS module intentionally has no declaration file.
import {FIRST_BREADTH_ARC,compileRunRecipe} from '../../causal-lag-content-r4/content-grammar.js';
// @ts-expect-error Browser-compatible JS module intentionally has no declaration file.
import {FIRST_PRESSURE_RUN,compilePressureRun} from '../pressure-topology.js';

const here=dirname(fileURLToPath(import.meta.url));
const root=resolve(here,'..');
const designPath=resolve(root,'../pc01-causal-works-f0/design.json');
const designBytes=readFileSync(designPath);
const design=JSON.parse(designBytes.toString('utf8'));
const sha256=(bytes:Buffer|string)=>'sha256:'+createHash('sha256').update(bytes).digest('hex');

const causes=design.hiddenCauseStates as string[];
const architectures=design.architectureModes as string[];
const diagnostics=design.diagnostics as string[];

function observation(diagnostic:string,cause:string){
  if(diagnostic==='none')return 'NONE';
  return diagnostic===cause?'FAULT':'OK';
}
function priorEntries(cycle:any){
  return Object.entries(cycle.causePrior).map(([cause,p])=>[cause,Number(p)] as const);
}
function executionDistribution(sourceCycle:any,sourceCause:string,persistence:number){
  const out=new Map(priorEntries(sourceCycle).map(([cause])=>[cause,0]));
  for(const [cause,p] of priorEntries(sourceCycle)){
    out.set(cause,(out.get(cause)??0)+(1-persistence)*p);
  }
  out.set(sourceCause,(out.get(sourceCause)??0)+persistence);
  return [...out.entries()];
}
function solvePolicy(
  sourceCycleIndex:number,
  executionCycleIndex:number,
  previousArchitecture:string,
  persistence:number,
  diagnosticCost:number,
  switchCost:number,
){
  const sourceCycle=design.cycles[sourceCycleIndex];
  const targetCycle=design.cycles[executionCycleIndex];
  let best:any=null;
  for(const diagnostic of diagnostics){
    const groups=new Map<string,string[]>();
    for(const [cause] of priorEntries(sourceCycle)){
      const obs=observation(diagnostic,cause);
      const group=groups.get(obs)??[];
      group.push(cause);
      groups.set(obs,group);
    }
    const keys=[...groups.keys()];
    const search=(index:number,architectureByObservation:Record<string,string>)=>{
      if(index===keys.length){
        const policy={diagnostic,architectureByObservation:{...architectureByObservation}};
        let expectedValue=diagnostic==='none'?0:-diagnosticCost;
        for(const [sourceCause,pSource] of priorEntries(sourceCycle)){
          const obs=observation(diagnostic,sourceCause);
          const architecture=policy.architectureByObservation[obs];
          if(!architecture)throw new Error(`policy missing architecture for ${obs}`);
          const switching=previousArchitecture!==architecture?switchCost:0;
          for(const [executionCause,pExecution] of executionDistribution(sourceCycle,sourceCause,persistence)){
            expectedValue+=pSource*pExecution*(
              Number(targetCycle.rewardByCauseAndArchitecture[executionCause][architecture])-switching
            );
          }
        }
        if(best===null||expectedValue>best.expectedValue)best={policy,expectedValue};
        return;
      }
      const obs=keys[index];
      if(obs===undefined)throw new Error('policy search observation index out of range');
      for(const architecture of architectures){
        architectureByObservation[obs]=architecture;
        search(index+1,architectureByObservation);
      }
    };
    search(0,{});
  }
  if(best===null)throw new Error('policy search produced no candidate');
  return best;
}
function signature(policy:any){
  return JSON.stringify([
    policy.diagnostic,
    Object.entries(policy.architectureByObservation).sort(([a],[b])=>String(a).localeCompare(String(b))),
  ]);
}
const localStates=[] as Array<{sourceCycleIndex:number,executionCycleIndex:number,previousArchitecture:string}>;
for(let sourceCycleIndex=0;sourceCycleIndex<design.cycles.length;sourceCycleIndex++){
  for(let executionCycleIndex=0;executionCycleIndex<design.cycles.length;executionCycleIndex++){
    for(const previousArchitecture of architectures)localStates.push({sourceCycleIndex,executionCycleIndex,previousArchitecture});
  }
}
function statesChanged<T>(levels:T[],params:(level:T)=>{persistence:number,diagnosticCost:number,switchCost:number}){
  let changed=0;
  for(const state of localStates){
    const signatures=levels.map(level=>{
      const p=params(level);
      return signature(solvePolicy(
        state.sourceCycleIndex,
        state.executionCycleIndex,
        state.previousArchitecture,
        p.persistence,
        p.diagnosticCost,
        p.switchCost,
      ).policy);
    });
    if(new Set(signatures).size>1)changed+=1;
  }
  return changed;
}
function conditioning(persistence:number){
  const costs=[3,6,12];
  let changed=0;
  let cheapScanStates=0;
  let baselineScanStates=0;
  let expensiveScanStates=0;
  for(const state of localStates){
    const solved=costs.map(diagnosticCost=>solvePolicy(
      state.sourceCycleIndex,
      state.executionCycleIndex,
      state.previousArchitecture,
      persistence,
      diagnosticCost,
      8,
    ).policy);
    if(new Set(solved.map(signature)).size>1)changed+=1;
    if(solved[0].diagnostic!=='none')cheapScanStates+=1;
    if(solved[1].diagnostic!=='none')baselineScanStates+=1;
    if(solved[2].diagnostic!=='none')expensiveScanStates+=1;
  }
  return {statesChanged:changed,cheapScanStates,baselineScanStates,expensiveScanStates};
}

const axisScreening={
  localStateCount:localStates.length,
  persistence:{
    levels:[0,0.2,0.55,0.9,1],
    statesChanged:statesChanged([0,0.2,0.55,0.9,1],persistence=>({persistence,diagnosticCost:6,switchCost:8})),
  },
  diagnosticCost:{
    levels:[0,3,6,9,12,18,30],
    statesChanged:statesChanged([0,3,6,9,12,18,30],diagnosticCost=>({persistence:0.55,diagnosticCost,switchCost:8})),
  },
  switchCost:{
    levels:[0,4,8,12,20,32],
    statesChanged:statesChanged([0,4,8,12,20,32],switchCost=>({persistence:0.55,diagnosticCost:6,switchCost})),
  },
  contractTarget:{
    levels:[200,320,560,690],
    statesChanged:0,
    solverDependency:false,
    note:'Current local policy objective does not consume targetTotal; target changes terminal feasibility only.',
  },
};

const regimeConditioning={
  '0.2':conditioning(0.2),
  '0.55':conditioning(0.55),
  '0.9':conditioning(0.9),
};

const compiled=compilePressureRun(design,FIRST_PRESSURE_RUN);
function terminalRun(architecture:string){
  const run=createSessionRun(design,{
    sessionRules:compiled.sessionRules,
    regime:'STABLE',
    initialCause:'route',
    transitionScript:Array(compiled.unitCount).fill('route'),
  });
  while(publicView(run).sessionStatus==='ACTIVE'){
    selectArchitecture(run,architecture);
    commitRound(run);
    if(publicView(run).sessionStatus==='ACTIVE')nextRound(run);
  }
  return publicView(run);
}
const success=terminalRun('route');
const failure=terminalRun('source');

const r4Compiled=compileRunRecipe(design,FIRST_BREADTH_ARC);
const r4Run=createSessionRun(design,{
  sessionRules:r4Compiled.sessionRules,
  regime:'STABLE',
  initialCause:'route',
  transitionScript:Array(r4Compiled.unitCount).fill('route'),
});
const r4Compatibility={
  roundCount:r4Compiled.sessionRules.roundCount,
  targetTotal:r4Compiled.sessionRules.targetTotal,
  currentCostPressure:publicView(r4Run).current?.costPressure,
};

const pass=
  axisScreening.localStateCount===27 &&
  axisScreening.persistence.statesChanged===19 &&
  axisScreening.diagnosticCost.statesChanged===27 &&
  axisScreening.switchCost.statesChanged===18 &&
  axisScreening.contractTarget.statesChanged===0 &&
  regimeConditioning['0.2'].statesChanged===0 &&
  regimeConditioning['0.55'].statesChanged===16 &&
  regimeConditioning['0.9'].statesChanged===27 &&
  regimeConditioning['0.9'].cheapScanStates===27 &&
  regimeConditioning['0.9'].expensiveScanStates===0 &&
  compiled.unitCount===10 &&
  compiled.newPlayerVerbsAdded===0 &&
  success.sessionStatus==='SUCCESS' &&
  success.totalNet===1000 &&
  failure.sessionStatus==='FAILURE' &&
  failure.totalNet===374 &&
  failure.contract.maxRecoverableTotal===774 &&
  r4Compatibility.roundCount===7 &&
  r4Compatibility.targetTotal===560 &&
  r4Compatibility.currentCostPressure?.diagnosticCost===6 &&
  r4Compatibility.currentCostPressure?.switchCost===8;

const out={
  schemaVersion:1,
  kind:'ordivon.game.causal-lag-pressure-r5-mechanical-acceptance',
  designId:design.id,
  designDigest:sha256(designBytes),
  legoMethod:{
    methodSnapshot:{
      project:'ordivon-next',
      observedRevision:'0032108f2fa9ce019e3735623e5b37fed23fc3a8',
      authority:'ANALYSIS_METHOD_PROVENANCE_ONLY',
    },
    questionCompiler:{
      target:'Create macro pressure that changes decisions rather than merely raising numbers.',
      survivingQuestions:[
        'Which existing pressure variables actually change optimal local policy?',
        'Which candidate is the smallest visible intervention that preserves current player verbs?',
        'Does its value depend on the hidden stability regime?',
        'Can content reference pressure without owning numeric rule semantics?',
        'Does a longer run preserve terminal stakes and R4 compatibility?',
      ],
    },
    ckDesign:{
      c0:'A longer Causal Lag run with non-fake pacing produced from existing mechanics.',
      selectedBranch:'visible diagnostic-cost pressure schedule over unchanged hidden run stability',
      deferredBranches:['persistence scheduling','switch-inertia scheduling','horizon-aware contract-margin policy','new player mechanics'],
      rejectedBranch:'targetTotal-only pacing under the current myopic local objective',
    },
    feedbackControl:{
      regulatedOutcome:'contract standing over a ten-beat run',
      existingHiddenDisturbance:'run-level cause persistence regime',
      newVisiblePressure:'current information acquisition cost',
      controller:'player policy',
      effectSetChanged:false,
      observationBoundary:'current cost is public; regime, persistence and unresolved execution cause remain private',
    },
  },
  axisScreening,
  regimeConditioning,
  selectedAxis:{
    id:'diagnosticCost',
    reason:'Broadest bounded local policy sensitivity while preserving the action set and hidden regime semantics.',
  },
  explorationPolicy:{
    used:false,
    reason:'Candidate screening is deterministic, exhaustive, low-cost and attribution is exact; adaptive allocation adds no decision value.',
  },
  compiledRun:compiled,
  terminalWitnesses:{success,failure},
  r4Compatibility,
  newPlayerVerbsAdded:0,
  pass,
  productSelected:false,
  g0Entered:false,
  humanOutcomeEstablished:false,
  gameCoreChanged:false,
  claimBoundary:'PRESSURE_TOPOLOGY_AND_POLICY_SENSITIVITY_MECHANICS_ONLY_NO_HUMAN_PACING_OR_PRODUCT_VALUE_CLAIM',
};

const evidencePath=resolve(root,'evidence/mechanical-acceptance-r5.json');
mkdirSync(dirname(evidencePath),{recursive:true});
writeFileSync(evidencePath,JSON.stringify(out,null,2)+'\n');
process.stdout.write(JSON.stringify(out,null,2)+'\n');
if(!pass)process.exitCode=3;
