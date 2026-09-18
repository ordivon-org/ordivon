import {PRESSURE_PROFILES} from '../causal-lag-pressure-r5/pressure-topology.js';

export const HORIZON_OBJECTIVE='CONTRACT_SUCCESS_PROBABILITY_THEN_EXPECTED_NET';

export const VOLATILE_HORIZON_WITNESS=Object.freeze({
  id:'r6-volatile-beats-2-3',
  persistence:0.2,
  previousArchitecture:'route',
  units:Object.freeze([
    Object.freeze({sourceCycleIndex:0,executionCycleIndex:1,pressureProfileId:'SCAN_CHEAP'}),
    Object.freeze({sourceCycleIndex:1,executionCycleIndex:1,pressureProfileId:'BASELINE'}),
  ]),
});

export const STABLE_HORIZON_WITNESS=Object.freeze({
  id:'r6-stable-beats-4-5',
  persistence:0.9,
  previousArchitecture:'process',
  units:Object.freeze([
    Object.freeze({sourceCycleIndex:1,executionCycleIndex:2,pressureProfileId:'BASELINE'}),
    Object.freeze({sourceCycleIndex:2,executionCycleIndex:2,pressureProfileId:'SCAN_EXPENSIVE'}),
  ]),
});

function round12(value){
  return Number(Number(value).toFixed(12));
}

function validateIndex(design,value,label){
  if(!Number.isInteger(value)||!design.cycles[value])throw new Error(`${label} context index is invalid`);
}

function validateWindow(design,input){
  if(!input||!Array.isArray(input.units)||input.units.length<1||input.units.length>3){
    throw new Error('horizon must be within 1..3 beats');
  }
  if(!design.architectureModes.includes(input.previousArchitecture)){
    throw new Error('previousArchitecture is invalid');
  }
  if(!(Number(input.persistence)>=0&&Number(input.persistence)<=1)){
    throw new Error('persistence must be within [0,1]');
  }
  for(const [index,unit] of input.units.entries()){
    validateIndex(design,unit.sourceCycleIndex,'source');
    validateIndex(design,unit.executionCycleIndex,'execution');
    if(!PRESSURE_PROFILES[unit.pressureProfileId]){
      throw new Error(`unknown pressure profile: ${unit.pressureProfileId}`);
    }
    if(index>0&&input.units[index-1].executionCycleIndex!==unit.sourceCycleIndex){
      throw new Error(`window seam does not compose between beats ${index} and ${index+1}`);
    }
  }
  return {
    units:input.units.map(unit=>({
      sourceCycleIndex:unit.sourceCycleIndex,
      executionCycleIndex:unit.executionCycleIndex,
      pressureProfileId:unit.pressureProfileId,
    })),
    persistence:Number(input.persistence),
    previousArchitecture:input.previousArchitecture,
  };
}

function observation(diagnostic,cause){
  if(diagnostic==='none')return 'NONE';
  return diagnostic===cause?'FAULT':'OK';
}

function executionDistribution(design,sourceCycleIndex,sourceCause,persistence){
  const cycle=design.cycles[sourceCycleIndex];
  const out=new Map(design.hiddenCauseStates.map(cause=>[
    cause,
    (1-persistence)*Number(cycle.causePrior[cause]),
  ]));
  out.set(sourceCause,(out.get(sourceCause)??0)+persistence);
  return [...out.entries()];
}

function policyCandidates(design,belief){
  const support=Object.entries(belief).filter(([,p])=>Number(p)>1e-15).map(([cause])=>cause);
  const candidates=[];
  for(const diagnostic of design.diagnostics){
    const observations=[...new Set(support.map(cause=>observation(diagnostic,cause)))].sort();
    const search=(index,architectureByObservation)=>{
      if(index===observations.length){
        candidates.push({
          diagnostic,
          architectureByObservation:{...architectureByObservation},
        });
        return;
      }
      const obs=observations[index];
      for(const architecture of design.architectureModes){
        architectureByObservation[obs]=architecture;
        search(index+1,architectureByObservation);
      }
    };
    search(0,{});
  }
  return candidates;
}

function policySignature(policy){
  return JSON.stringify([
    policy.diagnostic,
    Object.entries(policy.architectureByObservation).sort(([a],[b])=>a.localeCompare(b)),
  ]);
}

function compareRows(a,b){
  if(a.successProbability>b.successProbability+1e-12)return 1;
  if(b.successProbability>a.successProbability+1e-12)return -1;
  if(a.expectedTotalNet>b.expectedTotalNet+1e-12)return 1;
  if(b.expectedTotalNet>a.expectedTotalNet+1e-12)return -1;
  const as=policySignature(a.policy);
  const bs=policySignature(b.policy);
  if(as<bs)return 1;
  if(as>bs)return -1;
  return 0;
}

