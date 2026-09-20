import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { createRequire } from 'node:module';
const packageRoot=process.env.ARTIFACT_NODE_PACKAGE_ROOT;
if(!packageRoot) throw new Error('ARTIFACT_NODE_PACKAGE_ROOT is required');
const require=createRequire(path.join(path.resolve(packageRoot),'package.json'));
const {chromium,firefox}=require('@playwright/test');
const input=process.argv[2];if(!input){console.error('usage: node verify_svg_static.mjs FILE.svg');process.exit(2)}
const bytes=fs.readFileSync(path.resolve(input));const b64=bytes.toString('base64');
async function probe(name,type){let browser;const executable=type.executablePath();try{browser=await type.launch({headless:true});const page=await browser.newPage();const r=await page.evaluate(async b64=>{const img=new Image();img.src='data:image/svg+xml;base64,'+b64;await img.decode();const w=img.naturalWidth,h=img.naturalHeight;const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');x.clearRect(0,0,w,h);x.drawImage(img,0,0,w,h);const d=x.getImageData(0,0,w,h).data;let hash=2166136261>>>0,nonzero=0;for(let i=0;i<d.length;i++){hash^=d[i];hash=Math.imul(hash,16777619)>>>0;if(i%4===3&&d[i])nonzero++;}return {naturalWidth:w,naturalHeight:h,pixelFNV32:hash.toString(16).padStart(8,'0'),nonTransparentPixels:nonzero}},b64);return{name,status:'PASS',version:browser.version(),executable,...r}}catch(e){return{name,status:'FAIL',executable,error:String(e?.message??e).slice(0,4000)}}finally{if(browser)await browser.close()}}
const c=await probe('Chromium',chromium),f=await probe('Firefox',firefox);console.log(JSON.stringify({schemaVersion:1,kind:'artifact-svg-browser-matrix',status:c.status==='PASS'&&f.status==='PASS'?'PASS':'FAIL',browsers:{chromium:c,firefox:f},intrinsicDimensionAgreement:c.status==='PASS'&&f.status==='PASS'&&c.naturalWidth===f.naturalWidth&&c.naturalHeight===f.naturalHeight,pixelChecksumAgreement:c.status==='PASS'&&f.status==='PASS'&&c.pixelFNV32===f.pixelFNV32,nonTransparentPixelCountAgreement:c.status==='PASS'&&f.status==='PASS'&&c.nonTransparentPixels===f.nonTransparentPixels,boundary:'Browser image decode/render facts only; pixel checksum equality is observed, not required.'},null,2));
