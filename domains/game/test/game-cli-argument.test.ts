import assert from "node:assert/strict";
import test from "node:test";
import { cliArgument, cliQueryArguments } from "../scripts/cli-argument.ts";

test("Game CLI adapter preserves exact omission, order, and legacy numeric conversion", () => {
  const argv = ["node", "game", "--q", "first", "--q", "second", "--tag", "signal", "--limit", "3"];
  assert.equal(cliArgument("--q", argv), "first");
  assert.deepEqual(cliQueryArguments(["q", "tag", "missing"], argv), {
    q: "first", tag: "signal", limit: 3,
  });
  assert.deepEqual(cliQueryArguments(["q"], ["node", "game"]), {});
  assert.equal(cliQueryArguments(["q"], ["node", "game", "--q"]).q, undefined);
  assert.equal(Number.isNaN(cliQueryArguments([], ["node", "game", "--limit", "NaN"]).limit), true);
  assert.equal(cliQueryArguments([], ["node", "game", "--limit", ""]).limit, 0);
});
