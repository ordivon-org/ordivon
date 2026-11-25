import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { WebStore } from "../src/store.ts";
import { WebProblem } from "../src/errors.ts";
import { now, principalId, seed } from "./fixtures/effect-recovery.ts";

const cases = [
  ["note omitted", "BEFORE INSERT ON canary_notes BEGIN SELECT RAISE(IGNORE); END", "note-write-not-applied"],
  ["note mutated", "AFTER INSERT ON canary_notes BEGIN UPDATE canary_notes SET content='other' WHERE note_id=NEW.note_id; END", "note-business-mismatch"],
  ["audit omitted", "BEFORE INSERT ON audit_events WHEN NEW.event_type='canary.note.created' BEGIN SELECT RAISE(IGNORE); END", "note-write-not-applied"],
  ["audit mutated", "AFTER INSERT ON audit_events WHEN NEW.event_type='canary.note.created' BEGIN UPDATE audit_events SET detail_json='[]' WHERE event_id=NEW.event_id; END", "note-audit-mismatch"],
  ["audit duplicated", "AFTER INSERT ON audit_events WHEN NEW.event_type='canary.note.created' BEGIN INSERT INTO audit_events VALUES ('duplicate',NEW.principal_id,NEW.event_type,NEW.object_type,NEW.object_id,NEW.detail_json,NEW.created_at); END", "note-audit-mismatch"],
  ["audit changes note", "AFTER INSERT ON audit_events WHEN NEW.event_type='canary.note.created' BEGIN UPDATE canary_notes SET content='other' WHERE note_id=NEW.object_id; END", "note-business-mismatch"],
  ["audit aborts", "BEFORE INSERT ON audit_events WHEN NEW.event_type='canary.note.created' BEGIN SELECT RAISE(ABORT,'audit failure'); END", null],
] as const;

for (const [name, trigger, expected] of cases) {
  test("human note atomically rejects " + name, () => {
    const dir = mkdtempSync(join(tmpdir(), "ordivon-human-note-"));
    const store = new WebStore(join(dir, "web.sqlite"));
    seed(store);
    const peer = new WebStore(join(dir, "web.sqlite"));
    try {
      const observe = () => ({
        notes: peer.db.prepare("SELECT * FROM canary_notes").all(),
        audit: peer.db.prepare("SELECT * FROM audit_events ORDER BY event_id").all(),
      });
      const before = observe();
      store.db.exec("CREATE TEMP TRIGGER fail_note " + trigger);
      let error: unknown;
      try { store.createCanaryNote(principalId, "intended", now); } catch (e) { error = e; }
      assert.deepEqual(observe(), before, "no partial committed state");
      if (expected === null) assert.match(String(error), /audit failure/);
      else assert.ok(error instanceof WebProblem && error.code === expected, String(error));
      assert.equal(store.db.isTransaction, false);
      store.db.exec("DROP TRIGGER fail_note");
      const note = store.createCanaryNote(principalId, "intended", now);
      assert.deepEqual(peer.listCanaryNotes(principalId), [note]);
      const row = peer.db.prepare("SELECT * FROM audit_events WHERE event_type='canary.note.created'").get();
      assert.equal(row?.object_id, note.noteId);
      assert.equal(row?.detail_json, "{}");
    } finally { peer.close(); store.close(); rmSync(dir, { recursive: true, force: true }); }
  });
}

test("human note list has stable same-time ordering and indexed principal-local lookup", () => {
  const store = new WebStore(":memory:");
  try {
    seed(store);
    store.ensurePrincipal("other", "other", "Other", now);
    const insert = store.db.prepare("INSERT INTO canary_notes VALUES (?, ?, ?, 'DRAFT', ?, NULL)");
    for (const [id, at] of [["z",now],["a",now],["new",now+1],["old",now-1]] as const) insert.run(id,principalId,id,at);
    for (let i=0;i<500;i++) insert.run("other-"+i,"other","noise",now+2);
    assert.deepEqual(store.listCanaryNotes(principalId).map(n=>n.noteId),["new","a","z","old"]);
    const sql="SELECT * FROM canary_notes WHERE principal_id = ? ORDER BY created_at DESC, note_id ASC";
    const plan=store.db.prepare("EXPLAIN QUERY PLAN "+sql).all(principalId).map(r=>String(r.detail));
    assert.ok(plan.some(x=>x.includes("SEARCH canary_notes")),JSON.stringify(plan));
    assert.ok(!plan.some(x=>x.includes("TEMP B-TREE")),JSON.stringify(plan));
  } finally { store.close(); }
});

