import { WebStore } from "../../../src/store.ts";
import { WebProblem } from "../../../src/errors.ts";
import { exportOwnerSnapshot } from "../migration/sqlite-export.ts";
const store=new WebStore(":memory:");
const now=100;
try{
  const insert=(table:string,values:readonly (string|number|null|Uint8Array)[])=>store.db.prepare("INSERT INTO "+table+" VALUES ("+values.map(()=>"?").join(",")+")").run(...values);
  for(const p of ["p","q"])insert("principals",[p,p,p,1]);
  insert("webauthn_credentials",["credential","p",new Uint8Array([0,1,255]),0,"[]","singleDevice",0,1,1,null]);
  for(const id of ["g1","g2"])insert("agent_grants",[id,"digest-"+id,"p","agent","web",'["canary.note.create","canary.note.publish"]','["/canary/notes"]',200,"R4","R4",3,1,1]);
  for(const id of ["P","X"])insert("effect_approvals",[id,"digest-"+id,"p","credential",90,200,null]);
  const source=exportOwnerSnapshot(store.db);
  let noteId="";
  const snapshot=()=>{
    const grants=store.db.prepare("SELECT grant_id,remaining_effects,revision,active FROM agent_grants ORDER BY grant_id").all().map(r=>Object.values(r));
    const notes=store.db.prepare("SELECT principal_id,content,state,created_at,published_at FROM canary_notes ORDER BY content").all().map(r=>Object.values(r));
    const approvals=store.db.prepare("SELECT effect_id,consumed_at FROM effect_approvals ORDER BY effect_id").all().map(r=>Object.values(r));
    const receipts=store.db.prepare("SELECT effect_id,effect_digest,principal_id,agent_id,grant_id,action,committed_at,result_json FROM agent_effects ORDER BY effect_id").all().map(r=>{
      const result=JSON.parse(String(r.result_json));delete result.note.noteId;
      return [r.effect_id,r.effect_digest,r.principal_id,r.agent_id,r.grant_id,r.action,r.committed_at,result];
    });
    const audits=store.db.prepare("SELECT principal_id,event_type,object_type,object_id,detail_json,created_at FROM audit_events ORDER BY object_id").all().map(r=>Object.values(r));
    return {grants,notes,approvals,receipts,audits};
  };
  const trace=[
    ["E","g1",1,false,"agent","digest-E"],
    ["E","g2",1,false,"agent","digest-E"],
    ["E","g2",1,false,"agent","different"],
    ["E","g2",1,false,"other","digest-E"],
    ["F","g1",1,false,"agent","digest-F"],
    ["P","g1",2,true,"agent","digest-P"],
    ["P","g1",1,true,"agent","digest-P"],
    ["X","g2",1,true,"agent","digest-X"],
    ["N","g2",1,true,"agent","digest-N"],
    ["X","g2",1,true,"other","different"],
    ["G","g2",1,false,"agent","digest-G"],
  ] as const;
  const observed=[];
  for(const [id,g,revision,publish,agent,digest] of trace){
    const action=publish?"canary.note.publish":"canary.note.create";
    const req={effectId:id,effectDigest:digest,action,resource:publish?"/canary/notes/"+noteId:"/canary/notes",audience:"web",riskClass:publish?"R4" as const:"R2" as const,effectType:"website."+action};
    const grant={...store.getAgentGrant(g),revision};
    let outcome;
    try{
      const r=publish?store.commitAgentCanaryPublish(grant,agent,req,noteId,now):store.commitAgentCanaryCreate(grant,agent,req,id==="G"?"second":"draft 🦀",now);
      if(id==="E"&&!r.replayed)noteId=(r.receipt.result as {note:{noteId:string}}).note.noteId;
      outcome=r.replayed?"replay":"new";
    }catch(e){if(!(e instanceof WebProblem))throw e;outcome=e.code;}
    observed.push({outcome,state:snapshot()});
  }
  console.log(JSON.stringify({source,observed}));
}finally{store.close()}
