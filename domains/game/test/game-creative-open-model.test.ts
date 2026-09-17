import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { exploreGameComposition, loadGameCreativeGraph } from "../scripts/composition-explorer.ts";

const graph = loadGameCreativeGraph();

function read(path: string): string {
  return readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
}

test("creative composition defaults open, including unmodeled mechanisms", () => {
  assert.equal(graph.creativePolicy.defaultCreativeDisposition, "OPEN_EXPLORATION");
  assert.equal(graph.creativePolicy.unmodeledMechanismDisposition, "EXPLORE_NOT_BLOCK");
  assert.equal(graph.creativePolicy.componentEvidenceInheritance, "NEVER_AUTOMATIC");

  const result = exploreGameComposition(
    {
      intent: "explore",
      elements: ["mechanic.e03", "invented.time-reversal-dialogue-physics"],
      mechanisms: ["commitment", "time-reversal", "dialogue-as-physics"],
    },
    graph,
  );

  assert.equal(result.disposition, "OPEN_EXPLORATION");
  assert.deepEqual(result.novelUnmodeledElements, ["invented.time-reversal-dialogue-physics"]);
  assert.equal(result.semanticAuthorityClaimed, false);
  assert.equal(result.compositionEvidenceInherited, false);
});

test("D1-D8, G0-G8 and minimal-kernel model are removable advisory skills, not graph law", () => {
  const expected = new Map([
    ["skill.game-development-lenses", "skills/game-development-lenses/SKILL.md"],
    ["skill.game-stage-lens", "skills/game-stage-lens/SKILL.md"],
    ["skill.game-minimal-interaction-model", "skills/game-minimal-interaction-model/SKILL.md"],
  ]);
  assert.ok(Array.isArray(graph.advisorySkills));
  for (const [id, path] of expected) {
    const skill = graph.advisorySkills.find((candidate) => candidate.id === id);
    assert.ok(skill, `missing advisory skill ${id}`);
    assert.equal(skill.path, path);
    assert.equal(skill.removable, true);
    assert.equal(skill.canBlockCreativeComposition, false);
    const source = read(path);
    assert.match(source, /^---\nname:/);
    assert.match(source, /optional|advisory/i);
    assert.match(source, /never block|must not block/i);
  }

  assert.equal(graph.nodes.some((node) => node.kind === "development-responsibility"), false);
  assert.equal(graph.nodes.some((node) => node.kind === "commitment-stage"), false);
  assert.equal(graph.nodes.some((node) => node.kind === "kernel"), false);
  assert.equal(graph.constraints.some((constraint) => constraint.id === "constraint.invariant.kernel-minimality"), false);
  assert.equal(graph.constraints.some((constraint) => constraint.id === "constraint.invariant.stage-core-separation"), false);
  assert.equal(graph.decisionOperations.some((operation) => operation.id === "enter-g0"), false);
});

test("top-game teardowns form an advisory mechanism-combination pattern library, not design law", () => {
  assert.ok(Array.isArray(graph.mechanismCombinationPatterns));
  assert.ok(graph.mechanismCombinationPatterns.length >= 12);
  const names = new Set(graph.mechanismCombinationPatterns.map((pattern) => pattern.reference));
  for (const reference of ["Counter-Strike 2", "Dota 2", "Minecraft", "ELDEN RING", "Baldur's Gate 3", "Factorio", "Mario Kart 8 Deluxe", "Beat Saber"]) {
    assert.ok(names.has(reference), `missing reference pattern ${reference}`);
  }
  for (const pattern of graph.mechanismCombinationPatterns) {
    assert.equal(pattern.authority, "ADVISORY_HYPOTHESIS_PATTERN");
    assert.ok(pattern.mechanisms.length >= 2, `${pattern.id} should represent a combination`);
    assert.ok(pattern.sourceRefs.length > 0, `${pattern.id} needs teardown provenance`);
    assert.ok(pattern.confounds.length > 0, `${pattern.id} needs confounds`);
    assert.ok(pattern.falsifier.length > 0, `${pattern.id} needs a falsifier`);
    assert.equal(pattern.canBlockNovelCombination, false);
  }
});

test("pattern matches suggest experience without authorizing or rejecting a composition", () => {
  const result = exploreGameComposition(
    {
      intent: "explore",
      elements: ["new.game.idea"],
      mechanisms: ["persistent-transformation", "self-authored-goals", "resource-constraint"],
    },
    graph,
  );
  assert.equal(result.disposition, "OPEN_EXPLORATION");
  assert.ok(result.patternMatches.some((match) => match.reference === "Minecraft"));
  assert.ok(result.patternMatches.every((match) => match.authority === "ADVISORY_HYPOTHESIS_PATTERN"));
  assert.equal(result.compositionEvidenceInherited, false);
});

test("component evidence never becomes composition evidence automatically", () => {
  const constraint = graph.constraints.find((candidate) => candidate.id === "constraint.evidence.composition-noninheritance");
  assert.ok(constraint);
  assert.match(constraint.statement, /Evidence\(A\).*Evidence\(B\).*Evidence\(A\+B\)|component.*composition/i);

  const result = exploreGameComposition(
    {
      intent: "explore",
      elements: ["mechanic.e01", "mechanic.e02"],
      evidenceClasses: ["evidence.mechanical-causal"],
    },
    graph,
  );
  assert.equal(result.compositionEvidenceInherited, false);
  assert.ok(result.epistemicFences.includes("constraint.evidence.composition-noninheritance"));
});

test("claims and external effects remain bounded even though creation is open", () => {
  const claim = exploreGameComposition(
    {
      intent: "claim-human-value",
      elements: ["mechanic.e03", "composition.pc02"],
      evidenceClasses: ["evidence.mechanical-causal"],
    },
    graph,
  );
  assert.equal(claim.disposition, "EVIDENCE_NOT_TRANSFERABLE");
  assert.ok(claim.requiredEvidenceClasses.includes("evidence.human-participant"));

  const effect = exploreGameComposition(
    {
      intent: "external-effect",
      elements: ["service.distribution"],
      evidenceClasses: ["evidence.owner-currentness"],
    },
    graph,
  );
  assert.equal(effect.disposition, "EXTERNAL_EFFECT_BLOCKED");
  assert.ok(effect.requiredEvidenceClasses.includes("evidence.explicit-effect-authority"));
});

test("repository authority text no longer makes D/G lenses canonical development law", () => {
  const agents = read("AGENTS.md");
  const readme = read("README.md");
  const authority = read("docs/authority.md");
  for (const source of [agents, readme, authority]) {
    assert.doesNotMatch(source, /(?:G0[–-]G8 (?:remain|is|are) canonical|owns canonical G0[–-]G8|only Game authority for G0[–-]G8|sole authority for G0[–-]G8)/i);
  }
  assert.match(agents, /creative.*open|open.*creative/is);
  assert.match(authority, /advisory.*skill|skill.*advisory/is);
});

test("package exposes explorer rather than legality decision command", () => {
  const pkg = JSON.parse(read("package.json")) as { scripts: Record<string, string> };
  assert.equal(typeof pkg.scripts["explore:composition"], "string");
  assert.equal(pkg.scripts["decision:composition"], undefined);
});
