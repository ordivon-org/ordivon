#!/usr/bin/env python3
from __future__ import annotations
import sys

import hashlib
import json
import math
import os
import subprocess
from pathlib import Path
from typing import Any

_ARTIFACT_IMPORT_ROOT = Path(__file__).resolve().parents[1]
if str(_ARTIFACT_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(_ARTIFACT_IMPORT_ROOT))

from artifact_verification.claim_results import emits_explicit_claim_results

ROOT=Path(__file__).resolve().parents[1]
LOCK=ROOT/'artifact-delivery/cad-toolchain-r1.lock.json'
def sha256_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
 return h.hexdigest()
def fact(p:Path): return {'path':str(p),'sha256':sha256_file(p),'size':p.stat().st_size}
def load_lock(): return json.loads(LOCK.read_text())
def contract_failures(c:Any)->list[str]:
 if not isinstance(c,dict): return ['object contract must be a JSON object']
 fs=[]
 if c.get('schemaVersion')!=1 or c.get('kind')!='cad-step-solid-contract-v1': fs.append('object contract identity/version is not cad-step-solid-contract-v1')
 if c.get('units')!='mm': fs.append('R1 units must be mm')
 topology=c.get('topology')
 if not isinstance(topology,dict): fs.append('contract.topology must be an object')
 else:
  for k in ('solids','faces','edges'):
   value=topology.get(k)
   if isinstance(value,bool) or not isinstance(value,int) or value<1: fs.append(f'contract.topology.{k} must be a positive integer')
 bbox=c.get('bboxMm')
 if not isinstance(bbox,dict): fs.append('contract.bboxMm must be an object')
 else:
  for k in ('xmin','ymin','zmin','xmax','ymax','zmax'):
   value=bbox.get(k)
   if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(float(value)): fs.append(f'contract.bboxMm.{k} must be a finite number')
 for k in ('volumeMm3','geometryToleranceMm','volumeToleranceMm3'):
  value=c.get(k)
  if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(float(value)) or float(value)<=0: fs.append(f'contract.{k} must be a positive finite number')
 return fs
def parse_last_json(text:str)->dict[str,Any]:
 for line in reversed(text.splitlines()):
  line=line.strip()
  if line.startswith('{'):
   try: return json.loads(line)
   except Exception: pass
 raise ValueError('no JSON object in tool output')
def compare(obs:dict[str,Any],c:dict[str,Any],label:str)->list[str]:
 fs=[]; topo=c['topology']; bbox=c['bboxMm']; gt=float(c['geometryToleranceMm']); vt=float(c['volumeToleranceMm3'])
 if obs.get('valid') is not True: fs.append(f'{label} shape is not valid')
 for k in ('solids','faces','edges'):
  try: equal=int(obs[k])==int(topo[k])
  except Exception: equal=False
  if not equal: fs.append(f'{label} topology {k} differs from contract')
 observed_bbox=obs.get('bboxMm') if isinstance(obs.get('bboxMm'),dict) else {}
 for k in ('xmin','ymin','zmin','xmax','ymax','zmax'):
  try: equal=abs(float(observed_bbox[k])-float(bbox[k]))<=gt
  except Exception: equal=False
  if not equal: fs.append(f'{label} bbox {k} differs from contract')
 try: volume_equal=abs(float(obs['volumeMm3'])-float(c['volumeMm3']))<=vt
 except Exception: volume_equal=False
 if not volume_equal: fs.append(f'{label} volume differs from contract')
 return fs
CLAIM_POINTERS={
 'semantic':'/semantic',
 'structural':'/structural',
 'target':'/target',
 'toolIdentity':'/toolIdentity',
}

