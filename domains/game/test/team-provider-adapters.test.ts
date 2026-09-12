import assert from "node:assert/strict";
import test from "node:test";

import { createGameServer } from "../src/server.ts";
import type { CompiledTeamContext, TeamProviderDecision } from "../products/station-zero-v2/src/team/model.ts";
import { FixtureTeamProvider, type TeamDecisionProvider } from "../products/station-zero-v2/src/team/providers.ts";

async function listen(game: ReturnType<typeof createGameServer>): Promise<string> {
  await new Promise<void>((resolve) => game.server.listen(0, "127.0.0.1", resolve));
  const address = game.server.address();
  if (!address || typeof address === "string") throw new Error("server did not expose an address");
  return `http://127.0.0.1:${address.port}`;
}

class ExternalFixtureProvider implements TeamDecisionProvider {
  readonly providerId = "external:fixture-proxy";
  readonly fixture = new FixtureTeamProvider();
  async decide(context: CompiledTeamContext): Promise<TeamProviderDecision> {
    const decision = await this.fixture.decide(context);
    return { ...decision, providerId: this.providerId };
  }
  evidenceMetadata(): Record<string, unknown> { return { executionOwner: "external-test-double" }; }
}

test("default Game server has no Provider preflight endpoint and exposes only fixture", async () => {
  const game = createGameServer({ dbPath: ":memory:" });
  try {
    const base = await listen(game);
    const catalog = await (await fetch(`${base}/api/mission-control/catalog`)).json() as { providers: Array<{ providerId: string }> };
    assert.deepEqual(catalog.providers.map((entry) => entry.providerId), ["fixture"]);
    assert.equal((await fetch(`${base}/api/providers/preflight`)).status, 404);
  } finally { await game.close(); }
});

test("external cognition is injected as providerFactory plus catalog identity without Game process execution", async () => {
  const externalProviderId = "external:fixture-proxy";
  const game = createGameServer({
    dbPath: ":memory:",
    providerOptions: [
      { providerId: "fixture", label: "Fixture baseline", deterministic: true, executionOwner: "game" },
      { providerId: externalProviderId, label: "External fixture proxy", deterministic: false, executionOwner: "external" },
    ],
    providerFactory(name) {
      if (name === externalProviderId) return new ExternalFixtureProvider();
      return new FixtureTeamProvider();
    },
  });
  try {
    const base = await listen(game);
    const catalog = await (await fetch(`${base}/api/mission-control/catalog`)).json() as { providers: Array<{ providerId: string; executionOwner: string }> };
    assert.equal(catalog.providers.find((entry) => entry.providerId === externalProviderId)?.executionOwner, "external");
    const initialize = await fetch(`${base}/api/mission-control/initialize`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ runId: "run:external-provider-injection", providers: { "engineer-01": externalProviderId, "medic-01": externalProviderId, "security-01": externalProviderId } }) });
    assert.equal(initialize.status, 201);
    const advance = await fetch(`${base}/api/mission-control/advance?runId=run%3Aexternal-provider-injection`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ mode: "one-tick" }) });
    assert.equal(advance.status, 200);
    assert.ok(JSON.stringify(await advance.json()).includes(externalProviderId));
  } finally { await game.close(); }
});

test("default Game server rejects unconfigured external Provider identities", async () => {
  const game = createGameServer({ dbPath: ":memory:" });
  try {
    const base = await listen(game);
    const response = await fetch(`${base}/api/mission-control/initialize`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ runId: "run:unconfigured-provider", providers: { "engineer-01": "external:not-configured" } }) });
    assert.equal(response.status, 400);
  } finally { await game.close(); }
});
