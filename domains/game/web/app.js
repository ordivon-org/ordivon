const elements = {
  roomName: document.querySelector("#room-name"),
  powerBadge: document.querySelector("#power-badge"),
  oxygen: document.querySelector("#oxygen"),
  integrity: document.querySelector("#integrity"),
  turn: document.querySelector("#turn"),
  revision: document.querySelector("#revision"),
  eventCount: document.querySelector("#event-count"),
  output: document.querySelector("#output"),
  suggest: document.querySelector("#suggest"),
  restore: document.querySelector("#restore"),
  replay: document.querySelector("#replay"),
};

let currentState = null;

function show(value) {
  elements.output.textContent = JSON.stringify(value, null, 2);
}

function render(payload) {
  currentState = payload.state;
  const room = currentState.rooms["life-support"];
  elements.roomName.textContent = room.name;
  elements.powerBadge.textContent = room.powered ? "POWERED" : "OFFLINE";
  elements.powerBadge.dataset.state = room.powered ? "online" : "offline";
  elements.oxygen.textContent = `${room.oxygen}%`;
  elements.integrity.textContent = `${Math.round(room.equipmentIntegrity * 100)}%`;
  elements.turn.textContent = String(currentState.turn);
  elements.revision.textContent = String(currentState.revision);
  elements.eventCount.textContent = `${payload.eventCount} EVENT${payload.eventCount === 1 ? "" : "S"}`;
  elements.restore.disabled = room.powered;
}

async function request(path, options) {
  const response = await fetch(path, options);
  const body = await response.json();
  if (!response.ok) {
    throw new Error(JSON.stringify(body));
  }
  return body;
}

async function loadState() {
  const payload = await request("/api/state");
  render(payload);
  show({ recovered: true, digest: payload.digest, state: payload.state });
}

elements.suggest.addEventListener("click", async () => {
  try {
    show(await request("/api/suggestion"));
  } catch (error) {
    show({ error: String(error) });
  }
});

elements.restore.addEventListener("click", async () => {
  try {
    const result = await request("/api/actions", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        kind: "restore_power",
        commandId: crypto.randomUUID(),
        actorId: "engineer-01",
        targetId: "life-support",
        expectedRevision: currentState.revision,
      }),
    });
    show(result);
    await loadState();
  } catch (error) {
    show({ error: String(error) });
  }
});

elements.replay.addEventListener("click", async () => {
  try {
    show(await request("/api/replay"));
  } catch (error) {
    show({ error: String(error) });
  }
});

loadState().catch((error) => show({ error: String(error) }));
