export const CONTENT_ROLES=Object.freeze([
  'INTRODUCE',
  'PRACTICE',
  'VARY',
  'COMBINE',
  'STRESS',
  'RECONTEXTUALIZE',
  'CONCLUDE',
]);

export const FIRST_BREADTH_ARC=Object.freeze({
  id:'causal-lag-breadth-arc-r4',
  targetTotal:560,
  initialArchitecture:'route',
  units:Object.freeze([
    Object.freeze({id:'intro-baseline-hold',role:'INTRODUCE',sourceCycleIndex:0,executionCycleIndex:0}),
    Object.freeze({id:'practice-objective-shift',role:'PRACTICE',sourceCycleIndex:0,executionCycleIndex:1}),
    Object.freeze({id:'vary-route-hold',role:'VARY',sourceCycleIndex:1,executionCycleIndex:1}),
    Object.freeze({id:'combine-rule-revaluation',role:'COMBINE',sourceCycleIndex:1,executionCycleIndex:2}),
    Object.freeze({id:'stress-revaluation-hold',role:'STRESS',sourceCycleIndex:2,executionCycleIndex:2}),
    Object.freeze({id:'recontext-return-baseline',role:'RECONTEXTUALIZE',sourceCycleIndex:2,executionCycleIndex:0}),
    Object.freeze({id:'conclude-objective-shift',role:'CONCLUDE',sourceCycleIndex:0,executionCycleIndex:1}),
  ]),
});

function assertIndex(design,value,label){
  if(!Number.isInteger(value)||!design.cycles[value])throw new Error(`${label} context index is invalid`);
}

export function validateContentUnit(design,unit){
  if(!unit||typeof unit.id!=='string'||unit.id.length===0)throw new Error('content unit id is required');
  if(!CONTENT_ROLES.includes(unit.role))throw new Error(`unknown content role: ${unit.role}`);
  assertIndex(design,unit.sourceCycleIndex,'source');
  assertIndex(design,unit.executionCycleIndex,'execution');
  const allowed=new Set(['id','role','sourceCycleIndex','executionCycleIndex']);
  for(const key of Object.keys(unit)){
    if(!allowed.has(key))throw new Error(`content unit cannot own ${key}`);
  }
  return unit;
}

function maxExecutionReward(design,index){
  const cycle=design.cycles[index];
  let best=-Infinity;
  for(const byArchitecture of Object.values(cycle.rewardByCauseAndArchitecture)){
    for(const value of Object.values(byArchitecture))best=Math.max(best,Number(value));
  }
  if(!Number.isFinite(best))throw new Error('execution context has no finite reward');
  return best;
}

export function compileRunRecipe(design,recipe){
  if(!recipe||typeof recipe.id!=='string'||recipe.id.length===0)throw new Error('run recipe id is required');
  if(!Array.isArray(recipe.units)||recipe.units.length===0)throw new Error('run recipe requires content units');
  if(!design.architectureModes.includes(recipe.initialArchitecture))throw new Error('run recipe initialArchitecture is invalid');
  if(!(Number(recipe.targetTotal)>0))throw new Error('run recipe targetTotal must be positive');

  const ids=new Set();
  const units=recipe.units.map((unit,index)=>{
    validateContentUnit(design,unit);
    if(ids.has(unit.id))throw new Error(`duplicate content unit id: ${unit.id}`);
    ids.add(unit.id);
    if(index>0){
      const previous=recipe.units[index-1];
      if(previous.executionCycleIndex!==unit.sourceCycleIndex){
        throw new Error(`context seam does not compose between ${previous.id} and ${unit.id}`);
      }
    }
    return {...unit};
  });

  const maxTheoreticalBase=units.reduce(
    (sum,unit)=>sum+maxExecutionReward(design,unit.executionCycleIndex),
    0,
  );
  if(Number(recipe.targetTotal)>maxTheoreticalBase){
    throw new Error('run recipe targetTotal exceeds theoretical base maximum');
  }

  return {
    schemaVersion:1,
    kind:'ordivon.game.causal-lag-content-r4-compiled-recipe',
    recipeId:recipe.id,
    unitCount:units.length,
    units,
    maxTheoreticalBase,
    sessionRules:{
      roundCount:units.length,
      targetTotal:Number(recipe.targetTotal),
      initialArchitecture:recipe.initialArchitecture,
      contextChain:units.map(({sourceCycleIndex,executionCycleIndex})=>({
        sourceCycleIndex,
        executionCycleIndex,
      })),
    },
    productSelected:false,
    g0Entered:false,
    humanOutcomeEstablished:false,
    gameCoreChanged:false,
  };
}

