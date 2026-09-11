import assert from "node:assert/strict";
import test from "node:test";

import { createMissionControlCatalog, MISSION_PROVIDER_OPTIONS, validateMissionProviderOptions } from "../src/mission-control/catalog.ts";

test("default Game Provider catalog owns only the deterministic fixture baseline", () => {
  const catalog = createMissionControlCatalog();
  assert.deepEqual(catalog.providers, [{ providerId: "fixture", label: "Fixture baseline", deterministic: true, executionOwner: "game" }]);
  assert.deepEqual(MISSION_PROVIDER_OPTIONS.map((entry) => entry.providerId), ["fixture"]);
});

test("external Provider identities are explicit catalog inputs rather than local preflight discoveries", () => {
  const external = { providerId: "external:research-model", label: "Research model", deterministic: false, executionOwner: "external" as const };
  const catalog = createMissionControlCatalog([...MISSION_PROVIDER_OPTIONS, external]);
  assert.equal(catalog.providers.find((entry) => entry.providerId === external.providerId)?.executionOwner, "external");
  assert.throws(() => validateMissionProviderOptions([external]), /fixture baseline/);
  assert.throws(() => validateMissionProviderOptions([MISSION_PROVIDER_OPTIONS[0]!, { ...external, providerId: "fixture" }]), /duplicate/);
});
