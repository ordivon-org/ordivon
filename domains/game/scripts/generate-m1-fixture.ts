import { writeFileSync } from "node:fs";
import { canonicalJson, sha256 } from "../src/digest.ts";
import { initialWorld } from "../src/scenario.ts";
import { recoveryPolicy, communicationsFirstPolicy } from "../src/policies.ts";
import { applyWorldCommand, materializeAction } from "../src/world.ts";

function generate(policy: typeof recoveryPolicy, name: string) {
  let state = initialWorld();
  const commands = [];
  const events = [];
  const digests = [sha256(state)];
  let step = 0;
  while (state.mission.status === "running") {
    const action = policy.choose(state);
    if (!action) throw new Error("policy produced no action");
    const command = materializeAction(action, `${name}:${step}:${action.actionId}`);
    const result = applyWorldCommand(state, command);
    if (result.status !== "accepted") throw new Error(result.reason);
    commands.push(command);
    events.push(result.event);
    state = result.state;
    digests.push(sha256(state));
    step += 1;
  }
  writeFileSync(`fixtures/m1-v1/${name}.commands.jsonl`, commands.map(canonicalJson).join("\n") + "\n");
  writeFileSync(`fixtures/m1-v1/${name}.events.jsonl`, events.map(canonicalJson).join("\n") + "\n");
  writeFileSync(`fixtures/m1-v1/${name}.digests.json`, JSON.stringify(digests, null, 2) + "\n");
  return {
    name,
    terminalStatus: state.mission.status,
    terminalReason: state.mission.reason,
    turn: state.turn,
    commandCount: commands.length,
    genesisDigest: digests[0],
    terminalDigest: digests.at(-1),
  };
}

const genesis = initialWorld();
writeFileSync("fixtures/m1-v1/genesis.json", JSON.stringify(genesis, null, 2) + "\n");
const manifest = {
  fixtureVersion: 1,
  sourceCommit: "b437786c232b5fa74a5c262c981f563568a9396a",
  stateSchemaVersion: 2,
  scenario: { id: "station-zero", version: 1 },
  ruleset: { id: "station-zero-core", version: 1 },
  seed: genesis.seed,
  generatedAt: "2026-07-27",
  trajectories: [generate(recoveryPolicy, "success"), generate(communicationsFirstPolicy, "failure")],
};
writeFileSync("fixtures/m1-v1/manifest.json", JSON.stringify(manifest, null, 2) + "\n");
console.log(JSON.stringify(manifest, null, 2));