function priorEntries(cycle){
  return Object.entries(cycle.causePrior).map(([cause,p])=>[cause,Number(p)]);
}

function observation(diagnostic,cause){
  if(diagnostic==='none')return 'NONE';
  return diagnostic===cause?'FAULT':'OK';
}

function executionDistribution(sourceCycle,sourceCause,persistence){
  const out=new Map(priorEntries(sourceCycle).map(([cause])=>[cause,0]));
  for(const [cause,p] of priorEntries(sourceCycle)){
    out.set(cause,(out.get(cause)??0)+(1-persistence)*p);
  }
  out.set(sourceCause,(out.get(sourceCause)??0)+persistence);
  return [...out.entries()];
}

function evaluatePolicy(design,unit,previousArchitecture,policy,persistence){
  const sourceCycle=design.cycles[unit.sourceCycleIndex];
  const targetCycle=design.cycles[unit.executionCycleIndex];
  let total=policy.diagnostic==='none'?0:-Number(design.diagnosticCost);
  for(const [sourceCause,pSource] of priorEntries(sourceCycle)){
    const obs=observation(policy.diagnostic,sourceCause);
    const architecture=policy.architectureByObservation[obs];
    const switching=previousArchitecture!==architecture?Number(design.switchCost):0;
    for(const [executionCause,pExecution] of executionDistribution(sourceCycle,sourceCause,persistence)){
      total+=pSource*pExecution*(
        Number(targetCycle.rewardByCauseAndArchitecture[executionCause][architecture])-switching
      );
    }
  }
  return total;
}

function solveUnit(design,unit,previousArchitecture,persistence){
  const sourceCycle=design.cycles[unit.sourceCycleIndex];
  let best=null;
  for(const diagnostic of design.diagnostics){
    const groups=new Map();
    for(const [cause] of priorEntries(sourceCycle)){
      const obs=observation(diagnostic,cause);
      const group=groups.get(obs)??[];
      group.push(cause);
      groups.set(obs,group);
    }
    const keys=[...groups.keys()];
    const search=(index,architectureByObservation)=>{
      if(index===keys.length){
        const policy={diagnostic,architectureByObservation:{...architectureByObservation}};
        const expectedValue=evaluatePolicy(design,unit,previousArchitecture,policy,persistence);
        if(best===null||expectedValue>best.expectedValue){
          best={policy,expectedValue};
        }
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
  if(best===null)throw new Error('policy search produced no candidate');
  return best;
}

function signature(policy){
  return JSON.stringify([
    policy.diagnostic,
    Object.entries(policy.architectureByObservation).sort(([a],[b])=>a.localeCompare(b)),
  ]);
}

export function analyzeTransitionSpace(
  design,
  {
    persistences=[0.2,0.55,0.9],
    previousArchitectures=design.architectureModes,
  }={},
){
  const signatures=new Set();
  const transitions=[];
  let evaluatedStates=0;

  for(let sourceCycleIndex=0;sourceCycleIndex<design.cycles.length;sourceCycleIndex++){
    for(let executionCycleIndex=0;executionCycleIndex<design.cycles.length;executionCycleIndex++){
      const unit={id:`${sourceCycleIndex}->${executionCycleIndex}`,role:'VARY',sourceCycleIndex,executionCycleIndex};
      const local=new Set();
      for(const previousArchitecture of previousArchitectures){
        if(!design.architectureModes.includes(previousArchitecture))throw new Error('previousArchitecture is invalid');
        for(const persistence of persistences){
          if(!(Number(persistence)>=0&&Number(persistence)<=1))throw new Error('persistence must be within [0,1]');
          const solved=solveUnit(design,unit,previousArchitecture,Number(persistence));
          const sig=signature(solved.policy);
          local.add(sig);
          signatures.add(sig);
          evaluatedStates+=1;
        }
      }
      transitions.push({
        sourceCycleIndex,
        executionCycleIndex,
        distinctPolicySignatures:local.size,
      });
    }
  }

  return {
    schemaVersion:1,
    kind:'ordivon.game.causal-lag-content-r4-transition-analysis',
    transitionCount:transitions.length,
    evaluatedStates,
    distinctPolicySignatures:signatures.size,
    transitionsWithMultiplePolicies:transitions.filter(row=>row.distinctPolicySignatures>1).length,
    transitions,
    newPlayerVerbsAdded:0,
    humanOutcomeEstablished:false,
  };
}
