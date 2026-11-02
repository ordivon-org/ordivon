import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { WebStore } from "../src/store.ts";

test("WebStore schema bootstrap preserves the single SQLite schema and connection modes", () => {
  const dir = mkdtempSync(join(tmpdir(), "ordivon-webstore-schema-"));
  const file = join(dir, "web.sqlite");
  const expectedTables = [
    "agent_effects",
    "agent_grants",
    "audit_events",
    "canary_notes",
    "dpop_proofs",
    "effect_approvals",
    "pending_effect_approvals",
    "principals",
    "sessions",
    "webauthn_challenges",
    "webauthn_credentials",
  ];
  const expectedIndexes = [
    "agent_grants_resolution",
    "audit_events_principal_created",
    "dpop_proofs_expiry",
    "sessions_principal",
    "webauthn_credentials_principal",
  ];
  try {
    for (let iteration = 0; iteration < 2; iteration++) {
      const store = new WebStore(file);
      try {
        const tables = store.db.prepare(
          "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name",
        ).all().map((row) => String(row.name));
        const indexes = store.db.prepare(
          "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%' ORDER BY name",
        ).all().map((row) => String(row.name));
        assert.deepEqual(tables, expectedTables);
        assert.deepEqual(indexes, expectedIndexes);
        assert.equal(store.db.prepare("PRAGMA foreign_keys").get()?.foreign_keys, 1);
        assert.equal(store.db.prepare("PRAGMA journal_mode").get()?.journal_mode, "wal");
      } finally {
        store.close();
      }
    }
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
