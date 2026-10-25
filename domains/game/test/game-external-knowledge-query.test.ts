import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { queryExternalKnowledge } from "../scripts/external-knowledge-query.ts";

const pkg = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));

test("external knowledge query is exposed as retrieval rather than decision", () => {
  assert.equal(pkg.scripts["knowledge:external"], "node scripts/external-knowledge-query.ts");
  assert.equal(pkg.scripts["decide:external-knowledge"], undefined);
});

test("query finds source records by free text and authority without changing authority", () => {
  const result = queryExternalKnowledge({ type: "sources", q: "curiosity", authority: "PRIMARY_DEVELOPER_ACCOUNT" });
  assert.equal(result.kind, "ordivon.game.external-knowledge-query");
  assert.equal(result.semanticAuthorityClaimed, false);
  assert.ok(result.items.some((item: any) => item.id === "gdc-outer-wilds"));
  assert.ok(result.items.every((item: any) => item.authorityClass === "PRIMARY_DEVELOPER_ACCOUNT"));
});

test("query finds source-bound teardown targets and preserves creative-open boundary", () => {
  const result = queryExternalKnowledge({ type: "teardowns", q: "survival", status: "SOURCE_FOUND" });
  assert.ok(result.items.some((item: any) => item.id === "pacific-drive"));
  assert.ok(result.items.every((item: any) => item.status === "SOURCE_FOUND"));
  assert.ok(result.items.every((item: any) => item.canBlockNovelCombination === false));
});

test("query finds skills without treating them as tools or owners", () => {
  const result = queryExternalKnowledge({ type: "skills", q: "version" });
  assert.ok(result.items.some((item: any) => item.id === "gda-version-lock"));
  assert.ok(result.items.every((item: any) => item.instructionAuthority === "ADVISORY"));
  assert.equal(result.semanticAuthorityClaimed, false);
});
