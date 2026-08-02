import { commandAttribute, escapeHtml, humanize } from "./render-utils.js";

function commandLabel(command) {
  switch (command.action) {
    case "approve": return "Authorize";
    case "deny": return "Deny";
    case "pause": return "Pause specialist";
    case "resume": return "Resume specialist";
    default: return humanize(command.action);
  }
}

function forecastLines(forecast) {
  if (!forecast || forecast.status !== "available") return "";
  const changes = forecast.resources
    .filter((entry) => entry.delta !== 0)
    .map((entry) => `<li><span>${escapeHtml(entry.label)}</span><strong>${entry.before} → ${entry.after}</strong><small>${entry.delta > 0 ? "+" : ""}${entry.delta}</small></li>`)
    .join("");
  const effects = forecast.irreversibleEffects.map((entry) => `<li class="irreversible"><span>Committed effect</span><strong>${escapeHtml(entry)}</strong></li>`).join("");
  if (!changes && !effects) return "";
  return `<section class="intervention-forecast"><h3>Verified next-Tick forecast</h3><ul>${changes}${effects}</ul></section>`;
}

export function renderInbox(view) {
  const cards = view.inbox.length ? view.inbox.map((card) => `
    <article class="intervention ${escapeHtml(card.severity)} ${view.experience.activeInterventionId === card.cardId ? "active" : ""}">
      <header><span>${escapeHtml(humanize(card.kind))}</span><strong>${escapeHtml(card.title)}</strong></header>
      <p>${escapeHtml(card.explanation)}</p>
      <dl>
        <div><dt>Consequence</dt><dd>${escapeHtml(card.consequence)}</dd></div>
        <div><dt>Decision context</dt><dd>${escapeHtml(card.urgency)}</dd></div>
      </dl>
      ${forecastLines(card.forecast)}
      ${card.expiresAtTick === null ? "" : `<small>Decision window: Tick ${card.expiresAtTick}</small>`}
      <div class="button-row">${card.commands.map((command) => `<button class="${command.action === "deny" ? "danger" : command.action === "approve" ? "primary" : ""}" data-command="${commandAttribute(command)}">${escapeHtml(commandLabel(command))}</button>`).join("")}</div>
    </article>`).join("") : '<div class="inbox-clear"><strong>No command decision is pending</strong><p>The team can continue under the current standing orders.</p></div>';
  return `<aside class="panel inbox-panel"><div class="section-heading"><div><p class="eyebrow">MISSION CONTROL</p><h2>Interventions</h2></div><span>${view.inbox.length}</span></div><div class="inbox-list">${cards}</div></aside>`;
}
