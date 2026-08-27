import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { chromium } from "playwright";
import { resolveChromiumExecutable } from "./browser-equipment.ts";
import { createGameServer } from "../src/server.ts";

async function listen(game: ReturnType<typeof createGameServer>): Promise<string> {
  await new Promise<void>((resolve) => game.server.listen(0, "127.0.0.1", resolve));
  const address = game.server.address();
  if (!address || typeof address === "string") throw new Error("server has no TCP address");
  return `http://127.0.0.1:${address.port}`;
}
process.env.TMPDIR=process.env.ORDIVON_BROWSER_TMPDIR??"/tmp";
const directory=mkdtempSync(join(tmpdir(),"ordivon-pre-g0-"));
const game=createGameServer({researchSurfaces:true,dbPath:join(directory,"game.sqlite3"),v3DbPath:join(directory,"v3.sqlite3")});
const base=await listen(game);
const executablePath=resolveChromiumExecutable(chromium.executablePath());
if(!executablePath)throw new Error("No Chromium executable available");
const browser=await chromium.launch({headless:true,executablePath});
const page=await browser.newPage({viewport:{width:1280,height:960}});
const browserErrors:string[]=[];
page.on("pageerror",e=>browserErrors.push(`pageerror:${e.message}`));
page.on("console",m=>{if(m.type()==="error")browserErrors.push(`console:${m.text()}`)});
try{
  await page.goto(`${base}/pre-g0`,{waitUntil:"networkidle"});
  await page.getByRole("heading",{name:"Playable Proofs"}).waitFor();
  assert.match(await page.locator("body").textContent()??"",/AUTOMATION ≠ C0\/C1/);
  assert.equal(await page.locator('[data-packet]').count(),3);
  // A: keyboard input must move the avatar and manual reset must remain usable.
  const before=await page.evaluate(()=>{const c=document.querySelector<HTMLCanvasElement>('#traversal');return c?c.toDataURL():''});
  await page.keyboard.down('ArrowRight'); await page.waitForTimeout(300); await page.keyboard.up('ArrowRight');
  const after=await page.evaluate(()=>{const c=document.querySelector<HTMLCanvasElement>('#traversal');return c?c.toDataURL():''});
  assert.notEqual(after,before,"PGP-A canvas should react to player input");
  await page.locator('[data-reset-a]').click();
  const advanceTraversalRoom=async(room:number,minJumpX:number)=>{
    for(let decision=0;decision<16;decision+=1){
      const handle=await page.waitForFunction(({room,minJumpX}:{room:number;minJumpX:number})=>{
        const raw=localStorage.getItem('ordivon-pre-g0-c0-v1');
        const completed=raw?JSON.parse(raw).sessions.filter((item:{kind?:string})=>item.kind==='room-complete').length:0;
        if(completed>=room)return 'done';
        const canvas=document.querySelector<HTMLCanvasElement>('#traversal');
        if(canvas?.dataset.room===String(room)&&canvas.dataset.ground==='true'&&Number(canvas.dataset.playerX)>=minJumpX)return 'jump';
        return false;
      },{room,minJumpX},{timeout:9000});
      const action=await handle.jsonValue();
      await handle.dispose();
      if(action==='done')return;
      await page.keyboard.down('Space');
      await page.waitForTimeout(50);
      await page.keyboard.up('Space');
    }
    throw new Error(`PGP-A room ${room} did not complete within bounded jump decisions`);
  };
  await page.keyboard.down('ArrowRight');
  await advanceTraversalRoom(1,215);
  await advanceTraversalRoom(2,105);
  await advanceTraversalRoom(3,95);
  await page.keyboard.up('ArrowRight');
  const traversalEvidence=await page.evaluate(()=>JSON.parse(localStorage.getItem('ordivon-pre-g0-c0-v1')||'{"sessions":[]}').sessions.filter((item:{kind?:string})=>item.kind==='room-complete'));
  assert.ok(traversalEvidence.length>=3,"PGP-A should expose a mechanically completable three-room timing path");
  // D: answer is sealed until a determination; multi-clue causal commit path works.
  await page.locator('[data-packet="D"]').click();
  assert.equal(await page.locator('.outcome').count(),0);
  for(const i of [0,4,5])await page.locator(`[data-clue="${i}"]`).click();
  await page.locator('input[value="mara"]').check();
  await page.locator('#mechanism').fill('Badge timing plus remote terminal heartbeat defeats the local Archive alibi and the route is feasible.');
  await page.locator('[data-submit-d]').click();
  assert.match(await page.locator('.outcome').textContent()??"",/Mara sabotaged the relay/);
  // I: composition, transform, two saved revisions and local evidence persistence work.
  await page.locator('[data-packet="I"]').click();
  await page.locator('[data-add="circle"]').click();
  await page.locator('[data-add="bar"]').click();
  await page.locator('[data-save]').click();
  await page.locator('[data-mod="right"]').click();
  await page.locator('[data-mod="rotate"]').click();
  await page.locator('[data-save]').click();
  assert.equal(await page.locator('.revision').count(),2);
  const stored=await page.evaluate(()=>localStorage.getItem('ordivon-pre-g0-c0-v1'));
  assert.ok(stored && JSON.parse(stored).sessions.length>0);
  assert.equal(browserErrors.length,0,browserErrors.join("\n"));
  console.log(JSON.stringify({schemaVersion:1,kind:"ordivon.game.pre-g0-automated-apparatus-evidence",standing:"APPARATUS_ONLY_C0_UNOBSERVED_C1_UNOBSERVED",packets:{A:{inputReactive:true,manualReset:true,threeRoomPathCompletable:true},D:{answerSealedUntilCommit:true,multiClueDetermination:true},I:{composeTransformSaveCompare:true}},runtimeAgentProfile:"none",browserErrors},null,2));
}finally{await browser.close();await game.close();rmSync(directory,{recursive:true,force:true})}
