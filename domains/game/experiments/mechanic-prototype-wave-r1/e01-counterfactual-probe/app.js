import { ACTIONS, FAULTS, createState, publicView, runWitnesses, step } from './core.js';

const status = document.querySelector('[data-status]');
const signal = document.querySelector('[data-signal]');
const observations = document.querySelector('[data-observations]');
const budget = document.querySelector('[data-budget]');
const result = document.querySelector('[data-result]');
const scenario = document.querySelector('[data-scenario]');
let round = 0;
let state = createState(FAULTS.BLOCKAGE);

function reset() {
  round += 1;
  state = createState(round % 2 ? FAULTS.BLOCKAGE : FAULTS.DEPLETION);
  draw();
}

function draw() {
  const view = publicView(state);
  signal.textContent = view.publicSignal;
  observations.textContent = view.observations.length
    ? view.observations.map((x) => `${x.channel}: ${x.value}`).join(' · ')
    : 'none';
  budget.textContent = String(view.inspectionsLeft);
  status.textContent = view.consequence;
  result.textContent = view.terminal ? (view.success ? 'STABLE' : 'SHUTDOWN') : 'UNRESOLVED';
  scenario.textContent = `Case ${round}`;
  document.body.dataset.terminal = String(view.terminal);
  document.body.dataset.success = String(view.success);
}

for (const button of document.querySelectorAll('[data-action]')) {
  button.addEventListener('click', () => {
    step(state, button.dataset.action);
    draw();
  });
}
document.querySelector('[data-reset]').addEventListener('click', reset);
window.__E01_COUNTERFACTUAL_PROBE__ = { ACTIONS, reset, runWitnesses, snapshot: () => publicView(state) };
reset();
