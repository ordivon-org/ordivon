// Trusted local process adapter. No database, network service, policy or session secret.
import { generateAuthenticationOptions, verifyAuthenticationResponse, type AuthenticationResponseJSON, type WebAuthnCredential } from "@simplewebauthn/server";

type Wire = { op:"options"; rpID:string; credentials:{id:string;transports:NonNullable<WebAuthnCredential["transports"]>}[] } |
{ op:"verify"; rpID:string; origin:string; challenge:string; response:AuthenticationResponseJSON; credential:Omit<WebAuthnCredential,"publicKey">&{publicKey:number[]} };
try {
  const chunks:Buffer[]=[]; let total=0;
  for await(const chunk of process.stdin){const b=Buffer.from(chunk);total+=b.length;if(total>262144)throw new Error("input-limit");chunks.push(b);}
  const request=JSON.parse(Buffer.concat(chunks).toString("utf8")) as Wire;
  if(request.op==="options"){
    const options=await generateAuthenticationOptions({rpID:request.rpID,allowCredentials:request.credentials,userVerification:"required"});
    process.stdout.write(JSON.stringify({kind:"options",options}));
  }else if(request.op==="verify"){
    try{
      const result=await verifyAuthenticationResponse({response:request.response,expectedChallenge:request.challenge,expectedOrigin:request.origin,expectedRPID:request.rpID,credential:{...request.credential,publicKey:Uint8Array.from(request.credential.publicKey)},requireUserVerification:true});
      if(result.verified&&result.authenticationInfo.userVerified&&result.authenticationInfo.credentialID===request.credential.id){
        process.stdout.write(JSON.stringify({kind:"verified",counter:result.authenticationInfo.newCounter}));
      }else process.stdout.write(JSON.stringify({kind:"denied"}));
    }catch{process.stdout.write(JSON.stringify({kind:"denied"}));}
  }else throw new Error("unknown-operation");
}catch{process.exitCode=1;}
