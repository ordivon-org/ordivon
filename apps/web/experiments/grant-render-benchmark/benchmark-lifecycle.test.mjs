import assert from "node:assert/strict";
import {spawnSync} from "node:child_process";
import {cpSync,mkdtempSync,mkdirSync,readdirSync,readFileSync,rmSync,symlinkSync,writeFileSync} from "node:fs";
import {tmpdir} from "node:os";
import {dirname,join} from "node:path";
import test from "node:test";
import {fileURLToPath} from "node:url";

const benchmark=fileURLToPath(new URL("./bench.mjs",import.meta.url));

// Normative consumer contract: a failing invocation releases its own scratch
// and cannot remove a pre-existing build output. The fixture is independent
// of the implementation's choice of output-directory name.
test("benchmark failure releases its scratch without touching existing output",()=>{
 const root=mkdtempSync(join(tmpdir(),"wbc-"));
 try{
  const temp=join(root,"tmp"),dist=join(root,"dist","react-19");
  mkdirSync(temp);mkdirSync(dist,{recursive:true});
  const sentinel=join(dist,"previous-output.txt");
  writeFileSync(sentinel,"previous run");
  const run=spawnSync(process.execPath,[benchmark],{
   cwd:root,encoding:"utf8",timeout:15000,
   env:{...process.env,TMPDIR:temp,ORDIVON_WEB_CHROMIUM_EXECUTABLE:join(root,"missing-browser")}
  });
  assert.equal(run.status,1,run.stdout+run.stderr);
  assert.match(run.stderr,/ENOENT|executable doesn't exist/i);
  assert.deepEqual(readdirSync(temp),[]);
  assert.equal(readFileSync(sentinel,"utf8"),"previous run");
 }finally{rmSync(root,{recursive:true,force:true})}
});

// Opt-in native controls: fail after browser launch, and build/render the
// actual four variants. A pre-existing dist fixture is never a GC target.
const nativeBrowser=process.env.ORDIVON_WEB_CHROMIUM_EXECUTABLE;
for(const kind of ["missing-input","success"]){
 test("native benchmark "+kind+" releases its own scratch",{
  skip:!nativeBrowser,timeout:120000,
 },()=>{
  const root=mkdtempSync(join(tmpdir(),"wbn-"));
  let settled=false;
  try{
   const temp=join(root,"tmp"),dist=join(root,"dist","react-19");
   mkdirSync(temp);mkdirSync(dist,{recursive:true});
   const sentinel=join(dist,"previous-output.txt");
   writeFileSync(sentinel,"previous run");
   if(kind==="success"){
    const owner=dirname(benchmark);
    for(const input of ["react","solid","data.ts","package.json"])
     cpSync(join(owner,input),join(root,input),{recursive:true});
    symlinkSync(join(owner,"node_modules"),join(root,"node_modules"),"dir");
   }
   const run=spawnSync(process.execPath,[benchmark],{
    cwd:root,encoding:"utf8",timeout:110000,
    env:{...process.env,TMPDIR:temp,ORDIVON_WEB_CHROMIUM_EXECUTABLE:nativeBrowser},
    maxBuffer:4*1024*1024,
   });
   if(run.error||run.signal)throw Error("Native fixture exit unknown; preserve "+root,{cause:run.error});
   // Do not delete a failed-release recovery coordinate from the consumer test.
   if(run.stderr.includes("Benchmark cleanup incomplete"))throw Error(run.stderr);
   settled=true;
   if(kind==="success"){
    assert.equal(run.status,0,run.stdout+run.stderr);
    const result=run.stdout.match(/^GRANT_BENCHMARK_RESULT=(.+)$/m);
    assert.ok(result,run.stdout+run.stderr);
    assert.equal(JSON.parse(result[1]).results.length,4);
   }else{
    assert.equal(run.status,1,run.stdout+run.stderr);
    assert.match(run.stderr,/index\.html|Could not resolve entry/i);
   }
   assert.deepEqual(readdirSync(temp),[]);
   assert.deepEqual(readdirSync(join(root,"dist")),["react-19"]);
   assert.equal(readFileSync(sentinel,"utf8"),"previous run");
  }finally{if(settled)rmSync(root,{recursive:true,force:true})}
 });
}

test("long Linux temporary path is rejected before browser launch",{
 skip:process.platform!=="linux",
},()=>{
 const root=mkdtempSync(join(tmpdir(),"wbl-"));
 try{
  const temp=join(root,"long".repeat(20));
  mkdirSync(temp);
  const run=spawnSync(process.execPath,[benchmark],{
   cwd:root,encoding:"utf8",timeout:15000,
   env:{...process.env,TMPDIR:temp,ORDIVON_WEB_CHROMIUM_EXECUTABLE:process.execPath}
  });
  assert.equal(run.status,1,run.stdout+run.stderr);
  assert.match(run.stderr,/shorter TMPDIR/);
  assert.deepEqual(readdirSync(temp),[]);
 }finally{rmSync(root,{recursive:true,force:true})}
});
