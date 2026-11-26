import { WebStore } from "../../../src/store.ts";
import type { AgentGrantCreate } from "../../../src/model.ts";
import { grantDigest } from "../../../src/identity-digests.ts";
const store=new WebStore(":memory:");
try{
  store.ensurePrincipal("p","p","P",1);
  const alphabet=["🦀","\uE000","é","e\u0301","quote\"","\\","\n","\u2028","\u2029","\b","ascii",""];
  const vectors=[];
  for(let i=0;i<32;i++){
    const a=alphabet[i%alphabet.length]!;
    const b=alphabet[(i*7+3)%alphabet.length]!;
    const input:AgentGrantCreate={
      grantId:"grant-"+String(i).padStart(2,"0"),principalId:"p",agentId:"agent-"+a,
      audience:"web-"+b,allowedActions:["🦀","\uE000",a,b,a,"canary.note.create"],
      resourcePrefixes:["/🦀","/\uE000","/é","/e\u0301","/canary/notes","/🦀"],
      expiresAtEpochSeconds:i===31?Number.MAX_SAFE_INTEGER:200+i,maxRiskClass:"R4",
      stepUpAtOrAbove:"R4",remainingEffects:i===30?Number.MAX_SAFE_INTEGER:i%4,
    };
    const snapshot=store.createAgentGrant(input,100);
    const row=store.db.prepare("SELECT allowed_actions_json,resource_prefixes_json FROM agent_grants WHERE grant_id=?").get(input.grantId);
    const audit=store.db.prepare("SELECT detail_json FROM audit_events WHERE event_type='agent.grant.issued' AND object_id=?").get(input.grantId);
    vectors.push({input,snapshot,row,audit,withoutQuota:grantDigest({...input,remainingEffects:0})});
  }
  console.log(JSON.stringify(vectors));
}finally{store.close()}
