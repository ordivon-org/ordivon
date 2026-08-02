import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { HostContractStore } from "../src/host-contract/store.ts";
import { HostStore } from "../src/host-contract/journal.ts";
import { GameStore } from "../src/storage.ts";

test("HostContractStore batches idempotent protocol objects and exposes bounded queries", () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-contract-store-"));
  const game = new GameStore(join(directory, "world.sqlite3"));
  try {
    const host = new HostStore(game.db);
    const contracts = new HostContractStore(host);
    const runId = game.activeRunId;
    const value = { schemaVersion: 1, kind: "ordivon.test-object", value: 1 } as const;
    const artifact = contracts.batch(runId, () => {
      const first = contracts.putProtocolObject(
        runId,
        "host-contract.test",
        "host-contract:test:one",
        "subject:test",
        value,
      );
      const nested = contracts.batch(runId, () => contracts.putProtocolObject(
        runId,
        "host-contract.test",
        "host-contract:test:one",
        "subject:test",
        value,
      ));
      assert.equal(nested.digest, first.digest);
      return first;
    });
    assert.deepEqual(contracts.get<typeof value>(artifact.digest).content, value);
    assert.equal(contracts.count(runId, value.kind), 1);
    assert.equal(contracts.latest(runId, "subject:test", value.kind)?.contractDigest, artifact.digest);
    assert.equal(contracts.latest(runId, "subject:missing", value.kind), null);

    assert.throws(() => contracts.batch(runId, () => contracts.batch("run:other", () => null)), /different Runs/);
    assert.throws(() => contracts.putProtocolObject(runId, "wrong", "host-contract:test:bad-type", "subject:test", value), /event type/);
    assert.throws(() => contracts.putProtocolObject(runId, "host-contract.test", "wrong", "subject:test", value), /event identity/);
    assert.throws(() => contracts.putProtocolObject(runId, "host-contract.test", "host-contract:test:bad-subject", " ", value), /subjectRef/);
    assert.throws(() => contracts.putProtocolObject(
      runId,
      "host-contract.test",
      "host-contract:test:kind-conflict",
      "subject:test",
      value,
      { artifactKind: "another-kind" },
    ), /different content or kind/);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});

test("HostContractStore rejects malformed retained contract event payloads", () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-contract-store-corrupt-"));
  const game = new GameStore(join(directory, "world.sqlite3"));
  try {
    const host = new HostStore(game.db);
    const contracts = new HostContractStore(host);
    const runId = game.activeRunId;
    host.withTransaction(runId, () => {
      host.appendEventInTransaction(
        runId,
        "host-contract.invalid",
        "host-contract:invalid:payload",
        { invalid: true },
        new Date().toISOString(),
      );
    });
    assert.throws(() => contracts.transcript(runId), /invalid Host Contract journal payload/);
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
});
