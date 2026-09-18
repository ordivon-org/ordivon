import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import {chromium} from 'playwright';
import {resolveChromiumExecutable} from '../../../../tools/browser-equipment.ts';

const here=dirname(fileURLToPath(import.meta.url));
const root=resolve(here,'..');
const web=resolve(root,'web');
const pc01Design=resolve(root,'../pc01-causal-works-f0/design.json');
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
    if(u.pathname==='/experiments/product-composition-r1/pc01-causal-works-f0/design.json'){
      const body=await readFile(pc01Design);
      res.writeHead(200,{'content-type':'application/json; charset=utf-8','content-length':body.length,'cache-control':'no-store'});
      res.end(body);return;
    }
    const rel=u.pathname==='/'?'index.html':u.pathname.slice(1);
    const path=resolve(web,rel);
    if(!path.startsWith(web))throw new Error('invalid path');
    const body=await readFile(path);
    const ext=path.slice(path.lastIndexOf('.'));
    res.writeHead(200,{'content-type':types[ext]??'application/octet-stream','content-length':body.length,'cache-control':'no-store'});
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
const page=await browser.newPage({viewport:{width:1440,height:1000}});
const browserErrors:string[]=[];
page.on('pageerror',e=>browserErrors.push(`pageerror:${e.message}`));
page.on('console',m=>{if(m.type()==='error')browserErrors.push(`console:${m.text()}`)});

try{
  await page.goto(base,{waitUntil:'networkidle'});
  await page.getByRole('heading',{name:'Causal Lag Lab'}).waitFor();
  await page.waitForFunction(()=>Boolean((window as any).__PC01_E03_PLAYABLE__));

  const initial=await page.locator('body').textContent()??'';
  assert.match(initial,/CURRENT SIGNAL/i);
  assert.match(initial,/EXECUTION FORECAST/i);
  assert.match(initial,/1 CONTEXT SHIFT/i);
  assert.match(initial,/fault persists through the command delay/i);
  assert.doesNotMatch(initial,/optimal|best policy|expected value|route scan\s*→|choose process|choose route|choose source/i,'initial UI must not disclose the solution policy');
  assert.equal(await page.locator('body').getAttribute('data-cause-revealed'),'false');

  await page.evaluate(()=>((window as any).__PC01_E03_PLAYABLE__.resetForAcceptance('route-shift',{sourceCause:'process'})));
  await page.locator('[data-inspect="route"]').click();
  assert.equal((await page.locator('[data-inspection]').textContent()??'').trim(),'ROUTE SCAN → OK');
  assert.equal(await page.locator('body').getAttribute('data-cause-revealed'),'false');

  await page.locator('[data-arch="process"]').click();
  await page.locator('[data-commit]').click();
  assert.equal(await page.locator('body').getAttribute('data-cause-revealed'),'true');
  const aftermath=(await page.locator('[data-aftermath]').textContent()??'');
  assert.match(aftermath,/CURRENT CAUSE · PROCESS/);
  assert.match(aftermath,/EXECUTION CAUSE · PROCESS/);
  assert.match(aftermath,/NET · 86/);

  const resolved=await page.evaluate(()=>((window as any).__PC01_E03_PLAYABLE__.snapshot()));
  assert.equal(resolved.phase,'resolved');
  assert.equal(resolved.resolution.sourceCause,'process');
  assert.equal(resolved.resolution.executionCause,'process');
  assert.equal(resolved.resolution.executionContextId,'cycle-2-objective-shift');
  assert.equal(resolved.resolution.net,86);

  await page.selectOption('[data-scenario]','source-rule');
  const scenarioText=(await page.locator('[data-forecast-card]').textContent()??'');
  assert.match(scenarioText,/cycle-3-rule-revaluation/i);
  await page.evaluate(()=>((window as any).__PC01_E03_PLAYABLE__.resetForAcceptance('source-rule',{sourceCause:'source'})));
  await page.locator('[data-inspect="route"]').click();
  await page.locator('[data-arch="source"]').click();
  await page.locator('[data-commit]').click();
  const sourceRule=await page.evaluate(()=>((window as any).__PC01_E03_PLAYABLE__.snapshot()));
  assert.equal(sourceRule.resolution.sourceCause,'source');
  assert.equal(sourceRule.resolution.executionCause,'source');
  assert.equal(sourceRule.resolution.net,94);

  const witness=await page.evaluate(()=>((window as any).__PC01_E03_PLAYABLE__.runWitnesses()));
  assert.equal(witness.pass,true);
  assert.equal(witness.routeShift.forecastChangesPolicy,true);
  assert.equal(witness.routeShift.persistenceRequiredForDiagnosisValue,true);
  assert.equal(witness.sourceRule.forecastChangesPolicy,true);
  assert.equal(witness.sourceRule.persistenceRequiredForDiagnosisValue,true);
  assert.equal(witness.productSelected,false);
  assert.equal(witness.g0Entered,false);
  assert.equal(witness.humanOutcomeEstablished,false);
  assert.equal(browserErrors.length,0,browserErrors.join('\n'));

  console.log(JSON.stringify({
    scenario:'pc01-e03-playable-r1',
    routeShiftNet:resolved.resolution.net,
    sourceRuleNet:sourceRule.resolution.net,
    witnessPass:witness.pass,
    browserErrors,
  },null,2));
}finally{
  await browser.close();
  await new Promise<void>(r=>server.close(()=>r()));
}
