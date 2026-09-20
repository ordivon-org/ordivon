import {commitRound,createSessionRun,inspect,nextRound,publicView,selectArchitecture} from '../../causal-lag-session-r3/web/core.js';
import {FIRST_PRESSURE_RUN,compilePressureRun} from '../pressure-topology.js';

const design=await fetch('/experiments/product-composition-r1/pc01-causal-works-f0/design.json',{cache:'no-store'}).then(async response=>{
  if(!response.ok)throw new Error(`PC01 design load failed: ${response.status}`);
  return response.json();
});
const compiled=compilePressureRun(design,FIRST_PRESSURE_RUN);
const q=(s)=>document.querySelector(s);
const startEl=q('[data-start]'),newEl=q('[data-new]'),roundEl=q('[data-round]'),pressureEl=q('[data-pressure]');
const totalEl=q('[data-total]'),remainingEl=q('[data-remaining]'),maxEl=q('[data-max]'),outcomeEl=q('[data-outcome]');
const pressureNameEl=q('[data-pressure-name]'),scanCostEl=q('[data-scan-cost]'),switchCostEl=q('[data-switch-cost]'),stripEl=q('[data-pressure-strip]');
const currentIdEl=q('[data-current-id]'),currentContextEl=q('[data-current-context]'),currentSymptomEl=q('[data-current-symptom]');
const forecastIdEl=q('[data-forecast-id]'),forecastContextEl=q('[data-forecast-context]'),forecastSymptomEl=q('[data-forecast-symptom]');
const inspectionEl=q('[data-inspection]'),statusEl=q('[data-status]'),aftermathEl=q('[data-aftermath]'),historyEl=q('[data-history]');
const commitEl=q('[data-commit]'),nextEl=q('[data-next]');
const archButtons=[...document.querySelectorAll('[data-arch]')];
const inspectButtons=[...document.querySelectorAll('[data-inspect]')];
let run=null;

function pretty(v){return String(v??'').replaceAll('_',' ').replaceAll('-',' ').toUpperCase()}
function randomRegime(){return Math.random()<0.5?'STABLE':'VOLATILE'}
function activeUnit(view){
  const round=view?.current?.round??1;
  return compiled.units[Math.max(0,Math.min(compiled.units.length-1,round-1))];
}
function drawStrip(view){
  const currentRound=view?.current?.round??0;
  stripEl.innerHTML=compiled.units.map((unit,i)=>`<div class="pressure-beat ${i+1===currentRound?'current':''} ${i+1<currentRound?'done':''}" data-profile="${unit.pressureProfileId}"><span>${i+1}</span><strong>${pretty(unit.pressureProfileId)}</strong><small>${unit.sourceCycleIndex}→${unit.executionCycleIndex}</small></div>`).join('');
}
function historyHtml(history){
  if(history.length===0)return '<div class="history-empty">NO RESOLVED BEATS YET</div>';
  return history.map(item=>`<article class="history-row"><span class="history-round">R${item.round}</span><strong>${pretty(item.sourceCause)} → ${pretty(item.executionCause)}</strong><small>${pretty(item.architecture)} · ${pretty(item.diagnostic)} · NET ${item.net}</small></article>`).join('');
}
function enable(enabled,view){
  const resolved=view?.current?.phase==='resolved';
  for(const b of archButtons){
    const selected=b.dataset.arch===view?.current?.selectedArchitecture;
    b.classList.toggle('selected',selected);
    b.setAttribute('aria-pressed',String(selected));
    b.disabled=!enabled||resolved;
  }
  for(const b of inspectButtons)b.disabled=!enabled||resolved||Boolean(view?.current?.inspection);
  commitEl.disabled=!enabled||resolved||!view?.current?.selectedArchitecture;
}
function draw(){
  if(!run){
    drawStrip(null);enable(false,null);return;
  }
  const view=publicView(run),current=view.current,unit=activeUnit(view),pressure=current?.costPressure;
  roundEl.textContent=`ROUND ${current?.round??view.history.length} / ${compiled.unitCount}`;
  pressureEl.textContent=`PRESSURE · ${pretty(unit.pressureProfileId)}`;
  pressureNameEl.textContent=pretty(unit.pressureProfileId);
  scanCostEl.textContent=String(pressure?.diagnosticCost??'—');
  switchCostEl.textContent=String(pressure?.switchCost??'—');
  totalEl.textContent=String(view.totalNet);remainingEl.textContent=String(view.contract.remainingTarget);maxEl.textContent=String(view.contract.maxRecoverableTotal);
  startEl.hidden=true;newEl.hidden=false;drawStrip(view);historyEl.innerHTML=historyHtml(view.history);
  if(current){
    currentIdEl.textContent=current.currentContext.id;currentContextEl.textContent=current.currentContext.operatingContext;currentSymptomEl.textContent=`Observed · ${current.currentContext.visibleSymptom}`;
    forecastIdEl.textContent=current.executionForecast.id;forecastContextEl.textContent=current.executionForecast.operatingContext;forecastSymptomEl.textContent=`Forecast frame · ${current.executionForecast.visibleSymptom}`;
    inspectionEl.textContent=current.inspection?`${pretty(current.inspection.diagnostic)} SCAN → ${current.inspection.observation}`:'NO SCAN USED';
  }
  const active=view.sessionStatus==='ACTIVE';enable(active,view);
  if(view.sessionStatus==='SUCCESS'){outcomeEl.textContent='CONTRACT SECURED';statusEl.textContent='Pressure run complete: contract secured.'}
  else if(view.sessionStatus==='FAILURE'){outcomeEl.textContent='CONTRACT LOST';statusEl.textContent='Run terminated: target is mathematically unrecoverable.'}
  else{outcomeEl.textContent='CONTRACT ACTIVE';statusEl.textContent=`${pretty(unit.pressureProfileId)} · ${current?.selectedArchitecture?pretty(current.selectedArchitecture)+' selected.':'choose an architecture or inspect first.'}`}
  const resolved=current?.phase==='resolved';nextEl.hidden=!resolved||!active;commitEl.hidden=Boolean(resolved);
  if(resolved){
    const x=current.resolution;
    aftermathEl.textContent=['AFTERMATH',`PRESSURE · ${pretty(unit.pressureProfileId)}`,`BASE · ${x.baseReward}`,`SCAN · ${x.diagnosticCost}`,`SWITCH · ${x.switchCost}`,`NET · ${x.net}`].join('   |   ');
  }else aftermathEl.textContent='AFTERMATH · unresolved';
}
function create(options={}){
  run=createSessionRun(design,{sessionRules:compiled.sessionRules,regime:randomRegime(),...options});
  draw();
  return publicView(run);
}
startEl.addEventListener('click',()=>create());
newEl.addEventListener('click',()=>create());
for(const b of archButtons)b.addEventListener('click',()=>{selectArchitecture(run,b.dataset.arch);draw()});
for(const b of inspectButtons)b.addEventListener('click',()=>{inspect(run,b.dataset.inspect);draw()});
commitEl.addEventListener('click',()=>{commitRound(run);draw()});
nextEl.addEventListener('click',()=>{nextRound(run);draw()});
window.__CAUSAL_LAG_R5__={snapshot:()=>run?publicView(run):null,resetForAcceptance:(o={})=>create(o),compiled:()=>compiled};
draw();
