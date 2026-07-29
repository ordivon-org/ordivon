import assert from "node:assert/strict";
import { chmodSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { createMissionControlCatalog } from "../src/mission-control/catalog.ts";
import { providerPreflight } from "../src/providers/preflight.ts";

function executable(directory: string, name: string): string {
  const path = join(directory, name);
  writeFileSync(path, "#!/bin/sh\nexit 0\n");
  chmodSync(path, 0o755);
  return path;
}

test("Provider preflight keeps Fixture ready and fails live Providers closed", () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-provider-preflight-"));
  try {
    const missing = join(directory, "missing");
    const result = providerPreflight({
      codexExecutable: missing,
      hermesExecutable: missing,
      hermesCredentialPath: missing,
    });
    assert.equal(result.providers.find((entry) => entry.providerId === "fixture")?.ready, true);
    assert.equal(result.providers.find((entry) => entry.providerId === "codex")?.ready, false);
    assert.equal(result.providers.find((entry) => entry.providerId === "hermes")?.ready, false);
    assert.equal(result.providers.find((entry) => entry.providerId === "codex-hermes")?.ready, false);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Provider chains remain ready through one configured fallback", () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-provider-preflight-ready-"));
  try {
    const codex = executable(directory, "codex");
    const hermes = executable(directory, "hermes");
    const credentials = join(directory, ".env");
    writeFileSync(credentials, "DEEPSEEK_API_KEY=test-key\n");
    const result = providerPreflight({
      codexExecutable: codex,
      hermesExecutable: hermes,
      hermesCredentialPath: credentials,
    });
    assert.ok(result.providers.every((entry) => entry.ready));
    assert.equal(
      result.providers.find((entry) => entry.providerId === "hermes")?.credentialsReady,
      true,
    );
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Mission Control catalog exposes only measured Deployment choices", () => {
  const catalog = createMissionControlCatalog();
  assert.equal(catalog.fixedLoadout.profileId, "standard-loadout");
  assert.deepEqual(
    catalog.coordinationProfiles.map((profile) => profile.profileId),
    ["specialist-containment", "engineer-seal"],
  );
});
