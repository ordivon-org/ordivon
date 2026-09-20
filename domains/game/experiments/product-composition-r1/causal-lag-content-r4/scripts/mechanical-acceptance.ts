import {createHash} from 'node:crypto';
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

// @ts-expect-error Browser-compatible JS core intentionally has no declaration file.
import {commitRound,createSessionRun,nextRound,publicView,selectArchitecture} from '../../causal-lag-session-r3/web/core.js';
// @ts-expect-error Browser-compatible JS module intentionally has no declaration file.
import {FIRST_BREADTH_ARC,analyzeTransitionSpace,compileRunRecipe} from '../content-grammar.js';

const here=dirname(fileURLToPath(import.meta.url));
const root=resolve(here,'..');
const designPath=resolve(root,'../pc01-causal-works-f0/design.json');
const designBytes=readFileSync(designPath);
const design=JSON.parse(designBytes.toString('utf8'));
const sha256=(bytes:Buffer|string)=>'sha256:'+createHash('sha256').update(bytes).digest('hex');

const compiled=compileRunRecipe(design,FIRST_BREADTH_ARC);
const transitionAnalysis=analyzeTransitionSpace(design,{
  persistences:[0.2,0.55,0.9],
  previousArchitectures:design.architectureModes,
});

function runSuccess(){
  const run=createSessionRun(design,{
    sessionRules:compiled.sessionRules,
    regime:'STABLE',
    initialCause:'route',
    transitionScript:['route','route','route','route','route','route','route'],
  });
  for(let i=0;i<compiled.unitCount;i++){
    selectArchitecture(run,'route');
    commitRound(run);
    if(i<compiled.unitCount-1)nextRound(run);
  }
  return publicView(run);
}

function runFailure(){
  const run=createSessionRun(design,{
    sessionRules:compiled.sessionRules,
    regime:'STABLE',
    initialCause:'route',
    transitionScript:['route','route','route','route','route','route','route'],
  });
  while(publicView(run).sessionStatus==='ACTIVE'){
    selectArchitecture(run,'source');
    commitRound(run);
    if(publicView(run).sessionStatus==='ACTIVE')nextRound(run);
  }
  return publicView(run);
}

const defaultR3=createSessionRun(design,{
  regime:'STABLE',
  initialCause:'route',
  transitionScript:['route','route','route','route'],
});
const defaultR3Compatibility={
  roundCount:defaultR3.sessionRules.roundCount,
  targetTotal:publicView(defaultR3).contract.targetTotal,
  firstSourceCycleIndex:defaultR3.sessionRules.contextChain[0].sourceCycleIndex,
  firstExecutionCycleIndex:defaultR3.sessionRules.contextChain[0].executionCycleIndex,
};

const success=runSuccess();
const failure=runFailure();

const seamClosed=compiled.units.every((unit:any,index:number)=>{
  if(index===0)return true;
  return compiled.units[index-1].executionCycleIndex===unit.sourceCycleIndex;
});
const roleSequence=compiled.units.map((unit:any)=>unit.role);

const pass=
  seamClosed &&
  roleSequence.join('|')==='INTRODUCE|PRACTICE|VARY|COMBINE|STRESS|RECONTEXTUALIZE|CONCLUDE' &&
  transitionAnalysis.transitionCount===9 &&
  transitionAnalysis.evaluatedStates===81 &&
  transitionAnalysis.distinctPolicySignatures===7 &&
  transitionAnalysis.transitionsWithMultiplePolicies===9 &&
  transitionAnalysis.newPlayerVerbsAdded===0 &&
  success.sessionStatus==='SUCCESS' &&
  success.totalNet===700 &&
  success.history.length===7 &&
  failure.sessionStatus==='FAILURE' &&
  failure.totalNet===238 &&
  failure.contract.maxRecoverableTotal===538 &&
  defaultR3Compatibility.roundCount===4 &&
  defaultR3Compatibility.targetTotal===320;

const out={
  schemaVersion:1,
  kind:'ordivon.game.causal-lag-content-r4-mechanical-acceptance',
  designId:design.id,
  designDigest:sha256(designBytes),
  legoMethod:{
    methodSnapshot:{
      project:'ordivon-next',
      observedRevision:'4ec87fee31135995f096339b2598e0b925ca9729',
      authority:'ANALYSIS_METHOD_PROVENANCE_ONLY',
    },
    questionCompiler:{
      target:'Expand Causal Lag beyond one fixed four-round path without adding unproven player verbs.',
      decision:'Prefer existing-mechanic composition if it produces mechanically distinct policies and composes through explicit seams.',
      survivingQuestions:[
        'Do existing context transitions already alter optimal policies?',
        'Can authored content units compose without owning reward/session authority?',
        'Can the R3 session kernel accept compiled rules without a fork?',
        'Does one representative arc retain reachable success and failure?',
        'Which Human-value claims remain unresolved after mechanical breadth?',
      ],
      handoff:'PLAN_THEN_BOUNDED_EXPERIMENT',
    },
    ckDesign:{
      c0:'A broader Causal Lag game produced by recombining the existing kernel before adding new primitives.',
      selectedBranch:'context-transition recombination + authored semantic roles',
      deferredBranches:[
        'diagnostic reliability variation',
        'forecast degradation',
        'new architecture families',
        'new resource/economy layers',
        'meta progression',
      ],
      knowledgeGain:'The existing 3x3 transition space yields seven distinct optimal policy signatures over the tested state grid.',
    },
    compositionalContracts:{
      contentUnitAssumption:'source/execution context indices resolve to existing PC01 contexts and role is authored metadata only',
      contentUnitGuarantee:'one valid context transition with no reward/session authority',
      runRecipeAssumption:'adjacent execution/source contexts match and target is theoretically reachable',
      runRecipeGuarantee:'R3-compatible sessionRules',
      seamClosed,
    },
    feedbackControl:{
      regulatedOutcome:'session contract total relative to target',
      state:['latent cause','built architecture','round index','total net','resolved history'],
      observations:['current symptom','execution-context forecast','history','contract margin'],
      controller:'player policy',
      effects:['inspect','select architecture','commit'],
      disturbance:'hidden cause transition under run-level persistence regime',
      delay:'one context shift between commitment and execution',
      r4Change:'content varies the context path while preserving the control loop',
    },
  },
  compiledRecipe:compiled,
  transitionAnalysis,
  terminalWitnesses:{success,failure},
  defaultR3Compatibility,
  pass,
  productSelected:false,
  g0Entered:false,
  humanOutcomeEstablished:false,
  gameCoreChanged:false,
  claimBoundary:'CONTENT_GRAMMAR_AND_POLICY_BREADTH_MECHANICS_ONLY_NO_HUMAN_VALUE_OR_PRODUCT_SELECTION_CLAIM',
};

const evidencePath=resolve(root,'evidence/mechanical-acceptance-r4.json');
mkdirSync(dirname(evidencePath),{recursive:true});
writeFileSync(evidencePath,JSON.stringify(out,null,2)+'\n');
process.stdout.write(JSON.stringify(out,null,2)+'\n');
if(!pass)process.exitCode=3;
