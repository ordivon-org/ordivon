import {createHash} from 'node:crypto';
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

// @ts-expect-error Browser-compatible JS core intentionally has no declaration file.
import {createLearningRun,beginRound,selectArchitecture,commit,predictivePersistence,publicView,solveLearnedPolicy,updateRegimeBelief} from '../web/core.js';

const here=dirname(fileURLToPath(import.meta.url));
const root=resolve(here,'..');
const designPath=resolve(root,'../pc01-causal-works-f0/design.json');
const designBytes=readFileSync(designPath);
const design=JSON.parse(designBytes.toString('utf8'));
const sha256=(bytes:Buffer|string)=>'sha256:'+createHash('sha256').update(bytes).digest('hex');

const persistentHistory=[{sourceCycleIndex:0,sourceCause:'process',executionCause:'process'}];
const changedHistory=[{sourceCycleIndex:0,sourceCause:'process',executionCause:'route'}];

const persistentBelief=updateRegimeBelief(design,persistentHistory);
const changedBelief=updateRegimeBelief(design,changedHistory);
const persistentPrediction=predictivePersistence(persistentBelief);
const changedPrediction=predictivePersistence(changedBelief);

const learnedPersistent=solveLearnedPolicy(design,'route-shift',persistentHistory,{historyAware:true});
const learnedChanged=solveLearnedPolicy(design,'route-shift',changedHistory,{historyAware:true});
const blindPersistent=solveLearnedPolicy(design,'route-shift',persistentHistory,{historyAware:false});
const blindChanged=solveLearnedPolicy(design,'route-shift',changedHistory,{historyAware:false});

function resolvedRun(regime:string,sourceCause:string,executionCause:string,architecture:string){
  const run=createLearningRun(design,{regime});
  beginRound(run,'route-shift',{sourceCause,executionCause});
  selectArchitecture(run,architecture);
  commit(run);
  beginRound(run,'route-shift',{sourceCause:'source',executionCause:'source'});
  return publicView(run);
}

const stablePath=resolvedRun('STABLE','process','process','process');
const changedPath=resolvedRun('VOLATILE','process','route','process');
const sameCurrentDecision=
  JSON.stringify(stablePath.current?.currentContext)===JSON.stringify(changedPath.current?.currentContext) &&
  JSON.stringify(stablePath.current?.executionForecast)===JSON.stringify(changedPath.current?.executionForecast) &&
  stablePath.current?.previousArchitecture===changedPath.current?.previousArchitecture;

const publicLeakText=(JSON.stringify(stablePath)+JSON.stringify(changedPath)).toLowerCase();
const publicModelLeak=/(stable|volatile|posterior|probability|persistenceestimate|optimal|expectedvalue)/.test(publicLeakText);

const historySensitivePolicyFlip=
  learnedPersistent.policy.diagnostic==='route' &&
  learnedChanged.policy.diagnostic==='none' &&
  JSON.stringify(learnedPersistent.policy)!==JSON.stringify(learnedChanged.policy);

const historyBlindSame=
  blindPersistent.policy.diagnostic==='none' &&
  blindChanged.policy.diagnostic==='none' &&
  JSON.stringify(blindPersistent.policy)===JSON.stringify(blindChanged.policy);

const pass=
  persistentPrediction>0.6 &&
  changedPrediction<0.3 &&
  historySensitivePolicyFlip &&
  historyBlindSame &&
  sameCurrentDecision &&
  !publicModelLeak &&
  stablePath.history.length===1 &&
  changedPath.history.length===1;

const out={
  schemaVersion:1,
  kind:'ordivon.game.pc01-e03-multiround-r2-mechanical-acceptance',
  designId:design.id,
  designDigest:sha256(designBytes),
  hiddenModel:{
    regimes:{
      STABLE:{persistence:0.9},
      VOLATILE:{persistence:0.2},
    },
    prior:{STABLE:0.5,VOLATILE:0.5},
    exposedToPlayer:false,
  },
  histories:{
    persistent:persistentHistory,
    changed:changedHistory,
  },
  oracleEvidence:{
    persistentBelief,
    changedBelief,
    persistentPrediction,
    changedPrediction,
    learnedPersistent,
    learnedChanged,
    blindPersistent,
    blindChanged,
    historySensitivePolicyFlip,
    historyBlindSame,
  },
  publicCarrierEvidence:{
    sameCurrentDecision,
    publicModelLeak,
    stablePath,
    changedPath,
  },
  pass,
  productSelected:false,
  g0Entered:false,
  humanOutcomeEstablished:false,
  humanLearningEstablished:false,
  gameCoreChanged:false,
  claimBoundary:'MULTIROUND_HISTORY_SENSITIVE_MECHANICS_ONLY_NO_HUMAN_LEARNING_OR_PRODUCT_SELECTION_CLAIM',
};

const evidencePath=resolve(root,'evidence/mechanical-acceptance-r2.json');
mkdirSync(dirname(evidencePath),{recursive:true});
writeFileSync(evidencePath,JSON.stringify(out,null,2)+'\n');
process.stdout.write(JSON.stringify(out,null,2)+'\n');
if(!pass)process.exitCode=3;
