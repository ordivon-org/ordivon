import {createHash} from 'node:crypto';
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

// @ts-expect-error Browser-compatible JS core intentionally has no declaration file.
import {SCENARIOS,commit,createPlayableState,inspect,runWitnesses,selectArchitecture} from '../web/core.js';

const here=dirname(fileURLToPath(import.meta.url));
const root=resolve(here,'..');
const designPath=resolve(root,'../pc01-causal-works-f0/design.json');
const designBytes=readFileSync(designPath);
const design=JSON.parse(designBytes.toString('utf8'));
const sha256=(bytes:Buffer|string)=>'sha256:'+createHash('sha256').update(bytes).digest('hex');

function resolveTrace(
  scenarioId:string,
  {
    sourceCause,
    executionCause,
    causePersistence=true,
    diagnostic,
    architecture,
  }:{
    sourceCause:string;
    executionCause?:string;
    causePersistence?:boolean;
    diagnostic:string;
    architecture:string;
  },
){
  const state=createPlayableState(design,scenarioId,{
    sourceCause,
    executionCause:executionCause??null,
    causePersistence,
  });
  const inspected=inspect(state,diagnostic);
  selectArchitecture(state,architecture);
  const resolved=commit(state);
  return {inspection:inspected.inspection,resolution:resolved.resolution};
}

const witness=runWitnesses(design);
const routeShift=resolveTrace('route-shift',{
  sourceCause:'process',
  diagnostic:'route',
  architecture:'process',
});
const sourceRule=resolveTrace('source-rule',{
  sourceCause:'source',
  diagnostic:'route',
  architecture:'source',
});
const persistenceAblation=resolveTrace('route-shift',{
  sourceCause:'process',
  executionCause:'route',
  causePersistence:false,
  diagnostic:'process',
  architecture:'process',
});

const pass=
  witness.pass &&
  routeShift.inspection?.observation==='OK' &&
  routeShift.resolution?.net===86 &&
  sourceRule.inspection?.observation==='OK' &&
  sourceRule.resolution?.net===94 &&
  persistenceAblation.inspection?.observation==='FAULT' &&
  persistenceAblation.resolution?.sourceCause==='process' &&
  persistenceAblation.resolution?.executionCause==='route' &&
  persistenceAblation.resolution?.net===56;

const out={
  schemaVersion:1,
  kind:'ordivon.game.pc01-e03-playable-r1-mechanical-acceptance',
  designId:design.id,
  designDigest:sha256(designBytes),
  scenarios:SCENARIOS,
  witness,
  deterministicInteractiveTraces:{
    routeShift,
    sourceRule,
    persistenceAblation,
  },
  pass,
  productSelected:false,
  g0Entered:false,
  humanOutcomeEstablished:false,
  gameCoreChanged:false,
  claimBoundary:'PLAYABLE_MECHANICAL_COUPLING_ONLY_NO_HUMAN_VALUE_OR_PRODUCT_SELECTION_CLAIM',
};

const evidencePath=resolve(root,'evidence/mechanical-acceptance-r1.json');
mkdirSync(dirname(evidencePath),{recursive:true});
writeFileSync(evidencePath,JSON.stringify(out,null,2)+'\n');
process.stdout.write(JSON.stringify(out,null,2)+'\n');
if(!pass)process.exitCode=3;
