// Independent synthetic ES256 authenticator, test only, never an admission oracle.
import {generateKeyPairSync,createPrivateKey,createHash,sign} from "node:crypto";
const hash=b=>createHash("sha256").update(b).digest();
const b64=b=>Buffer.from(b).toString("base64url");
const id=b64(Buffer.from("ordivon-test-credential"));
if(process.argv[2]==="key"){
 const {privateKey,publicKey}=generateKeyPairSync("ec",{namedCurve:"prime256v1"});
 const jwk=publicKey.export({format:"jwk"});
 const cose=Buffer.concat([Buffer.from("a5010203262001215820","hex"),Buffer.from(jwk.x,"base64url"),Buffer.from("225820","hex"),Buffer.from(jwk.y,"base64url")]);
 console.log(JSON.stringify({id,key:[...cose],private:privateKey.export({format:"jwk"})}));
}else{
 const [key,challenge,variant]=process.argv.slice(2);
 const privateKey=createPrivateKey({key:JSON.parse(key),format:"jwk"});
 const client=Buffer.from(JSON.stringify({type:"webauthn.get",challenge:variant==="challenge"?"bad-challenge":challenge,origin:variant==="origin"?"https://evil.example":"https://web.example",crossOrigin:false}));
 const data=Buffer.alloc(37);hash(variant==="rp"?"evil.example":"web.example").copy(data);
 data[32]=variant==="uv"?1:5;data.writeUInt32BE(variant==="counter"?0:1,33);
 const sig=sign("sha256",Buffer.concat([data,hash(client)]),privateKey);
 if(variant==="signature")sig[sig.length-1]^=1;
 console.log(JSON.stringify({id,rawId:id,type:"public-key",response:{clientDataJSON:b64(client),authenticatorData:b64(data),signature:b64(sig)},clientExtensionResults:{}}));
}
