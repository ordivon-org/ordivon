import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { canonicalJson, sha256 } from "../src/digest.ts";
import type { WorldCommand, WorldEvent, WorldState } from "../src/model.ts";
import { resolveRuleset } from "../src/registry.ts";

function readJsonLines<T>(path: string): T[] {
  return readFileSync(path, "utf8")
    .trim()
    .split("\n")
    .filter(Boolean)
    .map((line) => JSON.parse(line) as T);
}

test("the frozen M1 v1 fixture remains executable and byte-stable", () => {
  const manifest = JSON.parse(readFileSync("fixtures/m1-v1/manifest.json", "utf8")) as {
    scenario: { id: string; version: number };
    ruleset: { id: string; version: number };
    trajectories: Array<{ name: string; terminalDigest: string; commandCount: number }>;
  };
  const genesis = JSON.parse(readFileSync("fixtures/m1-v1/genesis.json", "utf8")) as WorldState;
  const ruleset = resolveRuleset(manifest.ruleset.id, manifest.ruleset.version);

  for (const trajectory of manifest.trajectories) {
    const commands = readJsonLines<WorldCommand>(`fixtures/m1-v1/${trajectory.name}.commands.jsonl`);
    const expectedEvents = readJsonLines<WorldEvent>(`fixtures/m1-v1/${trajectory.name}.events.jsonl`);
    const expectedDigests = JSON.parse(
      readFileSync(`fixtures/m1-v1/${trajectory.name}.digests.json`, "utf8"),
    ) as string[];
    let state = structuredClone(genesis);
    assert.equal(sha256(state), expectedDigests[0]);
    assert.equal(commands.length, trajectory.commandCount);

    for (const [index, command] of commands.entries()) {
      const result = ruleset.apply(state, command);
      if (result.status !== "accepted") throw new Error(`${result.code}: ${result.reason}`);
      assert.equal(result.status, "accepted");
      assert.equal(canonicalJson(result.event), canonicalJson(expectedEvents[index]));
      state = result.state;
      assert.equal(sha256(state), expectedDigests[index + 1]);
    }
    assert.equal(sha256(state), trajectory.terminalDigest);
  }
});
