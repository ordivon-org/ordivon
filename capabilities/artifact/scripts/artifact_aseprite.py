#!/usr/bin/env python3
"""Bounded Aseprite source-to-horizontal-sheet derivative verifier."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,tempfile
from pathlib import Path
from typing import Any
import jsonschema
ROOT=Path(__file__).resolve().parents[1]
CONTRACT_SCHEMA=ROOT/'artifact-delivery/shadow-contracts/design-2d-aseprite-sheet-contract-v1.schema.json'
ASEPRITE=Path(os.environ.get('ARTIFACT_ASEPRITE','/opt/ordivon/external/aseprite/1.3.17.2/aseprite'))
STILL=ROOT/'scripts/artifact_still_image.py'
def sha_file(p:Path):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v:Any):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def fact(p:Path):return {'path':str(p.resolve()),'name':p.name,'size':p.stat().st_size,'sha256':sha_file(p)}
def validate_contract(c):
 s=json.loads(CONTRACT_SCHEMA.read_text());return [f"aseprite contract schema invalid: {e.message}" for e in sorted(jsonschema.Draft202012Validator(s).iter_errors(c),key=lambda e:list(e.path))]
def run_export(source:Path,root:Path,want:dict[str,Any]):
 root.mkdir(parents=True,exist_ok=True);sheet=root/want['sheetBasename'];data=root/want['dataBasename']
 cmd=[str(ASEPRITE),'-b','--list-tags',str(source),'--sheet-type','horizontal','--format','json-array','--sheet',str(sheet),'--data',str(data)]
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=120)
 return p,sheet,data,cmd
def load_still():
 spec=importlib.util.spec_from_file_location('artifact_aseprite_still_delegate',STILL);assert spec and spec.loader;mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod.verify_png_srgb

def verify_aseprite(path:Path,contract_path:Path,evidence_dir:Path|None=None)->dict[str,Any]:
 if not path.is_file():return {'schemaVersion':1,'kind':'artifact-aseprite-verification','profileId':'design-2d-aseprite-horizontal-sheet-r1','status':'FAIL','failures':['input is not a regular file']}
 try:c=json.loads(contract_path.read_text())
 except Exception as e:return {'schemaVersion':1,'kind':'artifact-aseprite-verification','profileId':'design-2d-aseprite-horizontal-sheet-r1','status':'FAIL','artifact':fact(path),'failures':[f'contract unreadable: {e}']}
 ev=evidence_dir or Path(tempfile.mkdtemp(prefix='artifact-aseprite-evidence-'));ev.mkdir(parents=True,exist_ok=True);failures=validate_contract(c);want=c.get('export',{});res={'schemaVersion':1,'kind':'artifact-aseprite-verification','profileId':'design-2d-aseprite-horizontal-sheet-r1','status':'FAIL','artifact':fact(path),'contract':{'path':str(contract_path.resolve()),'sha256':sha_file(contract_path),'canonicalDigest':canonical(c)},'tools':{},'failures':failures}
 if not ASEPRITE.is_file() or not os.access(ASEPRITE,os.X_OK):failures.append('required Workstation-managed Aseprite capability unavailable')
 else:res['tools']['aseprite']={'path':str(ASEPRITE.resolve()),'sha256':sha_file(ASEPRITE)}
 if not STILL.is_file():failures.append('required still-image PNG verifier unavailable')
 else:res['tools']['stillImageVerifier']={'path':str(STILL.resolve()),'sha256':sha_file(STILL)}
 if failures:return res
 with tempfile.TemporaryDirectory(prefix='artifact-aseprite-native-') as td:
  td=Path(td);p1,s1,d1,cmd1=run_export(path,td/'run1',want);p2,s2,d2,cmd2=run_export(path,td/'run2',want);native=[]
  (ev/'aseprite-run1.stdout.txt').write_bytes(p1.stdout);(ev/'aseprite-run1.stderr.txt').write_bytes(p1.stderr);(ev/'aseprite-run2.stdout.txt').write_bytes(p2.stdout);(ev/'aseprite-run2.stderr.txt').write_bytes(p2.stderr)
  if p1.returncode!=0 or not s1.is_file() or not d1.is_file():native.append('Aseprite native export run1 failed')
  if p2.returncode!=0 or not s2.is_file() or not d2.is_file():native.append('Aseprite native export run2 failed')
  png_equal=not native and s1.read_bytes()==s2.read_bytes();data_equal=not native and d1.read_bytes()==d2.read_bytes()
  if not native and not png_equal:native.append('two clean Aseprite exports produced different PNG bytes')
  if not native and not data_equal:native.append('two clean Aseprite exports produced different native metadata bytes')
  failures.extend(native);res['nativeDeterministicExport']={'status':'PASS' if not native else 'FAIL','commandShape':['aseprite','-b','--list-tags','SOURCE','--sheet-type','horizontal','--format','json-array','--sheet',want.get('sheetBasename'),'--data',want.get('dataBasename')],'pngExactAcrossRuns':png_equal,'metadataExactAcrossRuns':data_equal,'failures':native}
  if native:return res
  generated_png=ev/'generated-sheet.png';generated_json=ev/'native-export.json';shutil.copyfile(s1,generated_png);shutil.copyfile(d1,generated_json)
  facts_fail=[]
  try:meta=json.loads(d1.read_text())
  except Exception as e:facts_fail.append(f'Aseprite native metadata is invalid JSON: {e}');meta={}
  frames=meta.get('frames') if isinstance(meta,dict) else None;m=meta.get('meta') if isinstance(meta,dict) else None;size=(m or {}).get('size') if isinstance(m,dict) else None
  facts={'frameCount':len(frames) if isinstance(frames,list) else None,'width':size.get('w') if isinstance(size,dict) else None,'height':size.get('h') if isinstance(size,dict) else None,'format':(m or {}).get('format') if isinstance(m,dict) else None,'tagNames':[x.get('name') for x in ((m or {}).get('frameTags') or []) if isinstance(x,dict)] if isinstance(m,dict) else []}
  for k in ('frameCount','width','height'):
   if facts.get(k)!=want.get(k):facts_fail.append(f'native metadata {k} differs from object contract')
  if facts.get('format')!='RGBA8888':facts_fail.append('R1 requires Aseprite RGBA8888 native sheet metadata')
  failures.extend(facts_fail);res['nativeMetadataFacts']={'status':'PASS' if not facts_fail else 'FAIL','facts':facts,'nativeMetadataSha256':sha_file(d1),'failures':facts_fail}
  if facts_fail:return res
  identity=[];png_sha=sha_file(s1);data_sha=sha_file(d1)
  if png_sha!=want['expectedPngSha256']:identity.append('generated PNG SHA-256 differs from object contract')
  if data_sha!=want['expectedNativeMetadataSha256']:identity.append('generated native metadata SHA-256 differs from object contract')
  failures.extend(identity);res['derivativeIdentity']={'status':'PASS' if not identity else 'FAIL','generatedPngSha256':png_sha,'expectedPngSha256':want['expectedPngSha256'],'generatedNativeMetadataSha256':data_sha,'expectedNativeMetadataSha256':want['expectedNativeMetadataSha256'],'failures':identity}
  if identity:return res
  png_ev=ev/'generated-png-profile';png_ev.mkdir(parents=True,exist_ok=True);still=load_still()(generated_png,png_ev);sf=[]
  if still.get('status')!='PASS':sf.append('generated PNG did not pass still-image-png-srgb-r1')
  failures.extend(sf);res['derivedStillImageProfile']={'status':'PASS' if not sf else 'FAIL','profileId':'still-image-png-srgb-r1','verification':still,'failures':sf}
 res.update({'status':'PASS' if not failures else 'FAIL','failures':failures,'boundary':'PASS establishes that the exact admitted Aseprite source is accepted by the exact managed Aseprite exporter, produces byte-deterministic native horizontal-sheet PNG and JSON metadata across two clean exports, matches exact contract digests and technical facts, and that the generated PNG independently passes still-image-png-srgb-r1. It does not interpret frame/tag meaning, caller-owned metadata, actor/role identity, artistic/gameplay quality, other export modes, cross-version reproducibility, or rights.'});(ev/'verification.json').write_text(json.dumps(res,indent=2,sort_keys=True,ensure_ascii=False)+'\n');return res

def main():
 ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('--contract',type=Path,required=True);ap.add_argument('--evidence-directory',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args();v=verify_aseprite(a.input,a.contract,a.evidence_directory);s=json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n';a.output.write_text(s) if a.output else print(s,end='');return 0 if v.get('status')=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
