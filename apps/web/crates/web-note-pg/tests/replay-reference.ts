import { WebStore } from "../../../src/store.ts";
import { WebProblem } from "../../../src/errors.ts";
import { hashToken } from "../../../src/identity-digests.ts";
import type { ChallengePurpose } from "../../../src/model.ts";
const store=new WebStore(":memory:");
try{
  store.ensurePrincipal("p","p","P",1);
  const challenges=[];
  for(const [purpose,payload] of [
    ["register",{}],["login",{"z":"🦀","a":1e-7,"9":"nine","2":"two"}],
    ["grant-issue",{scope:["/notes","/é","/e\u0301"],quota:0}],
    ["grant-revoke",{grantId:"g",digest:"a\n\"b"}],
    ["effect-approve",{nested:{b:true,a:null},num:1e21}],
  ] as const){
    const record=store.createChallenge(purpose as ChallengePurpose,"p","challenge",100,20,payload);
    const row=store.db.prepare("SELECT payload_json,payload_digest FROM webauthn_challenges WHERE challenge_id=?").get(record.challengeId);
    const consumed=store.consumeChallenge(record.challengeId,purpose,101);
    challenges.push({purpose,row,expiresAt:consumed.expiresAt});
  }
  const commands=[["a",100,10],["a",101,20],["b",102,4],["a",110,2],["b",110,8],["🦀".repeat(64),111,1],["🦀".repeat(65),111,1],["",111,1],["c",111,0],["c",112,10]] as const;
  const proof=[];
  for(const [id,now,ttl] of commands){
    let outcome="ok";
    try{store.consumeDpopProof(id,now,ttl)}catch(e){if(!(e instanceof WebProblem))throw e;outcome=e.code}
    const live=store.db.prepare("SELECT proof_hash,expires_at FROM dpop_proofs WHERE expires_at>? ORDER BY proof_hash").all(now).map(r=>Object.values(r));
    proof.push({id,now,ttl,outcome,hash:hashToken(id),live});
  }
  console.log(JSON.stringify({challenges,proof}));
}finally{store.close()}
