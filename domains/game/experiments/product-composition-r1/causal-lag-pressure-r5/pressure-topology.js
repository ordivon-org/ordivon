import {compileRunRecipe} from '../causal-lag-content-r4/content-grammar.js';

export const PRESSURE_PROFILES=Object.freeze({
  SCAN_CHEAP:Object.freeze({diagnosticCost:3,switchCost:8}),
  BASELINE:Object.freeze({diagnosticCost:6,switchCost:8}),
  SCAN_EXPENSIVE:Object.freeze({diagnosticCost:12,switchCost:8}),
});

export const FIRST_PRESSURE_RUN=Object.freeze({
  id:'causal-lag-pressure-run-r5',
  targetTotal:780,
  initialArchitecture:'route',
  units:Object.freeze([
    Object.freeze({id:'r5-01-open-baseline',role:'INTRODUCE',sourceCycleIndex:0,executionCycleIndex:0,pressureProfileId:'SCAN_CHEAP'}),
    Object.freeze({id:'r5-02-open-shift',role:'PRACTICE',sourceCycleIndex:0,executionCycleIndex:1,pressureProfileId:'SCAN_CHEAP'}),
    Object.freeze({id:'r5-03-build-hold',role:'VARY',sourceCycleIndex:1,executionCycleIndex:1,pressureProfileId:'BASELINE'}),
    Object.freeze({id:'r5-04-build-revalue',role:'COMBINE',sourceCycleIndex:1,executionCycleIndex:2,pressureProfileId:'BASELINE'}),
    Object.freeze({id:'r5-05-tight-revalue',role:'STRESS',sourceCycleIndex:2,executionCycleIndex:2,pressureProfileId:'SCAN_EXPENSIVE'}),
    Object.freeze({id:'r5-06-tight-return',role:'STRESS',sourceCycleIndex:2,executionCycleIndex:0,pressureProfileId:'SCAN_EXPENSIVE'}),
    Object.freeze({id:'r5-07-tight-baseline',role:'RECONTEXTUALIZE',sourceCycleIndex:0,executionCycleIndex:0,pressureProfileId:'SCAN_EXPENSIVE'}),
    Object.freeze({id:'r5-08-release-shift',role:'PRACTICE',sourceCycleIndex:0,executionCycleIndex:1,pressureProfileId:'BASELINE'}),
    Object.freeze({id:'r5-09-release-revalue',role:'COMBINE',sourceCycleIndex:1,executionCycleIndex:2,pressureProfileId:'SCAN_CHEAP'}),
    Object.freeze({id:'r5-10-close-return',role:'CONCLUDE',sourceCycleIndex:2,executionCycleIndex:0,pressureProfileId:'SCAN_CHEAP'}),
  ]),
});

function validatePressureUnit(unit){
  const allowed=new Set(['id','role','sourceCycleIndex','executionCycleIndex','pressureProfileId']);
  for(const key of Object.keys(unit)){
    if(!allowed.has(key))throw new Error(`content unit cannot own ${key}`);
  }
  if(typeof unit.pressureProfileId!=='string'||!PRESSURE_PROFILES[unit.pressureProfileId]){
    throw new Error(`unknown pressure profile: ${unit.pressureProfileId}`);
  }
}

export function compilePressureRun(design,recipe){
  if(!recipe||!Array.isArray(recipe.units)||recipe.units.length===0){
    throw new Error('pressure run requires content units');
  }

  for(const unit of recipe.units)validatePressureUnit(unit);

  const baseRecipe={
    id:recipe.id,
    targetTotal:recipe.targetTotal,
    initialArchitecture:recipe.initialArchitecture,
    units:recipe.units.map(({id,role,sourceCycleIndex,executionCycleIndex})=>({
      id,
      role,
      sourceCycleIndex,
      executionCycleIndex,
    })),
  };
  const base=compileRunRecipe(design,baseRecipe);
  const units=recipe.units.map(unit=>({...unit}));
  const pressureChain=units.map(unit=>{
    const profile=PRESSURE_PROFILES[unit.pressureProfileId];
    return {
      profileId:unit.pressureProfileId,
      diagnosticCost:Number(profile.diagnosticCost),
      switchCost:Number(profile.switchCost),
    };
  });

  return {
    schemaVersion:1,
    kind:'ordivon.game.causal-lag-pressure-r5-compiled-run',
    recipeId:recipe.id,
    unitCount:base.unitCount,
    units,
    maxTheoreticalBase:base.maxTheoreticalBase,
    sessionRules:{
      ...base.sessionRules,
      pressureChain,
    },
    newPlayerVerbsAdded:0,
    productSelected:false,
    g0Entered:false,
    humanOutcomeEstablished:false,
    gameCoreChanged:false,
  };
}
