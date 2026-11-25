import assert from "node:assert/strict";
import {test} from "node:test";
import {readOperatorObservation} from "./operator-observation.ts";

const row={principalId:"p",grantId:"g",agentId:"a",active:true,revision:1,remainingEffects:3,
  expiresAtEpochSeconds:9,allowedActions:["<script>"],resourcePrefixes:["/note"],grantDigest:"not-retained"};
const input={principalId:"p",displayName:"<tag>",observedAt:1,grants:[row]};
test("operator retains full displayed fields only and preserves literal text",()=>{
  const actual=readOperatorObservation(input);
  const {grantDigest:_,...projection}=row;
  assert.deepEqual(actual,{...input,grants:[projection]});
  assert.equal("grantDigest" in actual.grants[0]!,false);
  assert.notEqual(actual.grants[0]?.allowedActions,row.allowedActions);
});
test("operator rejects malformed full projection before rendering",()=>{
  for(const broken of [
    {...input,displayName:1},{...input,observedAt:Number.MAX_SAFE_INTEGER},
    {...input,grants:[{...row,expiresAtEpochSeconds:Number.MAX_SAFE_INTEGER}]},
    {...input,grants:[{...row,allowedActions:[null]}]},
    {...input,grants:[{...row,resourcePrefixes:"/note"}]},
    {...input,grants:[{...row,principalId:"foreign"}]},
    {...input,grants:[row,row]},
  ]) assert.throws(()=>readOperatorObservation(broken));
});
