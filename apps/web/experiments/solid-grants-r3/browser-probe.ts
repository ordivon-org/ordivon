import assert from "node:assert/strict";
import {readFile,readdir} from "node:fs/promises";
import {chromium} from "playwright";
import {createWebApp} from "../../src/app.ts";
import {WebStore} from "../../src/store.ts";
import type {WebConfig} from "../../src/config.ts";

const executable=process.env.ORDIVON_WEB_CHROMIUM_EXECUTABLE;
if(!executable)throw Error("set ORDIVON_WEB_CHROMIUM_EXECUTABLE");
const config={host:"127.0.0.1",port:0,origin:"http://localhost",rpID:"localhost",rpName:"Solid read probe",databasePath:":memory:",sessionIdleSeconds:300,sessionAbsoluteSeconds:3600} satisfies WebConfig;
const now=()=>Math.floor(Date.now()/1000);
const store=new WebStore(":memory:");
const app=await createWebApp(config,{store});
const dist=new URL("./dist/",import.meta.url);
app.get("/__solid_probe/",async(_request,reply)=>reply.type("text/html").send(await readFile(new URL("index.html",dist))));
app.get("/__solid_probe/blank",async(_request,reply)=>reply.type("text/html").send("<!doctype html><html><title>Navigation fixture</title><p>Navigation fixture</p></html>"));
for(const file of await readdir(new URL("assets/",dist))){
  const data=await readFile(new URL("assets/"+file,dist));
  app.get("/__solid_probe/assets/"+file,async(_request,reply)=>reply.type(file.endsWith(".css")?"text/css":"text/javascript").send(data));
}
await app.listen({host:config.host,port:0});
const address=app.server.address();
assert.ok(address&&typeof address!=="string");
const origin="http://localhost:"+address.port;
// Bind actual ephemeral origin before the first request; sameOriginGuard reads this object.
config.origin=origin;
const browser=await chromium.launch({headless:true,executablePath:executable,ignoreDefaultArgs:["--disable-back-forward-cache"],args:["--host-resolver-rules=MAP localhost 127.0.0.1"]});
try{
 store.ensurePrincipal("principal:probe","probe","Probe",now());
 store.ensurePrincipal("principal:other","other","Other",now());
 const session=store.createSession("principal:probe",now(),300,3600,null);
 const make=(grantId:string,principalId:string)=>store.createAgentGrant({grantId,principalId,agentId:"agent:"+grantId,audience:origin,allowedActions:["canary.note.create"],resourcePrefixes:["/canary/notes"],expiresAtEpochSeconds:now()+300,maxRiskClass:"R2",stepUpAtOrAbove:"R4",remainingEffects:3},now());
 const first=make("grant:one","principal:probe");
 make("grant:two","principal:probe");make("grant:foreign","principal:other");
 const context=await browser.newContext();
 await context.addCookies([{name:"__Host-session",value:session.token,url:"https://localhost/",secure:true,httpOnly:true,sameSite:"Lax"}]);
 await context.addInitScript(()=>{
   (window as any).nativePageShow=[];
   window.addEventListener("pageshow",e=>(window as any).nativePageShow.push({persisted:e.persisted,trusted:e.isTrusted}));
 });
 const page=await context.newPage();
 const errors:string[]=[];page.on("pageerror",e=>errors.push(e.message));
 await page.goto(origin+"/__solid_probe/");
 await page.locator('[data-status="observed"]').waitFor();
 assert.equal(await page.locator("tbody tr").count(),2);
 assert.equal(await page.getByText("grant:foreign",{exact:true}).count(),0);
 const initial=await page.evaluate(()=> (window as any).probe.bridge.snapshot());
 assert.ok(initial.some((x:any)=>x.label==="Grant availability"&&x.value==="all"),JSON.stringify(initial));
 const query=await page.evaluate(()=> (window as any).probe.bridge.query({within:"Grant availability"}));
 assert.equal(query[0].items.length,5);
 store.revokeAgentGrant("principal:probe",first.grantId,first.grantDigest,now());
 await page.getByRole("button",{name:"Refresh owner observation"}).click();
 await page.locator('[data-status="observed"]').waitFor();
 const action=await page.evaluate(()=> (window as any).probe.bridge.act({steps:[{ref:"Grant availability",action:"setValue",args:["revoked"]}]}));
 assert.equal(action.ok,true,JSON.stringify(action));
 await page.waitForFunction(()=>document.querySelectorAll("tbody tr").length===1);
 assert.equal(await page.getByRole("row").filter({hasText:"grant:one"}).count(),1);
 assert.equal(await page.getByRole("row").filter({hasText:"grant:two"}).count(),0);
 const rejected=await page.evaluate(()=> (window as any).probe.bridge.act({steps:[{ref:"Grant availability",action:"setValue",args:["not-an-option"]}]}));
 assert.equal(rejected.ok,false);
 await page.getByTestId("filter").click();
 await page.getByText("All grants",{exact:true}).click();
 await page.waitForFunction(()=>document.querySelectorAll("tbody tr").length===2);
 assert.equal(store.getAgentGrant("grant:two").remainingEffects,3);
 // Hold an actual successful Owner GET, revoke its session, let newer denial
 // arrive, then release old response. It must not restore private rows.
 let held!:()=>void;const captured=new Promise<void>(r=>{held=r});
 let release!:()=>void;const gate=new Promise<void>(r=>{release=r});
 let requestCount=0;
 await page.route("**/api/security/agents/grants",async route=>{
   if(++requestCount!==1){await route.continue();return}
   const old=await route.fetch();assert.equal(old.status(),200);held();await gate;await route.fulfill({response:old});
 });
 await page.evaluate(()=>{(window as any).lateRefresh=(window as any).probe.refresh()});
 await captured;
 assert.equal(await page.locator("tbody tr").count(),0);
 store.revokeSession("principal:probe",session.session.sessionId,now());
 await page.evaluate(()=> (window as any).probe.refresh());
 await page.locator('[data-status="denied"]').waitFor();
 const responseDone=page.waitForResponse(r=>r.url().endsWith("/api/security/agents/grants")&&r.status()===200);
 release();await responseDone;
 await page.waitForFunction(()=>document.querySelector('[data-status="denied"]')!==null);
 // Explicitly wait for old response processing (refresh promise recorded separately).
 await page.evaluate(()=> (window as any).lateRefresh);
 assert.equal(await page.locator("tbody tr").count(),0);

 // Explicit lifecycle negative control: the first response is a real Owner
 // GET, then the document leaves the active lifecycle while that GET is held.
 await page.unroute("**/api/security/agents/grants");
 const secondSession=store.createSession("principal:probe",now(),300,3600,null);
 await context.addCookies([{name:"__Host-session",value:secondSession.token,url:"https://localhost/",secure:true,httpOnly:true,sameSite:"Lax"}]);
 await page.evaluate(()=> (window as any).probe.refresh());
 await page.locator('[data-status="observed"]').waitFor();
 assert.equal(await page.locator("tbody tr").count(),2);
 let holdLifecycle!:()=>void;const capturedLifecycle=new Promise<void>(r=>{holdLifecycle=r});
 let releaseLifecycle!:()=>void;const gateLifecycle=new Promise<void>(r=>{releaseLifecycle=r});
 await page.route("**/api/security/agents/grants",async route=>{
   const old=await route.fetch();assert.equal(old.status(),200);
   holdLifecycle();await gateLifecycle;await route.fulfill({response:old});
 });
 await page.evaluate(()=>{(window as any).lifecycleRefresh=(window as any).probe.refresh()});
 await capturedLifecycle;
 await page.evaluate(()=>window.dispatchEvent(new PageTransitionEvent("pagehide",{persisted:true})));
 releaseLifecycle();
 await page.evaluate(()=> (window as any).lifecycleRefresh);
 assert.equal(await page.locator('[data-status="suspended"]').count(),1);
 assert.equal(await page.locator("tbody tr").count(),0);
 await page.unroute("**/api/security/agents/grants");
 const otherSession=store.createSession("principal:other",now(),300,3600,null);
 await context.addCookies([{name:"__Host-session",value:otherSession.token,url:"https://localhost/",secure:true,httpOnly:true,sameSite:"Lax"}]);
 await page.evaluate(()=>window.dispatchEvent(new PageTransitionEvent("pageshow",{persisted:true})));
 await page.locator('[data-status="observed"]').waitFor({timeout:5000});
 assert.equal(await page.locator("tbody tr").count(),1);
 assert.equal(await page.getByText("grant:foreign",{exact:true}).count(),1);
 assert.equal(await page.getByText("grant:one",{exact:true}).count(),0);

 // Browser-native navigation, rather than dispatching a synthetic event.
 // Revoke the current session while the document is away, without changing
 // its cookie. BFCache eligibility is independently observed, not assumed.
 await page.goto(origin+"/__solid_probe/blank");
 store.revokeSession("principal:other",otherSession.session.sessionId,now());
 await page.goBack({waitUntil:"commit"});
 await page.locator('[data-status="denied"]').waitFor({timeout:10000});
 assert.equal(await page.locator("tbody tr").count(),0);
 const restoredFromBFCache=await page.evaluate(()=> (window as any).nativePageShow.some((e:any)=>e.trusted&&e.persisted));

 // Continuously visible, same-storage-partition tabs. A real native logout
 // plus an invalidation-only hint must fence an already-authorized response.
 const thirdSession=store.createSession("principal:probe",now(),300,3600,null);
 await context.addCookies([{name:"__Host-session",value:thirdSession.token,url:"https://localhost/",secure:true,httpOnly:true,sameSite:"Lax"}]);
 await page.evaluate(()=> (window as any).probe.refresh());
 await page.locator('[data-status="observed"]').waitFor();
 const peer=await context.newPage();
 await peer.goto(origin+"/__solid_probe/");
 await peer.locator('[data-status="observed"]').waitFor();
 assert.equal(await page.evaluate(()=>document.visibilityState),"visible");
 let holdPeer!:()=>void;const capturedPeer=new Promise<void>(r=>{holdPeer=r});
 let releasePeer!:()=>void;const peerGate=new Promise<void>(r=>{releasePeer=r});
 await page.route("**/api/security/agents/grants",async route=>{
   const old=await route.fetch();assert.equal(old.status(),200);
   holdPeer();await peerGate;await route.fulfill({response:old});
 });
 await page.evaluate(()=>{(window as any).peerRefresh=(window as any).probe.refresh()});
 await capturedPeer;
 await peer.evaluate(()=>{
   const channel=new BroadcastChannel("ordivon-web-observation-invalidation-v1");
   channel.postMessage({principalId:"forged",grants:[{grantId:"forged"}]});channel.close();
 });
 const logoutResponse=peer.waitForResponse(r=>r.url().endsWith("/api/session/logout"));
 await peer.getByRole("button",{name:"Sign out"}).click();
 assert.equal((await logoutResponse).status(),200);
 await peer.locator('[data-logout="confirmed"]').waitFor();
 assert.equal(await peer.locator("tbody tr").count(),0);
 await page.locator('[data-status="suspended"]').waitFor({timeout:3000});
 releasePeer();
 await page.evaluate(()=> (window as any).peerRefresh);
 assert.equal(await page.locator("tbody tr").count(),0);
 assert.equal(await page.locator('[data-status="suspended"]').count(),1);
 await page.unroute("**/api/security/agents/grants");
 await page.evaluate(()=> (window as any).probe.refresh());
 await page.locator('[data-status="denied"]').waitFor();
 // A same-origin hint is not a logout assertion: a valid owner
 // observation must still be accepted when the hint was unsolicited.
 const fourthSession=store.createSession("principal:other",now(),300,3600,null);
 await context.addCookies([{name:"__Host-session",value:fourthSession.token,url:"https://localhost/",secure:true,httpOnly:true,sameSite:"Lax"}]);
 await page.evaluate(()=> (window as any).probe.refresh());
 await page.locator('[data-status="observed"]').waitFor();
 await peer.evaluate(()=>{
   const channel=new BroadcastChannel("ordivon-web-observation-invalidation-v1");
   channel.postMessage("session-changed");channel.close();
 });
 await page.locator('[data-status="suspended"]').waitFor();
 assert.equal(await page.locator("tbody tr").count(),0);
 await page.evaluate(()=> (window as any).probe.refresh());
 await page.locator('[data-status="observed"]').waitFor();
 assert.equal(await page.getByText("grant:foreign",{exact:true}).count(),1);

 // A committed logout whose response is lost is not a confirmation.
 // Use the real owner POST once; discard only its response.
 await peer.evaluate(()=> (window as any).probe.refresh());
 await peer.locator('[data-status="observed"]').waitFor();
 let logoutRequests=0;
 await peer.route("**/api/session/logout",async route=>{
   logoutRequests++;
   const committed=await route.fetch();assert.equal(committed.status(),200);
   await route.abort("failed");
 });
 await peer.getByRole("button",{name:"Sign out"}).click();
 await peer.locator('[data-logout="unknown"]').waitFor();
 assert.equal(logoutRequests,1);
 assert.equal(await peer.locator("tbody tr").count(),0);
 await page.locator('[data-status="suspended"]').waitFor();
 assert.equal(await page.locator("tbody tr").count(),0);
 await page.evaluate(()=> (window as any).probe.refresh());
 await page.locator('[data-status="denied"]').waitFor();
 assert.equal(logoutRequests,1);
 await peer.close();
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({ownerRows:2,foreignRows:0,semanticChoices:5,filterApplied:true,unknownActionDenied:true,humanFilterApplied:true,quotaUnchanged:true,staleSuccessAfterDenialRejected:true,lifecycleLateResponseRejected:true,identityChangedOnResume:true,nativeBackNavigationDenial:true,restoredFromBFCache,peerNativeLogout:true,peerLateResponseRejected:true,unsolicitedHintDoesNotDenyOwner:true,committedLogoutResponseLossUnknown:true,noLogoutReplay:true,scope:"isolated test-only route; real WebStore/session, not physical WebAuthn"}));
 await context.close();
}finally{await browser.close();await app.close();store.close()}
