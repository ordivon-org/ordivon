import { createInteractiveState, interactiveStep, runWitnesses } from './core.js';

const lagEl = document.querySelector('[data-lag]');
const tickEl = document.querySelector('[data-tick]');
const observedEl = document.querySelector('[data-observed]');
const directionEl = document.querySelector('[data-direction]');
const executionEl = document.querySelector('[data-execution]');
const resultEl = document.querySelector('[data-result]');
const costEl = document.querySelector('[data-cost]');
let state = createInteractiveState(Number(lagEl.value));

function draw() {
  tickEl.textContent = String(state.tick);
  observedEl.textContent = String(state.target.lane);
  directionEl.textContent = state.target.direction > 0 ? '→' : '←';
  executionEl.textContent = state.last ? `${state.last.committedLane} vs ${state.last.executionLane} · ${state.last.hit ? 'HIT' : 'MISS'}` : 'none';
  costEl.textContent = String(state.recoveryCost);
  resultEl.textContent = state.terminal ? 'ROUND COMPLETE' : 'ACTIVE';
  document.body.dataset.terminal = String(state.terminal);
}

function reset() { state = createInteractiveState(Number(lagEl.value)); draw(); }
for (const button of document.querySelectorAll('[data-lane]')) {
  button.addEventListener('click', () => { interactiveStep(state, Number(button.dataset.lane)); draw(); });
}
lagEl.addEventListener('change', reset);
document.querySelector('[data-reset]').addEventListener('click', reset);
window.__E03_COMMITMENT_LAG__ = { runWitnesses, snapshot: () => JSON.parse(JSON.stringify(state)) };
draw();
