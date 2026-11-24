import assert from "node:assert/strict";
import {test} from "node:test";
import {WebStore} from "../src/store.ts";
import {WebProblem} from "../src/errors.ts";
import {stableDigest} from "../src/identity-digests.ts";

function fixture(){
 const store=new WebStore(":memory:");
 store.ensurePrincipal("principal:challenge","challenge","Challenge",100);
 return store;
}
const corruption=(error:unknown)=>error instanceof WebProblem &&
 error.status===500 && error.code==="challenge-corrupt";

test("a mismatched stored challenge payload is not returned or consumed",()=>{
 const store=fixture();
 try{
  const record=store.createChallenge("grant-issue","principal:challenge","fixture",100,60,{grantId:"original"});
  store.db.prepare("UPDATE webauthn_challenges SET payload_json = ? WHERE challenge_id = ?").run('{"grantId":"different"}',record.challengeId);
  assert.throws(()=>store.consumeChallenge(record.challengeId,"grant-issue",110),corruption);
  const row=store.db.prepare("SELECT consumed_at FROM webauthn_challenges WHERE challenge_id = ?").get(record.challengeId);
  assert.equal(row?.consumed_at,null);
 }finally{store.close()}
});

test("malformed stored challenge JSON rolls back before marking the challenge consumed",()=>{
 const store=fixture();
 try{
  const record=store.createChallenge("effect-approve","principal:challenge","fixture",100,60,{effectId:"test"});
  store.db.prepare("UPDATE webauthn_challenges SET payload_json = ? WHERE challenge_id = ?").run("{invalid",record.challengeId);
  assert.throws(()=>store.consumeChallenge(record.challengeId,"effect-approve",110),corruption);
  const row=store.db.prepare("SELECT consumed_at FROM webauthn_challenges WHERE challenge_id = ?").get(record.challengeId);
  assert.equal(row?.consumed_at,null);
  // A different valid ceremony remains usable; no transaction was left open.
  const valid=store.createChallenge("login","principal:challenge","next",110,60);
  assert.deepEqual(store.consumeChallenge(valid.challengeId,"login",111).payload,{});
 }finally{store.close()}
});

test("challenge creation binds one serialized payload snapshot even for stateful serialization",()=>{
 const store=fixture();
 try{
  let serializations=0;
  const payload={toJSON(){return {version:++serializations}}};
  const record=store.createChallenge("grant-revoke","principal:challenge","fixture",100,60,payload);
  assert.equal(serializations,1);
  assert.deepEqual(record.payload,{version:1});
  const consumed=store.consumeChallenge(record.challengeId,"grant-revoke",110);
  assert.deepEqual(consumed.payload,record.payload);
  assert.equal(consumed.payloadDigest,stableDigest(consumed.payload));
  assert.throws(()=>store.consumeChallenge(record.challengeId,"grant-revoke",111),/missing, expired, consumed/);
 }finally{store.close()}
});
