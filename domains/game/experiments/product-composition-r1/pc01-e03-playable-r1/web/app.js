import {
  commit,
  createPlayableState,
  inspect,
  publicView,
  runWitnesses,
  selectArchitecture,
} from './core.js';

const design=await fetch('/experiments/product-composition-r1/pc01-causal-works-f0/design.json',{cache:'no-store'}).then(async response=>{
  if(!response.ok)throw new Error(`PC01 design load failed: ${response.status}`);
  return response.json();
});

const scenarioEl=document.querySelector('[data-scenario]');
const resetEl=document.querySelector('[data-reset]');
const commitEl=document.querySelector('[data-commit]');
const inspectionEl=document.querySelector('[data-inspection]');
const aftermathEl=document.querySelector('[data-aftermath]');
const statusEl=document.querySelector('[data-status]');
const previousEl=document.querySelector('[data-previous]');
const currentIdEl=document.querySelector('[data-current-id]');
const currentContextEl=document.querySelector('[data-current-context]');
const currentSymptomEl=document.querySelector('[data-current-symptom]');
const forecastIdEl=document.querySelector('[data-forecast-id]');
const forecastContextEl=document.querySelector('[data-forecast-context]');
const forecastSymptomEl=document.querySelector('[data-forecast-symptom]');
const architectureButtons=[...document.querySelectorAll('[data-arch]')];
const inspectButtons=[...document.querySelectorAll('[data-inspect]')];

let state=createPlayableState(design,scenarioEl.value);

function pretty(value){
  return String(value??'').replaceAll('-',' ').replaceAll('_',' ').toUpperCase();
}

function draw(){
  const view=publicView(state);
  document.body.dataset.causeRevealed=String(view.phase==='resolved');

  currentIdEl.textContent=view.currentContext.id;
  currentContextEl.textContent=view.currentContext.operatingContext;
  currentSymptomEl.textContent=`Observed · ${view.currentContext.visibleSymptom}`;

  if(view.executionForecast.visible){
    forecastIdEl.textContent=view.executionForecast.id;
    forecastContextEl.textContent=view.executionForecast.operatingContext;
    forecastSymptomEl.textContent=`Expected signal frame · ${view.executionForecast.visibleSymptom}`;
  }else{
    forecastIdEl.textContent='FORECAST WITHHELD';
    forecastContextEl.textContent='No execution-context forecast is available.';
    forecastSymptomEl.textContent='';
  }

  previousEl.textContent=`Built architecture · ${view.previousArchitecture?pretty(view.previousArchitecture):'NONE'}`;
  inspectionEl.textContent=view.inspection
    ? `${pretty(view.inspection.diagnostic)} SCAN → ${view.inspection.observation}`
    : 'NO SCAN USED';

  for(const button of architectureButtons){
    const selected=button.dataset.arch===view.selectedArchitecture;
    button.classList.toggle('selected',selected);
    button.setAttribute('aria-pressed',String(selected));
    button.disabled=view.phase==='resolved';
  }
  for(const button of inspectButtons){
    button.disabled=view.phase==='resolved'||Boolean(view.inspection);
  }
  commitEl.disabled=view.phase==='resolved'||!view.selectedArchitecture;

  if(view.phase==='resolved'){
    const r=view.resolution;
    statusEl.textContent='Command executed after the forecast context shift.';
    aftermathEl.textContent=[
      'AFTERMATH',
      `CURRENT CAUSE · ${pretty(r.sourceCause)}`,
      `EXECUTION CAUSE · ${pretty(r.executionCause)}`,
      `COMMITTED · ${pretty(r.architecture)}`,
      `BASE · ${r.baseReward}`,
      `DIAGNOSTIC · ${r.diagnosticCost}`,
      `SWITCH · ${r.switchCost}`,
      `NET · ${r.net}`,
    ].join('   |   ');
  }else{
    statusEl.textContent=view.selectedArchitecture
      ? `${pretty(view.selectedArchitecture)} selected. Commit executes after the shown context shift.`
      : 'Select an architecture. You may inspect once before committing.';
    aftermathEl.textContent='AFTERMATH · unresolved';
  }
}

function reset(scenarioId=scenarioEl.value,options={}){
  scenarioEl.value=scenarioId;
  state=createPlayableState(design,scenarioId,options);
  draw();
  return publicView(state);
}

for(const button of architectureButtons){
  button.addEventListener('click',()=>{
    selectArchitecture(state,button.dataset.arch);
    draw();
  });
}
for(const button of inspectButtons){
  button.addEventListener('click',()=>{
    inspect(state,button.dataset.inspect);
    draw();
  });
}
commitEl.addEventListener('click',()=>{
  commit(state);
  draw();
});
resetEl.addEventListener('click',()=>reset());
scenarioEl.addEventListener('change',()=>reset(scenarioEl.value));

window.__PC01_E03_PLAYABLE__={
  runWitnesses:()=>runWitnesses(design),
  snapshot:()=>publicView(state),
  resetForAcceptance:(scenarioId,options={})=>reset(scenarioId,options),
};

draw();
