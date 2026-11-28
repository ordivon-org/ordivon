import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const library = JSON.parse(readFileSync(new URL("../knowledge/game_mechanism_experience_library_r1.json", import.meta.url), "utf8")) as any;
const kb = JSON.parse(readFileSync(new URL("../knowledge/game_external_knowledge_base_r1.json", import.meta.url), "utf8")) as any;

const unique = (values: string[]) => new Set(values).size === values.length;

test("mechanism experience library is source-grounded and creative-open", () => {
  assert.equal(library.schemaVersion, 1);
  assert.equal(library.libraryId, "ordivon-game-mechanism-experience-library-r1");
  assert.equal(library.policy.defaultAuthority, "ADVISORY_HYPOTHESIS");
  assert.equal(library.policy.canBlockNovelCombination, false);
  assert.equal(library.policy.componentEvidenceTransfersToComposition, false);
  assert.ok(library.experiences.length > 0, "mechanism query requires at least one grounded experience");
  assert.ok(unique(library.experiences.map((experience: any) => experience.id)));
  assert.ok(library.experiences.every((experience: any) => typeof experience.referenceGame === "string" && experience.referenceGame.trim().length > 0));
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

function qualifyExperiences(experiences: any[]): void {
  const sourceIds = new Set(kb.sources.map((source: any) => "kb:" + source.id));
  assert.ok(unique(experiences.map((experience) => experience.id)), "duplicate Experience IDs");
  for (const experience of experiences) {
    assert.ok(experience.mechanisms.length >= 2, experience.id + " mechanisms");
    for (const key of ["designProblem", "interaction", "playerDecisionHypothesis", "observedContext", "confounds", "transferRisks", "falsifier", "cheapProbe"]) {
      assert.ok(experience[key].length > 0, experience.id + " " + key);
    }
    assert.ok(experience.sourceRefs.length > 0, experience.id + " sourceRefs");
    for (const ref of experience.sourceRefs) assert.ok(sourceIds.has(ref), experience.id + " missing " + ref);
    assert.equal(experience.authority, "ADVISORY_HYPOTHESIS", experience.id + " authority");
    assert.equal(experience.inferenceLevel, "SOURCE_GROUNDED_HYPOTHESIS", experience.id + " inference");
    assert.equal(experience.humanOutcomeEstablished, false, experience.id + " cannot mint Human evidence");
    assert.equal(experience.canBlockNovelCombination, false, experience.id + " cannot veto");
  }
}

test("every experience has a falsifiable transfer shape, closed sources and no Human authority", () => {
  qualifyExperiences(library.experiences);
});

test("one independently useful experience is qualified; duplicate, orphan and veto fail", () => {
  const sample = library.experiences[0];
  assert.ok(sample);
  qualifyExperiences([sample]);
  assert.throws(() => qualifyExperiences([sample, sample]), /duplicate Experience IDs/);
  assert.throws(() => qualifyExperiences([{...sample, sourceRefs: ["kb:unknown-source"]}]), /missing kb:unknown-source/);
  assert.throws(() => qualifyExperiences([{...sample, canBlockNovelCombination: true}]), /cannot veto/);
  assert.throws(() => qualifyExperiences([{...sample, humanOutcomeEstablished: true}]), /cannot mint Human evidence/);
});

test("mechanism vocabulary is normalized and source-indexable", () => {
  const mechanisms = new Set(library.experiences.flatMap((experience: any) => experience.mechanisms));
  assert.ok([...mechanisms].every((tag: any) => typeof tag === "string" && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(tag)));
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
  assert.ok(library.experiences.some((experience: any) => ["FAILURE_MODE", "TENSION", "PRODUCTION_RESPONSE"].includes(experience.kind)));
  assert.ok(library.experiences.some((experience: any) => experience.referenceGame === "Saturnalia" && experience.kind === "PRODUCTION_RESPONSE"));
  assert.ok(library.experiences.some((experience: any) => experience.referenceGame === "Factorio" && /reopen/i.test(experience.interaction)));
  assert.ok(library.experiences.some((experience: any) => experience.referenceGame === "Into the Breach" && /cut|remove|delete/i.test(experience.interaction)));
});


test("mechanism experience is registered in the owner LEGO plan without a second ontology", () => {
  const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
  const project = readFileSync(new URL("../.ordivon/project.yaml", import.meta.url), "utf8");
  const plan = JSON.parse(readFileSync(new URL("../planning/lego-plan-r1.json", import.meta.url), "utf8")) as any;
  const node = plan.nodes.find((x: any) => x.id === "G02");
  assert.ok(node);
  assert.match(readme, /knowledge:mechanisms/);
  assert.match(project, /knowledge\/game_mechanism_experience_library_r1\.json/);
  assert.ok(node.evidence.includes("scripts/mechanism-experience-query.ts"));
  assert.match(node.behavioralContract, /novel compositions/i);
  assert.equal(plan.nodes.some((x: any) => x.label === "GameFramework"), false);
});
