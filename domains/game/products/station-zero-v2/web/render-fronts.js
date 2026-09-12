import { escapeHtml, humanize } from "./render-utils.js";

function statusMark(status) {
  if (status === "resolved") return "✓";
  if (status === "critical") return "!";
  if (status === "at-risk") return "△";
  return "○";
}

export function renderMissionFronts(view) {
  const fronts = view.experience.fronts.map((front) => `
    <article class="mission-front ${escapeHtml(front.status)}">
      <header>
        <span class="front-status">${statusMark(front.status)}</span>
        <div><strong>${escapeHtml(front.label)}</strong><small>${escapeHtml(humanize(front.status))}</small></div>
      </header>
      <p>${escapeHtml(front.forecast)}</p>
      ${front.primaryBlocker ? `<footer>Next blocker: ${escapeHtml(front.primaryBlocker)}</footer>` : ""}
    </article>`).join("");
  return `
    <section class="mission-front-section" aria-labelledby="mission-front-heading">
      <div class="section-heading">
        <div><p class="eyebrow">MISSION FRONTS</p><h2 id="mission-front-heading">What needs command attention</h2></div>
        <span>${view.experience.fronts.filter((front) => front.status === "resolved").length}/${view.experience.fronts.length} resolved</span>
      </div>
      <div class="mission-front-grid">${fronts}</div>
    </section>`;
}
