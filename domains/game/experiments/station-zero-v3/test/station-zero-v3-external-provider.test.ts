import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  FixtureStationZeroV3AgentProvider,
  StationZeroV3PlayService,
  StationZeroV3Store,
  loadStationZeroV3ExternalProviderModule,
  type StationZeroV3AgentDecision,
  type StationZeroV3AgentProvider,
} from "../src/index.ts";

test("external v3 Provider module loads an injected Provider factory without model transport in Game", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-provider-module-"));
  try {
    const modulePath = join(directory, "provider.ts");
    const fixtureUrl = new URL("../src/agent-planning.ts", import.meta.url).href;
    writeFileSync(modulePath, `
      import { FixtureStationZeroV3AgentProvider } from ${JSON.stringify(fixtureUrl)};
      export const providerModule = {
        schemaVersion: 1,
        kind: "ordivon.game.station-zero-v3-external-provider-module",
        providerId: "external:test-fixture",
        providerFactory() { return new FixtureStationZeroV3AgentProvider(); },
        evidenceSnapshot() { return { schemaVersion: 1, kind: "ordivon.game.station-zero-v3-external-provider-evidence", providerId: "external:test-fixture", calls: [] }; },
      };
    `);
    const loaded = await loadStationZeroV3ExternalProviderModule(modulePath);
    assert.equal(loaded.providerId, "external:test-fixture");
    assert.equal(loaded.evidenceSnapshot?.().calls.length, 0);
    const store = new StationZeroV3Store(":memory:");
    try {
      const play = new StationZeroV3PlayService(store, { providerFactory: loaded.providerFactory });
      const runId = "run:external-v3-provider";
      play.initialize({ runId });
      const preview = await play.generatePreview(runId);
      assert.ok(preview.preview.agentDecisions.length > 0);
      assert.ok(preview.preview.agentDecisions.every((decision) => decision.providerId === "fixture-station-zero-v3-agent-v1"));
    } finally { store.close(); }
  } finally { rmSync(directory, { recursive: true, force: true }); }
});

test("external v3 Provider module contract fails closed on malformed exports", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-provider-module-invalid-"));
  try {
    for (const [name, source] of [
      ["missing", `export default {};`],
      ["wrong-kind", `export default { schemaVersion: 1, kind: "wrong", providerId: "x", providerFactory() {} };`],
      ["blank-id", `export default { schemaVersion: 1, kind: "ordivon.game.station-zero-v3-external-provider-module", providerId: "", providerFactory() {} };`],
      ["no-factory", `export default { schemaVersion: 1, kind: "ordivon.game.station-zero-v3-external-provider-module", providerId: "x" };`],
    ] as const) {
      const path = join(directory, `${name}.ts`);
      writeFileSync(path, source);
      await assert.rejects(() => loadStationZeroV3ExternalProviderModule(path), TypeError);
    }
  } finally { rmSync(directory, { recursive: true, force: true }); }
});

test("high-fidelity Agent decisions remain concurrent under an externally supplied provider", async () => {
  const store = new StationZeroV3Store(":memory:");
  const fixture = new FixtureStationZeroV3AgentProvider();
  let active = 0;
  let maximumActive = 0;
  const provider: StationZeroV3AgentProvider = {
    providerId: "external:delayed-concurrency-test",
    async decide(context): Promise<StationZeroV3AgentDecision> {
      active += 1;
      maximumActive = Math.max(maximumActive, active);
      await new Promise((resolve) => setTimeout(resolve, 80));
      try {
        const decision = await fixture.decide(context);
        return { ...decision, providerId: "external:delayed-concurrency-test" };
      } finally { active -= 1; }
    },
  };
  try {
    const play = new StationZeroV3PlayService(store, { providerFactory: () => provider });
    const runId = "run:external-provider:parallel";
    play.initialize({ runId });
    const started = performance.now();
    const preview = await play.generatePreview(runId);
    const elapsed = performance.now() - started;
    assert.equal(maximumActive, 5);
    assert.ok(elapsed < 300, `parallel Preview took ${elapsed} ms`);
    assert.ok(preview.preview.agentDecisions.every((decision) => decision.providerId === provider.providerId));
  } finally { store.close(); }
});
