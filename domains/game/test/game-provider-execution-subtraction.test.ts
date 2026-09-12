import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";

const retired = [
  "products/station-zero-v2/src/team/provider-runtime.ts",
  "products/station-zero-v2/src/team/codex-cli.ts",
  "products/station-zero-v2/src/team/hermes-cli.ts",
  "products/station-zero-v2/src/team/provider-preflight.ts",
  "products/station-zero-v2/src/team/provider-chain.ts",
];

test("Game no longer owns generic Provider process, preflight, CLI transport, or fallback implementations", () => {
  for (const path of retired) assert.equal(existsSync(path), false, `${path} must stay retired`);
  const server = readFileSync("products/station-zero-v2/src/server.ts", "utf8");
  const service = readFileSync("products/station-zero-v2/src/mission-control/service.ts", "utf8");
  const team = [
    readFileSync("products/station-zero-v2/src/team/providers.ts", "utf8"),
    readFileSync("products/station-zero-v2/src/team/engine.ts", "utf8"),
  ].join("\n");
  for (const source of [server, service, team]) {
    assert.doesNotMatch(source, /node:child_process|\/usr\/bin\/codex|\/root\/\.local\/bin\/hermes|\.hermes\/\.env|TeamProviderChain|providerPreflight/);
  }
});

test("Game keeps Provider decision schema and admission while execution remains injected", () => {
  const providers = readFileSync("products/station-zero-v2/src/team/providers.ts", "utf8");
  const server = readFileSync("products/station-zero-v2/src/server.ts", "utf8");
  assert.match(providers, /interface TeamDecisionProvider/);
  assert.match(providers, /parseTeamProviderDecision/);
  assert.match(providers, /admitTeamProviderDecision/);
  assert.match(server, /providerFactory\?: MissionProviderFactory/);
  assert.match(server, /providerOptions\?: readonly MissionProviderOption\[\]/);
  assert.match(server, /requires an externally supplied providerFactory/);
});

test("Station Zero v3 no longer owns model HTTP transport or credential pools", () => {
  assert.equal(existsSync("experiments/station-zero-v3/src/deepseek-provider.ts"), false);
  assert.equal(existsSync("experiments/station-zero-v3/src/deepseek-credentials.ts"), false);
  const productServer = readFileSync("products/station-zero-v2/src/server.ts", "utf8");
  const researchServer = readFileSync("experiments/research-preview/server.ts", "utf8");
  const providerModule = readFileSync("experiments/station-zero-v3/src/provider-module.ts", "utf8");
  assert.doesNotMatch(productServer, /ORDIVON_GAME_V3_PROVIDER_MODULE|StationZeroV3/);
  assert.match(researchServer, /ORDIVON_GAME_V3_PROVIDER_MODULE/);
  assert.doesNotMatch(researchServer, /chat\/completions|apiKey|credentialPool/);
  assert.doesNotMatch(providerModule, /fetch\(|apiKey|credential|retry|cooldown|chat\/completions/i);
  assert.doesNotMatch(readFileSync("products/station-zero-v2/src/mission-control/catalog.ts", "utf8"), /deepseek|codex|hermes/i);
});
