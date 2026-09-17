import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const library = JSON.parse(readFileSync(new URL("../standards/game_mechanism_experience_library_r1.json", import.meta.url), "utf8")) as any;
const kb = JSON.parse(readFileSync(new URL("../standards/game_external_knowledge_base_r1.json", import.meta.url), "utf8")) as any;
const doc = readFileSync(new URL("../docs/GAME_MECHANISM_EXPERIENCE_LIBRARY_R1.md", import.meta.url), "utf8");

const unique = (values: string[]) => new Set(values).size === values.length;

test("mechanism experience library is large, source-grounded and creative-open", () => {
  assert.equal(library.schemaVersion, 1);
  assert.equal(library.libraryId, "ordivon-game-mechanism-experience-library-r1");
  assert.equal(library.policy.defaultAuthority, "ADVISORY_HYPOTHESIS");
  assert.equal(library.policy.canBlockNovelCombination, false);
  assert.equal(library.policy.componentEvidenceTransfersToComposition, false);
  assert.ok(library.experiences.length >= 48, `expected >=48 experiences, got ${library.experiences.length}`);
  assert.ok(unique(library.experiences.map((experience: any) => experience.id)));
  assert.ok(new Set(library.experiences.map((experience: any) => experience.referenceGame)).size >= 18);
});

test("experience kinds cover synergy, tension, inversion, substitution, learning, failure and production response", () => {
  const kinds = new Set(library.experiences.map((experience: any) => experience.kind));
  for (const kind of [
    "SYNERGY",
    "TENSION",
    "INVERSION",
    "SUBSTITUTION",
    "LEARNING_SCAFFOLD",
    "FAILURE_MODE",
    "PRODUCTION_RESPONSE",
    "REPRESENTATION_COUPLING",
  ]) assert.ok(kinds.has(kind), `missing ${kind}`);
});

test("every experience has a falsifiable transfer shape and never mints human evidence", () => {
  for (const experience of library.experiences) {
    assert.ok(experience.mechanisms.length >= 2, `${experience.id} mechanisms`);
    assert.ok(experience.designProblem.length > 0, `${experience.id} designProblem`);
    assert.ok(experience.interaction.length > 0, `${experience.id} interaction`);
    assert.ok(experience.playerDecisionHypothesis.length > 0, `${experience.id} playerDecisionHypothesis`);
    assert.ok(experience.observedContext.length > 0, `${experience.id} observedContext`);
    assert.ok(experience.confounds.length > 0, `${experience.id} confounds`);
    assert.ok(experience.transferRisks.length > 0, `${experience.id} transferRisks`);
    assert.ok(experience.falsifier.length > 0, `${experience.id} falsifier`);
    assert.ok(experience.cheapProbe.length > 0, `${experience.id} cheapProbe`);
    assert.ok(experience.sourceRefs.length > 0, `${experience.id} sourceRefs`);
    assert.equal(experience.authority, "ADVISORY_HYPOTHESIS");
    assert.equal(experience.inferenceLevel, "SOURCE_GROUNDED_HYPOTHESIS");
    assert.equal(experience.humanOutcomeEstablished, false);
    assert.equal(experience.canBlockNovelCombination, false);
  }
});

test("all kb source refs resolve to the external knowledge base", () => {
  const sourceIds = new Set(kb.sources.map((source: any) => `kb:${source.id}`));
  for (const experience of library.experiences) {
    for (const ref of experience.sourceRefs) assert.ok(sourceIds.has(ref), `${experience.id} missing ${ref}`);
  }
});

test("mechanism vocabulary is broad instead of one-loop biased", () => {
  const mechanisms = new Set(library.experiences.flatMap((experience: any) => experience.mechanisms));
  assert.ok(mechanisms.size >= 70, `expected >=70 mechanism tags, got ${mechanisms.size}`);
  for (const mechanism of [
    "knowledge-progression",
    "resource-recovery-from-enemies",
    "rule-as-world-object",
    "reactive-dialogue",
    "combinable-object-grammar",
    "shared-logistics-configuration",
    "fast-retry",
    "no-fail-narrative-progression",
    "copy-modify-create",
    "systemic-authorial-meaning",
  ]) assert.ok(mechanisms.has(mechanism), `missing mechanism ${mechanism}`);
});

test("failure/revision knowledge is first-class rather than success-only", () => {
  assert.ok(library.experiences.filter((experience: any) => ["FAILURE_MODE", "TENSION", "PRODUCTION_RESPONSE"].includes(experience.kind)).length >= 14);
  assert.ok(library.experiences.some((experience: any) => experience.referenceGame === "Saturnalia" && experience.kind === "PRODUCTION_RESPONSE"));
  assert.ok(library.experiences.some((experience: any) => experience.referenceGame === "Factorio" && /reopen/i.test(experience.interaction)));
  assert.ok(library.experiences.some((experience: any) => experience.referenceGame === "Into the Breach" && /cut|remove|delete/i.test(experience.interaction)));
});

test("human guide defines Pattern to Experience to Probe without making recipes", () => {
  assert.match(doc, /Pattern.*Experience.*Probe/is);
  assert.match(doc, /Creative-Open/i);
  assert.match(doc, /not.*recipe/is);
  assert.match(doc, /failure|tension|inversion/i);
  assert.match(doc, /Human evidence/i);
});


test("library is discoverable without inflating the domain graph into a second ontology", () => {
  const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
  const authority = readFileSync(new URL("../docs/authority.md", import.meta.url), "utf8");
  const project = readFileSync(new URL("../.ordivon/project.yaml", import.meta.url), "utf8");
  const graph = JSON.parse(readFileSync(new URL("../standards/game_domain_package_graph_r1.json", import.meta.url), "utf8")) as any;

  assert.match(readme, /GAME_MECHANISM_EXPERIENCE_LIBRARY_R1\.md/);
  assert.match(readme, /knowledge:mechanisms/);
  assert.match(authority, /Mechanism Experience Library/i);
  assert.match(project, /docs\/GAME_MECHANISM_EXPERIENCE_LIBRARY_R1\.md/);
  assert.match(project, /standards\/game_mechanism_experience_library_r1\.json/);
  assert.match(project, /scripts\/mechanism-experience-query\.ts/);

  assert.equal(graph.mechanismExperienceLibrary.path, "standards/game_mechanism_experience_library_r1.json");
  assert.equal(graph.mechanismExperienceLibrary.authority, "ADVISORY_HYPOTHESIS_MEMORY");
  assert.equal(graph.mechanismExperienceLibrary.canBlockNovelCombination, false);
  assert.equal(graph.mechanismExperienceLibrary.embeddedInGraph, false);
});
