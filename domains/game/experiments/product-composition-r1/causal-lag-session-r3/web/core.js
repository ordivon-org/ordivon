import {REGIMES} from '../../pc01-e03-multiround-r2/web/core.js';

export const SESSION_RULES=Object.freeze({
  roundCount:4,
  targetTotal:320,
  initialArchitecture:'route',
  contextChain:Object.freeze([
    Object.freeze({sourceCycleIndex:0,executionCycleIndex:1}),
    Object.freeze({sourceCycleIndex:1,executionCycleIndex:2}),
    Object.freeze({sourceCycleIndex:2,executionCycleIndex:0}),
    Object.freeze({sourceCycleIndex:0,executionCycleIndex:1}),
  ]),
});

function priorEntries(cycle){
  return Object.entries(cycle.causePrior).map(([cause,p])=>[cause,Number(p)]);
}

function validateCause(design,cause){
  if(!design.hiddenCauseStates.includes(cause))throw new Error(`unknown cause: ${cause}`);
}

function validateArchitecture(design,architecture){
  if(!design.architectureModes.includes(architecture))throw new Error(`unknown architecture: ${architecture}`);
}

function sampleCause(cycle,random){
  const roll=random();
  let cumulative=0;
  for(const [cause,p] of priorEntries(cycle)){
    cumulative+=p;
    if(roll<=cumulative)return cause;
  }
  return priorEntries(cycle).at(-1)[0];
}

function sampleExecutionCause(run,roundIndex){
  const scripted=run.transitionScript?.[roundIndex];
  if(scripted){
    validateCause(run.design,scripted);
    return scripted;
  }
  const chain=SESSION_RULES.contextChain[roundIndex];
  const sourceCycle=run.design.cycles[chain.sourceCycleIndex];
  const persistence=REGIMES[run.hiddenRegime].persistence;
  if(run.random()<persistence)return run.latentCause;
  return sampleCause(sourceCycle,run.random);
}

function observation(diagnostic,cause){
  if(diagnostic==='none')return 'NONE';
  return diagnostic===cause?'FAULT':'OK';
}

function startRound(run){
  if(run.roundIndex>=SESSION_RULES.roundCount)throw new Error('session has no remaining round');
  const chain=SESSION_RULES.contextChain[run.roundIndex];
  const executionCause=sampleExecutionCause(run,run.roundIndex);
  run.current={
    round:run.roundIndex+1,
    phase:'decision',
    sourceCycleIndex:chain.sourceCycleIndex,
    executionCycleIndex:chain.executionCycleIndex,
    sourceCause:run.latentCause,
    executionCause,
    previousArchitecture:run.currentArchitecture,
    inspection:null,
    selectedArchitecture:'',
    resolution:null,
  };
}

function maxRecoverableTotal(run){
  const remainingRounds=SESSION_RULES.roundCount-run.history.length;
  return run.totalNet+remainingRounds*100;
}

function updateSessionStanding(run){
  const remainingRounds=SESSION_RULES.roundCount-run.history.length;
  const maxRecoverable=maxRecoverableTotal(run);
  if(run.history.length===SESSION_RULES.roundCount){
    run.sessionStatus=run.totalNet>=run.targetTotal?'SUCCESS':'FAILURE';
    run.contractStatus=run.sessionStatus==='SUCCESS'?'ACHIEVED':'FAILED_UNRECOVERABLE';
    return;
  }
  if(maxRecoverable<run.targetTotal){
    run.sessionStatus='FAILURE';
    run.contractStatus='FAILED_UNRECOVERABLE';
    return;
  }
  run.sessionStatus='ACTIVE';
  run.contractStatus='ACTIVE';
}

export function createSessionRun(
  design,
  {
    regime='STABLE',
    initialCause=null,
    initialArchitecture=SESSION_RULES.initialArchitecture,
    transitionScript=null,
    targetTotal=SESSION_RULES.targetTotal,
    random=Math.random,
  }={},
){
  if(!REGIMES[regime])throw new Error(`unknown regime: ${regime}`);
  validateArchitecture(design,initialArchitecture);
  const cycle0=design.cycles[SESSION_RULES.contextChain[0].sourceCycleIndex];
  const cause=initialCause??sampleCause(cycle0,random);
  validateCause(design,cause);
  const run={
    design,
    hiddenRegime:regime,
    transitionScript,
    random,
    targetTotal,
    roundIndex:0,
    currentArchitecture:initialArchitecture,
    latentCause:cause,
    totalNet:0,
    history:[],
    sessionStatus:'ACTIVE',
    contractStatus:'ACTIVE',
    current:null,
  };
  startRound(run);
  return run;
}

