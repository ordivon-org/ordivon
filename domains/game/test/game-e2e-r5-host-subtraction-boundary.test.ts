import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

const CONSUMER_ROOTS = [
  "src/team",
  "src/deployment",
  "src/comparison",
  "src/replay",
  "src/mission-control",
];

function tsFiles(root: string): string[] {
  const result: string[] = [];
  for (const name of readdirSync(root)) {
    const path = join(root, name);
    if (statSync(path).isDirectory()) result.push(...tsFiles(path));
    else if (path.endsWith(".ts")) result.push(path);
  }
  return result.sort();
}

test("R5 Game consumers cannot directly import the legacy embedded Host journal", () => {
  const offenders: string[] = [];
  for (const root of CONSUMER_ROOTS) {
    for (const path of tsFiles(root)) {
      const text = readFileSync(path, "utf8");
      if (/host-contract\/journal\.ts/.test(text) || /\bHostStore\b/.test(text)) offenders.push(path);
    }
  }
  assert.deepEqual(offenders, []);
});

test("R5 legacy HostStore dependency is quarantined behind the Game evidence adapter", () => {
  const adapter = readFileSync("src/integration/game-evidence.ts", "utf8");
  assert.match(adapter, /class LegacyEmbeddedHostEvidenceAdapter/);
  assert.match(adapter, /new HostStore\(db\)/);
  assert.match(adapter, /source-current external Host replacement must preserve/);

  const teamStore = readFileSync("src/team/store.ts", "utf8");
  assert.match(teamStore, /readonly evidence: GameEvidencePort/);
  assert.doesNotMatch(teamStore, /readonly host:/);
});

test("R5 compatibility Host internals remain explicitly isolated instead of silently promoted", () => {
  const architecture = readFileSync("docs/GAME_E2E_R5_HOST_SUBSTITUTION.md", "utf8");
  assert.match(architecture, /FULL_EXTERNAL_SUBSTITUTION = NOT_ADMITTED/);
  assert.match(architecture, /same local transaction/);
  assert.match(architecture, /transactional outbox/i);
  assert.match(architecture, /Human UNKNOWN/);
});
