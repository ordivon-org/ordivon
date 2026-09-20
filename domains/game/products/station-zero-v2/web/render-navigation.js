import { escapeHtml, humanize } from "./render-utils.js";

const SURFACES = [
  ["mission", "Mission"],
  ["replay", "Replay"],
  ["diagnosis", "Diagnosis"],
  ["compare", "Compare"],
];

export function renderProductNav({ surface = "mission", runId = null, compareReady = false } = {}) {
  const tabs = SURFACES.map(([id, label]) => {
    const disabled = !runId || (id === "compare" && !compareReady);
    return `<button class="product-tab ${surface === id ? "active" : ""}" data-surface="${id}" ${disabled ? "disabled" : ""}>${label}</button>`;
  }).join("");
  return `
    <nav class="product-nav" aria-label="Station Zero views">
      <div><span>ORDIVON GAME</span><strong>${runId ? escapeHtml(humanize(runId)) : "Station Zero"}</strong></div>
      <div class="product-tabs">${tabs}</div>
    </nav>`;
}
