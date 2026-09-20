import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const core = readFileSync(new URL("../docs/GAME_DEVELOPMENT_CORE.md", import.meta.url), "utf8");
const skill = readFileSync(new URL("../skills/game-development-lenses/SKILL.md", import.meta.url), "utf8");
const research = readFileSync(new URL("../docs/GAME_DEVELOPMENT_PARADIGM_RESEARCH.md", import.meta.url), "utf8");

test("D1-D8 is an optional lens set rather than required Development Core", () => {
  assert.match(core, /Creative-open correction — 2026-09-18/);
  assert.match(core, /D1–D8 is no longer a required Game Development Core/);
  assert.match(skill, /optional and advisory/i);
  assert.match(skill, /must not block creative composition/i);
  for (const view of ["D1 Intent / Audience Context", "D2 Play Causality", "D3 Player Learning / Legibility", "D4 Evidence / Prototyping", "D5 Content / Progression Architecture", "D6 Expression / Feel", "D7 Production Realization", "D8 Product Ecology / Evolution"]) assert.match(skill, new RegExp(view.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
});

test("useful prototype/evidence distinctions remain reusable advice", () => {
  assert.match(core, /PrototypeEvidenceContract/);
  assert.match(core, /CheapestPrototype != CheapestValidPrototype/);
  assert.match(core, /MachineTrajectory != HumanExperience/);
});

test("content/expression/production observations remain available without mandatory slots", () => {
  assert.match(core, /ContentProgressionArchitecture/);
  assert.match(core, /ExpressionCriticality/);
  assert.match(core, /Production Realization/);
});

test("paradigm research remains comparative evidence, not current law", () => {
  for (const concept of ["Formal Abstract Design Tools", "MDA", "Cerny", "Rational Game", "Games User Research"]) assert.match(research, new RegExp(concept));
});
