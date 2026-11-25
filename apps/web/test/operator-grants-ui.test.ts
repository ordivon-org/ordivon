import assert from "node:assert/strict";
import {mkdtempSync,mkdirSync,writeFileSync,rmSync} from "node:fs";
import {tmpdir} from "node:os";
import {join} from "node:path";
import {test} from "node:test";
import {loadOperatorGrantsUi} from "../src/operator-grants-ui.ts";

test("operator build allowlist binds only manifest paths and rejects missing assets",()=>{
  const dir=mkdtempSync(join(tmpdir(),"ordivon-operator-ui-"));
  try {
    mkdirSync(join(dir,".vite"));mkdirSync(join(dir,"assets"));
    const write=(entry:unknown)=>writeFileSync(join(dir,".vite","manifest.json"),JSON.stringify({"operator.html":entry}));
    assert.throws(()=>loadOperatorGrantsUi(dir));
    write({isEntry:true,file:"assets/operator-abc.js",css:["assets/operator-abc.css"]});
    assert.throws(()=>loadOperatorGrantsUi(dir));
    writeFileSync(join(dir,"assets","operator-abc.js"),"export {}");
    writeFileSync(join(dir,"assets","operator-abc.css"),"body{}");
    writeFileSync(join(dir,"assets","not-in-manifest.js"),"private fixture");
    const result=loadOperatorGrantsUi(dir);
    assert.deepEqual([...result.assets.keys()],["/_web/grants/assets/operator-abc.js","/_web/grants/assets/operator-abc.css"]);
    assert.match(result.html,/src="\/_web\/grants\/assets\/operator-abc.js"/);
    assert.match(result.html,/href="\/_web\/grants\/assets\/operator-abc.css"/);
    for(const bad of ["../outside.js","assets/../outside.js","assets/x.js?secret","assets/x\".js","assets/x.svg","/assets/x.js"]) {
      write({isEntry:true,file:bad});
      assert.throws(()=>loadOperatorGrantsUi(dir),/Invalid operator UI asset path/);
    }
    for(const invalid of [
      {isEntry:true,file:"assets/operator-abc.js",imports:["missing"]},
      {isEntry:true,file:"assets/operator-abc.js",dynamicImports:"invalid"},
      {isEntry:true,file:"assets/operator-abc.js",assets:["assets/unexpected.png"]},
    ]) {
      write(invalid);assert.throws(()=>loadOperatorGrantsUi(dir));
    }
    write({isEntry:false,file:"assets/operator-abc.js"});
    assert.throws(()=>loadOperatorGrantsUi(dir),/Missing operator UI entry/);
  }finally{rmSync(dir,{recursive:true,force:true})}
});
