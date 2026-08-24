import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import test from "node:test";
import { gameCurrentDirectionContext } from "../scripts/current-direction-context.ts";

function digest(path: string) {
  return `sha256:${createHash("sha256").update(readFileSync(new URL(`../${path}`, import.meta.url))).digest("hex")}`;
}

test("current direction context projects exact owner frontier without gaining product authority", () => {
  const value = gameCurrentDirectionContext();
  assert.equal(value.kind, "ordivon.game.current-direction-context");
  assert.equal(value.truthRole, "exact-source-current-direction-projection-not-product-authority");
  assert.equal(value.currentness.state, "CURRENT_TO_WORKSPACE_SOURCE");
  assert.equal(value.currentness.canonicalRevisionClaimed, false);
  assert.equal(value.direction.sourcePath, "docs/GAME_CORE_RESEARCH_RESET.md");
  assert.equal(value.direction.sourceDigest, digest(value.direction.sourcePath));
  assert.match(value.direction.exactSource, /^## Current frontier/);
  assert.match(value.direction.exactSource, /Return to Game Core itself\./);
  assert.match(value.direction.exactSource, /maximizes information gain rather than prototype count/);
  assert.match(value.direction.exactSource, /only later decide whether evidence is mature enough to intentionally begin a real product at canonical G0/);
  assert.equal(value.authority.sourceDigest, digest(value.authority.sourcePath));
  assert.deepEqual(value.authority.exactGuards, [
    "`AGENTS.md` governs repository work rather than product truth.",
    "Its historical stage labels do not select the next Ordivon Game product or redefine current Game Core research.",
  ]);
});

test("stable AGENTS guidance does not claim current Station Zero work", () => {
  const agents = readFileSync(new URL("../AGENTS.md", import.meta.url), "utf8");
  assert.doesNotMatch(agents, /Improve the current Station Zero product/);
  assert.match(agents, /stable repository operating guidance, not current product\/research standing/);
  assert.match(agents, /must not select the next project action by itself/);
  assert.match(agents, /follow `docs\/authority\.md` to the current owner/);
  assert.match(agents, /do not infer it from the registered Station Zero product/);
});
