// Disposable local issuer. Actual RSA JWT/ES256 proof signatures; no real credentials.
import {createServer} from "node:http";
import {createHash,generateKeyPairSync,sign,randomUUID} from "node:crypto";
import {createInterface} from "node:readline";
const b64=b=>Buffer.from(b).toString("base64url");
const enc=v=>b64(JSON.stringify(v));
const hash=v=>createHash("sha256").update(v).digest("base64url");
const {privateKey:asPrivate,publicKey:asPublic}=generateKeyPairSync("rsa",{modulusLength:2048});
const {privateKey:dpopPrivate,publicKey:dpopPublic}=generateKeyPairSync("ec",{namedCurve:"prime256v1"});
const jwk={...asPublic.export({format:"jwk"}),kid:"fixture-as",alg:"RS256",use:"sig"};
const proofKey=dpopPublic.export({format:"jwk"});
const thumbprint=hash(JSON.stringify({crv:proofKey.crv,kty:proofKey.kty,x:proofKey.x,y:proofKey.y}));
const audience="https://web.example";
let issuer;
const server=createServer((req,res)=>{
 const data=req.url==="/.well-known/openid-configuration"?{issuer,jwks_uri:issuer+"jwks",token_endpoint:issuer+"token"}:req.url==="/jwks"?{keys:[jwk]}:null;
 res.writeHead(data?200:404,{"content-type":"application/json"});res.end(JSON.stringify(data));
});
await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
issuer="http://127.0.0.1:"+server.address().port+"/";
console.log(JSON.stringify({issuer}));
function jwt(h,p,key,ec=false){
 const value=enc(h)+"."+enc(p);
 return value+"."+b64(sign("sha256",Buffer.from(value),ec?{key,dsaEncoding:"ieee-p1363"}:key));
}
for await(const line of createInterface({input:process.stdin})){
 const {path,variant="ok",jti=randomUUID(),client="agent-test"}=JSON.parse(line);
 const now=Math.floor(Date.now()/1000);
 let token=jwt({alg:"RS256",typ:"at+jwt",kid:"fixture-as"},{iss:issuer,exp:now+300,aud:variant==="audience"?"https://wrong.example":audience,sub:"fixture-service",iat:now,jti:randomUUID(),client_id:client,cnf:{jkt:variant==="binding"?"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA":thumbprint}},asPrivate);
 const proof=jwt({alg:"ES256",typ:"dpop+jwt",jwk:proofKey},{jti,iat:variant==="expired"?now-10000:now,htm:variant==="method"?"GET":"POST",htu:audience+(variant==="path"?"/wrong":path),ath:hash(token)},dpopPrivate,true);
 if(variant==="token-signature")token=token.slice(0,-4)+"AAAA";
 console.log(JSON.stringify({authorization:"DPoP "+token,dpop:proof,jti}));
}
server.close();
