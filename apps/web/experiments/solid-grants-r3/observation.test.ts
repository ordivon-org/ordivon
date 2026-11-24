import assert from "node:assert/strict";
import {test} from "node:test";
import {initial,begin,settle,readObservation} from "./observation.ts";
const observed={status:"observed",observation:{principalId:"p",observedAt:1,grants:[]}} as const;
const denied={status:"denied",observation:null} as const;
test("newest refresh invalidates preceding snapshot and late success cannot resurrect it",()=>{
 const first=begin(initial), second=begin(first);
 const end=settle(second,second.generation,denied);
 assert.equal(settle(end,first.generation,observed),end);
 assert.equal(settle(end,second.generation,observed),end);
 assert.equal(end.observation,null);
});
test("newer success is not overwritten by older response or duplicate completion",()=>{
 const first=begin(initial), second=begin(first);
 const end=settle(second,second.generation,observed);
 assert.equal(settle(end,first.generation,denied),end);
 assert.equal(settle(end,second.generation,denied),end);
 assert.equal(begin(end).observation,null);
});
test("read rejects foreign rows and malformed observations",()=>{
 assert.throws(()=>readObservation({principalId:"p",observedAt:0,grants:[{principalId:"q"}]}));
 assert.throws(()=>readObservation({principalId:"p",observedAt:NaN,grants:[]}));
 assert.deepEqual(readObservation(observed.observation),observed.observation);
});

test("consumer retains only the row fields it renders",()=>{
 const result=readObservation({principalId:"p",observedAt:1,grants:[{
   principalId:"p",grantId:"g",agentId:"a",active:true,revision:1,remainingEffects:3,expiresAtEpochSeconds:9,grantDigest:"owner-only-extra"
 }]});
 assert.equal("grantDigest" in result.grants[0]!,false);
});
