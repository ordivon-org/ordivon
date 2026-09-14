import { W, H, FLOOR_Y, WORLD, WORLD_INVARIANT, freshState, physicsStep, runWitnesses } from './core.js';

const canvas = document.querySelector('#world');
const ctx = canvas.getContext('2d');
const regionEl = document.querySelector('[data-region]');
const routeEl = document.querySelector('[data-route]');
const attemptEl = document.querySelector('[data-attempt]');
const phaseEl = document.querySelector('[data-phase]');
const traceEl = document.querySelector('[data-trace]');
const keys = new Set();
let state = freshState();
let raf = null;

function regionName(s) {
  if (s.x < 160) return s.phase === 'outbound' ? 'Hub' : 'Hub return';
  if (s.x < 330) return s.phase === 'outbound' ? 'Fork' : 'Fork revisit';
  if (s.x < 600) return 'Gate A';
  if (s.x < 865) return 'Gate B';
  return 'Far turn';
}

function inputFromKeys() {
  return {
    left:keys.has('ArrowLeft') || keys.has('KeyA'),
    right:keys.has('ArrowRight') || keys.has('KeyD'),
    jump:keys.has('Space') || keys.has('ArrowUp'),
  };
}

function draw() {
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = '#07101a'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#26384a';
  for (const p of WORLD.platforms) ctx.fillRect(p.x, p.y, p.w, p.h);
  ctx.fillStyle = '#d96b72';
  for (const h of WORLD.hazards) ctx.fillRect(h.x, h.y, h.w, h.h);
  ctx.fillStyle = '#d8a64f';
  for (const w of WORLD.ruleWindows) {
    const platform = WORLD.platforms.find(p => p.id === w.platform);
    if (platform) ctx.fillRect(w.x0 - 12, platform.y - 6, Math.max(12, w.x1 - w.x0), 6);
  }
  ctx.fillStyle = '#79e0c5';
  ctx.fillRect(WORLD.fastTurnX, 278, 10, 42);
  ctx.fillRect(WORLD.safeTurnX, FLOOR_Y - 42, 10, 42);
  ctx.fillStyle = '#92aaff'; ctx.fillRect(state.x, state.y, 24, 32);
  ctx.fillStyle = '#96a3b7'; ctx.font = '13px ui-monospace';
  ctx.fillText('Hub', 18, 24); ctx.fillText('Fork', 190, 24); ctx.fillText('Gate A', 390, 24); ctx.fillText('Gate B', 680, 24); ctx.fillText('Turn', 900, 24);
  regionEl.textContent = regionName(state);
  routeEl.textContent = state.route;
  attemptEl.textContent = String(state.attempt);
  phaseEl.textContent = state.phase;
  traceEl.innerHTML = state.events.slice(-14).reverse().map(e => `<div>${e.frame} · ${e.kind}${e.route ? ` · ${e.route}` : ''}${e.window ? ` · ${e.window}` : ''}${e.reason ? ` · ${e.reason}` : ''}</div>`).join('') || '<div>No events yet.</div>';
  canvas.dataset.playerX = state.x.toFixed(2);
  canvas.dataset.playerY = state.y.toFixed(2);
  canvas.dataset.phase = state.phase;
  canvas.dataset.route = state.route;
  canvas.dataset.attempt = String(state.attempt);
  canvas.dataset.worldInvariant = WORLD_INVARIANT;
}

function loop() {
  physicsStep(state, inputFromKeys());
  draw();
  raf = requestAnimationFrame(loop);
}

window.addEventListener('keydown', e => {
  if (['ArrowLeft','ArrowRight','ArrowUp','Space','KeyA','KeyD'].includes(e.code)) {
    e.preventDefault(); keys.add(e.code);
  }
});
window.addEventListener('keyup', e => keys.delete(e.code));
document.querySelector('[data-reset]').addEventListener('click', () => { state = freshState(); draw(); });
window.__PC03_F0__ = {
  runWitnesses,
  snapshot:() => JSON.parse(JSON.stringify(state)),
  worldInvariant:WORLD_INVARIANT,
};
draw();
raf = requestAnimationFrame(loop);
