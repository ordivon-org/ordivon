import {SCENARIOS} from '../../pc01-e03-playable-r1/web/core.js';

export const REGIMES=Object.freeze({
  STABLE:Object.freeze({persistence:0.9}),
  VOLATILE:Object.freeze({persistence:0.2}),
});

function scenarioFor(id){
  const scenario=SCENARIOS[id];
  if(!scenario)throw new Error(`unknown scenario: ${id}`);
  return scenario;
}

function priorEntries(cycle){
  return Object.entries(cycle.causePrior).map(([cause,p])=>[cause,Number(p)]);
}

function observation(diagnostic,cause){
  if(diagnostic==='none')return 'NONE';
  return diagnostic===cause?'FAULT':'OK';
}

function switchCost(design,previous,next){
  return previous&&previous!==next?Number(design.switchCost):0;
}

function transitionProbability(sourceCycle,sourceCause,executionCause,persistence){
  const marginal=Number(sourceCycle.causePrior[executionCause]);
  if(sourceCause===executionCause)return persistence+(1-persistence)*marginal;
  return (1-persistence)*marginal;
}

export function updateRegimeBelief(design,history){
  let stable=0.5;
  let volatile=0.5;
  for(const event of history){
    const cycle=design.cycles[event.sourceCycleIndex];
    if(!cycle)throw new Error(`unknown sourceCycleIndex: ${event.sourceCycleIndex}`);
    const stableLike=transitionProbability(
      cycle,
      event.sourceCause,
      event.executionCause,
      REGIMES.STABLE.persistence,
    );
    const volatileLike=transitionProbability(
      cycle,
      event.sourceCause,
      event.executionCause,
      REGIMES.VOLATILE.persistence,
    );
    const stableWeight=stable*stableLike;
    const volatileWeight=volatile*volatileLike;
    const z=stableWeight+volatileWeight;
    if(!(z>0))throw new Error('belief update has zero evidence mass');
    stable=stableWeight/z;
    volatile=volatileWeight/z;
  }
  return {STABLE:stable,VOLATILE:volatile};
}

export function predictivePersistence(belief){
  return belief.STABLE*REGIMES.STABLE.persistence+belief.VOLATILE*REGIMES.VOLATILE.persistence;
}

function executionDistribution(sourceCycle,sourceCause,persistence){
  const out=new Map(priorEntries(sourceCycle).map(([cause])=>[cause,0]));
  for(const [cause,p] of priorEntries(sourceCycle)){
    out.set(cause,(out.get(cause)??0)+(1-persistence)*p);
  }
  out.set(sourceCause,(out.get(sourceCause)??0)+persistence);
  return [...out.entries()];
}

function evaluatePolicyAtPersistence(design,scenarioId,policy,persistence){
  const scenario=scenarioFor(scenarioId);
  const sourceCycle=design.cycles[scenario.sourceCycleIndex];
  const targetCycle=design.cycles[scenario.executionCycleIndex];
  let total=policy.diagnostic==='none'?0:-Number(design.diagnosticCost);
  for(const [sourceCause,pSource] of priorEntries(sourceCycle)){
    const obs=observation(policy.diagnostic,sourceCause);
    const architecture=policy.architectureByObservation[obs];
    if(!architecture)throw new Error(`policy missing architecture for ${obs}`);
    const switching=switchCost(design,scenario.previousArchitecture,architecture);
    for(const [executionCause,pExecution] of executionDistribution(sourceCycle,sourceCause,persistence)){
      total+=pSource*pExecution*(
        Number(targetCycle.rewardByCauseAndArchitecture[executionCause][architecture])-switching
      );
    }
  }
  return total;
}

function solveAtPersistence(design,scenarioId,persistence){
  const scenario=scenarioFor(scenarioId);
  const sourceCycle=design.cycles[scenario.sourceCycleIndex];
  let best=null;
  for(const diagnostic of design.diagnostics){
    const groups=new Map();
    for(const [cause] of priorEntries(sourceCycle)){
      const obs=observation(diagnostic,cause);
      const current=groups.get(obs)??[];
      current.push(cause);
      groups.set(obs,current);
    }

    const keys=[...groups.keys()];
    const search=(index,architectureByObservation)=>{
      if(index===keys.length){
        const policy={diagnostic,architectureByObservation:{...architectureByObservation}};
        const expectedValue=evaluatePolicyAtPersistence(design,scenarioId,policy,persistence);
        if(best===null||expectedValue>best.expectedValue)best={policy,expectedValue};
        return;
      }
      const obs=keys[index];
      for(const architecture of design.architectureModes){
        architectureByObservation[obs]=architecture;
        search(index+1,architectureByObservation);
      }
    };
    search(0,{});
  }
  if(best===null)throw new Error('no policy candidate');
  return best;
}

