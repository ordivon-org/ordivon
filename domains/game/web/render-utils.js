export function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  })[character]);
}

export function humanize(value) {
  return String(value ?? "")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replaceAll("-", " ")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function commandAttribute(command) {
  return encodeURIComponent(JSON.stringify(command));
}

export function providerOptions(providers, selected = "fixture") {
  return (providers ?? []).map((provider) => {
    const suffix = provider.deterministic ? " · deterministic" : provider.executionOwner === "external" ? " · external" : "";
    return `<option value="${escapeHtml(provider.providerId)}" ${provider.providerId === selected ? "selected" : ""}>${escapeHtml(provider.label + suffix)}</option>`;
  }).join("");
}


export function inventorySummary(inventory) {
  const values = Object.entries(inventory ?? {}).filter(([, quantity]) => Number(quantity) > 0);
  return values.length ? values.map(([item, quantity]) => `${quantity}× ${humanize(item)}`).join(", ") : "Empty";
}

export function bandClass(band) {
  return ["critical", "warning", "terminal"].includes(band) ? band : "stable";
}
