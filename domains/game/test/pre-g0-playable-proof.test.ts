import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const portfolio = readFileSync(new URL("../docs/GAME_PRE_G0_PLAYABLE_PROOF_PORTFOLIO.md", import.meta.url), "utf8");
const apparatus = readFileSync(new URL("../docs/GAME_PRE_G0_PLAYABLE_WAVE1_APPARATUS.md", import.meta.url), "utf8");
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const agents = readFileSync(new URL("../AGENTS.md", import.meta.url), "utf8");

test("Pre-G0 playable wave remains below human Player Value and G0 admission", () => {
  assert.match(portfolio, /FROZEN PROOF DESIGN \/ NO G0 ADMISSION/);
  assert.match(apparatus, /AUTOMATED APPARATUS MATERIALIZED \/ C0 UNOBSERVED \/ C1 UNOBSERVED \/ NO G0 ADMISSION/);
  assert.match(apparatus, /AutomatedApparatusEvidence[\s\S]*!= C0HumanCanary[\s\S]*!= C1MechanismEvidence[\s\S]*!= DirectionalComparison[\s\S]*!= G0Admission/);
  assert.match(apparatus, /HumanPlayerValueEvidence = unobserved/);
  assert.match(apparatus, /G0Admission = false/);
});

test("first implementation wave preserves the frozen A D I portfolio and no-Agent baseline", () => {
  for (const packet of ["PGP-A", "PGP-D", "PGP-I"]) {
    assert.match(apparatus, new RegExp(packet));
  }
  assert.match(apparatus, /PGP-B\/C\/E\/F\/G\/H\/J` remain \*\*UNTESTED\*\*, not inferior/);
  assert.match(apparatus, /Runtime Agent profile: \*\*none\*\*/);
  assert.match(apparatus, /PGP-A\.threeRoomPathCompletable = true/);
  assert.match(apparatus, /PGP-D\.multiClueDetermination = true/);
  assert.match(apparatus, /PGP-I\.composeTransformSaveCompare = true/);
});

test("first-lookup navigation exposes both frozen proof design and bounded apparatus evidence", () => {
  for (const document of ["GAME_PRE_G0_PLAYABLE_PROOF_PORTFOLIO.md", "GAME_PRE_G0_PLAYABLE_WAVE1_APPARATUS.md"]) {
    assert.match(readme, new RegExp(document.replaceAll(".", "\\.")));
    assert.match(agents, new RegExp(document.replaceAll(".", "\\.")));
  }
});
