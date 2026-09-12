import { renderProductNav } from "./render-navigation.js";
import { escapeHtml, humanize } from "./render-utils.js";

function metricRows(comparison) {
  return comparison.metricDifferences.map((difference) => `
    <tr><th>${escapeHtml(humanize(difference.metric))}</th><td>${escapeHtml(difference.left)}</td><td>${escapeHtml(difference.right)}</td></tr>`).join("");
}

function manifestCard(label, side) {
  const manifest = side.manifest;
  const metrics = side.metrics;
  return `
    <article class="comparison-run ${metrics.status}">
      <p class="eyebrow">${label}</p>
      <h2>${escapeHtml(humanize(metrics.status))}</h2>
      <p>${escapeHtml(humanize(metrics.reason ?? "active"))}</p>
      <dl>
        <div><dt>Coordination</dt><dd>${escapeHtml(humanize(manifest.coordinationProfileId))}</dd></div>
        <div><dt>Score</dt><dd>${metrics.score}</dd></div>
        <div><dt>Revisions</dt><dd>${metrics.revisions}</dd></div>
        <div><dt>Minimum battery</dt><dd>${metrics.minimumBattery}</dd></div>
      </dl>
      <code>${escapeHtml(manifest.manifestDigest.slice(0, 20))}</code>
    </article>`;
}

export function renderCompare(comparison) {
  return `
    <main class="product-shell">
      ${renderProductNav({ surface: "compare", runId: comparison.right.manifest.runId, compareReady: true })}
      <header class="product-header">
        <div><p class="eyebrow">RUN COMPARISON</p><h1>${comparison.mode === "exact" ? "Exact compatible comparison" : "Descriptive comparison"}</h1><p>${escapeHtml(comparison.compatibilityReasons.join(" "))}</p></div>
        <div class="digest-chip"><span>${escapeHtml(humanize(comparison.mode))}</span><code>${escapeHtml(comparison.comparisonDigest.slice(0, 16))}</code></div>
      </header>
      <section class="comparison-grid">
        ${manifestCard("BASE RUN", comparison.left)}
        <div class="comparison-arrow" aria-hidden="true">→</div>
        ${manifestCard("CURRENT RUN", comparison.right)}
      </section>
      <section class="panel comparison-differences">
        <div class="section-heading"><div><p class="eyebrow">INPUT DIFFERENCES</p><h2>What changed</h2></div><span>${comparison.inputDifferences.length}</span></div>
        <div class="difference-list">${comparison.inputDifferences.map((difference) => `<article><strong>${escapeHtml(humanize(difference.field))}</strong><span>${escapeHtml(JSON.stringify(difference.left))}</span><b>→</b><span>${escapeHtml(JSON.stringify(difference.right))}</span></article>`).join("") || "<p>No Deployment input changed.</p>"}</div>
      </section>
      <section class="panel comparison-metrics">
        <div class="section-heading"><div><p class="eyebrow">VERIFIED METRICS</p><h2>Outcome difference</h2></div></div>
        <table><thead><tr><th>Metric</th><th>Base</th><th>Current</th></tr></thead><tbody>${metricRows(comparison)}</tbody></table>
      </section>
    </main>`;
}
