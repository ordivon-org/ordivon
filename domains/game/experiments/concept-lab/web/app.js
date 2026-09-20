const app = document.querySelector('#app');

const concepts = [
  { id:'casefile', name:'Casefile', tag:'social detective', promise:'Infer truth from people who know and want different things.' },
  { id:'last-light', name:'Last Light', tag:'persistent companion', promise:'Reach safety with someone you need but cannot fully control.' },
  { id:'echo-hunt', name:'Echo Hunt', tag:'adaptive predator', promise:'Learn a hidden threat before it learns your habits.' },
  { id:'station-zero', name:'Station Zero', tag:'reference baseline', promise:'Existing delegated-crisis experiment; opens the retained v3 surface.' },
];

let conceptId = 'casefile';
let autonomy = true;
let seed = 1;
let state = createState();

function rng(n){ let x=(n*1664525+1013904223)>>>0; return () => ((x=(x*1664525+1013904223)>>>0)/4294967296); }
function esc(value){ return String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function logEntry(text,tone=''){ state.log.unshift({turn:state.turn,text,tone}); }
function reset(){ seed += 1; state=createState(); render(); }
function setConcept(id){ if(id==='station-zero'){ location.href='/v3'; return; } conceptId=id; state=createState(); render(); }
function setAutonomy(value){ autonomy=value; state=createState(); render(); }

function createState(){
  if(conceptId==='casefile') return newCasefile(seed);
  if(conceptId==='last-light') return newLastLight(seed);
  return newEchoHunt(seed);
}

function newCasefile(s){
  const names=['Mira','Sol','Ivo','Nera'];
  const culprit=names[s%names.length];
  const rotations={Mira:'Archive',Sol:'Lab',Ivo:'Dock',Nera:'Galley'};
  const clueByCulprit={Mira:'Badge history shows Mira crossed the relay corridor at 20:52, but her Archive terminal was active again at 21:18.',Sol:'Coolant fiber at the relay matches Lab glove stock from Sol’s shift, but the rack is shared.',Ivo:'Tool scoring matches the Dock ratchet Ivo signed out, but the sign-out does not prove who held it.',Nera:'A camera reflection shows Nera near the relay corridor at 21:07, but the face is partially obscured.'};
  return {kind:'casefile',turn:0,actionsLeft:6,culprit,names,rotations,clueByCulprit,pressure:Object.fromEntries(names.map(n=>[n,0])),revealed:[],inspected:new Set(),log:[{turn:0,text:'Navigation relay sabotaged at 21:10. Six investigation moves before the ship departs.',tone:'warn'}],terminal:null};
}

function caseQuestion(name){
  if(state.terminal||state.actionsLeft<=0) return;
  state.turn++; state.actionsLeft--; state.pressure[name]++;
  const culprit=name===state.culprit;
  const p=state.pressure[name];
  let text;
  if(!culprit){
    const saw=state.names[(state.names.indexOf(name)+1)%state.names.length];
    text=p===1 ? `${name}: “I was in ${state.rotations[name]}. Check the ordinary access record.”`
      : `${name}: “You asked already. I also saw ${saw} crossing the central corridor before the alarm.”`;
  } else if(!autonomy){
    text=`${name}: “I stayed in ${state.rotations[state.names[(state.names.indexOf(name)+2)%4]]} all evening.”`;
  } else {
    const contradicted=state.inspected.size>0;
    text=p===1 ? `${name}: “I was nowhere near the relay. I stayed in ${state.rotations[state.names[(state.names.indexOf(name)+2)%4]]}.”`
      : contradicted ? `${name}: “Fine. I passed the corridor, but only after I heard the alarm. Someone is trying to pin this on me.”`
      : `${name}: “Why keep circling back to me? Ask ${state.names[(state.names.indexOf(name)+1)%4]} where they really were.”`;
  }
  state.revealed.push(text); logEntry(text,culprit&&p>1?'warn':'');
  if(state.actionsLeft===0) logEntry('No investigation time remains. Commit an accusation.','warn');
  render();
}

const traceNames=['badge log','coolant fiber','tool scoring','camera reflection'];
function inspectTrace(index){
  if(state.terminal||state.actionsLeft<=0||state.inspected.has(index)) return;
  state.turn++; state.actionsLeft--; state.inspected.add(index);
  const targetIndex=state.names.indexOf(state.culprit);
  const relevant=index===targetIndex;
  const text=relevant ? state.clueByCulprit[state.culprit] : `${traceNames[index]} is authentic and broadly consistent with ${state.names[index]}'s account before 21:00; it does not resolve the sabotage.`;
  state.revealed.push(text); logEntry(`TRACE — ${text}`,relevant?'warn':'');
  if(state.actionsLeft===0) logEntry('No investigation time remains. Commit an accusation.','warn');
  render();
}
function accuse(name){
  if(state.terminal) return;
  state.turn++;
  state.terminal={win:name===state.culprit,text:name===state.culprit?`Correct. ${name} sabotaged the relay.`:`Wrong. ${name} is cleared when the sealed relay log is opened; ${state.culprit} was responsible.`};
  logEntry(state.terminal.text,state.terminal.win?'':'bad'); render();
}

function newLastLight(s){
  const temperaments=['protective','pragmatic','restless'];
  return {kind:'last-light',turn:1,day:1,progress:0,energy:8,food:6,maraHealth:3,trust:3,stress:0,temperament:temperaments[s%3],memory:[],log:[{turn:1,text:'Storm reaches the valley after Day 6. The beacon is 8 progress away.',tone:'warn'}],terminal:null};
}
function mood(){ if(state.stress>=4) return 'frayed'; if(state.trust>=5) return 'warm'; if(state.trust<=1) return 'guarded'; return 'watchful'; }
function companionAction(kind){
  if(state.terminal) return;
  state.turn++; const day=state.day;
  let actual=kind, note='';
  if(autonomy){
    if(kind==='send' && (state.trust<=2 || state.stress>=3)){ actual='rest'; note='Mara refuses to be used as expendable scouting and calls for a halt.'; }
    else if(kind==='shortcut' && state.maraHealth===1){ actual='rest'; note='Mara refuses the shortcut while injured.'; }
    else if(kind==='rest' && state.temperament==='restless' && state.progress<day){ actual='shortcut'; note='Mara pushes for distance despite your call to rest.'; }
  }
  if(!note) note=actual===kind ? `Mara ${autonomy?'accepts':'follows'} the plan.` : note;
  if(actual==='shortcut'){
    state.progress+=2; state.energy-=2; state.food-=1; state.stress+=1;
    if((day+seed)%3===0){ state.maraHealth--; note+=' Loose rock injures her.'; }
    if(kind==='shortcut' && autonomy) state.trust+=1;
    state.memory.push(`Day ${day}: took the hard route together`);
  } else if(actual==='send'){
    state.progress+=2; state.energy-=1; state.food-=1; state.stress+=2; state.trust-=1;
    if((day+seed)%2===0) state.maraHealth--;
    state.memory.push(`Day ${day}: you sent Mara ahead alone`);
  } else {
    state.energy=Math.min(9,state.energy+2); state.food-=2; state.stress=Math.max(0,state.stress-2); state.trust+=1; state.progress+=1;
    state.memory.push(`Day ${day}: shared food and recovered`);
  }
  logEntry(`DAY ${day} — ${note}`,(actual!==kind)?'warn':'');
  state.day++; state.turn=state.day;
  if(state.maraHealth<=0 || state.energy<=0 || state.food<0){ state.terminal={win:false,text:state.maraHealth<=0?'Mara cannot continue. The journey ends here.':'Supplies collapse before the beacon.'}; }
  else if(state.day>6){ const win=state.progress>=8; state.terminal={win,text:win?`You reach the beacon together. Mara is ${mood()} toward you.`:`The storm arrives with the beacon still ${8-state.progress} progress away.`}; }
  if(state.terminal) logEntry(state.terminal.text,state.terminal.win?'':'bad'); render();
}

function newEchoHunt(s){
  const predatorStart=[[2,2],[1,2],[2,1]][s%3];
  return {kind:'echo-hunt',turn:0,player:[0,0],predator:[...predatorStart],cores:new Set(),decoys:2,decoyUses:0,listens:2,lastMoves:[],sensor:'The hull is quiet. Two signal fragments are marked somewhere ahead.',terminal:null,log:[{turn:0,text:'Recover both signal fragments and return to Dock. The hunter is not shown on the map.',tone:'warn'}]};
}
const cellName=(x,y)=>[['Dock','Gallery','Archive'],['Service','Atrium','Relay'],['Stores','Lab','Engine']][y][x];
function dist(a,b){ return Math.abs(a[0]-b[0])+Math.abs(a[1]-b[1]); }
function stepToward(from,to){ const [x,y]=from; const dx=to[0]-x,dy=to[1]-y; if(Math.abs(dx)>=Math.abs(dy)&&dx!==0) return [x+Math.sign(dx),y]; if(dy!==0) return [x,y+Math.sign(dy)]; return [x,y]; }
function predatorStep(action){
  let target=[...state.player];
  if(action==='decoy' && (!autonomy || state.decoyUses<=1)) target=[2-state.player[0],2-state.player[1]];
  if(autonomy && state.cores.size===2) target=[0,0];
  else if(autonomy && state.lastMoves.length>=2 && state.lastMoves.at(-1)===state.lastMoves.at(-2)){
    const [dx,dy]=state.lastMoves.at(-1); target=[Math.max(0,Math.min(2,state.player[0]+dx)),Math.max(0,Math.min(2,state.player[1]+dy))];
  }
  state.predator=stepToward(state.predator,target);
}
function echoAction(action,dx=0,dy=0){
  if(state.terminal) return;
  state.turn++;
  if(action==='move'){
    const nx=state.player[0]+dx,ny=state.player[1]+dy;
    if(nx<0||ny<0||nx>2||ny>2){ state.sensor='Bulkhead. No route that way.'; state.turn--; render(); return; }
    state.player=[nx,ny]; state.lastMoves.push([dx,dy]); if(state.lastMoves.length>3) state.lastMoves.shift();
    const key=`${nx},${ny}`;
    if((key==='2,0'||key==='0,2')&&!state.cores.has(key)){ state.cores.add(key); logEntry(`Recovered signal fragment in ${cellName(nx,ny)}.`); }
  } else if(action==='listen'){
    const d=dist(state.player,state.predator); state.listens--; state.sensor=d===0?'Something is in this room. Hide or move now.':d===1?'Metal shifts immediately beyond a bulkhead. You have one action before it closes.':d===2?'A faint scrape crosses the ventilation grid.':'Only distant vibration.';
  } else if(action==='decoy' && state.decoys>0){ state.decoys--; state.decoyUses++; state.sensor=autonomy&&state.decoyUses>1?'The decoy screams. The answering footsteps do not turn toward it.':'The decoy fires; movement veers away.'; }
  if(action!=='listen') predatorStep(action);
  const caught=dist(state.player,state.predator)===0 && action!=='hide' && action!=='listen';
  if(caught){ state.terminal={win:false,text:'The hunter intercepts you before the next bulkhead closes.'}; logEntry(state.terminal.text,'bad'); }
  else if(action==='hide' && dist(state.player,state.predator)===0){ state.sensor='It enters the room, searches, then moves on. Your hiding pattern is now known.'; state.predator=stepToward(state.predator,[2,2]); }
  else if(state.cores.size===2 && state.player[0]===0 && state.player[1]===0){ state.terminal={win:true,text:'Both fragments reach Dock. Extraction seal closes behind you.'}; logEntry(state.terminal.text); }
  else if(action!=='listen'&&action!=='decoy'){
    const d=dist(state.player,state.predator); state.sensor=d<=1?'A pressure alarm flashes nearby.':d===2?'You hear one hard impact through the deck.':'No clear contact.';
  }
  render();
}

function header(){
  return `<header class="hero"><div><p class="eyebrow">Game Core research · cheap falsifiers</p><h1>Concept Lab</h1><p>Three disposable game kernels and one retained baseline. This surface measures whether an idea creates play before it earns infrastructure or production art. Switching treatment restarts the current kernel on the same seed.</p></div><div class="mode"><span>autonomy</span><button data-mode="1" class="${autonomy?'active':''}">on</button><button data-mode="0" class="${!autonomy?'active':''}">cheap baseline</button></div></header>
  <nav class="tabs">${concepts.map(c=>`<button data-concept="${c.id}" class="${conceptId===c.id?'active':''}"><strong>${c.name}</strong><span>${c.tag} · ${c.promise}</span></button>`).join('')}</nav>`;
}
function metric(label,value,detail=''){ return `<div class="metric"><span>${esc(label)}</span><strong>${esc(value)}</strong>${detail?`<small>${esc(detail)}</small>`:''}</div>`; }
function logHtml(){ return `<div class="panel"><p class="eyebrow">consequence log</p><div class="log">${state.log.map(x=>`<article class="${x.tone}"><span>step ${x.turn}</span>${esc(x.text)}</article>`).join('')}</div></div>`; }
function finishHtml(){ return state.terminal?`<div class="finish"><p class="eyebrow">session outcome</p><h3>${state.terminal.win?'SURVIVED / SOLVED':'FAILED / WRONG'}</h3><p>${esc(state.terminal.text)}</p><button data-reset>New seed</button></div>`:''; }

function renderCasefile(){
  return `<section class="game-grid"><div class="panel"><p class="eyebrow">Casefile · ${autonomy?'motive-sensitive testimony':'fixed-testimony baseline'}</p><h2>Relay sabotage / departure in ${state.actionsLeft} moves</h2>
  <div class="status-grid">${metric('moves left',state.actionsLeft)}${metric('people',4)}${metric('traces inspected',state.inspected.size)}${metric('mode',autonomy?'adaptive':'fixed')}</div>
  <h3>Question a person</h3><div class="case-people">${state.names.map(n=>`<button data-question="${n}" ${state.actionsLeft<=0||state.terminal?'disabled':''}><span class="person-card"><strong>${n}</strong><small>pressure ${state.pressure[n]}</small></span></button>`).join('')}</div>
  <h3 style="margin-top:1rem">Inspect a trace</h3><div class="action-grid">${traceNames.map((n,i)=>`<button data-trace="${i}" ${state.inspected.has(i)||state.actionsLeft<=0||state.terminal?'disabled':''}><strong>${n}</strong><br><small>spends 1 move</small></button>`).join('')}</div>
  <h3 style="margin-top:1rem">Commit accusation</h3><div class="accuse-row">${state.names.map(n=>`<button class="danger" data-accuse="${n}" ${state.terminal?'disabled':''}>Accuse ${n}</button>`).join('')}</div>${finishHtml()}
  <p class="prototype-note">Hidden truth is never rendered. In autonomy mode repeated questioning can change what a suspect volunteers or withholds; the baseline repeats a fixed testimony.</p></div>${logHtml()}</section>`;
}
function renderLastLight(){
  return `<section class="game-grid"><div class="panel"><p class="eyebrow">Last Light · ${autonomy?'autonomous companion':'puppet baseline'}</p><h2>Day ${Math.min(state.day,6)} / Beacon crossing</h2>
  <div class="status-grid">${metric('progress',`${state.progress}/8`)}${metric('energy',state.energy)}${metric('food',state.food)}${metric('Mara',mood(),`${state.maraHealth}/3 health`)}</div>
  <p>Mara is <strong>${state.temperament}</strong>. You can ask for a plan, but in autonomy mode her state and remembered treatment can change what she actually does.</p>
  <div class="action-grid"><button data-companion="shortcut" ${state.terminal?'disabled':''}><strong>Take the dangerous shortcut together</strong><br><small>+2 progress · −2 energy · −1 food · injury risk</small></button><button data-companion="send" ${state.terminal?'disabled':''}><strong>Send Mara ahead alone</strong><br><small>+2 progress · −1 energy · −1 food · stress/trust risk</small></button><button data-companion="rest" ${state.terminal?'disabled':''}><strong>Travel carefully, share food, recover</strong><br><small>+1 progress · +2 energy · −2 food · +trust</small></button></div>
  <div class="memory">${state.memory.slice(-5).map(m=>`<span>${esc(m)}</span>`).join('')||'<span>no shared history yet</span>'}</div>${finishHtml()}
  <p class="prototype-note">The falsifier is explicit: if refusal/initiative feels like arbitrary friction and the puppet baseline is clearer or more satisfying, this form does not earn autonomous cognition.</p></div>${logHtml()}</section>`;
}
function renderEcho(){
  const cells=[]; for(let y=0;y<3;y++) for(let x=0;x<3;x++){ const key=`${x},${y}`; const cls=[state.player[0]===x&&state.player[1]===y?'player':'',(key==='2,0'||key==='0,2')&&!state.cores.has(key)?'objective':'',key==='0,0'?'exit':''].filter(Boolean).join(' '); cells.push(`<div class="cell ${cls}"><div><strong>${cellName(x,y)}</strong><br><small>${state.player[0]===x&&state.player[1]===y?'YOU ':''}${key==='0,0'?'EXIT ':''}${((key==='2,0'||key==='0,2')&&!state.cores.has(key))?'SIGNAL':''}</small></div></div>`); }
  return `<section class="game-grid"><div class="panel"><p class="eyebrow">Echo Hunt · ${autonomy?'pattern-adaptive hunter':'fixed pursuit baseline'}</p><h2>Recover 2 signals, return to Dock</h2>
  <div class="status-grid">${metric('signals',`${state.cores.size}/2`)}${metric('decoys',state.decoys)}${metric('listens',state.listens)}${metric('hunter',autonomy?'adaptive':'fixed')}</div>
  <div class="map">${cells.join('')}</div><div class="sensor">${esc(state.sensor)}</div>
  <div class="action-grid"><button data-echo="move" data-dx="0" data-dy="-1" ${state.player[1]<=0?'disabled':''}>Move north</button><button data-echo="move" data-dx="1" data-dy="0" ${state.player[0]>=2?'disabled':''}>Move east</button><button data-echo="move" data-dx="0" data-dy="1" ${state.player[1]>=2?'disabled':''}>Move south</button><button data-echo="move" data-dx="-1" data-dy="0" ${state.player[0]<=0?'disabled':''}>Move west</button><button data-echo="listen" ${state.listens<=0?'disabled':''}>Listen</button><button data-echo="decoy" ${state.decoys<=0?'disabled':''}>Throw decoy</button><button data-echo="hide">Hide</button></div>${finishHtml()}
  <p class="prototype-note">The hunter is intentionally invisible. Adaptive mode predicts repeated movement, learns decoy use and guards extraction after both signals are taken. The fixed baseline simply pursues the last known player position.</p></div>${logHtml()}</section>`;
}
function render(){
  const game=conceptId==='casefile'?renderCasefile():conceptId==='last-light'?renderLastLight():renderEcho();
  app.innerHTML=`<div class="shell">${header()}${game}<section class="lab-gate"><div><strong>Goal clarity</strong><span>Can a player name the next useful action?</span></div><div><strong>Consequence</strong><span>Do choices teach quickly?</span></div><div><strong>Autonomy value</strong><span>Does the cheap baseline lose something?</span></div><div><strong>Replay desire</strong><span>Is another seed a new reasoning problem?</span></div></section></div>`;
  bind();
}
function bind(){
  document.querySelectorAll('[data-concept]').forEach(b=>b.onclick=()=>setConcept(b.dataset.concept));
  document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>setAutonomy(b.dataset.mode==='1'));
  document.querySelectorAll('[data-question]').forEach(b=>b.onclick=()=>caseQuestion(b.dataset.question));
  document.querySelectorAll('[data-trace]').forEach(b=>b.onclick=()=>inspectTrace(Number(b.dataset.trace)));
  document.querySelectorAll('[data-accuse]').forEach(b=>b.onclick=()=>accuse(b.dataset.accuse));
  document.querySelectorAll('[data-companion]').forEach(b=>b.onclick=()=>companionAction(b.dataset.companion));
  document.querySelectorAll('[data-echo]').forEach(b=>b.onclick=()=>echoAction(b.dataset.echo,Number(b.dataset.dx||0),Number(b.dataset.dy||0)));
  document.querySelectorAll('[data-reset]').forEach(b=>b.onclick=reset);
}
render();
