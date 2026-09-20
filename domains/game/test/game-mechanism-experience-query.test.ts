import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { queryMechanismExperiences } from "../scripts/mechanism-experience-query.ts";
import { exploreGameComposition, loadGameCreativeGraph } from "../scripts/composition-explorer.ts";

const pkg = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));
const graph = loadGameCreativeGraph();

test("mechanism experience retrieval is exposed without a decision command", () => {
  assert.equal(pkg.scripts["knowledge:mechanisms"], "node scripts/mechanism-experience-query.ts");
  assert.equal(pkg.scripts["decide:mechanisms"], undefined);
});

test("query can retrieve by mechanism, game and relation kind", () => {
  const byMechanism = queryMechanismExperiences({ mechanism: "knowledge-progression" });
  assert.ok(byMechanism.items.some((item: any) => item.id === "exp.outerwilds.knowledge-as-progression"));

  const byGame = queryMechanismExperiences({ reference: "Factorio" });
  assert.ok(byGame.totalMatched >= 4);
  assert.ok(byGame.items.every((item: any) => item.referenceGame === "Factorio"));

  const byKind = queryMechanismExperiences({ kind: "INVERSION" });
  assert.ok(byKind.items.length > 0);
  assert.ok(byKind.items.every((item: any) => item.kind === "INVERSION"));
});

test("query never upgrades hypotheses into evidence or recommendation", () => {
  const result = queryMechanismExperiences({ q: "genre" });
  assert.equal(result.semanticAuthorityClaimed, false);
  assert.equal(result.recommendationClaimed, false);
  assert.ok(result.items.every((item: any) => item.authority === "ADVISORY_HYPOTHESIS"));
  assert.ok(result.items.every((item: any) => item.humanOutcomeEstablished === false));
  assert.ok(result.items.every((item: any) => item.canBlockNovelCombination === false));
});

test("composition explorer recalls fine-grained experience matches but remains open", () => {
  const result = exploreGameComposition(
    {
      intent: "explore",
      elements: ["new.looping-mystery"],
      mechanisms: ["knowledge-progression", "time-loop-reset", "persistent-player-knowledge"],
    },
    graph,
  );
  assert.equal(result.disposition, "OPEN_EXPLORATION");
  assert.ok(result.experienceMatches.some((match: any) => match.id === "exp.outerwilds.knowledge-as-progression"));
  assert.ok(result.experienceMatches.every((match: any) => match.authority === "ADVISORY_HYPOTHESIS"));
  assert.ok(result.experienceMatches.every((match: any) => match.canBlockNovelCombination === false));
  assert.equal(result.compositionEvidenceInherited, false);
});

test("experience matches rank by overlap only and expose cheap probes rather than scores", () => {
  const result = exploreGameComposition(
    {
      intent: "explore",
      elements: ["new.combat"],
      mechanisms: ["forward-aggression", "resource-recovery-from-enemies", "close-range-finisher"],
    },
    graph,
  );
  assert.equal(result.experienceMatches[0]?.id, "exp.doom.push-forward-resource-loop");
  assert.equal(result.experienceMatches[0]?.matchedMechanisms.length, 3);
  assert.match(result.experienceMatches[0]?.cheapProbe ?? "", /arena|recovery/i);
  assert.equal((result.experienceMatches[0] as any)?.score, undefined);
});

test("a completely novel mechanism remains open even when the experience library has no match", () => {
  const result = exploreGameComposition(
    {
      intent: "explore",
      elements: ["unknown.synesthetic-contract-dream"],
      mechanisms: ["synesthetic-contract-dream"],
    },
    graph,
  );
  assert.equal(result.disposition, "OPEN_EXPLORATION");
  assert.deepEqual(result.experienceMatches, []);
  assert.equal(result.semanticAuthorityClaimed, false);
});
