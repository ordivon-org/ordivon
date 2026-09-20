import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const evidence = readFileSync(new URL("../docs/GAME_PLAYER_EVIDENCE_PROGRAMME.md", import.meta.url), "utf8");
const prod = readFileSync(new URL("../docs/GAME_PRODUCTION_AGENT_ENVIRONMENT.md", import.meta.url), "utf8");
const core = readFileSync(new URL("../docs/GAME_DEVELOPMENT_CORE.md", import.meta.url), "utf8");
const reset = readFileSync(new URL("../docs/GAME_CORE_RESEARCH_RESET.md", import.meta.url), "utf8");
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const authority = readFileSync(new URL("../docs/authority.md", import.meta.url), "utf8");
const navigation = readFileSync(new URL("../research/core/PRODUCT-AND-DIRECTION-RESEARCH.md", import.meta.url), "utf8");

test("player evidence separates subject method measure and claim", () => {
  assert.match(evidence, /EvidenceSubject != Method != Measure != Claim/);
  for (const claim of [
    "Usability / Actionability",
    "Understanding / Mental Model / Learning",
    "Experience / Appeal / Meaning",
    "Balance / Challenge / Strategy / Fairness",
    "Population Behaviour / Ecology",
    "Population Causal Effect",
    "Accessibility / Population-Specific Fit",
  ]) assert.match(evidence, new RegExp(claim.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
});

test("telemetry experiments and synthetic subjects retain distinct authority", () => {
  assert.match(evidence, /BehaviourProxy != PhenomenologicalTruth/);
  assert.match(evidence, /Retention != Fun/);
  assert.match(evidence, /Intervention → MetricEffect[\s\S]*PlayerValue by identity/);
  assert.match(evidence, /SyntheticSubject != HumanSubject/);
  assert.match(evidence, /LargeN != CausalIdentification/);
});

test("player evidence contract preserves horizon population transport currentness and reopen", () => {
  assert.match(evidence, /PlayerEvidenceContract/);
  for (const field of ["DecisionToInform", "ClaimFamily", "EvidenceSubject", "TargetPopulation / Context", "GameVersion / Condition", "EvidenceHorizon", "TransportScope", "KnownBias / Limitation", "ResultStanding", "ReopenCondition"]) {
    assert.match(evidence, new RegExp(field.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
  assert.match(evidence, /STALE_TO_VERSION/);
  assert.match(evidence, /TRANSPORT_UNRESOLVED/);
});

test("sample size is decision relative and no universal magic number is admitted", () => {
  assert.match(evidence, /There is no universal “correct number of playtesters.”/);
  assert.match(evidence, /SamplePlan = f/);
  assert.match(evidence, /SmallN qualitative discovery[\s\S]*population prevalence estimate/);
  assert.match(evidence, /LargeN survey[\s\S]*deep causal explanation/);
});

test("production environment comparison preserves consume adapt fork own and owner boundaries", () => {
  for (const env of ["Unity", "Unreal Engine 5.8", "Roblox", "Godot 4.6"]) assert.match(prod, new RegExp(env));
  assert.match(prod, /CONSUME[\s\S]*ADAPT \/ WRAP[\s\S]*FORK \/ MODIFY[\s\S]*OWN/);
  assert.match(prod, /External != Non-Ordivon by identity/);
  assert.match(prod, /Do not build an Ordivon Game editor\/engine platform now/);
  assert.match(prod, /Game owns[\s\S]*design\/evidence intent/);
  assert.match(prod, /Workstation owns[\s\S]*which exact local tool\/equipment\/provider is available and healthy/);
});

test("agent roles do not inherit research or metric authority", () => {
  assert.match(evidence, /ResearchAgent != SyntheticPlayer/);
  assert.match(evidence, /AnalyticsAgent != MetricAuthority/);
  assert.match(evidence, /ExperimentAgent != ProductDecisionAuthority/);
  assert.match(prod, /ProductionAgentCapability[\s\S]*AgentIntelligence × EnvironmentAffordance × FeedbackQuality × Recovery/);
});

test("owner navigation and frontier expose player evidence and production environment without new product momentum", () => {
  assert.match(core, /GAME_PLAYER_EVIDENCE_PROGRAMME\.md/);
  assert.match(core, /GAME_PRODUCTION_AGENT_ENVIRONMENT\.md/);
  assert.match(reset, /EvidenceSubject, Method, Measure and Claim remain distinct/);
  assert.match(reset, /consume → adapt → fork → own/);
  assert.match(readme, /GAME_PLAYER_EVIDENCE_PROGRAMME\.md/);
  assert.match(readme, /GAME_PRODUCTION_AGENT_ENVIRONMENT\.md/);
  assert.match(navigation, /Player Evidence Programme/);
  assert.match(navigation, /Production Agent Environment Comparison/);
  assert.match(authority, /creates no Human truth store, analytics platform or product authority/);
  assert.match(authority, /creates no engine\/editor ownership or global tool choice/);
});
