import { escapeHtml, humanize } from "./render-utils.js";

export function renderObjectives(view) {
  const nodes = view.objectives.map((objective) => `
    <article class="objective ${escapeHtml(objective.status)} ${escapeHtml(objective.priority)}">
      <header><span>${objective.status === "satisfied" ? "✓" : objective.status === "superseded" ? "↷" : objective.status === "active" ? "▶" : "○"}</span><strong>${escapeHtml(objective.label)}</strong></header>
      <small>${escapeHtml(humanize(objective.priority))} · ${escapeHtml(humanize(objective.status))}</small>
      ${objective.dependencies.length ? `<p>After: ${objective.dependencies.map(humanize).map(escapeHtml).join(", ")}</p>` : ""}
      ${objective.alternatives.length ? `<p>Alternative path: ${objective.alternatives.map((group) => group.map(humanize).join(" or ")).map(escapeHtml).join("; ")}</p>` : ""}
      ${objective.actorIds.length ? `<p>Assigned: ${objective.actorIds.map(humanize).map(escapeHtml).join(", ")}</p>` : ""}
    </article>`).join("");
  return `<section class="panel objective-panel"><div class="section-heading"><div><p class="eyebrow">MISSION GRAPH</p><h2>Verified rescue objectives</h2></div><span>${view.mission.objectiveProgress.resolved}/${view.mission.objectiveProgress.total}</span></div><div class="objective-grid">${nodes}</div></section>`;
}
