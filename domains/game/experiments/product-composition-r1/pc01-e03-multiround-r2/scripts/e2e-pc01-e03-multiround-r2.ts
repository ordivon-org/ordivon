import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {dirname,resolve,extname} from 'node:path';
import {chromium} from 'playwright';
import {resolveChromiumExecutable} from '../../../../tools/browser-equipment.ts';

const here=dirname(fileURLToPath(import.meta.url));
const repo=resolve(here,'../../../..');
const pagePath='/experiments/product-composition-r1/pc01-e03-multiround-r2/web/';
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
const page=await browser.newPage({viewport:{width:1480,height:1050}});
const browserErrors:string[]=[];
page.on('pageerror',e=>browserErrors.push(`pageerror:${e.message}`));
page.on('console',m=>{if(m.type()==='error')browserErrors.push(`console:${m.text()}`)});

async function reset(script:any[]){
  await page.evaluate((transitions)=>((window as any).__PC01_E03_R2__.resetForAcceptance({regime:'STABLE',transitions})),script);
}

try{
  await page.goto(base+pagePath,{waitUntil:'networkidle'});
  await page.getByRole('heading',{name:'Causal Lag Lab · Memory Run'}).waitFor();
  await page.waitForFunction(()=>Boolean((window as any).__PC01_E03_R2__));

  const initial=(await page.locator('body').textContent()??'');
  assert.match(initial,/SYSTEM MEMORY/i);
  assert.match(initial,/ROUND 1 \/ 4/i);
  assert.match(initial,/CURRENT SIGNAL/i);
  assert.match(initial,/EXECUTION FORECAST/i);
  assert.doesNotMatch(initial,/STABLE|VOLATILE|posterior|probability|persistence estimate|optimal|expected value/i);

  await reset([
    {scenarioId:'route-shift',sourceCause:'process',executionCause:'process'},
    {scenarioId:'route-shift',sourceCause:'source',executionCause:'source'},
  ]);
  await page.locator('[data-inspect="route"]').click();
  await page.locator('[data-arch="process"]').click();
  await page.locator('[data-commit]').click();
  const history1=(await page.locator('[data-history]').textContent()??'');
  assert.match(history1,/PROCESS\s*→\s*PROCESS/i);
  assert.match(history1,/PERSISTED/i);
  assert.doesNotMatch(history1,/0\.\d+|STABLE|posterior/i);
  await page.locator('[data-next-round]').click();

  const stableCurrent=await page.evaluate(()=>((window as any).__PC01_E03_R2__.snapshot()));
  assert.equal(stableCurrent.current.scenarioId,'route-shift');
  assert.equal(stableCurrent.history.length,1);

  await page.evaluate(()=>((window as any).__PC01_E03_R2__.resetForAcceptance({
    regime:'VOLATILE',
    transitions:[
      {scenarioId:'route-shift',sourceCause:'process',executionCause:'route'},
      {scenarioId:'route-shift',sourceCause:'source',executionCause:'source'},
    ],
  })));
  await page.locator('[data-arch="process"]').click();
  await page.locator('[data-commit]').click();
  const history2=(await page.locator('[data-history]').textContent()??'');
  assert.match(history2,/PROCESS\s*→\s*ROUTE/i);
  assert.match(history2,/CHANGED/i);
  await page.locator('[data-next-round]').click();

  const volatileCurrent=await page.evaluate(()=>((window as any).__PC01_E03_R2__.snapshot()));
  assert.deepEqual(stableCurrent.current.currentContext,volatileCurrent.current.currentContext);
  assert.deepEqual(stableCurrent.current.executionForecast,volatileCurrent.current.executionForecast);
  assert.notDeepEqual(stableCurrent.history,volatileCurrent.history);

  const body=(await page.locator('body').textContent()??'');
  assert.doesNotMatch(body,/STABLE|VOLATILE|posterior|probability|persistence estimate|optimal|expected value/i);
  assert.equal(browserErrors.length,0,browserErrors.join('\n'));

  console.log(JSON.stringify({
    scenario:'pc01-e03-multiround-r2',
    stableHistory:stableCurrent.history,
    volatileHistory:volatileCurrent.history,
    sameCurrentDecision:
      JSON.stringify(stableCurrent.current.currentContext)===JSON.stringify(volatileCurrent.current.currentContext)&&
      JSON.stringify(stableCurrent.current.executionForecast)===JSON.stringify(volatileCurrent.current.executionForecast),
    browserErrors,
  },null,2));
}finally{
  await browser.close();
  await new Promise<void>(r=>server.close(()=>r()));
}
