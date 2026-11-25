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
    "audit_events_committed_effect",
    "audit_events_created_note",
    "audit_events_principal_created",
    "canary_notes_principal_created",
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

test("committed effect audit observation uses a bounded indexed lookup and preserves duplicates", () => {
  const store = new WebStore(":memory:");
  try {
    const db = store.db;
    const insert = db.prepare("INSERT INTO audit_events VALUES (?, NULL, ?, ?, ?, '{}', 0)");
    for (let i = 0; i < 500; i++) {
      insert.run("unrelated-" + i, "agent.effect.committed", "effect", "other-" + i);
    }
    insert.run("first", "agent.effect.committed", "effect", "target");
    insert.run("second", "agent.effect.committed", "effect", "target");
    insert.run("third", "agent.effect.committed", "effect", "target");
    insert.run("not-an-effect", "other", "effect", "target");
    const sql = "SELECT * FROM audit_events WHERE event_type = 'agent.effect.committed' AND object_type = 'effect' AND object_id = ? LIMIT 2";
    const plan = db.prepare("EXPLAIN QUERY PLAN " + sql).all("target");
    assert.ok(plan.some(row => String(row.detail).includes("SEARCH audit_events")), JSON.stringify(plan));
    const rows = db.prepare(sql).all("target");
    assert.equal(rows.length, 2);
    assert.ok(rows.every(row => row.event_type === "agent.effect.committed" && row.object_id === "target"));
  } finally {
    store.close();
  }
});

test("opening a database without the effect audit index preserves existing audit history", () => {
  const dir = mkdtempSync(join(tmpdir(), "ordivon-webstore-audit-upgrade-"));
  const file = join(dir, "web.sqlite");
  try {
    const old = new WebStore(file);
    try {
      old.db.exec("DROP INDEX audit_events_committed_effect");
      old.audit("agent.effect.committed", 1, null, "effect", "historical", { value: 1 });
      old.audit("agent.effect.committed", 2, null, "effect", "historical", { value: 2 });
    } finally {
      old.close();
    }
    const reopened = new WebStore(file);
    try {
      const rows = reopened.db.prepare("SELECT detail_json FROM audit_events WHERE object_id = ? ORDER BY created_at").all("historical");
      assert.deepEqual(rows.map(row => row.detail_json), ['{"value":1}', '{"value":2}']);
      const sql = "SELECT * FROM audit_events WHERE event_type = 'agent.effect.committed' AND object_type = 'effect' AND object_id = ? LIMIT 2";
      assert.equal(reopened.db.prepare(sql).all("historical").length, 2);
      assert.ok(reopened.db.prepare("EXPLAIN QUERY PLAN " + sql).all("historical").some(row => String(row.detail).includes("SEARCH audit_events")));
    } finally {
      reopened.close();
    }
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
