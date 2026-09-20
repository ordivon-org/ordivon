import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const kb = JSON.parse(readFileSync(new URL("../standards/game_external_knowledge_base_r1.json", import.meta.url), "utf8")) as any;
const doc = readFileSync(new URL("../docs/GAME_EXTERNAL_KNOWLEDGE_BASE_R1.md", import.meta.url), "utf8");
const queue = JSON.parse(readFileSync(new URL("../standards/game_teardown_queue_r1.json", import.meta.url), "utf8")) as any;
const skills = JSON.parse(readFileSync(new URL("../standards/game_external_skill_watchlist_r1.json", import.meta.url), "utf8")) as any;

const unique = (values: string[]) => new Set(values).size === values.length;

test("external knowledge base is broad and explicitly non-legislative", () => {
  assert.equal(kb.schemaVersion, 1);
  assert.equal(kb.knowledgePolicy.defaultDisposition, "ADVISORY_UNLESS_NATIVE_AUTHORITY_APPLIES");
  assert.equal(kb.knowledgePolicy.externalKnowledgeCanDefineGameOntology, false);
  assert.equal(kb.knowledgePolicy.teardownCanBlockNovelComposition, false);
  assert.equal(kb.knowledgePolicy.skillCanInheritAuthority, false);
  assert.ok(kb.sources.length >= 60, `expected large first-wave corpus, got ${kb.sources.length}`);
  assert.ok(unique(kb.sources.map((source: any) => source.id)));
});

test("corpus covers standards, design, research, production, teardown and agent-skill ecosystems", () => {
  const categories = new Set(kb.sources.map((source: any) => source.category));
  for (const category of [
    "STANDARD_OR_NORMATIVE_GUIDANCE",
    "ACCESSIBILITY_AND_INCLUSIVE_DESIGN",
    "GAME_DESIGN_THEORY",
    "PLAYER_RESEARCH_AND_MEASUREMENT",
    "ENGINE_AND_PRODUCTION_PRACTICE",
    "PRIMARY_DEVELOPER_TEARDOWN",
    "PLATFORM_RELEASE_AND_FEEDBACK",
    "AGENT_SKILL_AND_TOOLING",
  ]) assert.ok(categories.has(category), `missing category ${category}`);

  const authorityClasses = new Set(kb.sources.map((source: any) => source.authorityClass));
  for (const authority of [
    "NORMATIVE_STANDARD",
    "PLATFORM_GUIDANCE",
    "PEER_REVIEWED_MODEL",
    "PRIMARY_DEVELOPER_ACCOUNT",
    "OFFICIAL_ENGINE_DOCUMENTATION",
    "AGENT_SKILL_IMPLEMENTATION",
  ]) assert.ok(authorityClasses.has(authority), `missing authority ${authority}`);
});

test("every source exposes scope, extraction targets, evidence limit and currentness", () => {
  for (const source of kb.sources) {
    assert.match(source.url, /^https:\/\//, `${source.id} needs https provenance`);
    assert.ok(source.title.length > 3, `${source.id} title`);
    assert.ok(source.scope.length > 0, `${source.id} scope`);
    assert.ok(source.extractedIdeas.length > 0, `${source.id} extractedIdeas`);
    assert.ok(source.candidateUses.length > 0, `${source.id} candidateUses`);
    assert.ok(source.evidenceLimit.length > 0, `${source.id} evidenceLimit`);
    assert.ok(["CURRENT", "CURRENT_WITH_VERSION", "HISTORICAL_STILL_USEFUL", "CHECK_BEFORE_ACTION"].includes(source.currentness), `${source.id} currentness`);
    if (source.authorityClass !== "NORMATIVE_STANDARD" && source.authorityClass !== "PLATFORM_GUIDANCE") {
      assert.equal(source.canCreateGameHardConstraint, false, `${source.id} must not become Game law`);
    }
  }
});

test("teardown queue is mechanism-diverse and requires primary evidence before extraction", () => {
  assert.equal(queue.schemaVersion, 1);
  assert.ok(queue.targets.length >= 36, `expected >=36 teardown targets, got ${queue.targets.length}`);
  assert.ok(unique(queue.targets.map((target: any) => target.id)));
  const axes = new Set(queue.targets.flatMap((target: any) => target.axes));
  for (const axis of ["combat-feel", "systems-emergence", "narrative-reactivity", "economy-progression", "social-live", "puzzle-rules", "creation-ugc", "accessibility-ux", "failure-counterexample"]) assert.ok(axes.has(axis), `missing teardown axis ${axis}`);
  for (const target of queue.targets) {
    assert.ok(target.primarySourceTargets.length > 0, `${target.id} needs primary source target`);
    assert.ok(target.extractionQuestions.length >= 3, `${target.id} needs extraction questions`);
    assert.ok(target.transferRisks.length > 0, `${target.id} needs transfer risks`);
    assert.equal(target.canBlockNovelCombination, false);
  }
});

test("external skill watchlist separates knowledge, skill and tool authority", () => {
  assert.equal(skills.schemaVersion, 1);
  assert.ok(skills.skills.length >= 10);
  assert.ok(unique(skills.skills.map((skill: any) => skill.id)));
  for (const skill of skills.skills) {
    assert.ok(skill.trigger.length > 0, `${skill.id} trigger`);
    assert.ok(skill.goodParts.length > 0, `${skill.id} goodParts`);
    assert.ok(skill.risks.length > 0, `${skill.id} risks`);
    assert.ok(skill.ordivonDisposition.length > 0, `${skill.id} disposition`);
    assert.equal(skill.instructionAuthority, "ADVISORY");
  }
  assert.ok(skills.principles.some((principle: string) => /Skill.*Tool.*separate/i.test(principle)));
  assert.ok(skills.principles.some((principle: string) => /version/i.test(principle)));
});

test("human guide explains authority ladder and creative-open ingestion", () => {
  assert.match(doc, /Native authority/i);
  assert.match(doc, /Creative-Open/i);
  assert.match(doc, /Mechanism Combination Experience Library/i);
  assert.match(doc, /never.*Game constitution/is);
  assert.match(doc, /primary developer/i);
  assert.match(doc, /Skill.*Tool.*MCP/is);
});