@emits_explicit_claim_results(CLAIM_POINTERS)
def verify_step_solid(subject:Path,contract_path:Path,evidence_directory:Path)->dict[str,Any]:
 evidence_directory.mkdir(parents=True,exist_ok=True); failures=[]
 if not subject.is_file(): return {'schemaVersion':1,'kind':'artifact-cad-step-solid-verification','profileId':'design-3d-step-solid-r1','status':'FAIL','failures':['STEP subject is not a regular file']}
 try: c=json.loads(contract_path.read_text())
 except Exception as e: return {'schemaVersion':1,'kind':'artifact-cad-step-solid-verification','profileId':'design-3d-step-solid-r1','status':'FAIL','failures':[f'contract unreadable: {e}']}
 contract_errors=contract_failures(c); failures+=contract_errors
 lock=load_lock(); free=lock['freecad']; occ=lock['occtInspector']
 app=Path(free['appImagePath']); root=Path(free['rootPath']); cmd=root/free['freecadCmdPath']; part_module=root/free['partModulePath']; app_lib=root/free['freecadAppLibraryPath']; base_lib=root/free['freecadBaseLibraryPath']; inspector=Path(occ['path']); source=ROOT/occ['sourcePath']
 tool_failures=[]
 for path,name in ((app,'FreeCAD AppImage'),(cmd,'FreeCAD CLI'),(part_module,'FreeCAD Part module'),(app_lib,'FreeCAD App library'),(base_lib,'FreeCAD Base library'),(inspector,'OCCT inspector'),(source,'OCCT inspector source')):
  if not path.is_file(): tool_failures.append(f'required external tool unavailable: {name} {path}')
 if not contract_errors and not tool_failures:
  locked=((app,free['appImageSha256'],'FreeCAD AppImage'),(cmd,free['freecadCmdSha256'],'FreeCAD CLI'),(part_module,free['partModuleSha256'],'FreeCAD Part module'),(app_lib,free['freecadAppLibrarySha256'],'FreeCAD App library'),(base_lib,free['freecadBaseLibrarySha256'],'FreeCAD Base library'),(inspector,occ['binarySha256'],'OCCT inspector binary'),(source,occ['sourceSha256'],'OCCT inspector source'))
  for path,expected,label in locked:
   if sha256_file(path)!=expected: tool_failures.append(f'{label} digest differs from lock')
  package=subprocess.run(['/usr/bin/pacman','-Q','opencascade'],text=True,capture_output=True,check=False,timeout=15)
  if package.returncode!=0 or package.stdout.strip()!=occ['occtPackage']: tool_failures.append('system Open CASCADE package identity differs from lock')
 failures+=tool_failures
 tool_status='NOT_EVALUATED' if contract_errors else ('PASS' if not tool_failures else 'FAIL')
 tool_identity={'status':tool_status,'failures':tool_failures}
 if failures:
  return {'schemaVersion':1,'kind':'artifact-cad-step-solid-verification','profileId':'design-3d-step-solid-r1','status':'FAIL','toolIdentity':tool_identity,'failures':failures}

 occ_proc=subprocess.run([str(inspector),str(subject)],text=True,capture_output=True,check=False,timeout=60)
 try: occ_json=parse_last_json(occ_proc.stdout)
 except Exception as e: occ_json={'status':'FAIL','parseError':str(e),'raw':occ_proc.stdout[-2000:]}
 (evidence_directory/'occt-readback.json').write_text(json.dumps(occ_json,indent=2,sort_keys=True)+'\n')
 structural_failures=[]
 if occ_proc.returncode!=0 or occ_json.get('status')!='PASS': structural_failures.append('system OCCT STEP/BRep readback failed')
 failures+=structural_failures

 script=evidence_directory/'freecad-readback.py'
 script.write_text("import json,os,Part\nshape=Part.read(os.environ['ARTIFACT_CAD_STEP_SUBJECT'])\nb=shape.BoundBox\nprint(json.dumps({'status':'PASS','valid':shape.isValid(),'solids':len(shape.Solids),'faces':len(shape.Faces),'edges':len(shape.Edges),'volumeMm3':shape.Volume,'areaMm2':shape.Area,'bboxMm':{'xmin':b.XMin,'ymin':b.YMin,'zmin':b.ZMin,'xmax':b.XMax,'ymax':b.YMax,'zmax':b.ZMax}},sort_keys=True))\n")
 env=os.environ.copy(); env['ARTIFACT_CAD_STEP_SUBJECT']=str(subject); env['LD_LIBRARY_PATH']=f"{root}/usr/lib:{root}/usr/lib/x86_64-linux-gnu:"+env.get('LD_LIBRARY_PATH',''); env['PYTHONHOME']=str(root/'usr')
 free_proc=subprocess.run([str(cmd),str(script)],text=True,capture_output=True,check=False,timeout=90,env=env)
 try: free_json=parse_last_json(free_proc.stdout)
 except Exception as e: free_json={'status':'FAIL','parseError':str(e),'raw':free_proc.stdout[-2000:]}
 (evidence_directory/'freecad-readback.json').write_text(json.dumps(free_json,indent=2,sort_keys=True)+'\n')
 target_failures=[]
 if free_proc.returncode!=0 or free_json.get('status')!='PASS': target_failures.append('FreeCAD native STEP readback failed')
 failures+=target_failures

 semantic_failures=[]
 if occ_json.get('status')=='PASS': semantic_failures+=compare(occ_json,c,'OCCT')
 if free_json.get('status')=='PASS': semantic_failures+=compare(free_json,c,'FreeCAD')
 if occ_json.get('status')=='PASS' and free_json.get('status')=='PASS':
  gt=float(c['geometryToleranceMm']); vt=float(c['volumeToleranceMm3'])
  for k in ('xmin','ymin','zmin','xmax','ymax','zmax'):
   if abs(float(occ_json['bboxMm'][k])-float(free_json['bboxMm'][k]))>gt: semantic_failures.append(f'cross-reader bbox {k} differs')
  if abs(float(occ_json['volumeMm3'])-float(free_json['volumeMm3']))>vt: semantic_failures.append('cross-reader volume differs')
 failures+=semantic_failures
 semantic_status='NOT_EVALUATED' if structural_failures or target_failures else ('PASS' if not semantic_failures else 'FAIL')
 return {'schemaVersion':1,'kind':'artifact-cad-step-solid-verification','profileId':'design-3d-step-solid-r1','status':'PASS' if not failures else 'FAIL','subject':fact(subject),'contract':fact(contract_path),'tools':{'freecad':{'appImage':fact(app),'command':fact(cmd),'partModule':fact(part_module),'appLibrary':fact(app_lib),'baseLibrary':fact(base_lib),'version':free['version']},'occtInspector':{'binary':fact(inspector),'source':fact(source),'occtPackage':occ['occtPackage']}},'toolIdentity':tool_identity,'structural':{'status':'PASS' if not structural_failures else 'FAIL','readback':occ_json,'failures':structural_failures},'target':{'status':'PASS' if not target_failures else 'FAIL','readback':free_json,'failures':target_failures},'semantic':{'status':semantic_status,'failures':semantic_failures},'occtReadback':occ_json,'freecadReadback':free_json,'failures':failures,'boundary':'PASS proves exact STEP bytes import as a valid single-solid BREP in official FreeCAD 1.1.3 and system OCCT 7.9.3, and both readbacks match the request-bound metric topology/bbox/volume contract. FreeCAD and the system inspector share OCCT lineage, so PASS is not cross-kernel proof and does not prove feature-history preservation, assemblies, PMI/GD&T, BIM, manufacturing feasibility, tolerances, safety or fitness.'}
def main()->int:
 import argparse
 ap=argparse.ArgumentParser(); ap.add_argument('input',type=Path); ap.add_argument('--contract',type=Path,required=True); ap.add_argument('--evidence-directory',type=Path); ap.add_argument('--output',type=Path); a=ap.parse_args(); ev=(a.evidence_directory or Path('out/artifact-cad-step')).resolve(); r=verify_step_solid(a.input.resolve(),a.contract.resolve(),ev); t=json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)+'\n';
 if a.output:
  a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(t)
 else: print(t,end='')
 return 0 if r.get('status')=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())