export function solveLearnedPolicy(design,scenarioId,history,{historyAware=true}={}){
  const belief=historyAware?updateRegimeBelief(design,history):{STABLE:0.5,VOLATILE:0.5};
  const persistenceEstimate=predictivePersistence(belief);
  const solved=solveAtPersistence(design,scenarioId,persistenceEstimate);
  const scenario=scenarioFor(scenarioId);
  return {
    scenarioId,
    currentContextId:design.cycles[scenario.sourceCycleIndex].id,
    executionContextId:design.cycles[scenario.executionCycleIndex].id,
    previousArchitecture:scenario.previousArchitecture,
    persistenceEstimate,
    ...solved,
  };
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

function validateCause(design,cause){
  if(!design.architectureModes.includes(cause))throw new Error(`unknown cause: ${cause}`);
}

export function createLearningRun(design,{regime='STABLE',random=Math.random}={}){
  if(!REGIMES[regime])throw new Error(`unknown regime: ${regime}`);
  return {
    design,
    hiddenRegime:regime,
    random,
    history:[],
    current:null,
    totalNet:0,
  };
}

export function beginRound(run,scenarioId,{sourceCause=null,executionCause=null}={}){
  if(run.current&&run.current.phase==='decision')throw new Error('resolve current round before starting another');
  const scenario=scenarioFor(scenarioId);
  const sourceCycle=run.design.cycles[scenario.sourceCycleIndex];
  const resolvedSource=sourceCause??sampleCause(sourceCycle,run.random);
  validateCause(run.design,resolvedSource);

  let resolvedExecution=executionCause;
  if(resolvedExecution===null){
    const persistence=REGIMES[run.hiddenRegime].persistence;
    if(run.random()<persistence)resolvedExecution=resolvedSource;
    else resolvedExecution=sampleCause(sourceCycle,run.random);
  }
  validateCause(run.design,resolvedExecution);

  run.current={
    scenario,
    round:run.history.length+1,
    phase:'decision',
    sourceCause:resolvedSource,
    executionCause:resolvedExecution,
    inspection:null,
    selectedArchitecture:'',
    resolution:null,
  };
  return publicView(run);
}

export function inspect(run,diagnostic){
  if(!run.current||run.current.phase!=='decision')throw new Error('inspection requires active decision round');
  if(run.current.inspection)throw new Error('inspection already used');
  if(!run.design.diagnostics.includes(diagnostic)||diagnostic==='none')throw new Error(`invalid diagnostic: ${diagnostic}`);
  run.current.inspection={
    diagnostic,
    observation:observation(diagnostic,run.current.sourceCause),
  };
  return publicView(run);
}

export function selectArchitecture(run,architecture){
  if(!run.current||run.current.phase!=='decision')throw new Error('selection requires active decision round');
  validateCause(run.design,architecture);
  run.current.selectedArchitecture=architecture;
  return publicView(run);
}

export function commit(run){
  if(!run.current||run.current.phase!=='decision')throw new Error('commit requires active decision round');
  if(!run.current.selectedArchitecture)throw new Error('select architecture before commit');
  const scenario=run.current.scenario;
  const executionCycle=run.design.cycles[scenario.executionCycleIndex];
  const diagnostic=run.current.inspection?.diagnostic??'none';
  const baseReward=Number(
    executionCycle.rewardByCauseAndArchitecture[
      run.current.executionCause
    ][run.current.selectedArchitecture]
  );
  const diagnosticCost=diagnostic==='none'?0:Number(run.design.diagnosticCost);
  const switching=switchCost(
    run.design,
    scenario.previousArchitecture,
    run.current.selectedArchitecture,
  );
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
  run.history.push({
    round:run.current.round,
    scenarioId:scenario.id,
    sourceCycleIndex:scenario.sourceCycleIndex,
    sourceCause:run.current.sourceCause,
    executionCause:run.current.executionCause,
    persisted:run.current.sourceCause===run.current.executionCause,
    net,
  });
  return publicView(run);
}

export function publicView(run){
  const current=run.current;
  let currentView=null;
  if(current){
    const sourceCycle=run.design.cycles[current.scenario.sourceCycleIndex];
    const executionCycle=run.design.cycles[current.scenario.executionCycleIndex];
    currentView={
      round:current.round,
      scenarioId:current.scenario.id,
      phase:current.phase,
      lagSteps:current.scenario.lagSteps,
      previousArchitecture:current.scenario.previousArchitecture,
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
      resolution:current.resolution?{...current.resolution}:null,
    };
  }
  return {
    schemaVersion:1,
    kind:'ordivon.game.pc01-e03-multiround-r2-state',
    history:run.history.map(({sourceCycleIndex,...event})=>({...event})),
    totalNet:run.totalNet,
    current:currentView,
  };
}
