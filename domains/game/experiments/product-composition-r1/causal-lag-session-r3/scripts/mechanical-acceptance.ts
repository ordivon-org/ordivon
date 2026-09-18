import {createHash} from 'node:crypto';
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

// @ts-expect-error Browser-compatible JS core intentionally has no declaration file.
import {SESSION_RULES,commitRound,createSessionRun,inspect,nextRound,publicView,selectArchitecture} from '../web/core.js';

const here=dirname(fileURLToPath(import.meta.url));
const root=resolve(here,'..');
const designPath=resolve(root,'../pc01-causal-works-f0/design.json');
const designBytes=readFileSync(designPath);
const design=JSON.parse(designBytes.toString('utf8'));
const sha256=(bytes:Buffer|string)=>'sha256:'+createHash('sha256').update(bytes).digest('hex');

function runSuccess(){
  const run=createSessionRun(design,{
    regime:'STABLE',
    initialCause:'route',
    transitionScript:['route','route','route','route'],
  });
  for(let i=0;i<4;i++){
    selectArchitecture(run,'route');
    commitRound(run);
    if(i<3)nextRound(run);
  }
  return publicView(run);
}

function runFailure(){
  const run=createSessionRun(design,{
    regime:'STABLE',
    initialCause:'route',
    transitionScript:['route','route','route','route'],
  });
  for(let i=0;i<2;i++){
    selectArchitecture(run,'source');
    commitRound(run);
    if(i<1)nextRound(run);
  }
  return publicView(run);
}

function runCarryover(){
  const run=createSessionRun(design,{
    regime:'STABLE',
    initialCause:'process',
    transitionScript:['process','route','source','process'],
  });
  inspect(run,'route');
  selectArchitecture(run,'process');
  const first=commitRound(run);
  nextRound(run);
  const second=publicView(run);
  return {first,second};
}

const success=runSuccess();
const failure=runFailure();
const carryover=runCarryover();
const beforeResolution=createSessionRun(design,{
  regime:'VOLATILE',
  initialCause:'process',
  transitionScript:['route','source','process','route'],
});
const publicBefore=publicView(beforeResolution);
const publicLeak=/(stable|volatile|hiddenregime|executioncause)/i.test(JSON.stringify(publicBefore));

const pass=
  success.sessionStatus==='SUCCESS' &&
  success.totalNet===400 &&
  success.contract.status==='ACHIEVED' &&
  failure.sessionStatus==='FAILURE' &&
  failure.totalNet===115 &&
  failure.contract.maxRecoverableTotal===315 &&
  failure.contract.status==='FAILED_UNRECOVERABLE' &&
  carryover.first.current?.resolution?.net===86 &&
  carryover.second.current?.previousArchitecture==='process' &&
  (carryover as any).second.current?.currentContext?.id===design.cycles[1].id &&
  !publicLeak;

const out={
  schemaVersion:1,
  kind:'ordivon.game.causal-lag-session-r3-mechanical-acceptance',
  designId:design.id,
  designDigest:sha256(designBytes),
  sessionRules:SESSION_RULES,
  continuityWitness:{
    firstRound:carryover.first,
    secondRound:carryover.second,
  },
  terminalWitnesses:{
    success,
    failure,
  },
  publicBoundary:{
    preResolution:publicBefore,
    publicLeak,
  },
  pass,
  productSelected:false,
  g0Entered:false,
  humanOutcomeEstablished:false,
  gameCoreChanged:false,
  claimBoundary:'STATEFUL_SESSION_MECHANICS_ONLY_NO_HUMAN_VALUE_OR_PRODUCT_SELECTION_CLAIM',
};

const evidencePath=resolve(root,'evidence/mechanical-acceptance-r3.json');
mkdirSync(dirname(evidencePath),{recursive:true});
writeFileSync(evidencePath,JSON.stringify(out,null,2)+'\n');
process.stdout.write(JSON.stringify(out,null,2)+'\n');
if(!pass)process.exitCode=3;