export function inspect(run,diagnostic){
  if(run.sessionStatus!=='ACTIVE')throw new Error('session is terminal');
  if(!run.current||run.current.phase!=='decision')throw new Error('inspection requires decision phase');
  if(run.current.inspection)throw new Error('inspection already used');
  if(!run.design.diagnostics.includes(diagnostic)||diagnostic==='none')throw new Error(`invalid diagnostic: ${diagnostic}`);
  run.current.inspection={
    diagnostic,
    observation:observation(diagnostic,run.current.sourceCause),
  };
  return publicView(run);
}

export function selectArchitecture(run,architecture){
  if(run.sessionStatus!=='ACTIVE')throw new Error('session is terminal');
  if(!run.current||run.current.phase!=='decision')throw new Error('selection requires decision phase');
  validateArchitecture(run.design,architecture);
  run.current.selectedArchitecture=architecture;
  return publicView(run);
}

export function commitRound(run){
  if(run.sessionStatus!=='ACTIVE')throw new Error('session is terminal');
  if(!run.current||run.current.phase!=='decision')throw new Error('commit requires decision phase');
  if(!run.current.selectedArchitecture)throw new Error('select architecture before commit');

  const targetCycle=run.design.cycles[run.current.executionCycleIndex];
  const diagnostic=run.current.inspection?.diagnostic??'none';
  const baseReward=Number(
    targetCycle.rewardByCauseAndArchitecture[
      run.current.executionCause
    ][run.current.selectedArchitecture]
  );
  const diagnosticCost=diagnostic==='none'?0:Number(run.design.diagnosticCost);
  const switching=
    run.current.previousArchitecture!==run.current.selectedArchitecture
      ? Number(run.design.switchCost)
      : 0;
  const net=baseReward-diagnosticCost-switching;

  run.current.phase='resolved';
  run.current.resolution={
    sourceCause:run.current.sourceCause,
    executionCause:run.current.executionCause,
    architecture:run.current.selectedArchitecture,
    baseReward,
    diagnosticCost,
    switchCost:switching,
    net,
  };

  run.totalNet+=net;
  run.currentArchitecture=run.current.selectedArchitecture;
  run.latentCause=run.current.executionCause;
  run.history.push({
    round:run.current.round,
    sourceCycleIndex:run.current.sourceCycleIndex,
    executionCycleIndex:run.current.executionCycleIndex,
    sourceCause:run.current.sourceCause,
    executionCause:run.current.executionCause,
    persisted:run.current.sourceCause===run.current.executionCause,
    previousArchitecture:run.current.previousArchitecture,
    architecture:run.current.selectedArchitecture,
    diagnostic,
    net,
  });

  updateSessionStanding(run);
  return publicView(run);
}

export function nextRound(run){
  if(run.sessionStatus!=='ACTIVE')throw new Error('session is terminal');
  if(!run.current||run.current.phase!=='resolved')throw new Error('resolve current round before advancing');
  run.roundIndex+=1;
  if(run.roundIndex>=SESSION_RULES.roundCount)throw new Error('session is terminal');
  startRound(run);
  return publicView(run);
}

export function publicView(run){
  const current=run.current;
  let currentView=null;
  if(current){
    const sourceCycle=run.design.cycles[current.sourceCycleIndex];
    const executionCycle=run.design.cycles[current.executionCycleIndex];
    currentView={
      round:current.round,
      phase:current.phase,
      previousArchitecture:current.previousArchitecture,
      currentContext:{
        id:sourceCycle.id,
        operatingContext:sourceCycle.operatingContext,
        visibleSymptom:sourceCycle.visibleSymptom,
      },
      executionForecast:{
        id:executionCycle.id,
        operatingContext:executionCycle.operatingContext,
        visibleSymptom:executionCycle.visibleSymptom,
      },
      inspection:current.inspection?{...current.inspection}:null,
      selectedArchitecture:current.selectedArchitecture,
      resolution:current.phase==='resolved'&&current.resolution?{...current.resolution}:null,
    };
  }

  return {
    schemaVersion:1,
    kind:'ordivon.game.causal-lag-session-r3-state',
    sessionStatus:run.sessionStatus,
    totalNet:run.totalNet,
    contract:{
      targetTotal:run.targetTotal,
      remainingTarget:Math.max(0,run.targetTotal-run.totalNet),
      maxRecoverableTotal:maxRecoverableTotal(run),
      status:run.contractStatus,
    },
    history:run.history.map(({sourceCycleIndex,executionCycleIndex,...event})=>({...event})),
    current:currentView,
    productSelected:false,
    g0Entered:false,
    humanOutcomeEstablished:false,
    gameCoreChanged:false,
  };
}
