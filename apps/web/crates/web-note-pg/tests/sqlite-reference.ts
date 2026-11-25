import { WebStore } from "../../../src/store.ts";
import assert from "node:assert/strict";
const store=new WebStore(":memory:");
try {
  for (const p of ["p","q"])store.ensurePrincipal(p,p,p.toUpperCase(),1);
  const normalize=({noteId:_,...n}:ReturnType<WebStore["createCanaryNote"]>)=>n;
  const sorted=(v:{content:string}[])=>v.sort((a,b)=>a.content<b.content?-1:a.content>b.content?1:0);
  const trace=[];
  for(const [p,content,now] of [["p","first",100],["q","foreign",102],["p","emoji 🦀 / 汉字 / \n",103],["p","same clock",103]] as const){
    const note=store.createCanaryNote(p,content,now);
    const list=store.listCanaryNotes(p);
    for(let i=1;i<list.length;i++)assert.ok(list[i-1]!.createdAt>list[i]!.createdAt||list[i-1]!.createdAt===list[i]!.createdAt&&list[i-1]!.noteId<list[i]!.noteId);
    const audit=store.db.prepare("SELECT * FROM audit_events WHERE event_type='canary.note.created' AND object_id=?").get(note.noteId)!;
    assert.equal(audit.object_id,note.noteId);
    trace.push({note:normalize(note),audit:{principal:audit.principal_id,event:audit.event_type,objectType:audit.object_type,detail:audit.detail_json,at:audit.created_at},list:sorted(list.map(normalize)),counts:[store.db.prepare("SELECT count(*) AS n FROM canary_notes").get()!.n,store.db.prepare("SELECT count(*) AS n FROM audit_events WHERE event_type='canary.note.created'").get()!.n]});
  }
  console.log(JSON.stringify(trace));
}finally{store.close()}
