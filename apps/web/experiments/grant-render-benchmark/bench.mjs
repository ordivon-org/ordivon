import assert from "node:assert/strict";
import {build,preview} from "vite";
import react from "@vitejs/plugin-react";
import solid from "@solidjs/vite-plugin";
import {chromium} from "playwright";
import {readdir,readFile} from "node:fs/promises";
import {gzipSync} from "node:zlib";
import {resolve} from "node:path";
import {performance} from "node:perf_hooks";
import {cpus,totalmem,platform,arch} from "node:os";

const executable=process.env.ORDIVON_WEB_CHROMIUM_EXECUTABLE;
if(!executable)throw Error("set ORDIVON_WEB_CHROMIUM_EXECUTABLE");
const variants=[
 {name:"react-19",root:"react",plugin:()=>react(),memo:false},
 {name:"react-19-memo",root:"react",plugin:()=>react(),memo:true},
 {name:"react-19-native-compiler-configured",root:"react",plugin:()=>react({compiler:true}),memo:false},
 {name:"solid-2",root:"solid",plugin:()=>solid(),memo:false},
];
const servers=[],results=[];
const browser=await chromium.launch({headless:true,executablePath:executable});
const quantile=(v,q)=>{const a=[...v].sort((a,b)=>a-b);return Math.round(a[Math.ceil(q*a.length)-1]*100)/100};
try{
 for(const v of variants){
   const root=resolve(v.root),out=resolve("dist",v.name);
   const options={root,configFile:false,plugins:[v.plugin()],define:{BENCH_MEMO:JSON.stringify(v.memo)},base:"./",build:{outDir:out,emptyOutDir:true}};
   const start=performance.now();await build(options);
   const buildMs=Math.round(performance.now()-start);
   const js=(await readdir(resolve(out,"assets"))).filter(x=>x.endsWith(".js"));
   let bytes=0,gz=0;
   for(const f of js){const b=await readFile(resolve(out,"assets",f));bytes+=b.length;gz+=gzipSync(b).length;}
   const server=await preview({...options,preview:{host:"127.0.0.1",port:0,strictPort:true}});servers.push(server);
   results.push({name:v.name,port:server.httpServer.address().port,buildMs,jsBytes:bytes,gzipBytes:gz,loads:{}});
 }
 for(const n of [1000,5000]){
  const samples=Object.fromEntries(results.map(v=>[v.name,{mount:[],update:[]}]));
  for(let rep=0;rep<5;rep++){
   // Rotate starting order to distribute browser/JIT/host drift; one browser,
   // a fresh page per case, same warmup, no interleaved framework work.
   for(let k=0;k<results.length;k++){
    const v=results[(rep+k)%results.length];
    const page=await browser.newPage();
    try{
     await page.goto("http://127.0.0.1:"+v.port);
     await page.waitForFunction(()=>typeof window.mountRows==="function",null,{timeout:5000});
     const sample=await page.evaluate(({n})=>{
      const count=()=>document.querySelectorAll("tbody tr").length;
      const row=(i)=>document.querySelector('tr[data-id="grant:'+i+'"]');
      const cell=(i)=>row(i).querySelector("[data-quota]");
      window.mountRows(100);window.mountRows(0);
      const t=performance.now();window.mountRows(n);const mount=performance.now()-t;
      if(count()!==n)throw Error("mount mismatch "+count());
      const updates=[],touched=new Set();
      for(let i=0;i<50;i++){
       const k=(i*97)%n;const node=cell(k),original=row(k);
       if(node.textContent!=="8")throw Error("bad initial value");
       const start=performance.now();window.changeRow(k);updates.push(performance.now()-start);
       if(row(k)!==original||cell(k)!==node||node.textContent!=="7"||row(k).querySelector("[data-revision]").textContent!=="2")throw Error("row identity/value mismatch");
       touched.add(k);
      }
      if(count()!==n)throw Error("row count changed");
      // Verify all rows outside the timed region, not just a sentinel.
      for(let i=0;i<n;i++){
        if(cell(i).textContent!==(touched.has(i)?"7":"8"))throw Error("unexpected row change "+i);
        if(row(i).querySelector("[data-revision]").textContent!==(touched.has(i)?"2":"1"))throw Error("unexpected revision "+i);
      }
      return {mount,updates};
     },{n});
     samples[v.name].mount.push(sample.mount);samples[v.name].update.push(...sample.updates);
    }finally{await page.close()}
   }
  }
  for(const v of results){const x=samples[v.name];assert.equal(x.mount.length,5);assert.equal(x.update.length,250);v.loads[n]={mountMedianMs:quantile(x.mount,.5),updateMedianMs:quantile(x.update,.5),updateP95Ms:quantile(x.update,.95),mountSamples:x.mount.length,updateSamples:x.update.length}}
 }
 console.log("GRANT_BENCHMARK_RESULT="+JSON.stringify({browser:browser.version(),node:process.version,host:{platform:platform(),arch:arch(),cpu:cpus()[0]?.model,logicalCpus:cpus().length,totalMemoryBytes:totalmem()},metrics:"synchronous array update and DOM commit; excludes layout/paint, network and agent tokens; compiler configuration is not a proof of transform coverage",results:results.map(({port,...v})=>v)}));
}finally{await browser.close();for(const s of servers)await new Promise(r=>s.httpServer.close(r))}