function roundOutcomes(design,unit,previousArchitecture,persistence,belief,policy){
  const sourceCycle=design.cycles[unit.sourceCycleIndex];
  const targetCycle=design.cycles[unit.executionCycleIndex];
  const pressure=PRESSURE_PROFILES[unit.pressureProfileId];
  const outcomes=[];
  for(const [sourceCause,pSourceRaw] of Object.entries(belief)){
    const pSource=Number(pSourceRaw);
    if(pSource<=1e-15)continue;
    const obs=observation(policy.diagnostic,sourceCause);
    const architecture=policy.architectureByObservation[obs];
    if(!architecture)throw new Error(`policy missing architecture for observation ${obs}`);
    const diagnosticCost=policy.diagnostic==='none'?0:Number(pressure.diagnosticCost);
    const switchCost=architecture===previousArchitecture?0:Number(pressure.switchCost);
    for(const [executionCause,pExecution] of executionDistribution(
      design,
      unit.sourceCycleIndex,
      sourceCause,
      persistence,
    )){
      outcomes.push({
        probability:pSource*pExecution,
        net:Number(targetCycle.rewardByCauseAndArchitecture[executionCause][architecture])
          -diagnosticCost
          -switchCost,
        executionCause,
        architecture,
      });
    }
  }
  return outcomes;
}

function immediateExpectedNet(design,unit,previousArchitecture,persistence,belief,policy){
  return roundOutcomes(
    design,
    unit,
    previousArchitecture,
    persistence,
    belief,
    policy,
  ).reduce((sum,row)=>sum+row.probability*row.net,0);
}

function sourcePrior(design,sourceCycleIndex){
  return Object.fromEntries(
    Object.entries(design.cycles[sourceCycleIndex].causePrior).map(([cause,p])=>[cause,Number(p)]),
  );
}

export function solveMyopicPolicy(design,input){
  const window=validateWindow(design,input);
  const belief=sourcePrior(design,window.units[0].sourceCycleIndex);
  let best=null;
  for(const policy of policyCandidates(design,belief)){
    const expectedImmediateNet=immediateExpectedNet(
      design,
      window.units[0],
      window.previousArchitecture,
      window.persistence,
      belief,
      policy,
    );
    const row={policy,expectedImmediateNet};
    if(
      best===null
      || expectedImmediateNet>best.expectedImmediateNet+1e-12
      || (
        Math.abs(expectedImmediateNet-best.expectedImmediateNet)<=1e-12
        && policySignature(policy)<policySignature(best.policy)
      )
    )best=row;
  }
  return {
    schemaVersion:1,
    kind:'ordivon.game.causal-lag-r6-myopic-oracle',
    objective:'IMMEDIATE_EXPECTED_NET',
    expectedImmediateNet:round12(best.expectedImmediateNet),
    policy:best.policy,
    solverAuthority:'MECHANICAL_ORACLE_ONLY',
    productSelected:false,
    g0Entered:false,
    humanOutcomeEstablished:false,
    gameCoreChanged:false,
  };
}

export function solveHorizonPolicy(design,input){
  const window=validateWindow(design,input);
  if(!Number.isFinite(Number(input.remainingTarget))||Number(input.remainingTarget)<=0){
    throw new Error('remainingTarget must be positive');
  }
  const initialBelief=sourcePrior(design,window.units[0].sourceCycleIndex);
  const memo=new Map();

  const solve=(index,belief,previousArchitecture,remainingTarget)=>{
    if(index===window.units.length){
      return {
        successProbability:remainingTarget<=0?1:0,
        expectedTotalNet:0,
        policy:{diagnostic:'END',architectureByObservation:{}},
      };
    }
    const beliefKey=Object.entries(belief).sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>[k,round12(v)]);
    const key=JSON.stringify([index,beliefKey,previousArchitecture,remainingTarget]);
    const cached=memo.get(key);
    if(cached)return cached;

    const unit=window.units[index];
    let best=null;
    for(const policy of policyCandidates(design,belief)){
      let successProbability=0;
      let expectedTotalNet=0;
      for(const outcome of roundOutcomes(
        design,
        unit,
        previousArchitecture,
        window.persistence,
        belief,
        policy,
      )){
        const next=solve(
          index+1,
          {[outcome.executionCause]:1},
          outcome.architecture,
          remainingTarget-outcome.net,
        );
        successProbability+=outcome.probability*next.successProbability;
        expectedTotalNet+=outcome.probability*(outcome.net+next.expectedTotalNet);
      }
      const row={successProbability,expectedTotalNet,policy};
      if(best===null||compareRows(row,best)>0)best=row;
    }
    memo.set(key,best);
    return best;
  };

  const result=solve(
    0,
    initialBelief,
    window.previousArchitecture,
    Number(input.remainingTarget),
  );
  const firstPolicyImmediateExpectedNet=immediateExpectedNet(
    design,
    window.units[0],
    window.previousArchitecture,
    window.persistence,
    initialBelief,
    result.policy,
  );

  return {
    schemaVersion:1,
    kind:'ordivon.game.causal-lag-r6-horizon-oracle',
    objective:HORIZON_OBJECTIVE,
    horizon:window.units.length,
    remainingTarget:Number(input.remainingTarget),
    persistence:window.persistence,
    previousArchitecture:window.previousArchitecture,
    window:window.units,
    successProbability:round12(result.successProbability),
    expectedTotalNet:round12(result.expectedTotalNet),
    firstPolicyImmediateExpectedNet:round12(firstPolicyImmediateExpectedNet),
    firstPolicy:result.policy,
    solverAuthority:'MECHANICAL_ORACLE_ONLY',
    newPlayerVerbsAdded:0,
    productSelected:false,
    g0Entered:false,
    humanOutcomeEstablished:false,
    gameCoreChanged:false,
  };
}

