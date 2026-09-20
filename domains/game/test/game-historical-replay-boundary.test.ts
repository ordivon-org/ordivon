import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

function text(relativePath: string): string {
  return readFileSync(new URL(`../${relativePath}`, import.meta.url), "utf8");
}

test("historical GDF2-F replay cannot route or admit current GDF4", () => {
  const currentResearch = text("research/README.md");
  const currentFoundations = text("research/core/CURRENT-FOUNDATIONS.md");
  const handoff = JSON.parse(text("evidence/gdf2-f/downstream-handoff-map.json")) as {
    nextBranch: string;
    handoffs: Array<{ owner: string }>;
    selectionPolicy: {
      knownHandoffsArePriorityOrdered: boolean;
      mustSearchBeyondKnownHandoffs: boolean;
    };
  };
  const pkg = JSON.parse(text("package.json")) as { scripts?: Record<string, string> };

  assert.match(currentResearch, /GDF4 = NOT ADMITTED/);
  assert.match(currentFoundations, /GDF4 = NOT ADMITTED/);
  assert.equal(handoff.nextBranch, "UNRESOLVED_BY_DESIGN");
  assert.equal(handoff.selectionPolicy.knownHandoffsArePriorityOrdered, false);
  assert.equal(handoff.selectionPolicy.mustSearchBeyondKnownHandoffs, true);
  assert.ok(handoff.handoffs.some((row) => row.owner === "GDF4 Time / Rhythm / Pacing"));

  const currentCommands = Object.values(pkg.scripts ?? {}).join("\n");
  assert.equal(currentCommands.includes("scripts/gdf2-f/audit-freeze.mjs"), false);
  assert.equal(currentCommands.includes("evidence/gdf2-f/downstream-handoff-map.json"), false);
});
