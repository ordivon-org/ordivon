import {commitRound,createSessionRun,inspect,nextRound,publicView,selectArchitecture,SESSION_RULES} from './core.js';

const design=await fetch('/experiments/product-composition-r1/pc01-causal-works-f0/design.json',{cache:'no-store'}).then(async response=>{
  if(!response.ok)throw new Error(`PC01 design load failed: ${response.status}`);
  return response.json();
});

const startEl=document.querySelector('[data-start]');
const newEl=document.querySelector('[data-new]');
const roundEl=document.querySelector('[data-round]');
const contractEl=document.querySelector('[data-contract]');
const totalEl=document.querySelector('[data-total]');
const remainingEl=document.querySelector('[data-remaining]');
const maxEl=document.querySelector('[data-max]');
const outcomeEl=document.querySelector('[data-outcome]');
const builtEl=document.querySelector('[data-built]');
const historyEl=document.querySelector('[data-history]');
const currentIdEl=document.querySelector('[data-current-id]');
const currentContextEl=document.querySelector('[data-current-context]');
const currentSymptomEl=document.querySelector('[data-current-symptom]');
const forecastIdEl=document.querySelector('[data-forecast-id]');
const forecastContextEl=document.querySelector('[data-forecast-context]');
const forecastSymptomEl=document.querySelector('[data-forecast-symptom]');
const inspectionEl=document.querySelector('[data-inspection]');
const statusEl=document.querySelector('[data-status]');
const aftermathEl=document.querySelector('[data-aftermath]');
const commitEl=document.querySelector('[data-commit]');
const nextEl=document.querySelector('[data-next]');
const archButtons=[...document.querySelectorAll('[data-arch]')];
const inspectButtons=[...document.querySelectorAll('[data-inspect]')];

let run=null;

function pretty(value){
  return String(value??'').replaceAll('-',' ').replaceAll('_',' ').toUpperCase();
}

function randomRegime(){
  return Math.random()<0.5?'STABLE':'VOLATILE';
}

function historyHtml(history){
  if(history.length===0)return '<div class="history-empty">NO RESOLVED ROUNDS YET</div>';
  return history.map(item=>`
    <article class="history-row">
      <span class="history-round">R${item.round}</span>
      <strong>${pretty(item.sourceCause)} <b>→</b> ${pretty(item.executionCause)}</strong>
      <span class="history-state ${item.persisted?'persisted':'changed'}">${item.persisted?'PERSISTED':'CHANGED'}</span>
      <small>${pretty(item.previousArchitecture)} → ${pretty(item.architecture)} · NET ${item.net}</small>
    </article>
  `).join('');
}

function setDecisionEnabled(enabled,view){
  const resolved=view?.current?.phase==='resolved';
  for(const button of archButtons){
    const selected=button.dataset.arch===view?.current?.selectedArchitecture;
    button.classList.toggle('selected',selected);
    button.setAttribute('aria-pressed',String(selected));
    button.disabled=!enabled||resolved;
  }
  for(const button of inspectButtons){
    button.disabled=!enabled||resolved||Boolean(view?.current?.inspection);
  }
  commitEl.disabled=!enabled||resolved||!view?.current?.selectedArchitecture;
}

function draw(){
  if(!run){
    roundEl.textContent='NOT STARTED';
    totalEl.textContent='0';
    remainingEl.textContent=String(SESSION_RULES.targetTotal);
    maxEl.textContent=String(SESSION_RULES.roundCount*100);
    outcomeEl.textContent='AWAITING START';
    builtEl.textContent=`BUILT · ${pretty(SESSION_RULES.initialArchitecture)}`;
    historyEl.innerHTML='<div class="history-empty">START THE CONTRACT TO BEGIN</div>';
    setDecisionEnabled(false,null);
    return;
  }

  const view=publicView(run);
  const current=view.current;
  totalEl.textContent=String(view.totalNet);
  remainingEl.textContent=String(view.contract.remainingTarget);
  maxEl.textContent=String(view.contract.maxRecoverableTotal);
  historyEl.innerHTML=historyHtml(view.history);
  builtEl.textContent=`BUILT · ${pretty(current?.previousArchitecture??run.currentArchitecture)}`;
  startEl.hidden=true;
  newEl.hidden=false;

  if(current){
    roundEl.textContent=`ROUND ${current.round} / ${SESSION_RULES.roundCount}`;
    currentIdEl.textContent=current.currentContext.id;
    currentContextEl.textContent=current.currentContext.operatingContext;
    currentSymptomEl.textContent=`Observed · ${current.currentContext.visibleSymptom}`;
    forecastIdEl.textContent=current.executionForecast.id;
    forecastContextEl.textContent=current.executionForecast.operatingContext;
    forecastSymptomEl.textContent=`Expected signal frame · ${current.executionForecast.visibleSymptom}`;
    inspectionEl.textContent=current.inspection
      ? `${pretty(current.inspection.diagnostic)} SCAN → ${current.inspection.observation}`
      : 'NO SCAN USED';
  }

  const active=view.sessionStatus==='ACTIVE';
  setDecisionEnabled(active,view);

  if(view.sessionStatus==='SUCCESS'){
    outcomeEl.textContent='CONTRACT SECURED';
    outcomeEl.dataset.state='success';
    statusEl.textContent='Session complete. The four-shift contract target was met.';
  }else if(view.sessionStatus==='FAILURE'){
    outcomeEl.textContent='CONTRACT LOST';
    outcomeEl.dataset.state='failure';
    statusEl.textContent='Session ended: even perfect remaining shifts cannot recover the contract.';
  }else{
    outcomeEl.textContent='CONTRACT ACTIVE';
    outcomeEl.dataset.state='active';
    statusEl.textContent=current?.selectedArchitecture
      ? `${pretty(current.selectedArchitecture)} selected. Commit lands in the forecast context.`
      : 'Select an architecture. You may inspect once before committing.';
  }

  const resolved=current?.phase==='resolved';
  nextEl.hidden=!resolved||!active;
  commitEl.hidden=Boolean(resolved);

  if(resolved){
    const r=current.resolution;
    aftermathEl.textContent=[
      'AFTERMATH',
      `CURRENT CAUSE · ${pretty(r.sourceCause)}`,
      `EXECUTION CAUSE · ${pretty(r.executionCause)}`,
      `ARCHITECTURE · ${pretty(r.architecture)}`,
      `BASE · ${r.baseReward}`,
      `SCAN · ${r.diagnosticCost}`,
      `SWITCH · ${r.switchCost}`,
      `NET · ${r.net}`,
    ].join('   |   ');
  }else{
    aftermathEl.textContent='AFTERMATH · unresolved';
  }
}

function create(options={}){
  run=createSessionRun(design,{regime:randomRegime(),...options});
  draw();
  return publicView(run);
}

startEl.addEventListener('click',()=>create());
newEl.addEventListener('click',()=>create());

for(const button of archButtons){
  button.addEventListener('click',()=>{
    selectArchitecture(run,button.dataset.arch);
    draw();
  });
}
for(const button of inspectButtons){
  button.addEventListener('click',()=>{
    inspect(run,button.dataset.inspect);
    draw();
  });
}
commitEl.addEventListener('click',()=>{
  commitRound(run);
  draw();
});
nextEl.addEventListener('click',()=>{
  nextRound(run);
  draw();
});

window.__CAUSAL_LAG_R3__={
  snapshot:()=>run?publicView(run):null,
  resetForAcceptance:(options={})=>create(options),
};

draw();
