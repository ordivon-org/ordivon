import { escapeHtml, humanize } from "./render-utils.js";

export function renderTimeline(view) {
  const items = view.timeline.length ? view.timeline.map((item) => `
    <article class="timeline-item ${escapeHtml(item.status)}">
      <header><strong>Tick ${item.turn}</strong><span>${escapeHtml(humanize(item.status))}</span></header>
      <p>${escapeHtml(item.summary)}</p>
      ${item.actorActions.length ? `<ul>${item.actorActions.map((action) => `<li>${escapeHtml(action)}</li>`).join("")}</ul>` : ""}
      ${item.facts.length ? `<div class="verified-facts">${item.facts.map((fact) => `<span>${escapeHtml(fact)}</span>`).join("")}</div>` : ""}
    </article>`).join("") : '<p class="empty-label">No coordination Round has been verified.</p>';
  return `<section class="panel timeline-panel"><div class="section-heading"><div><p class="eyebrow">RECENT VERIFIED HISTORY</p><h2>Mission timeline</h2></div><span>Latest ${view.timeline.length}</span></div><div class="timeline-list">${items}</div></section>`;
}
