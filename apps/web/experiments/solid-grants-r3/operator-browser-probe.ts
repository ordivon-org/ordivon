import assert from "node:assert/strict";
import {fileURLToPath} from "node:url";
import {chromium} from "playwright";
import {createWebApp} from "../../src/app.ts";
import {WebStore} from "../../src/store.ts";
import type {WebConfig} from "../../src/config.ts";

const now=()=>1800000000;
const store=new WebStore(":memory:");
const config:WebConfig={host:"127.0.0.1",port:0,origin:"http://localhost",rpID:"localhost",rpName:"Operator test",databasePath:":memory:",sessionIdleSeconds:300,sessionAbsoluteSeconds:3600};
const app=await createWebApp({...config,operatorGrantsDist:fileURLToPath(new URL("./dist-operator/",import.meta.url))},{store,now});
const reference=await createWebApp(config,{store,now});
await app.listen({host:config.host,port:0});
const address=app.server.address();assert.ok(address&&typeof address!=="string");
const origin="http://localhost:"+address.port;
const executable=process.env.ORDIVON_WEB_CHROMIUM_EXECUTABLE;
const browser=await chromium.launch({headless:true,...(executable?{executablePath:executable}:{}),ignoreDefaultArgs:["--disable-back-forward-cache"]});
try{
  const p="principal:operator",other="principal:other";
  store.ensurePrincipal(p,"operator","Operator <tag>",now());
  store.ensurePrincipal(other,"other","Other",now());
  const make=(grantId:string,principalId:string,expires:number,quota:number)=>store.createAgentGrant({
    grantId,principalId,agentId:"agent:<script>alert(1)</script>",audience:origin,
    allowedActions:["canary.note.create"],resourcePrefixes:["/canary/notes"],expiresAtEpochSeconds:expires,
    maxRiskClass:"R2",stepUpAtOrAbove:"R4",remainingEffects:quota
  },now());
  const revoked=make("grant:revoked",p,now()+30,3);
  store.revokeAgentGrant(p,revoked.grantId,revoked.grantDigest,now());
  make("grant:current",p,now()+30,3);
  make("grant:expired",p,now()-1,3);
  make("grant:exhausted",p,now()+30,0);
  make("grant:foreign",other,now()+30,3);
  const session=store.createSession(p,now(),300,3600,null);
  const referenceResponse=await reference.inject({url:"/operator/grants",headers:{cookie:"__Host-session="+session.token}});
  assert.equal(referenceResponse.statusCode,200);
  const shell=await app.inject({url:"/operator/grants",headers:{cookie:"__Host-session="+session.token}});
  assert.equal(shell.statusCode,200);
  assert.equal(shell.headers["cache-control"],"no-store");
  assert.match(String(shell.headers["content-security-policy"]),/script-src 'self'/);
  assert.doesNotMatch(shell.body,/grant:current|Operator &lt;tag&gt;|grant:foreign/);
  assert.equal((await app.inject({url:"/operator/grants"})).statusCode,401);
  const context=await browser.newContext();
  await context.addCookies([{name:"__Host-session",value:session.token,url:"https://localhost/",secure:true,httpOnly:true,sameSite:"Lax"}]);
  // Fixture-only instrumentation: record completion of real response decoding.
  // Do not rely on networkidle, which may include intercepted resources.
  await context.addInitScript(()=>{
    const original=Response.prototype.json;
    Object.assign(window,{operatorDecoded:0});
    Response.prototype.json=async function(){
      const data=await original.call(this);
      if(data&&typeof data==="object"&&Array.isArray(data.grants)){
        (window as unknown as {operatorDecoded:number}).operatorDecoded++;
      }
      return data;
    };
  });
  const page=await context.newPage();
  const errors:string[]=[];page.on("pageerror",e=>errors.push(e.message));
  page.on("console",msg=>{if(msg.type()==="error"&&msg.text().includes("Content Security Policy"))errors.push(msg.text())});
  await page.goto(origin+"/operator/grants?principalId="+encodeURIComponent(other));
  await page.locator('[data-status="observed"]').waitFor();
  const comparison=await page.evaluate(html=>{
    const normalize=(doc:Document)=>[...doc.querySelectorAll("tbody tr")].map(row=>Array.from(row.children).map(cell=>cell.textContent)).sort((a,b)=>String(a[0]).localeCompare(String(b[0])));
    const ref=new DOMParser().parseFromString(html,"text/html");
    return {expected:normalize(ref),actual:normalize(document),name:document.querySelector("strong")?.textContent,
      probe:"probe" in window,headers:[...document.querySelectorAll("thead th")].map(x=>x.textContent)};
  },referenceResponse.body);
  assert.deepEqual(comparison.actual,comparison.expected);
  assert.equal(comparison.actual.length,4);assert.equal(comparison.headers.length,8);
  assert.equal(comparison.name,"Operator <tag>");assert.equal(comparison.probe,false);
  assert.equal(await page.locator("tbody script").count(),0);
  assert.equal(await page.getByText("grant:foreign",{exact:true}).count(),0);
  const filter=page.getByRole("combobox",{name:"Grant availability"});
  await filter.selectOption("candidate");
  await page.waitForFunction(()=>document.querySelectorAll("tbody tr").length===1);
  assert.equal(await page.getByText("grant:current",{exact:true}).count(),1);
  assert.equal(store.getAgentGrant("grant:current").remainingEffects,3);
  await filter.selectOption("all");
  await page.waitForFunction(()=>document.querySelectorAll("tbody tr").length===4);
  let held!:()=>void;const captured=new Promise<void>(r=>held=r);
  let release!:()=>void;const gate=new Promise<void>(r=>release=r);
  let requests=0;
  await page.route("**/api/security/agents/grants",async route=>{
    if(++requests!==1){await route.continue();return}
    const prior=await route.fetch();assert.equal(prior.status(),200);held();await gate;await route.fulfill({response:prior});
  });
  await page.getByRole("button",{name:"Refresh owner observation"}).click();
  await captured;
  assert.equal(await page.locator("tbody tr").count(),0);
  assert.equal(await page.locator("strong").textContent(),"");
  store.revokeSession(p,session.session.sessionId,now());
  await page.getByRole("button",{name:"Refresh owner observation"}).click();
  await page.locator('[data-status="denied"]').waitFor();
  const decoded=await page.evaluate(()=>(window as unknown as {operatorDecoded:number}).operatorDecoded);
  const prior=page.waitForResponse(r=>r.url().endsWith("/api/security/agents/grants")&&r.status()===200);
  release();await (await prior).finished();
  await page.waitForFunction(n=>(window as unknown as {operatorDecoded:number}).operatorDecoded===n+1,decoded);
  await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>resolve())));
  assert.equal(await page.locator('[data-status="denied"]').count(),1);
  assert.equal(await page.locator("tbody tr").count(),0);
  await page.unroute("**/api/security/agents/grants");
  const next=store.createSession(other,now(),300,3600,null);
  await context.addCookies([{name:"__Host-session",value:next.token,url:"https://localhost/",secure:true,httpOnly:true,sameSite:"Lax"}]);
  await page.getByRole("button",{name:"Refresh owner observation"}).click();
  await page.locator('[data-status="observed"]').waitFor();
  assert.equal(await page.getByText("grant:foreign",{exact:true}).count(),1);
  assert.equal(await page.getByText("grant:current",{exact:true}).count(),0);
  await page.evaluate(()=>{const c=new BroadcastChannel("ordivon-web-observation-invalidation-v1");c.postMessage("session-changed");c.close()});
  await page.locator('[data-status="suspended"]').waitFor();
  assert.equal(await page.locator("tbody tr").count(),0);
  await page.getByRole("button",{name:"Refresh owner observation"}).click();
  await page.locator('[data-status="observed"]').waitFor();
  assert.equal(await page.locator("tbody tr").count(),1);
  // Corrupt only the projection, not the actual owner DB/authority.
  await page.route("**/api/security/agents/grants",async route=>{
    const response=await route.fetch();assert.equal(response.status(),200);
    const data=await response.json();data.grants[0].allowedActions=[null];
    await route.fulfill({response,json:data});
  });
  await page.getByRole("button",{name:"Refresh owner observation"}).click();
  await page.locator('[data-status="unavailable"]').waitFor();
  assert.equal(await page.locator("tbody tr").count(),0);
  assert.equal(await page.locator("strong").textContent(),"");
  await page.unroute("**/api/security/agents/grants");
  await page.getByRole("button",{name:"Refresh owner observation"}).click();
  await page.locator('[data-status="observed"]').waitFor();
  // Native lifecycle navigation: leave the actual product page, revoke its
  // session, then return with the same cookie. No stale private rows.
  await page.goto(origin+"/health");
  store.revokeSession(other,next.session.sessionId,now());
  const back=await page.goBack({waitUntil:"domcontentloaded"});
  if(back===null||back.status()===200)await page.locator('[data-status="denied"]').waitFor();
  else assert.equal(back.status(),401);
  assert.equal(await page.locator("tbody tr").count(),0);
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({actualRoute:"/operator/grants",referenceRows:4,referenceColumns:8,exactCellParity:true,foreignRows:0,displayNameParity:true,xssAsText:true,nativeFilter:true,quotaUnchanged:true,noProbeGlobal:true,staleAfterDenialRejected:true,identityChange:true,peerHintClears:true,malformedWireClears:true,nativeBackNavigationDenial:true,scope:"isolated actual product composition, seeded session, no production install"}));
  await context.close();
}finally{await browser.close();await app.close();await reference.close();store.close()}
