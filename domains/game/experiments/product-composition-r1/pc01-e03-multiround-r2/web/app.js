import {beginRound,commit,createLearningRun,inspect,publicView,selectArchitecture} from './core.js';

const design=await fetch('/experiments/product-composition-r1/pc01-causal-works-f0/design.json',{cache:'no-store'}).then(async response=>{
  if(!response.ok)throw new Error(`PC01 design load failed: ${response.status}`);
  return response.json();
});

const ROUND_SEQUENCE=['route-shift','route-shift','source-rule','route-shift'];
const roundEl=document.querySelector('[data-round]');
const newRunEl=document.querySelector('[data-new-run]');
const historyEl=document.querySelector('[data-history]');
const totalEl=document.querySelector('[data-total]');
const currentIdEl=document.querySelector('[data-current-id]');
const currentContextEl=document.querySelector('[data-current-context]');
const currentSymptomEl=document.querySelector('[data-current-symptom]');
const forecastIdEl=document.querySelector('[data-forecast-id]');
const forecastContextEl=document.querySelector('[data-forecast-context]');
const forecastSymptomEl=document.querySelector('[data-forecast-symptom]');
const previousEl=document.querySelector('[data-previous]');
const inspectionEl=document.querySelector('[data-inspection]');
const statusEl=document.querySelector('[data-status]');
const aftermathEl=document.querySelector('[data-aftermath]');
const commitEl=document.querySelector('[data-commit]');
const nextEl=document.querySelector('[data-next-round]');
const archButtons=[...document.querySelectorAll('[data-arch]')];
const inspectButtons=[...document.querySelectorAll('[data-inspect]')];

let run=null;
let acceptanceTransitions=null;

function pretty(value){
  return String(value??'').replaceAll('-',' ').replaceAll('_',' ').toUpperCase();
}

function randomRegime(){
  return Math.random()<0.5?'STABLE':'VOLATILE';
}

function transitionForIndex(index){
  if(acceptanceTransitions&&acceptanceTransitions[index])return acceptanceTransitions[index];
  return {scenarioId:ROUND_SEQUENCE[index]};
}

function beginIndex(index){
  const transition=transitionForIndex(index);
  beginRound(run,transition.scenarioId??ROUND_SEQUENCE[index],{
    sourceCause:transition.sourceCause??null,
    executionCause:transition.executionCause??null,
  });
}

function historyHtml(history){
  if(history.length===0)return '<div class="history-empty">NO RESOLVED ROUNDS YET</div>';
  return history.map(item=>`
    <article class="history-row">
      <span class="history-round">R${item.round}</span>
      <strong>${pretty(item.sourceCause)} <b>→</b> ${pretty(item.executionCause)}</strong>
      <span class="history-state ${item.persisted?'persisted':'changed'}">${item.persisted?'PERSISTED':'CHANGED'}</span>
      <small>NET ${item.net}</small>
    </article>
  `).join('');
}

function draw(){
  const view=publicView(run);
  historyEl.innerHTML=historyHtml(view.history);
  totalEl.textContent=String(view.totalNet);

  if(!view.current)return;
  const current=view.current;
  roundEl.textContent=`ROUND ${current.round} / ${ROUND_SEQUENCE.length}`;
  currentIdEl.textContent=current.currentContext.id;
  currentContextEl.textContent=current.currentContext.operatingContext;
  currentSymptomEl.textContent=`Observed · ${current.currentContext.visibleSymptom}`;
  forecastIdEl.textContent=current.executionForecast.id;
  forecastContextEl.textContent=current.executionForecast.operatingContext;
  forecastSymptomEl.textContent=`Expected signal frame · ${current.executionForecast.visibleSymptom}`;
  previousEl.textContent=`Built architecture · ${current.previousArchitecture?pretty(current.previousArchitecture):'NONE'}`;
  inspectionEl.textContent=current.inspection
    ? `${pretty(current.inspection.diagnostic)} SCAN → ${current.inspection.observation}`
    : 'NO SCAN USED';

  for(const button of archButtons){
    const selected=button.dataset.arch===current.selectedArchitecture;
    button.classList.toggle('selected',selected);
    button.setAttribute('aria-pressed',String(selected));
    button.disabled=current.phase==='resolved';
  }
  for(const button of inspectButtons){
    button.disabled=current.phase==='resolved'||Boolean(current.inspection);
  }

  const resolved=current.phase==='resolved';
  commitEl.hidden=resolved;
  commitEl.disabled=resolved||!current.selectedArchitecture;
  nextEl.hidden=!resolved||view.history.length>=ROUND_SEQUENCE.length;

  if(resolved){
    const r=current.resolution;
    statusEl.textContent=view.history.length>=ROUND_SEQUENCE.length
      ? 'Run complete. The transition ledger is your only model evidence.'
      : 'Round resolved. Carry the observed transition into the next decision.';
    aftermathEl.textContent=[
      'AFTERMATH',
      `CURRENT CAUSE · ${pretty(r.sourceCause)}`,
      `EXECUTION CAUSE · ${pretty(r.executionCause)}`,
      `COMMITTED · ${pretty(r.architecture)}`,
      `NET · ${r.net}`,
    ].join('   |   ');
  }else{
    statusEl.textContent=current.selectedArchitecture
      ? `${pretty(current.selectedArchitecture)} selected. Commit executes after the forecast context shift.`
      : 'Select an architecture. You may inspect once before committing.';
    aftermathEl.textContent='AFTERMATH · unresolved';
  }
}

function reset({regime=randomRegime(),transitions=null}={}){
  run=createLearningRun(design,{regime});
  acceptanceTransitions=transitions;
  beginIndex(0);
  draw();
  return publicView(run);
}

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
  commit(run);
  draw();
});
nextEl.addEventListener('click',()=>{
  if(run.history.length>=ROUND_SEQUENCE.length)return;
  beginIndex(run.history.length);
  draw();
});
newRunEl.addEventListener('click',()=>reset());

window.__PC01_E03_R2__={
  snapshot:()=>publicView(run),
  resetForAcceptance:({regime='STABLE',transitions=[]}={})=>reset({regime,transitions}),
};

reset();
