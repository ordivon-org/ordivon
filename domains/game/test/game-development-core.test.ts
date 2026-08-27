import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const core = readFileSync(new URL("../docs/GAME_DEVELOPMENT_CORE.md", import.meta.url), "utf8");
const research = readFileSync(new URL("../docs/GAME_DEVELOPMENT_PARADIGM_RESEARCH.md", import.meta.url), "utf8");
const development = readFileSync(new URL("../docs/DEVELOPMENT_MODEL.md", import.meta.url), "utf8");
const reset = readFileSync(new URL("../docs/GAME_CORE_RESEARCH_RESET.md", import.meta.url), "utf8");
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const authority = readFileSync(new URL("../docs/authority.md", import.meta.url), "utf8");
const navigation = readFileSync(new URL("../research/core/PRODUCT-AND-DIRECTION-RESEARCH.md", import.meta.url), "utf8");

test("Game Development Core is responsibility evidence state beneath G0-G8 rather than new stages", () => {
  assert.match(core, /DevelopmentCore != StageProjection/);
  for (const view of [
    "D1 Intent / Audience Context",
    "D2 Play Causality",
    "D3 Player Learning / Legibility",
    "D4 Evidence / Prototyping",
    "D5 Content / Progression Architecture",
    "D6 Expression / Feel",
    "D7 Production Realization",
    "D8 Product Ecology / Evolution",
  ]) assert.match(core, new RegExp(view.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  assert.match(development, /GameDevelopmentCore != G0–G8 StageProjection/);
  assert.match(authority, /GAME_DEVELOPMENT_CORE\.md.*creates no product stage, Foundation or repository service/s);
});

test("prototype evidence is medium-relative and vertical slice remains a compound evidence bundle", () => {
  assert.match(core, /PrototypeEvidenceContract/);
  assert.match(core, /CheapestPrototype != CheapestValidPrototype/);
  assert.match(core, /FalsePositiveRisks/);
  assert.match(core, /Vertical Slice is a compound evidence bundle/);
  for (const claim of ["ExperienceRepresentativeness", "QualityBar", "IntegrationProof", "PipelineProof", "ThroughputEstimate", "PerformanceEnvelope"]) {
    assert.match(core, new RegExp(claim));
  }
  assert.match(development, /cheapest \*\*valid evidence carrier\*\*/);
  assert.match(development, /vertical slice is a \*\*compound evidence bundle\*\*/i);
});

test("player evidence, content progression and ecology remain typed rather than collapsed", () => {
  assert.match(core, /PlayerEvidenceRecord/);
  assert.match(core, /PopulationExperiment != MachineCounterfactual/);
  assert.match(core, /ContentProgressionArchitecture/);
  assert.match(core, /MacroArchitecture != MicroContent/);
  assert.match(core, /TelemetryCorrelation != CausalEffect/);
  assert.match(development, /target population\/context, method, sample scope, decision, known limitation and result standing/);
});

test("external paradigm research changes development representation without reopening foundations or prototypes", () => {
  for (const concept of ["Formal Abstract Design Tools", "MDA", "Cerny", "Rational Game", "Games User Research", "Procedural/content pipelines", "Agent-era production"]) {
    assert.match(research, new RegExp(concept));
  }
  assert.match(research, /GDF0–GDF3 = unchanged/);
  assert.match(research, /Existing playable experiments = retained apparatus \/ no product momentum/);
  assert.match(reset, /do not advance them as products/);
  assert.match(reset, /decision-relevant uncertainty removed/);
});

test("first lookup exposes the development-core repair", () => {
  assert.match(readme, /GAME_DEVELOPMENT_CORE\.md/);
  assert.match(readme, /GAME_DEVELOPMENT_PARADIGM_RESEARCH\.md/);
  assert.match(navigation, /Development Core Responsibility Model/);
  assert.match(navigation, /Game Development Paradigm Research/);
});
