import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {dirname,resolve,extname} from 'node:path';
import {chromium} from 'playwright';
import {resolveChromiumExecutable} from '../../../../tools/browser-equipment.ts';

const here=dirname(fileURLToPath(import.meta.url));
const repo=resolve(here,'../../../..');
const pagePath='/experiments/product-composition-r1/causal-lag-pressure-r5/web/';
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
const page=await browser.newPage({viewport:{width:1500,height:1100}});
const browserErrors:string[]=[];
page.on('pageerror',e=>browserErrors.push(`pageerror:${e.message}`));
page.on('console',m=>{if(m.type()==='error')browserErrors.push(`console:${m.text()}`)});

async function reset(options:any){
  await page.evaluate((o)=>((window as any).__CAUSAL_LAG_R5__.resetForAcceptance(o)),options);
}
async function playArchitecture(architecture:string,rounds:number){
  for(let i=0;i<rounds;i++){
    await page.locator(`[data-arch="${architecture}"]`).click();
    await page.locator('[data-commit]').click();
    const state=await page.evaluate(()=>((window as any).__CAUSAL_LAG_R5__.snapshot()));
    if(i<rounds-1&&state.sessionStatus==='ACTIVE')await page.locator('[data-next]').click();
  }
}

try{
  await page.goto(base+pagePath,{waitUntil:'networkidle'});
  await page.getByRole('heading',{name:'Causal Lag · Pressure Run'}).waitFor();
  await page.waitForFunction(()=>Boolean((window as any).__CAUSAL_LAG_R5__));

  await reset({
    regime:'STABLE',
    initialCause:'route',
    transitionScript:Array(10).fill('route'),
  });
  assert.match((await page.locator('[data-round]').textContent()??''),/ROUND 1 \/ 10/i);
  assert.match((await page.locator('[data-pressure]').textContent()??''),/SCAN CHEAP/i);
  assert.match((await page.locator('[data-scan-cost]').textContent()??''),/3/);
  let snap=await page.evaluate(()=>((window as any).__CAUSAL_LAG_R5__.snapshot()));
  assert.deepEqual(snap.current.costPressure,{profileId:'SCAN_CHEAP',diagnosticCost:3,switchCost:8});
  assert.doesNotMatch(JSON.stringify(snap).toLowerCase(),/stable|volatile|persistence|executioncause/);

  await playArchitecture('route',2);
  await page.locator('[data-next]').click();
  assert.match((await page.locator('[data-round]').textContent()??''),/ROUND 3 \/ 10/i);
  assert.match((await page.locator('[data-pressure]').textContent()??''),/BASELINE/i);
  assert.match((await page.locator('[data-scan-cost]').textContent()??''),/6/);

  await page.locator('[data-arch="route"]').click();
  await page.locator('[data-commit]').click();
  await page.locator('[data-next]').click();
  await page.locator('[data-arch="route"]').click();
  await page.locator('[data-commit]').click();
  await page.locator('[data-next]').click();
  assert.match((await page.locator('[data-round]').textContent()??''),/ROUND 5 \/ 10/i);
  assert.match((await page.locator('[data-pressure]').textContent()??''),/SCAN EXPENSIVE/i);
  assert.match((await page.locator('[data-scan-cost]').textContent()??''),/12/);

  await reset({
    regime:'STABLE',
    initialCause:'route',
    transitionScript:Array(10).fill('route'),
  });
  await playArchitecture('route',10);
  const success=await page.evaluate(()=>((window as any).__CAUSAL_LAG_R5__.snapshot()));
  assert.equal(success.sessionStatus,'SUCCESS');
  assert.equal(success.totalNet,1000);
  assert.equal(success.history.length,10);
  assert.match((await page.locator('[data-outcome]').textContent()??''),/CONTRACT SECURED/i);

  await reset({
    regime:'STABLE',
    initialCause:'route',
    transitionScript:Array(10).fill('route'),
  });
  await playArchitecture('source',6);
  const failure=await page.evaluate(()=>((window as any).__CAUSAL_LAG_R5__.snapshot()));
  assert.equal(failure.sessionStatus,'FAILURE');
  assert.equal(failure.totalNet,374);
  assert.equal(failure.contract.maxRecoverableTotal,774);
  assert.match((await page.locator('[data-outcome]').textContent()??''),/CONTRACT LOST/i);

  assert.equal(browserErrors.length,0,browserErrors.join('\n'));
  console.log(JSON.stringify({
    scenario:'causal-lag-pressure-r5',
    pressureSequence:['SCAN_CHEAP','SCAN_CHEAP','BASELINE','BASELINE','SCAN_EXPENSIVE','SCAN_EXPENSIVE','SCAN_EXPENSIVE','BASELINE','SCAN_CHEAP','SCAN_CHEAP'],
    successTotal:success.totalNet,
    failureTotal:failure.totalNet,
    failureMaxRecoverable:failure.contract.maxRecoverableTotal,
    browserErrors,
  },null,2));
}finally{
  await browser.close();
  await new Promise<void>(r=>server.close(()=>r()));
}
