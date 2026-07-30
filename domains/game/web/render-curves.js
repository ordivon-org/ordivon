import { escapeHtml } from "./render-utils.js";

function points(points, width, height, maximum = null) {
  if (!points?.length) return "";
  const values = points.map((point) => Number(point.value));
  const low = Math.min(0, ...values);
  const high = maximum ?? Math.max(1, ...values);
  const span = Math.max(1, high - low);
  return points.map((point, index) => {
    const x = points.length === 1 ? width / 2 : (index / (points.length - 1)) * width;
    const y = height - ((Number(point.value) - low) / span) * height;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
}

export function renderCurve(label, series, revision, maximum = null) {
  const width = 420;
  const height = 110;
  const selected = series?.find((point) => point.revision === revision) ?? series?.at(-1);
  const markerX = series?.length > 1 ? (revision / (series.length - 1)) * width : 0;
  return `
    <article class="curve-card">
      <header><span>${escapeHtml(label)}</span><strong>${selected?.value ?? "—"}</strong></header>
      <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(label)} by revision">
        <line x1="0" y1="${height}" x2="${width}" y2="${height}" class="curve-axis" />
        <polyline points="${points(series, width, height, maximum)}" class="curve-line" />
        <line x1="${markerX.toFixed(1)}" y1="0" x2="${markerX.toFixed(1)}" y2="${height}" class="curve-marker" />
      </svg>
      <small>Revision ${revision} · ${series?.length ?? 0} verified points</small>
    </article>`;
}

export function renderCoreCurves(curves, revision) {
  if (!curves) return "";
  return `<section class="curve-grid" aria-label="Mission resource curves">
    ${renderCurve("Battery", curves.battery, revision, 100)}
    ${renderCurve("Oxygen", curves.oxygen, revision, 100)}
    ${renderCurve("Reactor heat", curves.reactorHeat, revision, 100)}
  </section>`;
}
