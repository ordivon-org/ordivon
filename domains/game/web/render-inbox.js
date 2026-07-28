import { commandAttribute, escapeHtml, humanize } from "./render-utils.js";

function commandLabel(command) {
  switch (command.action) {
    case "approve": return "Approve";
    case "deny": return "Deny";
    case "pause": return "Pause actor";
    case "resume": return "Resume actor";
    default: return humanize(command.action);
  }
}

export function renderInbox(view) {
  const cards = view.inbox.length ? view.inbox.map((card) => `
    <article class="intervention ${escapeHtml(card.severity)}">
      <header><span>${escapeHtml(humanize(card.kind))}</span><strong>${escapeHtml(card.title)}</strong></header>
      <p>${escapeHtml(card.explanation)}</p>
      <dl>
        <div><dt>Consequence</dt><dd>${escapeHtml(card.consequence)}</dd></div>
        <div><dt>Urgency</dt><dd>${escapeHtml(card.urgency)}</dd></div>
      </dl>
      ${card.expiresAtTick === null ? "" : `<small>Decision window: Tick ${card.expiresAtTick}</small>`}
      <div class="button-row">${card.commands.map((command) => `<button class="${command.action === "deny" ? "danger" : ""}" data-command="${commandAttribute(command)}">${escapeHtml(commandLabel(command))}</button>`).join("")}</div>
    </article>`).join("") : '<div class="inbox-clear"><strong>No intervention required</strong><p>The current frontier can proceed without player authority.</p></div>';
  return `<aside class="panel inbox-panel"><div class="section-heading"><div><p class="eyebrow">INTERVENTION INBOX</p><h2>Decisions requiring attention</h2></div><span>${view.inbox.length}</span></div><div class="inbox-list">${cards}</div></aside>`;
}
