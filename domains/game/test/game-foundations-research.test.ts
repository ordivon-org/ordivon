import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const corpus = readFileSync(
  new URL("../docs/GAME_FOUNDATIONS_RESEARCH_R1_R17.md", import.meta.url),
  "utf8",
);
const map = readFileSync(
  new URL("../docs/GAME_FOUNDATIONS_RESEARCH_MAP.md", import.meta.url),
  "utf8",
);
const continuation = readFileSync(
  new URL("../docs/GAME_FOUNDATIONS_CONTINUATION.md", import.meta.url),
  "utf8",
);
const project = readFileSync(new URL("../.ordivon/project.yaml", import.meta.url), "utf8");

test("Game foundations corpus preserves all seventeen completed research rounds", () => {
  for (let round = 1; round <= 17; round += 1) {
    assert.match(corpus, new RegExp(`R${round} \\u2014|R${round} —`));
  }
  assert.match(corpus, /AI Game != Agent World/);
  assert.match(corpus, /No new Ordivon Game product has been selected by R1–R17/);
  assert.match(corpus, /A research round is a search method\. It is not a product phase\./);
});

test("foundation navigation keeps the exact post-R17 continuation frontier", () => {
  assert.match(map, /R18 — Goals, Utility, Needs, Values and Desire/);
  assert.match(continuation, /R18 — Goals, Utility, Needs, Values and Desire/);
  assert.match(continuation, /AI Game != Agent World/);
  assert.match(continuation, /Do not begin intentional new-product G0 merely because the research corpus is large\./);
});

test("foundation research records are managed repository documentation", () => {
  for (const path of [
    "docs/GAME_FOUNDATIONS_RESEARCH_R1_R17.md",
    "docs/GAME_FOUNDATIONS_RESEARCH_MAP.md",
    "docs/GAME_FOUNDATIONS_CONTINUATION.md",
  ]) {
    assert.match(project, new RegExp(path.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
});
