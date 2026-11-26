import { WebStore } from "../../../src/store.ts";
import { hashToken } from "../../../src/identity-digests.ts";
const store=new WebStore(":memory:");
try{
  const principal=store.ensurePrincipal("new-p","new-user","新用户 🦀",100);
  store.ensurePrincipal("new-p","new-user","新用户 🦀",101);
  store.putCredential("new-p",{id:"new-c",publicKey:new Uint8Array([0,255,128,1]),counter:1,transports:["internal","hybrid"],deviceType:"multiDevice",backedUp:true},100);
  const credential=()=>{const c=store.getActiveCredential("new-c");return {...c,publicKey:[...c.publicKey]}};
  const initial=credential();
  store.updateCredentialCounter("new-c",1,2,101);
  const advanced=credential();
  const created=store.createSession("new-p",100,20,50,"browser");
  const normalize=(s:typeof created.session)=>({...s,sessionId:"normalized"});
  const auth=store.authenticateSession(created.token,110,50);
  const before=normalize(auth.session);
  const hashExact=auth.tokenHash===hashToken(created.token);
  const revoked=store.revokeSession("new-p",created.session.sessionId,111);
  const repeated=store.revokeSession("new-p",created.session.sessionId,112);
  const bulk=store.revokeAllSessions("new-p",113);
  const audits=store.db.prepare("SELECT event_type,detail_json,created_at FROM audit_events ORDER BY rowid").all().map(r=>Object.values(r));
  console.log(JSON.stringify({principal,initial,advanced,created:normalize(created.session),before,hashExact,revoked,repeated,bulk,final:store.listSessions("new-p").map(normalize),audits}));
}finally{store.close()}
