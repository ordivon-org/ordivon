#!/usr/bin/env python3
"""Standards-first bounded GLB 2.0 static-mesh verifier."""
from __future__ import annotations
import argparse,hashlib,json,os,re,subprocess,tempfile
from pathlib import Path
from typing import Any
import jsonschema
ROOT=Path(__file__).resolve().parents[1]
CONTRACT_SCHEMA=ROOT/'artifact-delivery/shadow-contracts/design-3d-glb-contract-v1.schema.json'
VALIDATOR=Path(os.environ.get('ARTIFACT_GLTF_VALIDATOR','/opt/ordivon/external/gltf-validator/2.0.0-dev.3.10/gltf-validator'))
ASSIMP=Path(os.environ.get('ARTIFACT_ASSIMP','/usr/bin/assimp'))
BLENDER=Path(os.environ.get('ARTIFACT_BLENDER','/usr/bin/blender'))

def run(a:list[str],timeout=120): return subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout)
def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def validate_contract(c):
 s=json.loads(CONTRACT_SCHEMA.read_text()); return [f"design-3d contract schema invalid: {e.message}" for e in sorted(jsonschema.Draft202012Validator(s).iter_errors(c),key=lambda e:list(e.path))]
def floats(text): return [float(x) for x in text.strip('() ').split()]

def parse_assimp(out:str)->dict[str,Any]:
 def one(pat,cast=int,default=None):
  m=re.search(pat,out,re.M); return cast(m.group(1)) if m else default
 mn=re.search(r'^Minimum point\s+\(([^)]+)\)',out,re.M); mx=re.search(r'^Maximum point\s+\(([^)]+)\)',out,re.M)
 return {'nodes':one(r'^Nodes:\s+(\d+)'),'meshes':one(r'^Meshes:\s+(\d+)'),'animations':one(r'^Animations:\s+(\d+)'),'textures':one(r'^Textures \(embed\.\):\s+(\d+)'),'cameras':one(r'^Cameras:\s+(\d+)'),'lights':one(r'^Lights:\s+(\d+)'),'vertices':one(r'^Vertices:\s+(\d+)'),'faces':one(r'^Faces:\s+(\d+)'),'bones':one(r'^Bones:\s+(\d+)'),'primitiveTriangles':bool(re.search(r'^Primitive Types:\s+triangles\s*$',out,re.M)),'boundsMin':floats(mn.group(1)) if mn else None,'boundsMax':floats(mx.group(1)) if mx else None}

def blender_probe(path:Path,evidence:Path)->tuple[dict[str,Any],list[str]]:
 script=evidence/'blender-probe.py'
 script.write_text('''import bpy,json,sys\np=sys.argv[-1]\nbpy.ops.wm.read_factory_settings(use_empty=True)\nr=bpy.ops.import_scene.gltf(filepath=p)\nmeshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]\nx={"result":sorted(r),"sceneCount":len(bpy.data.scenes),"objectCount":len(bpy.context.scene.objects),"meshObjectCount":len(meshes),"meshes":[{"vertexCount":len(o.data.vertices),"polygonCount":len(o.data.polygons),"materialSlots":len(o.material_slots)} for o in meshes]}\nprint("ORDIVON_JSON="+json.dumps(x,sort_keys=True,separators=(",",":")))\n''')
 p=run([str(BLENDER),'--background','--factory-startup','--python',str(script),'--',str(path)],180)
 (evidence/'blender.stdout.txt').write_bytes(p.stdout); (evidence/'blender.stderr.txt').write_bytes(p.stderr)
 m=re.search(rb'^ORDIVON_JSON=(.+)$',p.stdout,re.M)
 if p.returncode or not m: return {},['Blender headless import/probe failed']
 try:return json.loads(m.group(1)),[]
 except:return {},['Blender probe JSON unreadable']

