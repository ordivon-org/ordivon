import assert from "node:assert/strict";
import {createHash} from "node:crypto";
import {resolve} from "node:path";
import {build} from "vite";
import react from "@vitejs/plugin-react";

// This witness is deliberately about the pinned fixture's actual transform,
// not global bundle markers (the React runtime contains some even uncompiled).
// It does not assert optimization coverage for any other component or release.
function section(code,name,next){
 const start=code.lastIndexOf("function "+name+"(");
 assert.ok(start>=0,"fixture function missing: "+name);
 const end=code.indexOf(next,start);
 assert.ok(end>start,"fixture boundary missing: "+name);
 return code.slice(start,end);
}
function witness(code){
 const row=section(code,"GrantRow","function App(");
 const app=section(code,"App","var root");
 const slots=body=>Number(body.match(/import_compiler_runtime\.c\)\((\d+)\)/)?.[1]??0);
 const hash=body=>createHash("sha256").update(body).digest("hex");
 return {GrantRow:{cacheSlots:slots(row),sha256:hash(row)},App:{cacheSlots:slots(app),sha256:hash(app)}};
}
const cases=[];
for(const compiler of [false,true]){
 const result=await build({root:resolve("react"),configFile:false,plugins:[react({compiler})],define:{BENCH_MEMO:"false"},base:"./",build:{write:false,minify:false,sourcemap:false}});
 const chunks=(Array.isArray(result)?result:[result]).flatMap(p=>p.output).filter(p=>p.type==="chunk"&&p.code.includes("function GrantRow(")&&p.code.includes("function App("));
 assert.equal(chunks.length,1,"fixture components must be in one inspectable chunk");
 const observed=witness(chunks[0].code);
 for(const component of Object.values(observed)) {
  if(compiler)assert.ok(component.cacheSlots>0,"no per-component compiler cache found");
  else assert.equal(component.cacheSlots,0,"baseline unexpectedly contains compiler cache");
 }
 cases.push({compiler,...observed});
}
console.log("REACT_COMPILER_FIXTURE_WITNESS="+JSON.stringify(cases));
