import assert from "node:assert/strict";
import {mkdtemp,writeFile,rm} from "node:fs/promises";
import {tmpdir} from "node:os";
import {join} from "node:path";
import test from "node:test";
import {acquirePreview,releasePreviews} from "./preview-lifecycle.mjs";

for(const kind of ["success","partial-start","before-handle"]){
 test("native preview "+kind+" respects the owner release boundary",async()=>{
  const root=await mkdtemp(join(tmpdir(),"owp-"));
  const claims=[];
  let observed, releases=0;
  try{
   await writeFile(join(root,"index.html"),"<p>preview</p>");
   const probe={
    name:"independent-native-release-consumer",
    config(){
     if(kind==="before-handle")throw Error("injected config failure");
    },
    configurePreviewServer(server){
     observed=server;
     if(kind==="partial-start")throw Error("injected setup failure");
    },
    closePreviewServer(){releases++},
   };
   const options={root,configFile:false,logLevel:"silent",
    build:{outDir:root},plugins:[probe],preview:{host:"127.0.0.1",port:0,strictPort:true}};
   if(kind==="success"){
    const server=await acquirePreview(claims,options);
    assert.equal(server,observed);
    const port=server.httpServer.address().port;
    const reply=await fetch("http://127.0.0.1:"+port);
    assert.equal(await reply.text(),"<p>preview</p>");
   }else{
    await assert.rejects(acquirePreview(claims,options),/injected (config|setup) failure/);
   }
   const settled=await releasePreviews(claims);
   assert.equal(settled.length,1,"every admission has a release disposition");
   if(kind==="before-handle"){
    assert.equal(settled[0].status,"rejected","unknown acquisition cannot prove release");
    assert.equal(releases,0);
   }else{
    assert.equal(settled[0].status,"fulfilled");
    assert.equal(releases,1,"native plugin close hook was not consumed");
    assert.equal(observed.httpServer.listening,false);
    assert.equal(observed.resolvedUrls,null);
   }
  }finally{
   // The independent fixture owns the exact observed handle. This fallback
   // prevents a deliberately broken candidate from leaking test resources.
   if(observed)await observed.close().catch(()=>{});
   await rm(root,{recursive:true,force:true});
  }
 });
}

test("one native close hook rejects without suppressing the other owner release",async()=>{
 const root=await mkdtemp(join(tmpdir(),"owp-"));
 const claims=[], observed=[], released=[];
 try{
  await writeFile(join(root,"index.html"),"<p>preview</p>");
  for(const name of ["fault","healthy"]){
   const probe={
    name:"independent-close-"+name,
    configurePreviewServer(server){observed.push(server)},
    closePreviewServer(){
     released.push(name);
     if(name==="fault")throw Error("injected close hook failure");
    },
   };
   await acquirePreview(claims,{root,configFile:false,logLevel:"silent",
    build:{outDir:root},plugins:[probe],preview:{host:"127.0.0.1",port:0,strictPort:true}});
  }
  const outcomes=await releasePreviews(claims);
  assert.deepEqual(outcomes.map(x=>x.status),["rejected","fulfilled"]);
  assert.match(outcomes[0].reason.message,/injected close hook failure/);
  assert.deepEqual(released.sort(),["fault","healthy"]);
  assert.ok(observed.every(server=>!server.httpServer.listening));
 }finally{
  await Promise.allSettled(observed.map(server=>server.close()));
  await rm(root,{recursive:true,force:true});
 }
});