def verify_glb(path:Path,contract_path:Path,evidence_dir:Path|None=None)->dict[str,Any]:
 if not path.is_file(): return {'schemaVersion':1,'kind':'artifact-design3d-verification','profileId':'design-3d-glb-static-mesh-r1','status':'FAIL','failures':['input is not a regular file']}
 try:c=json.loads(contract_path.read_text())
 except Exception as e:return {'schemaVersion':1,'kind':'artifact-design3d-verification','profileId':'design-3d-glb-static-mesh-r1','status':'FAIL','failures':[f'contract unreadable: {e}']}
 failures=validate_contract(c); ev=evidence_dir or Path(tempfile.mkdtemp(prefix='artifact-design3d-evidence-')); ev.mkdir(parents=True,exist_ok=True)
 res={'schemaVersion':1,'kind':'artifact-design3d-verification','profileId':'design-3d-glb-static-mesh-r1','status':'FAIL','artifact':{'path':str(path.resolve()),'size':path.stat().st_size,'sha256':sha(path)},'contract':{'sha256':sha(contract_path),'canonicalDigest':canonical(c)},'failures':failures,'tools':{}}
 if failures:(ev/'verification.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n'); return res
 for n,p in [('validator',VALIDATOR),('assimp',ASSIMP),('blender',BLENDER)]:
  if not p.is_file() or not os.access(p,os.X_OK): failures.append(f'required mature external capability unavailable: {n}')
  else: res['tools'][n]={'path':str(p.resolve()),'sha256':sha(p)}
 if failures: res['failures']=failures; (ev/'verification.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n'); return res
 # Khronos validator
 v=run([str(VALIDATOR),str(path)]); (ev/'khronos-validator.json').write_bytes(v.stdout if v.stdout else v.stderr)
 vf=[]
 try:vr=json.loads(v.stdout) if v.stdout else {}
 except:vr={}
 issues=vr.get('issues') or {}; info=vr.get('info') or {}
 if v.returncode!=0 or issues.get('numErrors')!=0: vf.append('Khronos glTF Validator reports errors')
 if issues.get('numWarnings')!=0: vf.append('R1 requires zero Khronos validator warnings')
 if vr.get('mimeType')!='model/gltf-binary' or info.get('version')!='2.0': vf.append('artifact is not GLB/glTF 2.0')
 # profile facts via official validator report
 pf=[]
 expected_info={'animationCount':0,'materialCount':0,'hasMorphTargets':False,'hasSkins':False,'hasTextures':False,'hasDefaultScene':True,'drawCallCount':1}
 for k,w in expected_info.items():
  if info.get(k)!=w: pf.append(f'bounded profile fact differs: {k}')
 want=c['scene']
 if info.get('totalVertexCount')!=want['vertexCount']: pf.append('validator vertex count differs from contract')
 if info.get('totalTriangleCount')!=want['triangleCount']: pf.append('validator triangle count differs from contract')
 failures.extend(vf+pf)
 # Assimp independent source-coordinate scene view
 a=run([str(ASSIMP),'info',str(path)]); aout=a.stdout.decode('utf-8','replace'); (ev/'assimp-info.txt').write_text(aout+a.stderr.decode('utf-8','replace'))
 af=[]; ai=parse_assimp(aout) if a.returncode==0 else {}
 if a.returncode!=0: af.append('Assimp import failed')
 checks={'nodes':'nodeCount','meshes':'meshCount','vertices':'vertexCount','faces':'triangleCount'}
 for gotkey,wantkey in checks.items():
  if ai.get(gotkey)!=want[wantkey]: af.append(f'Assimp {gotkey} differs from contract')
 if not ai.get('primitiveTriangles'): af.append('Assimp primitive type is not triangles')
 if ai.get('animations')!=0 or ai.get('textures')!=0 or ai.get('bones')!=0 or ai.get('cameras')!=0 or ai.get('lights')!=0: af.append('Assimp observes scene features outside bounded R1')
 tol=1e-6
 for label in ('boundsMin','boundsMax'):
  got=ai.get(label); exp=want[label]
  if got is None or len(got)!=3 or any(abs(float(x)-float(y))>tol for x,y in zip(got,exp)): af.append(f'Assimp {label} differs from contract')
 failures.extend(af)
 # Blender independent importer acceptance; topology only due axis conversion.
 bi,bf=blender_probe(path,ev)
 if not bf:
  if bi.get('result')!=['FINISHED']: bf.append('Blender importer did not finish')
  if bi.get('meshObjectCount')!=1 or bi.get('objectCount')!=1: bf.append('Blender object topology outside bounded R1')
  ms=bi.get('meshes') or []
  if len(ms)!=1 or ms[0].get('vertexCount')!=want['vertexCount'] or ms[0].get('polygonCount')!=want['triangleCount']: bf.append('Blender mesh topology differs from contract')
  if ms and ms[0].get('materialSlots')!=0: bf.append('Blender observes material slots outside bounded R1')
 failures.extend(bf)
 res.update({'khronosConformance':{'status':'PASS' if not vf else 'FAIL','validatorVersion':vr.get('validatorVersion'),'errors':issues.get('numErrors'),'warnings':issues.get('numWarnings'),'evidenceSha256':sha(ev/'khronos-validator.json'),'failures':vf},'boundedProfileFacts':{'status':'PASS' if not pf else 'FAIL','info':{k:info.get(k) for k in [*expected_info,'totalVertexCount','totalTriangleCount']},'failures':pf},'assimpScene':{'status':'PASS' if not af else 'FAIL','facts':ai,'evidenceSha256':sha(ev/'assimp-info.txt'),'failures':af},'blenderImport':{'status':'PASS' if not bf else 'FAIL','facts':bi,'stdoutSha256':sha(ev/'blender.stdout.txt'),'stderrSha256':sha(ev/'blender.stderr.txt'),'failures':bf},'status':'PASS' if not failures else 'FAIL','failures':failures,'boundary':'PASS is bounded to a static unmaterialed/untextured/unanimated GLB 2.0 triangle-mesh scene under one exact object contract. It establishes Khronos validator acceptance, bounded feature facts, Assimp source-coordinate topology/bounds and Blender independent import topology. It does not establish artistic quality, materials/textures/animation/skinning behavior, CAD/BIM semantics, or cross-renderer pixel equivalence.'})
 (ev/'verification.json').write_text(json.dumps(res,indent=2,sort_keys=True,ensure_ascii=False)+'\n'); return res

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('input',type=Path); ap.add_argument('--contract',type=Path,required=True); ap.add_argument('--evidence-directory',type=Path); ap.add_argument('--output',type=Path); a=ap.parse_args(); v=verify_glb(a.input,a.contract,a.evidence_directory); s=json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n'; (a.output.write_text(s) if a.output else print(s,end='')); return 0 if v.get('status')=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())
