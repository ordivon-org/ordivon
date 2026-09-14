import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import {chromium} from 'playwright';
import {resolveChromiumExecutable} from '../../../tools/browser-equipment.ts';

const here=dirname(fileURLToPath(import.meta.url));
const web=resolve(here,'../web');
const sharedKernel=resolve(here,'../../pre-g0/web/pgp-a-kernel.js');
const types:Record<string,string>={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8'};
const server=createServer(async(req,res)=>{try{
  const u=new URL(req.url??'/', 'http://localhost');
  if(u.pathname==='/favicon.ico'){res.writeHead(204);res.end();return}
  if(u.pathname==='/pre-g0/web/pgp-a-kernel.js'){
    const body=await readFile(sharedKernel);
    res.writeHead(200,{'content-type':'text/javascript; charset=utf-8','content-length':body.length,'cache-control':'no-store'});res.end(body);return;
  }
  const rel=u.pathname==='/'?'index.html':u.pathname.slice(1);
  const path=resolve(web,rel);if(!path.startsWith(web))throw new Error('invalid path');
  const body=await readFile(path);const ext=path.slice(path.lastIndexOf('.'));
  res.writeHead(200,{'content-type':types[ext]??'application/octet-stream','content-length':body.length,'cache-control':'no-store'});res.end(body);
}catch{res.writeHead(404);res.end('not found')}});
await new Promise<void>(r=>server.listen(0,'127.0.0.1',r));
const addr=server.address();if(!addr||typeof addr==='string')throw new Error('no address');
const base=`http://127.0.0.1:${addr.port}`;
const executablePath=resolveChromiumExecutable(chromium.executablePath());if(!executablePath)throw new Error('No Chromium executable available');
const browser=await chromium.launch({headless:true,executablePath});
const page=await browser.newPage({viewport:{width:1280,height:900}});
const browserErrors:string[]=[];page.on('pageerror',e=>browserErrors.push(`pageerror:${e.message}`));page.on('console',m=>{if(m.type()==='error')browserErrors.push(`console:${m.text()}`)});
try{
  await page.goto(base,{waitUntil:'networkidle'});
  await page.getByRole('heading',{name:'Loop Cartographer'}).waitFor();
  assert.equal(await page.locator('canvas#world').count(),1);
  const initialText=await page.locator('body').textContent()??'';
  assert.doesNotMatch(initialText,/jump (at|near) the .*edge|optimal route|fast route is shorter|preserve.*horizontal|late-edge-jump/i,'initial UI must not disclose the exact rule or optimal route');

  const before=Number(await page.locator('#world').getAttribute('data-player-x'));
  await page.keyboard.down('ArrowRight');await page.waitForTimeout(250);await page.keyboard.up('ArrowRight');
  const after=Number(await page.locator('#world').getAttribute('data-player-x'));assert.ok(after>before+2,'interactive right input must move player');
  const worldBefore=await page.locator('#world').getAttribute('data-world-invariant');
  await page.locator('[data-reset]').click();
  const worldAfter=await page.locator('#world').getAttribute('data-world-invariant');
  assert.equal(worldAfter,worldBefore,'reset must preserve exact World/rule serialization');

  const result=await page.evaluate(()=>((window as any).__PC03_F0__.runWitnesses()));
  assert.equal(result.stableRule.id,'late-edge-jump-v1');
  assert.deepEqual(result.stableRule.instances,['gap-a-out/back','gap-b-out/back']);
  assert.equal(result.stableRule.authoritativeKnowledgeState,false);
  assert.equal(result.uninformed.complete,true);
  assert.equal(result.uninformed.route,'safe');
  assert.equal(result.uninformed.turnKind,'safe');
  assert.equal(result.uninformed.failures,0);
  assert.equal(result.insensitive.complete,false);
  assert.ok(result.insensitive.routeEvents.includes('fast'),'timing-insensitive informed policy must enter demanding route before failing');
  assert.ok(result.insensitive.failures>=1,'timing-insensitive informed policy must remain capable of failure');
  assert.equal(result.aware.complete,true);
  assert.equal(result.aware.route,'fast');
  assert.equal(result.aware.turnKind,'fast');
  assert.equal(result.aware.failures,0);
  assert.ok(result.aware.ruleUses>=4,'same reusable timing relation must matter at both gaps outbound and return');
  assert.ok(result.aware.frames<result.uninformed.frames,'demanding route must be mechanically shorter than safe baseline');
  assert.deepEqual(result.aware.turns,['fast'],'demanding completion must include a physical far turn, not terminal reset');
  assert.ok(result.aware.events.some((e:any)=>e.kind==='loop-complete'&&e.route==='fast'),'fast route must physically revisit hub and complete the loop');
  assert.equal(result.uninformed.worldInvariant,result.insensitive.worldInvariant);
  assert.equal(result.uninformed.worldInvariant,result.aware.worldInvariant,'matched policies must run against identical World/rule serialization');
  assert.equal(result.mechanismLibraryModified,false);
  assert.equal(result.runtimeAgentProfile,'none');
  assert.equal(browserErrors.length,0,browserErrors.join('\n'));

  const core=await readFile(resolve(web,'core.js'),'utf8');
  const app=await readFile(resolve(web,'app.js'),'utf8');
  const kernel=await readFile(sharedKernel,'utf8');
  assert.doesNotMatch(`${core}\n${app}`,/knowledgeUnlocked|questFlag|inventoryKey|hasKey|routeOpen|railCarry|railLaunch|-10\.8|7\.4|Math\.min\(1\.8|Math\.max\(-1\.8/,'forbidden knowledge authority or movement-law mutation present');
  for(const literal of ['acceleration: 0.55','damping: 0.82','maxVx: 5','jumpVy: -9.5','gravity: 0.48'])assert.match(kernel,new RegExp(literal.replace('.','\\.')));
  assert.match(core,/phase: 'outbound'/);
  assert.match(core,/s\.phase = 'return'/);
  assert.match(core,/s\.x <= WORLD\.hubReturnX/);
  console.log(JSON.stringify(result,null,2));
}finally{await browser.close();await new Promise<void>(r=>server.close(()=>r()))}
