import { ACTIONS, createRouteState, publicView, runWitnesses, step } from './core.js';

const routeEl = document.querySelector('[data-route]');
const positionEl = document.querySelector('[data-position]');
const markerEl = document.querySelector('[data-marker]');
const pulseEl = document.querySelector('[data-pulse]');
const resultEl = document.querySelector('[data-result]');
const consequenceEl = document.querySelector('[data-consequence]');
let routeId = 'route1';
let state = createRouteState(routeId);

function draw() {
  const v = publicView(state);
  routeEl.textContent = v.routeId;
  positionEl.textContent = String(v.position);
  markerEl.textContent = v.launchMarker ? 'YES' : 'NO';
  pulseEl.textContent = v.pulse;
  resultEl.textContent = v.terminal ? (v.success ? 'CLEARED' : 'MISSED') : 'RUNNING';
  consequenceEl.textContent = v.consequence;
  document.body.dataset.success = String(v.success);
}

for (const button of document.querySelectorAll('[data-action]')) {
  button.addEventListener('click', () => { step(state, button.dataset.action); draw(); });
}
document.querySelector('[data-switch]').addEventListener('click', () => {
  routeId = routeId === 'route1' ? 'route2' : 'route1';
  state = createRouteState(routeId);
  draw();
});
document.querySelector('[data-reset]').addEventListener('click', () => { state = createRouteState(routeId); draw(); });
window.__E02_TRANSFER_ROUTE__ = { ACTIONS, runWitnesses, snapshot: () => publicView(state) };
draw();
