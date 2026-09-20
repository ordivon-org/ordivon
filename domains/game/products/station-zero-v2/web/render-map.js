import { escapeHtml, inventorySummary } from "./render-utils.js";

function entities(room, actorById) {
  const actorBadges = room.actorIds.map((actorId) => {
    const actor = actorById.get(actorId);
    return `<span class="entity actor ${escapeHtml(actor?.role ?? "actor")}">${escapeHtml(actor?.name ?? actorId)}</span>`;
  });
  const crewBadges = (room.crew ?? []).map((crew) => `<span class="entity crew">${escapeHtml(crew.name)} · ${crew.health}%</span>`);
  const systemBadges = (room.systems ?? []).map((system) => `<span class="entity system ${system.powered ? "online" : "offline"}">${escapeHtml(system.name)} · ${Math.round(system.integrity * 100)}%</span>`);
  const hazardBadges = (room.hazards ?? []).map((hazard) => `<span class="entity hazard ${hazard.controlled ? "controlled" : "active"}">${escapeHtml(hazard.name)} · ${hazard.controlled ? "controlled" : "active"}</span>`);
  return [...actorBadges, ...crewBadges, ...systemBadges, ...hazardBadges].join("");
}

export function renderMap(view) {
  const actorById = new Map(view.actors.map((actor) => [actor.actorId, actor]));
  const rooms = view.station.rooms.map((room) => `
    <article class="station-room" style="--room-x:${room.x};--room-y:${room.y}" data-room-id="${escapeHtml(room.roomId)}">
      <header><strong>${escapeHtml(room.name)}</strong><span>${room.neighbors.length} links</span></header>
      <div class="room-entities">${entities(room, actorById) || '<span class="empty-label">No local entities</span>'}</div>
      <footer>${escapeHtml(inventorySummary(room.inventory))}</footer>
    </article>`).join("");
  return `
    <section class="panel map-panel">
      <div class="section-heading">
        <div><p class="eyebrow">STATION TOPOLOGY</p><h2>Station Zero</h2></div>
        <span class="signal ${view.station.communicationAvailable ? "online" : "offline"}">${view.station.communicationAvailable ? "RADIO ONLINE" : "RADIO UNAVAILABLE"}</span>
      </div>
      <div class="station-map">${rooms}</div>
    </section>`;
}
