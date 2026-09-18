import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {dirname,resolve,extname} from 'node:path';
import {chromium} from 'playwright';
import {resolveChromiumExecutable} from '../../../../tools/browser-equipment.ts';

const here=dirname(fileURLToPath(import.meta.url));
const repo=resolve(here,'../../../..');
const pagePath='/experiments/product-composition-r1/causal-lag-session-r3/web/';
const types:Record<string,string>={
  '.html':'text/html; charset=utf-8',
  '.css':'text/css; charset=utf-8',
  '.js':'text/javascript; charset=utf-8',
  '.json':'application/json; charset=utf-8',
};
const server=createServer(async(req,res)=>{
  try{
    const u=new URL(req.url??'/', 'http://localhost');
    if(u.pathname==='/favicon.ico'){res.writeHead(204);res.end();return}
    const rel=u.pathname.endsWith('/')?u.pathname.slice(1)+'index.html':u.pathname.slice(1);
    const path=resolve(repo,rel);
    if(!path.startsWith(repo))throw new Error('invalid path');
    const body=await readFile(path);
    res.writeHead(200,{'content-type':types[extname(path)]??'application/octet-stream','content-length':body.length,'cache-control':'no-store'});
    res.end(body);
  }catch{
    res.writeHead(404);res.end('not found');
  }
});
await new Promise<void>(r=>server.listen(0,'127.0.0.1',r));
const addr=server.address();if(!addr||typeof addr==='string')throw new Error('no address');
const base=`http://127.0.0.1:${addr.port}`;
const executablePath=resolveChromiumExecutable(chromium.executablePath());
if(!executablePath)throw new Error('No Chromium executable available');
const browser=await chromium.launch({headless:true,executablePath});
const page=await browser.newPage({viewport:{width:1500,height:1050}});
const browserErrors:string[]=[];
page.on('pageerror',e=>browserErrors.push(`pageerror:${e.message}`));
page.on('console',m=>{if(m.type()==='error')browserErrors.push(`console:${m.text()}`)});

async function reset(options:any){
  await page.evaluate((o)=>((window as any).__CAUSAL_LAG_R3__.resetForAcceptance(o)),options);
}

try{
  await page.goto(base+pagePath,{waitUntil:'networkidle'});
  await page.getByRole('heading',{name:'Causal Lag · Stateful Run'}).waitFor();
  await page.waitForFunction(()=>Boolean((window as any).__CAUSAL_LAG_R3__));

  assert.equal(await page.locator('[data-start]').isVisible(),true);
  assert.match((await page.locator('[data-contract]').textContent()??''),/TARGET · 320/i);
  await page.locator('[data-start]').click();
  assert.match((await page.locator('[data-round]').textContent()??''),/ROUND 1 \/ 4/i);
  assert.match((await page.locator('[data-built]').textContent()??''),/BUILT · ROUTE/i);

  await reset({
    regime:'STABLE',
    initialCause:'process',
    transitionScript:['process','process','process','process'],
  });
  await page.locator('[data-arch="process"]').click();
  await page.locator('[data-commit]').click();
  assert.match((await page.locator('[data-aftermath]').textContent()??''),/NET · 92/i);
  await page.locator('[data-next]').click();
  assert.match((await page.locator('[data-built]').textContent()??''),/BUILT · PROCESS/i);
  const carry=await page.evaluate(()=>((window as any).__CAUSAL_LAG_R3__.snapshot()));
  assert.equal(carry.current.previousArchitecture,'process');
  assert.equal(carry.current.currentContext.id,'cycle-2-objective-shift');

  await reset({
    regime:'STABLE',
    initialCause:'route',
    transitionScript:['route','route','route','route'],
  });
  for(let i=0;i<4;i++){
    await page.locator('[data-arch="route"]').click();
    await page.locator('[data-commit]').click();
    if(i<3)await page.locator('[data-next]').click();
  }
  assert.match((await page.locator('[data-outcome]').textContent()??''),/CONTRACT SECURED/i);
  const success=await page.evaluate(()=>((window as any).__CAUSAL_LAG_R3__.snapshot()));
  assert.equal(success.sessionStatus,'SUCCESS');
  assert.equal(success.totalNet,400);

  await reset({
    regime:'STABLE',
    initialCause:'route',
    transitionScript:['route','route','route','route'],
  });
  for(let i=0;i<2;i++){
    await page.locator('[data-arch="source"]').click();
    await page.locator('[data-commit]').click();
    if(i<1)await page.locator('[data-next]').click();
  }
  assert.match((await page.locator('[data-outcome]').textContent()??''),/CONTRACT LOST/i);
  const failure=await page.evaluate(()=>((window as any).__CAUSAL_LAG_R3__.snapshot()));
  assert.equal(failure.sessionStatus,'FAILURE');
  assert.equal(failure.totalNet,115);
  assert.equal(failure.contract.maxRecoverableTotal,315);

  await reset({
    regime:'VOLATILE',
    initialCause:'process',
    transitionScript:['route','source','process','route'],
  });
  const before=await page.evaluate(()=>((window as any).__CAUSAL_LAG_R3__.snapshot()));
  const beforeText=JSON.stringify(before).toLowerCase();
  assert.doesNotMatch(beforeText,/stable|volatile|executioncause/);
  assert.equal(before.sessionStatus,'ACTIVE');
  assert.equal(browserErrors.length,0,browserErrors.join('\n'));

  console.log(JSON.stringify({
    scenario:'causal-lag-session-r3',
    successTotal:success.totalNet,
    failureTotal:failure.totalNet,
    failureMaxRecoverable:failure.contract.maxRecoverableTotal,
    carryoverArchitecture:carry.current.previousArchitecture,
    browserErrors,
  },null,2));
}finally{
  await browser.close();
  await new Promise<void>(r=>server.close(()=>r()));
}
