import { readFileSync } from "node:fs";

const requiredFiles = [
  "web/render-navigation.js",
  "web/render-curves.js",
  "web/render-replay.js",
  "web/render-diagnosis.js",
  "web/render-compare.js",
];
for (const file of requiredFiles) readFileSync(file, "utf8");

const app = readFileSync("web/app.js", "utf8");
for (const marker of [
  "loadReplayReport",
  "loadReplayFrame",
  "loadDeploymentManifest",
  "compareRuns",
  "compareBaseRunId",
]) {
  if (!app.includes(marker)) throw new Error(`M5 Web app is missing ${marker}`);
}

const shell = readFileSync("web/render-shell.js", "utf8");
if (!shell.includes("data-clone-run")) throw new Error("Mission terminal surface is missing Deploy Again");

const replay = readFileSync("web/render-replay.js", "utf8");
for (const marker of ["data-replay-revision", "data-replay-jump", "renderCoreCurves"]) {
  if (!replay.includes(marker)) throw new Error(`Replay surface is missing ${marker}`);
}

const diagnosis = readFileSync("web/render-diagnosis.js", "utf8");
for (const marker of ["VERIFIED_DIRECT", "COUNTERFACTUAL_SENSITIVE", "evidenceNodeIds"]) {
  if (!diagnosis.includes(marker)) throw new Error(`Diagnosis surface is missing ${marker}`);
}

const compare = readFileSync("web/render-compare.js", "utf8");
for (const marker of ["inputDifferences", "metricDifferences", "comparisonDigest"]) {
  if (!compare.includes(marker)) throw new Error(`Compare surface is missing ${marker}`);
}

const styles = readFileSync("web/styles.css", "utf8");
for (const marker of [".product-nav", ".curve-grid", ".diagnosis-claim", ".comparison-grid"]) {
  if (!styles.includes(marker)) throw new Error(`M5 Web styles are missing ${marker}`);
}

console.log("M5 Web structural checks passed");
