import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { readGameKnowledge, readGameKnowledgeSource } from "../src/knowledge-file.ts";

test("knowledge reader preserves exact source text and parsed semantics from the same read", () => {
  const root = mkdtempSync(join(tmpdir(), "game-knowledge-"));
  try {
    const raw = '{ "name": "游戏",\r\n  "items": [1, 2] }\n';
    writeFileSync(join(root, "fixture.json"), raw);
    const source = readGameKnowledgeSource("fixture.json", root);
    assert.equal(source.raw, raw);
    assert.deepEqual(source.value, { name: "游戏", items: [1, 2] });
    assert.deepEqual(readGameKnowledge("fixture.json", root), source.value);
    writeFileSync(join(root, "fixture.json"), "{");
    assert.throws(() => readGameKnowledgeSource("fixture.json", root), SyntaxError);
    assert.throws(() => readGameKnowledge("fixture.json", root), SyntaxError);
    assert.throws(() => readGameKnowledgeSource("missing.json", root), { code: "ENOENT" });
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
