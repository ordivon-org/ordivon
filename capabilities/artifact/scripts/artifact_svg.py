#!/usr/bin/env python3
"""Bounded static-safe SVG verifier using mature XML, SVG and browser implementations."""
from __future__ import annotations
import argparse,hashlib,json,math,os,re,subprocess,tempfile,xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
XMLLINT=Path(os.environ.get('ARTIFACT_XMLLINT','/usr/bin/xmllint'));RSVG=Path(os.environ.get('ARTIFACT_RSVG_CONVERT','/usr/bin/rsvg-convert'));NODE=Path(os.environ.get('ARTIFACT_NODE','/usr/bin/node'));BROWSER_PROBE=ROOT/'artifact-delivery/node/verify_svg_static.mjs';NODE_PACKAGE_ROOT=Path(os.environ.get('ARTIFACT_NODE_PACKAGE_ROOT','/opt/ordivon/external/artifact-toolchain/node/1.63.0'))
PLAYWRIGHT_BROWSERS_ROOT=Path(os.environ.get('ARTIFACT_PLAYWRIGHT_BROWSERS_PATH','/opt/ordivon/external/artifact-toolchain/playwright-browsers/1.63.0'))
SVG_NS='http://www.w3.org/2000/svg';ALLOWED_ELEMENTS={'svg','g','defs','title','desc','path','rect','circle','ellipse','line','polyline','polygon'}
ALLOWED_ATTRS={'id','version','width','height','viewBox','transform','fill','fill-opacity','stroke','stroke-opacity','stroke-width','stroke-linecap','stroke-linejoin','opacity','x','y','x1','y1','x2','y2','rx','ry','cx','cy','r','d','points'}
def run(a,**kw):return subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=kw.get('timeout',120),env=kw.get('env'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fact(p):return {'path':str(p.resolve()),'name':p.name,'size':p.stat().st_size,'sha256':sha(p)}
def number(v):
 try:x=float(v);return x if math.isfinite(x) else None
 except:return None
def verify_svg(path:Path,evidence_dir:Path|None=None)->dict[str,Any]:
 if not path.is_file():return {'schemaVersion':1,'kind':'artifact-svg-verification','profileId':'still-image-svg-static-r1','status':'FAIL','failures':['input is not a regular file']}
 ev=evidence_dir or Path(tempfile.mkdtemp(prefix='artifact-svg-evidence-'));ev.mkdir(parents=True,exist_ok=True);failures=[];observations=[];res={'schemaVersion':1,'kind':'artifact-svg-verification','profileId':'still-image-svg-static-r1','status':'FAIL','artifact':fact(path),'tools':{},'failures':failures,'observations':observations}
 for n,p in [('xmllint',XMLLINT),('rsvgConvert',RSVG),('node',NODE),('browserProbe',BROWSER_PROBE)]:
  if not p.is_file() or (n!='browserProbe' and not os.access(p,os.X_OK)):failures.append(f'required mature external capability unavailable: {n}')
  else:res['tools'][n]={'path':str(p.resolve()),'sha256':sha(p)}
 if not PLAYWRIGHT_BROWSERS_ROOT.is_dir():failures.append('pinned Artifact Playwright browser root unavailable')
 if not (NODE_PACKAGE_ROOT/'package.json').is_file():failures.append('pinned Artifact Node/Playwright package root unavailable')
 else:res['tools']['nodePackageRoot']={'path':str(NODE_PACKAGE_ROOT.resolve()),'packageJsonSha256':sha(NODE_PACKAGE_ROOT/'package.json')}
 if failures:return res
 raw=path.read_bytes();txt=raw.decode('utf-8','strict') if raw else ''
 xp=run([str(XMLLINT),'--nonet','--noout',str(path)]);(ev/'xmllint.stderr.txt').write_bytes(xp.stderr);xml_fail=[]
 if xp.returncode:xml_fail.append('xmllint rejected SVG XML')
 if re.search(r'<!DOCTYPE|<!ENTITY',txt,re.I):xml_fail.append('DOCTYPE/entity declarations are outside R1')
 failures+=xml_fail;res['xmlWellFormedness']={'status':'PASS' if not xml_fail else 'FAIL','failures':xml_fail,'evidenceSha256':sha(ev/'xmllint.stderr.txt')}
 if xml_fail:return res
 profile_fail=[]
 try:root=ET.fromstring(raw)
 except Exception as e:profile_fail.append(f'XML parser failed after xmllint: {e}');root=None
 tags={};attrs={}
 if root is not None:
  if root.tag!=f'{{{SVG_NS}}}svg':profile_fail.append('root is not SVG namespace svg')
  w=number(root.attrib.get('width'));h=number(root.attrib.get('height'));vb=root.attrib.get('viewBox','').strip().replace(',',' ').split();vbn=[number(x) for x in vb] if len(vb)==4 else []
  if w is None or w<=0 or h is None or h<=0:profile_fail.append('positive numeric width and height are required')
  if len(vbn)!=4 or any(x is None for x in vbn):profile_fail.append('numeric four-value viewBox is required')
  elif w is not None and h is not None and (abs(vbn[0])>1e-9 or abs(vbn[1])>1e-9 or abs(vbn[2]-w)>1e-6 or abs(vbn[3]-h)>1e-6):profile_fail.append('R1 requires viewBox exactly 0 0 width height')
  for e in root.iter():
   if not isinstance(e.tag,str):continue
   if e.tag.startswith('{'):
    ns,local=e.tag[1:].split('}',1)
   else:ns,local='',e.tag
   tags[local]=tags.get(local,0)+1
   if ns!=SVG_NS:profile_fail.append(f'non-SVG namespace element is outside R1: {local}')
   if local not in ALLOWED_ELEMENTS:profile_fail.append(f'element outside R1 static primitive set: {local}')
   for k,v in e.attrib.items():
    if k.startswith('{'):
     ans,localattr=k[1:].split('}',1)
     profile_fail.append(f'namespaced attribute outside R1: {localattr}');continue
    attrs[k]=attrs.get(k,0)+1
    if k.lower().startswith('on'):profile_fail.append(f'event-handler attribute outside R1: {k}')
    elif k not in ALLOWED_ATTRS:profile_fail.append(f'attribute outside R1 static primitive set: {k}')
    if k in {'href','xlink:href'}:profile_fail.append('references are outside R1')
  geom={'width':w,'height':h,'viewBox':vbn,'expectedRasterWidth':math.ceil(w) if w else None,'expectedRasterHeight':math.ceil(h) if h else None,'tags':tags,'attributes':attrs}
 else:geom={}
 failures+=profile_fail;res['boundedStaticProfile']={'status':'PASS' if not profile_fail else 'FAIL','geometry':geom,'failures':profile_fail}
 if profile_fail:return res
 out=ev/'librsvg.png';rp=run([str(RSVG),'--format=png','--output',str(out),str(path)]);(ev/'rsvg.stderr.txt').write_bytes(rp.stderr);render_fail=[];render={}
 if rp.returncode or not out.is_file():render_fail.append('librsvg failed to render SVG')
 else:
  try:
   im=Image.open(out).convert('RGBA');alpha=im.getchannel('A');bbox=alpha.getbbox();render={'width':im.width,'height':im.height,'pngSha256':sha(out),'nonEmptyAlpha':bbox is not None,'alphaBoundingBox':bbox}
   if im.width!=geom['expectedRasterWidth'] or im.height!=geom['expectedRasterHeight']:render_fail.append('librsvg intrinsic raster dimensions differ from bounded root geometry')
   if bbox is None:render_fail.append('librsvg render is fully transparent')
  except Exception as e:render_fail.append(f'librsvg output PNG unreadable: {e}')
 failures+=render_fail;res['referenceRender']={'status':'PASS' if not render_fail else 'FAIL','render':render,'evidence':{'pngPath':str(out),'stderrSha256':sha(ev/'rsvg.stderr.txt')},'failures':render_fail}
 if render_fail:return res
 env=dict(os.environ);env['ARTIFACT_NODE_PACKAGE_ROOT']=str(NODE_PACKAGE_ROOT);env['PLAYWRIGHT_BROWSERS_PATH']=str(PLAYWRIGHT_BROWSERS_ROOT);bp=run([str(NODE),str(BROWSER_PROBE),str(path)],env=env);bout,berr=bp.stdout.decode('utf-8','replace'),bp.stderr.decode('utf-8','replace');(ev/'browser-matrix.json').write_text(bout if bout else berr);bfail=[]
 try:b=json.loads(bout) if bp.returncode==0 else {}
 except:b={}
 browsers=b.get('browsers') or {}
 for k in ('chromium','firefox'):
  v=browsers.get(k) or {}
  if v.get('status')!='PASS':bfail.append(f'{k} SVG image decode failed')
  elif v.get('naturalWidth')!=render['width'] or v.get('naturalHeight')!=render['height']:bfail.append(f'{k} intrinsic dimensions differ from librsvg')
  elif int(v.get('nonTransparentPixels') or 0)<=0:bfail.append(f'{k} rendered SVG is fully transparent')
 if not b.get('intrinsicDimensionAgreement'):bfail.append('Chromium and Firefox intrinsic dimensions differ')
 failures+=bfail
 facts={k:{q:(browsers.get(k) or {}).get(q) for q in ('status','version','executable','naturalWidth','naturalHeight','pixelFNV32','nonTransparentPixels')} for k in ('chromium','firefox')}
 pixel=bool(b.get('pixelChecksumAgreement'));countagree=bool(b.get('nonTransparentPixelCountAgreement'))
 if not pixel:observations.append('Chromium and Firefox SVG raster pixel checksums differ')
 res['browserTargetMatrix']={'status':'PASS' if not bfail else 'FAIL','browsers':facts,'intrinsicDimensionAgreement':bool(b.get('intrinsicDimensionAgreement')),'pixelChecksumAgreement':pixel,'nonTransparentPixelCountAgreement':countagree,'standing':'TARGET_RENDERER_PIXEL_DIVERGENCE_OBSERVED' if not pixel else 'TARGET_PIXEL_CHECKSUM_AGREEMENT','evidenceSha256':sha(ev/'browser-matrix.json'),'failures':bfail}
 res.update({'status':'PASS' if not failures else 'FAIL','failures':failures,'observations':observations,'targetCompatibilityStanding':res['browserTargetMatrix']['standing'],'boundary':'PASS establishes exact bytes as well-formed XML within a deliberately narrow static SVG primitive subset, successful non-empty librsvg reference rendering, and successful pinned Chromium/Firefox image decoding with matching intrinsic dimensions. Pixel-exact raster equality is observed but not required. It does not establish full SVG conformance, dynamic/CSS/external-resource behavior, accessibility, aesthetics, rights, or caller-domain suitability.'});(ev/'verification.json').write_text(json.dumps(res,indent=2,sort_keys=True,ensure_ascii=False)+'\n');return res

def main():
 ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('--evidence-directory',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args();v=verify_svg(a.input,a.evidence_directory);s=json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n';a.output.write_text(s) if a.output else print(s,end='');return 0 if v.get('status')=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
