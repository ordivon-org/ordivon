// Trusted local protocol adapter. "candidate" is NOT a durable verified Agent.
// The native owner must acknowledge the captured replay obligation before use.
import { OAuthDpopAgentRequestVerifier } from "../../../platform/security/contracts/agent-request-verifier-v1/src/index.ts";
type Input={issuer:string;audience:string;allowInsecure:boolean;path:string;authorization:string;dpop:string;now:number};
try {
 const chunks:Buffer[]=[];let total=0;
 for await(const chunk of process.stdin){const b=Buffer.from(chunk);total+=b.length;if(total>262144)throw new Error("input-limit");chunks.push(b);}
 const r=JSON.parse(Buffer.concat(chunks).toString("utf8")) as Input;
 let obligation:{proofId:string;verifiedAt:number;ttlSeconds:number}|undefined;
 const verifier=new OAuthDpopAgentRequestVerifier({issuer:r.issuer,audience:r.audience,allowInsecure:r.allowInsecure,now:()=>r.now},{
  consumeDpopProof(id,now,ttl){
   if(obligation!==undefined||ttl!==600)throw new Error("replay protocol");
   obligation={proofId:id,verifiedAt:now,ttlSeconds:ttl};
  },
 });
 try{
  const agent=await verifier.verify(new Request(r.audience+r.path,{method:"POST",headers:{authorization:r.authorization,dpop:r.dpop}}));
  if(obligation===undefined)throw new Error("missing replay obligation");
  process.stdout.write(JSON.stringify({kind:"candidate",agent,replay:obligation}));
 }catch{process.stdout.write(JSON.stringify({kind:"denied"}));}
}catch{process.exitCode=1;}
