import { renderCoreCurves } from "./render-curves.js";
import { renderProductNav } from "./render-navigation.js";
import { escapeHtml, humanize } from "./render-utils.js";

const CLASS_LABELS = {
  VERIFIED_DIRECT: "Verified direct",
  VERIFIED_CONTRIBUTOR: "Verified contributor",
  COUNTERFACTUAL_SENSITIVE: "Counterfactual sensitive",
  CONTEXT_ONLY: "Context only",
};

function claims(diagnosis) {
  return diagnosis.claims.map((claim) => `
    <article class="diagnosis-claim ${claim.evidenceClass.toLowerCase().replaceAll("_", "-")}">
      <header><span>${CLASS_LABELS[claim.evidenceClass] ?? humanize(claim.evidenceClass)}</span><small>Revision ${claim.revision}</small></header>
      <h3>${escapeHtml(claim.title)}</h3>
      <p>${escapeHtml(claim.explanation)}</p>
      <details><summary>${claim.evidenceNodeIds.length} retained evidence references</summary><ul>${claim.evidenceNodeIds.map((id) => `<li><code>${escapeHtml(id)}</code></li>`).join("")}</ul></details>
    </article>`).join("");
}

export function renderDiagnosis(report, { compareReady = false } = {}) {
  const diagnosis = report.diagnosis;
  return `
    <main class="product-shell">
      ${renderProductNav({ surface: "diagnosis", runId: report.runId, compareReady })}
      <header class="product-header">
        <div><p class="eyebrow">EVIDENCE-LINKED DIAGNOSIS</p><h1>${diagnosis.terminal.status === "victory" ? "Why the mission succeeded" : diagnosis.terminal.status === "failure" ? "Why the mission failed" : "Mission remains active"}</h1><p>Deterministic explanation from retained authority records. Contributors are not presented as unique causes.</p></div>
        <div class="terminal-badge ${diagnosis.terminal.status}"><strong>${escapeHtml(humanize(diagnosis.terminal.status))}</strong><span>${escapeHtml(humanize(diagnosis.terminal.reason ?? "running"))}</span></div>
      </header>
      ${renderCoreCurves(report.curves, diagnosis.terminal.revision)}
      <section class="diagnosis-layout">
        <section class="diagnosis-claims">${claims(diagnosis)}</section>
        <aside class="panel diagnosis-method">
          <p class="eyebrow">METHOD BOUNDARY</p>
          <h2>What this report can claim</h2>
          <dl>
            <div><dt>Direct</dt><dd>Triggered the retained terminal predicate.</dd></div>
            <div><dt>Contributor</dt><dd>Verified to reduce mission margin, not asserted as sole cause.</dd></div>
            <div><dt>Counterfactual</dt><dd>One legal final-Round replacement changed terminal status.</dd></div>
            <div><dt>Context</dt><dd>Relevant retained fact without causal elevation.</dd></div>
          </dl>
          <p>${escapeHtml(diagnosis.unsupportedCounterfactualReason ?? "A bounded counterfactual sensitivity was certified.")}</p>
          <code>${escapeHtml(diagnosis.diagnosisDigest.slice(0, 24))}</code>
        </aside>
      </section>
    </main>`;
}
