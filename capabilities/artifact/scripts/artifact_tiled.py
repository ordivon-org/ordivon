#!/usr/bin/env python3
"""Bounded Tiled TMJ finite orthogonal object-map verifier."""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,tempfile
from pathlib import Path
from typing import Any
import jsonschema
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
CONTRACT_SCHEMA=ROOT/'artifact-delivery/shadow-contracts/design-2d-tiled-tmj-contract-v1.schema.json'
TILED=Path(os.environ.get('ARTIFACT_TILED','/usr/bin/tiled'))
TMXRASTERIZER=Path(os.environ.get('ARTIFACT_TMXRASTERIZER','/usr/bin/tmxrasterizer'))

def sha_file(p:Path):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical_sha(v:Any):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def fact(p:Path):return {'path':str(p.resolve()),'name':p.name,'size':p.stat().st_size,'sha256':sha_file(p)}
def run(args:list[str],timeout=120):
 env=dict(os.environ);env.setdefault('QT_QPA_PLATFORM','offscreen');return subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout,env=env)
def validate_contract(c):
 s=json.loads(CONTRACT_SCHEMA.read_text());return [f"tiled contract schema invalid: {e.message}" for e in sorted(jsonschema.Draft202012Validator(s).iter_errors(c),key=lambda e:list(e.path))]
def object_shape(o:dict[str,Any])->str:
 if 'polyline' in o:return 'polyline'
 if any(k in o for k in ('polygon','ellipse','point','text','gid','template')):return 'unsupported'
 return 'rectangle'
