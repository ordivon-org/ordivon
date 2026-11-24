import assert from "node:assert/strict";
import {readFile,readdir} from "node:fs/promises";
import {chromium} from "playwright";
import {createWebApp} from "../../src/app.ts";
import {WebStore} from "../../src/store.ts";
import type {WebConfig} from "../../src/config.ts";

const executable=process.env.ORDIVON_WEB_CHROMIUM_EXECUTABLE;
if(!executable)throw Error("set ORDIVON_WEB_CHROMIUM_EXECUTABLE");
const config:WebConfig={host:"127.0.0.1",port:0,origin:"http://localhost",rpID:"localhost",rpName:"Solid read probe",databasePath:":memory:",sessionIdleSeconds:300,sessionAbsoluteSeconds:3600};
const now=()=>Math.floor(Date.now()/1000);
const store=new WebStore(":memory:");
const app=await createWebApp(config,{store});
const dist=new URL("./dist/",import.meta.url);
app.get("/__solid_probe/",async(_request,reply)=>reply.type("text/html").send(await readFile(new URL("index.html",dist))));
for(const file of await readdir(new URL("assets/",dist))){
  const data=await readFile(new URL("assets/"+file,dist));
  app.get("/__solid_probe/assets/"+file,async(_request,reply)=>reply.type(file.endsWith(".css")?"text/css":"text/javascript").send(data));
}
await app.listen({host:config.host,port:0});
const address=app.server.address();
assert.ok(address&&typeof address!=="string");
const origin="http://localhost:"+address.port;
const browser=await chromium.launch({headless:true,executablePath:executable,args:["--host-resolver-rules=MAP localhost 127.0.0.1"]});
try{
 store.ensurePrincipal("principal:probe","probe","Probe",now());
 store.ensurePrincipal("principal:other","other","Other",now());
 const session=store.createSession("principal:probe",now(),300,3600,null);
 const make=(grantId:string,principalId:string)=>store.createAgentGrant({grantId,principalId,agentId:"agent:"+grantId,audience:origin,allowedActions:["canary.note.create"],resourcePrefixes:["/canary/notes"],expiresAtEpochSeconds:now()+300,maxRiskClass:"R2",stepUpAtOrAbove:"R4",remainingEffects:3},now());
 const first=make("grant:one","principal:probe");
 make("grant:two","principal:probe");make("grant:foreign","principal:other");
 const context=await browser.newContext();
 await context.addCookies([{name:"__Host-session",value:session.token,url:"https://localhost/",secure:true,httpOnly:true,sameSite:"Lax"}]);
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
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({ownerRows:2,foreignRows:0,semanticChoices:5,filterApplied:true,unknownActionDenied:true,humanFilterApplied:true,quotaUnchanged:true,staleSuccessAfterDenialRejected:true,scope:"isolated test-only route; real WebStore/session, not physical WebAuthn"}));
 await context.close();
}finally{await browser.close();await app.close();store.close()}
