import { DatabaseSync } from "node:sqlite";
import assert from "node:assert/strict";
import { mkdtempSync,rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { initializeWebStoreSchema } from "../../../src/store-schema.ts";
import { exportOwnerSnapshot } from "../migration/sqlite-export.ts";
const root=mkdtempSync(join(tmpdir(),"ordivon-web-migration-source-"));
const path=join(root,"source.sqlite");
const db=new DatabaseSync(path);
const reader=new DatabaseSync(path,{readOnly:true});
try{
  initializeWebStoreSchema(db);
  // Every actual table has data; original whitespace/key ordering, Unicode,
  // empty strings, binary and nullable fields are deliberately nontrivial.
  const insert=(table:string,values:readonly (string|number|null|Uint8Array)[])=>db.prepare("INSERT INTO "+table+" VALUES ("+values.map(()=>"?").join(",")+")").run(...values);
  insert("principals",["p","p","汉字 🦀",1]);
  insert("principals",["q","q","e\u0301",2]);
  insert("webauthn_credentials",["credential","p",new Uint8Array([0,255,128,1,0]),7,'[ "usb", "internal" ]',"singleDevice",0,1,2,null]);
  insert("webauthn_challenges",["challenge","register","p","challenge-bytes","sha256:payload",' { "z":2, "a":1 } ',100,null]);
  insert("sessions",["session","token-hash","p",1,1,2,100,200,null,"webauthn",null]);
  insert("sessions",["session-2","token-hash-2","q",1,1,2,100,200,3,"webauthn",""]);
  for(const [id,content] of [["a","a"],["e\u0301","decomposed"],["é","composed"],["\uE000","BMP private"],["🦀","astral"]]){
    insert("canary_notes",[id!,"p",content!,"DRAFT",Number.MAX_SAFE_INTEGER,null]);
  }
  insert("canary_notes",["published","q","text\n\t","PUBLISHED",Number.MIN_SAFE_INTEGER,4]);
  insert("agent_grants",["grant","sha256:grant","p","agent","web",'[ "canary.note.create", "canary.note.publish" ]','[ "/canary/notes" ]',100,"R4","R2",3,1,7]);
  insert("agent_effects",["effect","sha256:effect","p","agent","grant","canary.note.create","/canary/notes",' { "note": {"content":"🦀","noteId":"a"} } ',4]);
  insert("pending_effect_approvals",["pending","sha256:pending","p",100,4]);
  insert("effect_approvals",["effect","sha256:effect","p","credential",3,100,4]);
  insert("effect_approvals",["pending","sha256:pending","p","credential",3,100,null]);
  insert("dpop_proofs",["proof",100]);
  insert("audit_events",["audit","p","agent.effect.committed","effect","effect",' { "z":2, "a":1 } ',4]);
  insert("audit_events",["audit-duplicate","p","agent.effect.committed","effect","effect",'{}',4]);
  insert("audit_events",["audit-null",null,"system",null,null,"{}",5]);
  const original=exportOwnerSnapshot(reader);
  assert.equal(reader.prepare("PRAGMA journal_mode").get()?.journal_mode,"wal");
  reader.exec("BEGIN");
  assert.throws(()=>exportOwnerSnapshot(reader),/source transaction must be idle/);
  assert.equal(reader.isTransaction,true);
  reader.exec("ROLLBACK");

  const indexes=db.prepare("SELECT name FROM sqlite_schema WHERE type='index' AND sql IS NOT NULL ORDER BY name COLLATE BINARY").all().map(r=>r.name);
  assert.equal(Object.keys(original).length,11);
  assert.equal(indexes.length,8);
  // Negative source representation controls: source exporter must not round
  // unsafe integers or normalize nonintegral SQLite REAL values.
  db.exec("UPDATE dpop_proofs SET expires_at=9223372036854775807");
  assert.throws(()=>exportOwnerSnapshot(reader),/outside JS exact range/);
  assert.equal(reader.isTransaction,false);
  db.exec("UPDATE dpop_proofs SET expires_at=1.5");
  assert.throws(()=>exportOwnerSnapshot(reader),/unsupported SQLite storage class/);
  assert.equal(reader.isTransaction,false);
  db.exec("UPDATE dpop_proofs SET expires_at=100");
  db.exec("UPDATE canary_notes SET content=CAST(X'80' AS TEXT) WHERE note_id='a'");
  const badUtf8=exportOwnerSnapshot(reader);
  db.exec("UPDATE canary_notes SET content=CAST(X'610062' AS TEXT) WHERE note_id='a'");
  const badNul=exportOwnerSnapshot(reader);
  db.exec("UPDATE canary_notes SET content='a' WHERE note_id='a'");
  assert.deepEqual(exportOwnerSnapshot(reader),original);
  console.log(JSON.stringify({original,indexes,badUtf8,badNul}));
}finally{reader.close();db.close();rmSync(root,{recursive:true,force:true})}