def verify_tiled_tmj(path:Path,contract_path:Path,evidence_dir:Path|None=None)->dict[str,Any]:
 if not path.is_file():return {'schemaVersion':1,'kind':'artifact-tiled-tmj-verification','profileId':'design-2d-tiled-tmj-object-map-r1','status':'FAIL','failures':['input is not a regular file']}
 try:c=json.loads(contract_path.read_text())
 except Exception as e:return {'schemaVersion':1,'kind':'artifact-tiled-tmj-verification','profileId':'design-2d-tiled-tmj-object-map-r1','status':'FAIL','artifact':fact(path),'failures':[f'contract unreadable: {e}']}
 ev=evidence_dir or Path(tempfile.mkdtemp(prefix='artifact-tiled-evidence-'));ev.mkdir(parents=True,exist_ok=True);failures=validate_contract(c);want=c.get('map',{});res={'schemaVersion':1,'kind':'artifact-tiled-tmj-verification','profileId':'design-2d-tiled-tmj-object-map-r1','status':'FAIL','artifact':fact(path),'contract':{'path':str(contract_path.resolve()),'sha256':sha_file(contract_path),'canonicalDigest':canonical_sha(c)},'tools':{},'failures':failures}
 for n,p in [('tiled',TILED),('tmxrasterizer',TMXRASTERIZER)]:
  if not p.is_file() or not os.access(p,os.X_OK):failures.append(f'required mature external capability unavailable: {n}')
  else:res['tools'][n]={'path':str(p.resolve()),'sha256':sha_file(p)}
 if failures:return res
 try:src=json.loads(path.read_text())
 except Exception as e:failures.append(f'subject is not valid JSON: {e}');return res
 # Bounded object-map subset: format identity and no external/resource-heavy features.
 bounded=[];layers=src.get('layers') if isinstance(src,dict) else None
 if src.get('type')!='map':bounded.append('Tiled root type must be map')
 if src.get('orientation')!='orthogonal':bounded.append('R1 requires orthogonal orientation')
 if src.get('infinite') is not False:bounded.append('R1 requires finite map')
 if src.get('tilesets') not in ([],None):bounded.append('R1 forbids tilesets')
 if not isinstance(layers,list) or not layers:bounded.append('R1 requires at least one object layer');layers=[]
 layer_ids=[];object_ids=[];objects=[]
 for l in layers:
  if not isinstance(l,dict) or l.get('type')!='objectgroup':bounded.append('R1 allows objectgroup layers only');continue
  layer_ids.append(l.get('id'));lo=l.get('objects')
  if not isinstance(lo,list):bounded.append(f"object layer {l.get('name')} lacks objects array");continue
  for o in lo:
   if not isinstance(o,dict):bounded.append('object must be JSON object');continue
   objects.append(o);object_ids.append(o.get('id'))
   if 'class' in o:bounded.append(f"object {o.get('id')} uses legacy class field instead of current type")
   if not isinstance(o.get('type'),str) or not o.get('type'):bounded.append(f"object {o.get('id')} requires non-empty current Tiled type")
   shape=object_shape(o)
   if shape not in ('rectangle','polyline'):bounded.append(f"object {o.get('id')} shape outside R1: {shape}")
   if 'template' in o:bounded.append(f"object {o.get('id')} uses external template")
   for prop in o.get('properties',[]) or []:
    if isinstance(prop,dict) and prop.get('type')=='file':bounded.append(f"object {o.get('id')} has external file property")
 if len(layer_ids)!=len(set(layer_ids)):bounded.append('layer IDs are not unique')
 if len(object_ids)!=len(set(object_ids)):bounded.append('object IDs are not unique')
 facts={'formatVersion':str(src.get('version')),'tiledVersion':str(src.get('tiledversion')),'orientation':src.get('orientation'),'width':src.get('width'),'height':src.get('height'),'tileWidth':src.get('tilewidth'),'tileHeight':src.get('tileheight'),'layerCount':len(layers),'objectCount':len(objects),'canonicalJsonSha256':canonical_sha(src),'layerTypes':[l.get('type') for l in layers if isinstance(l,dict)],'objectShapeCounts':{k:sum(object_shape(o)==k for o in objects) for k in ('rectangle','polyline','unsupported')}}
 for ck,fk in [('formatVersion','formatVersion'),('tiledVersion','tiledVersion'),('orientation','orientation'),('width','width'),('height','height'),('tileWidth','tileWidth'),('tileHeight','tileHeight'),('layerCount','layerCount'),('objectCount','objectCount')]:
  if facts[fk]!=want.get(ck):bounded.append(f'{fk} differs from object contract')
 failures.extend(bounded);res['boundedObjectMap']={'status':'PASS' if not bounded else 'FAIL','facts':facts,'failures':bounded}
 if bounded:return res
 semantic_fail=[]
 if facts['canonicalJsonSha256']!=want['expectedCanonicalJsonSha256']:semantic_fail.append('canonical sorted JSON SHA-256 differs from object contract')
 failures.extend(semantic_fail);res['canonicalSemanticIdentity']={'status':'PASS' if not semantic_fail else 'FAIL','canonicalJsonSha256':facts['canonicalJsonSha256'],'expectedCanonicalJsonSha256':want['expectedCanonicalJsonSha256'],'failures':semantic_fail}
 if semantic_fail:return res
 with tempfile.TemporaryDirectory(prefix='artifact-tiled-native-') as td:
  td=Path(td);tmj=td/'roundtrip.tmj';tmx=td/'roundtrip.tmx';back=td/'back.tmj';png=ev/'tmxrasterizer.png'
  p=run([str(TILED),'--export-map',str(path),str(tmj)]);(ev/'tiled-tmj.stderr.txt').write_bytes(p.stderr);native_fail=[]
  if p.returncode!=0 or not tmj.is_file():native_fail.append('Tiled native TMJ export failed')
  else:
   try:roundtrip=json.loads(tmj.read_text())
   except Exception as e:native_fail.append(f'Tiled native TMJ output is invalid JSON: {e}');roundtrip=None
   if roundtrip is not None and roundtrip!=src:native_fail.append('Tiled native TMJ export changes JSON semantics; source is not canonical under current Tiled')
  failures.extend(native_fail);res['nativeTmjRoundTrip']={'status':'PASS' if not native_fail else 'FAIL','roundTripCanonicalJsonSha256':canonical_sha(roundtrip) if 'roundtrip' in locals() and roundtrip is not None else None,'evidenceStderrSha256':sha_file(ev/'tiled-tmj.stderr.txt'),'failures':native_fail}
  if native_fail:return res
  p1=run([str(TILED),'--export-map',str(path),str(tmx)]);p2=run([str(TILED),'--export-map',str(tmx),str(back)]) if p1.returncode==0 and tmx.is_file() else None;(ev/'tiled-cross-format.stderr.txt').write_bytes(p1.stderr+(p2.stderr if p2 else b''));cross=[]
  if p1.returncode!=0 or not tmx.is_file() or p2 is None or p2.returncode!=0 or not back.is_file():cross.append('Tiled TMJ→TMX→TMJ round-trip failed')
  else:
   try:back_obj=json.loads(back.read_text())
   except Exception as e:cross.append(f'Tiled cross-format TMJ output invalid JSON: {e}');back_obj=None
   if back_obj is not None and back_obj!=src:cross.append('Tiled TMJ→TMX→TMJ changes JSON semantics')
  failures.extend(cross);res['nativeCrossFormatRoundTrip']={'status':'PASS' if not cross else 'FAIL','backCanonicalJsonSha256':canonical_sha(back_obj) if 'back_obj' in locals() and back_obj is not None else None,'evidenceStderrSha256':sha_file(ev/'tiled-cross-format.stderr.txt'),'failures':cross}
  if cross:return res
  rr=run([str(TMXRASTERIZER),str(path),str(png)]);(ev/'tmxrasterizer.stderr.txt').write_bytes(rr.stderr);rf=[];render={}
  if rr.returncode!=0 or not png.is_file():rf.append('tmxrasterizer failed to render map')
  else:
   try:
    im=Image.open(png).convert('RGBA');bbox=im.getchannel('A').getbbox();render={'width':im.width,'height':im.height,'pngSha256':sha_file(png),'alphaBoundingBox':bbox,'nonEmptyAlpha':bbox is not None}
    ew=want['width']*want['tileWidth'];eh=want['height']*want['tileHeight']
    if (im.width,im.height)!=(ew,eh):rf.append('tmxrasterizer pixel dimensions differ from map grid dimensions')
    if bbox is None:rf.append('tmxrasterizer output is fully transparent')
   except Exception as e:rf.append(f'tmxrasterizer PNG unreadable: {e}')
  failures.extend(rf);res['nativeRasterReadback']={'status':'PASS' if not rf else 'FAIL','render':render,'evidenceStderrSha256':sha_file(ev/'tmxrasterizer.stderr.txt'),'failures':rf}
 res.update({'status':'PASS' if not failures else 'FAIL','failures':failures,'boundary':'PASS establishes one exact finite orthogonal object-layer-only TMJ subject under the current Tiled native parser/exporter, stable TMJ and TMJ→TMX→TMJ semantics, exact bounded technical facts, and non-empty tmxrasterizer readback. It does not establish Game topology meaning, navigation/collision correctness, tile/tileset support, external resource resolution, aesthetics, or caller-domain suitability.'});(ev/'verification.json').write_text(json.dumps(res,indent=2,sort_keys=True,ensure_ascii=False)+'\n');return res

def main():
 ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('--contract',type=Path,required=True);ap.add_argument('--evidence-directory',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args();v=verify_tiled_tmj(a.input,a.contract,a.evidence_directory);s=json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n';a.output.write_text(s) if a.output else print(s,end='');return 0 if v.get('status')=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