test("old database reopen adds both indexes without changing historical rows or duplicate evidence", () => {
  const dir = mkdtempSync(join(tmpdir(), "ordivon-human-note-upgrade-"));
  const path = join(dir,"web.sqlite");
  try {
    const old = new WebStore(path);
    seed(old);
    const note = old.createCanaryNote(principalId,"historical",now);
    old.db.exec("DROP INDEX canary_notes_principal_created; DROP INDEX audit_events_created_note");
    old.audit("canary.note.created",now,principalId,"canary-note",note.noteId,{});
    const before = old.db.prepare("SELECT * FROM audit_events ORDER BY event_id").all();
    old.close();
    const reopened = new WebStore(path);
    try {
      assert.deepEqual(reopened.listCanaryNotes(principalId),[note]);
      assert.deepEqual(reopened.db.prepare("SELECT * FROM audit_events ORDER BY event_id").all(),before);
      const sql="SELECT * FROM audit_events WHERE event_type='canary.note.created' AND object_type='canary-note' AND object_id=? LIMIT 2";
      assert.equal(reopened.db.prepare(sql).all(note.noteId).length,2);
      assert.ok(reopened.db.prepare("EXPLAIN QUERY PLAN "+sql).all(note.noteId).some(r=>String(r.detail).includes("audit_events_created_note")));
    } finally { reopened.close(); }
  } finally { rmSync(dir,{recursive:true,force:true}); }
});

test("human note uses native pre-acquisition busy and preserves peer transaction", () => {
  const dir=mkdtempSync(join(tmpdir(),"ordivon-human-note-busy-"));
  const path=join(dir,"web.sqlite");
  const store=new WebStore(path);
  seed(store);
  const peer=new WebStore(path);
  try {
    peer.db.exec("BEGIN IMMEDIATE");
    try {
      assert.throws(()=>store.createCanaryNote(principalId,"busy",now),(e:unknown)=>e instanceof WebProblem && e.status===503 && e.code==="note-writer-busy");
      assert.equal(peer.db.isTransaction,true);
      assert.equal(store.db.isTransaction,false);
      assert.equal(peer.listCanaryNotes(principalId).length,0);
    } finally { peer.db.exec("ROLLBACK"); }
    assert.equal(store.createCanaryNote(principalId,"explicit",now).content,"explicit");
    assert.equal(peer.listCanaryNotes(principalId).length,1);
  } finally { peer.close();store.close();rmSync(dir,{recursive:true,force:true}); }
});

test("human note ambiguous commit acknowledgement does not auto-reissue", () => {
  const dir=mkdtempSync(join(tmpdir(),"ordivon-human-note-ack-"));
  const path=join(dir,"web.sqlite");
  const store=new WebStore(path);
  seed(store);
  const peer=new WebStore(path);
  const native=store.db.exec.bind(store.db);
  const ack=new Error("commit acknowledgement lost");
  try {
    Object.defineProperty(store.db,"exec",{configurable:true,value:(sql:string)=>{
      native(sql);
      if(sql==="COMMIT")throw ack;
    }});
    assert.throws(()=>store.createCanaryNote(principalId,"committed",now),(e:unknown)=>e===ack);
    assert.equal(store.db.isTransaction,false);
    const notes=peer.listCanaryNotes(principalId);
    assert.equal(notes.length,1);
    assert.equal(notes[0]?.content,"committed");
    assert.equal(peer.db.prepare("SELECT count(*) AS n FROM audit_events WHERE event_type='canary.note.created'").get()?.n,1);
  } finally {
    Reflect.deleteProperty(store.db,"exec");
    peer.close();store.close();rmSync(dir,{recursive:true,force:true});
  }
});