function localExpectedPolicy(design,unit,previousArchitecture,persistence){
  const belief=sourcePrior(design,unit.sourceCycleIndex);
  let best=null;
  for(const policy of policyCandidates(design,belief)){
    const expectedImmediateNet=immediateExpectedNet(
      design,
      unit,
      previousArchitecture,
      persistence,
      belief,
      policy,
    );
    const row={policy,expectedImmediateNet};
    if(
      best===null
      || expectedImmediateNet>best.expectedImmediateNet+1e-12
      || (
        Math.abs(expectedImmediateNet-best.expectedImmediateNet)<=1e-12
        && policySignature(policy)<policySignature(best.policy)
      )
    )best=row;
  }
  return best.policy;
}

function unitFingerprint(design,unit){
  return JSON.stringify(
    [0.2,0.9].flatMap(persistence=>
      design.architectureModes.map(previousArchitecture=>
        localExpectedPolicy(design,unit,previousArchitecture,persistence)
      )
    ).map(policy=>JSON.parse(policySignature(policy))),
  );
}

export function analyzePressureCompositionSaturation(design,{maxSequenceLength=5}={}){
  if(!Number.isInteger(maxSequenceLength)||maxSequenceLength<1||maxSequenceLength>5){
    throw new Error('maxSequenceLength must be within 1..5');
  }
  const profileIds=Object.keys(PRESSURE_PROFILES);
  const units=[];
  for(let sourceCycleIndex=0;sourceCycleIndex<design.cycles.length;sourceCycleIndex++){
    for(let executionCycleIndex=0;executionCycleIndex<design.cycles.length;executionCycleIndex++){
      for(const pressureProfileId of profileIds){
        units.push({sourceCycleIndex,executionCycleIndex,pressureProfileId});
      }
    }
  }

  const fingerprints=new Map();
  for(const unit of units){
    const key=unitFingerprint(design,unit);
    const rows=fingerprints.get(key)??[];
    rows.push(unit);
    fingerprints.set(key,rows);
  }

  const classIdByFingerprint=new Map(
    [...fingerprints.keys()].map((key,index)=>[key,index]),
  );
  const classIdByUnit=new Map(
    units.map(unit=>[
      JSON.stringify(unit),
      classIdByFingerprint.get(unitFingerprint(design,unit)),
    ]),
  );

  const sequenceSaturation=[];
  for(let length=1;length<=maxSequenceLength;length++){
    const words=new Set();
    const walk=(sourceCycleIndex,depth,word)=>{
      if(depth===length){
        words.add(JSON.stringify(word));
        return 1;
      }
      let total=0;
      for(let executionCycleIndex=0;executionCycleIndex<design.cycles.length;executionCycleIndex++){
        for(const pressureProfileId of profileIds){
          const unit={sourceCycleIndex,executionCycleIndex,pressureProfileId};
          word.push(classIdByUnit.get(JSON.stringify(unit)));
          total+=walk(executionCycleIndex,depth+1,word);
          word.pop();
        }
      }
      return total;
    };
    let validSequenceCount=0;
    for(let sourceCycleIndex=0;sourceCycleIndex<design.cycles.length;sourceCycleIndex++){
      validSequenceCount+=walk(sourceCycleIndex,0,[]);
    }
    sequenceSaturation.push({
      length,
      validSequenceCount,
      distinctEquivalenceWords:words.size,
      uniqueFraction:words.size/validSequenceCount,
    });
  }

  const baselineFingerprints=new Set(
    units
      .filter(unit=>unit.pressureProfileId==='BASELINE')
      .map(unit=>unitFingerprint(design,unit)),
  );

  return {
    schemaVersion:1,
    kind:'ordivon.game.causal-lag-r6-composition-saturation',
    localUnitCount:units.length,
    localEquivalenceClasses:fingerprints.size,
    redundantLocalUnits:units.length-fingerprints.size,
    uniqueFraction:fingerprints.size/units.length,
    baselineOnlyEquivalenceClasses:baselineFingerprints.size,
    sequenceSaturation,
    saturationEstablished:false,
    interpretation:'LOCAL_EQUIVALENCE_EXISTS_BUT_SEQUENCE_COMPRESSION_DOES_NOT_WORSEN_THROUGH_BOUND',
    productSelected:false,
    humanOutcomeEstablished:false,
  };
}
