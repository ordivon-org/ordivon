import assert from "node:assert/strict";
import {createRoot,createSignal,createMemo,createDeferred,flush,isPending,latest} from "solid-js";

// Run with Node's browser export condition. This measures the pinned native
// reactive primitives, not a DOM or owner-authorization test. Keep the
// observation fence independent of the chosen rendering/runtime primitive.
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const results=[];
for(const [name,factory] of [["memo",createMemo],["deferred",createDeferred]]){
  const pending=new Map();
  let model;
  createRoot(dispose=>{
    const [generation,setGeneration]=createSignal(0);
    const source=factory(()=>{
      const id=generation();
      return new Promise(resolve=>pending.set(id,resolve));
    },{loadingValue:"empty"});
    model={setGeneration,source,dispose};
  });
  try{
    flush();
    assert.equal(model.source(),"empty");
    pending.get(0)("synthetic-A");await tick();flush();
    assert.equal(model.source(),"synthetic-A");
    model.setGeneration(1);flush();
    const during=model.source();
    const duringLatest=latest(model.source);
    const isRefreshing=isPending(()=>model.source());
    // The pin is a witness for the current runtime, not a requirement that
    // future Solid versions must retain prior answers while pending.
    model.setGeneration(2);flush();
    pending.get(2)("denied");await tick();flush();
    assert.equal(model.source(),"denied");
    pending.get(1)("synthetic-old-A");await tick();flush();
    assert.equal(model.source(),"denied");
    results.push({name,during,duringLatest,isRefreshing,newDenied:"denied",late:"denied"});
  }finally{model.dispose()}
}
console.log("NATIVE_ASYNC_WITNESS="+JSON.stringify(results));
