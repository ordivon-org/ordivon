import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const ds1 = readFileSync(new URL("../docs/GAME_PRE_G0_DS1_CHEAP_FALSIFIERS.md", import.meta.url), "utf8");
const evidence = JSON.parse(readFileSync(new URL("../evidence/pre-g0/ds1-structural-battery.json", import.meta.url), "utf8")) as {
  kind: string;
  results: Array<{ candidateId: string; verdict: string; metrics: Record<string, unknown>; nextEvidence: string }>;
  summary: { structuralSurvivors: string[]; realizationEliminated: string[]; structuralFailures: string[]; foundationReopenConditionTriggered: boolean };
};
const packageJson = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8")) as { scripts: Record<string, string> };
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const agents = readFileSync(new URL("../AGENTS.md", import.meta.url), "utf8");

test("DS1 keeps structural falsification below human Player Value claims", () => {
  assert.match(ds1, /SimulationSurvival != PlayerValueProof/);
  assert.match(ds1, /Structural failure can kill a cheap realization\.[\s\S]*Structural survival only earns the next falsifier/);
  assert.match(ds1, /Poor realization != dead form/);
  assert.match(ds1, /Product selected: no/);
  assert.match(ds1, /G0 entered: no/);
});

test("DS1 evidence records measured survivors and realization deletions without a foundation reopen", () => {
  assert.equal(evidence.kind, "ordivon.game.pre-g0-ds1-structural-battery");
  assert.deepEqual(evidence.summary.structuralSurvivors, ["D03", "D04", "D05", "D14"]);
  assert.deepEqual(evidence.summary.realizationEliminated, ["D02", "D15"]);
  assert.deepEqual(evidence.summary.structuralFailures, []);
  assert.equal(evidence.summary.foundationReopenConditionTriggered, false);
  assert.equal(evidence.results.length, 6);
});

test("D03 scarcity ablation and D14 cheaper-baseline result are retained exactly", () => {
  const d03 = evidence.results.find((result) => result.candidateId === "D03");
  const d14 = evidence.results.find((result) => result.candidateId === "D14");
  assert.ok(d03);
  assert.ok(d14);
  assert.equal(d03.verdict, "structural-survivor");
  assert.equal(d03.metrics.scarcityCreatesAdaptiveAdvantage, true);
  assert.equal(d03.metrics.generousBudgetCollapsesAdaptiveAdvantage, true);
  assert.equal(d14.verdict, "structural-survivor");
  assert.match(d14.nextEvidence, /expensive model cognition is not yet necessary/);
  assert.match(ds1, /ResponsiveOtherNeed[\s\S]*!=[\s\S]*LLMNeed/);
});

test("DS1 is reproducible from the repository and canonical navigation exposes it", () => {
  assert.equal(packageJson.scripts["eval:pre-g0:ds1"], "node scripts/pre-g0/ds1-battery.ts");
  assert.match(readme, /GAME_PRE_G0_DS1_CHEAP_FALSIFIERS\.md/);
  assert.match(agents, /GAME_PRE_G0_DS1_CHEAP_FALSIFIERS\.md/);
});
