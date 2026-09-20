#!/usr/bin/env python3
"""Standards-first bounded GLB 2.0 verifier for explicit Design/3D profiles."""
from __future__ import annotations
import argparse,hashlib,json,os,re,subprocess,tempfile
from pathlib import Path
from typing import Any
import jsonschema
ROOT=Path(__file__).resolve().parents[1]
VALIDATOR=Path(os.environ.get('ARTIFACT_GLTF_VALIDATOR','/opt/ordivon/external/gltf-validator/2.0.0-dev.3.10/gltf-validator'))
ASSIMP=Path(os.environ.get('ARTIFACT_ASSIMP','/usr/bin/assimp'))
BLENDER=Path(os.environ.get('ARTIFACT_BLENDER','/usr/bin/blender'))
GODOT=Path(os.environ.get('ARTIFACT_GODOT','/usr/bin/godot'))
PROFILE_SPECS={
 'design-3d-glb-static-mesh-r1':{
  'schema':'artifact-delivery/shadow-contracts/design-3d-glb-contract-v1.schema.json','godot':False,
  'boundary':'PASS is bounded to a static unmaterialed/untextured/unanimated GLB 2.0 triangle-mesh scene under one exact object contract. It establishes Khronos validator acceptance, bounded feature facts, Assimp source-coordinate topology/bounds and Blender independent import topology. It does not establish artistic quality, materials/textures/animation/skinning behavior, CAD/BIM semantics, or cross-renderer pixel equivalence.'},
 'design-3d-glb-material-scene-r1':{
  'schema':'artifact-delivery/shadow-contracts/design-3d-glb-material-scene-contract-v1.schema.json','godot':True,
  'boundary':'PASS is bounded to an untextured, unanimated, unskinned GLB 2.0 material scene under one exact object contract. It establishes Khronos zero-warning conformance plus exact Assimp, Blender and Godot import facts. It does not establish artistic/PBR intent, Game semantics, renderer pixel equivalence, texture/color semantics, animation/skinning behavior, or rights.'},
 'design-3d-glb-skinned-animation-r1':{
  'schema':'artifact-delivery/shadow-contracts/design-3d-glb-skinned-animation-contract-v1.schema.json','godot':True,
  'boundary':'PASS is bounded to an untextured GLB 2.0 skinned-animation scene under one exact object contract. It establishes Khronos zero-warning conformance plus exact Assimp, Blender and Godot import facts for topology, material count, animation identities/count and skeleton size. It does not establish animation meaning, deformation/artistic quality, Game behavior, cross-renderer visual equivalence, or rights.'},
}

def run(a:list[str],timeout=180): return subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout)
def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def floats(text): return [float(x) for x in text.strip('() ').split()]

def validate_contract(c:Any)->tuple[list[str],dict[str,Any]|None]:
 if not isinstance(c,dict): return ['design-3d contract must be an object'],None
 pid=c.get('profileId');spec=PROFILE_SPECS.get(pid)
 if spec is None:return [f'unsupported design-3d profileId: {pid}'],None
 schema=json.loads((ROOT/spec['schema']).read_text())
 failures=[f"design-3d contract schema invalid: {e.message}" for e in sorted(jsonschema.Draft202012Validator(schema).iter_errors(c),key=lambda e:list(e.path))]
 return failures,spec

def parse_assimp(out:str)->dict[str,Any]:
 def one(pat,cast=int,default=None):
  m=re.search(pat,out,re.M);return cast(m.group(1)) if m else default
 mn=re.search(r'^Minimum point\s+\(([^)]+)\)',out,re.M);mx=re.search(r'^Maximum point\s+\(([^)]+)\)',out,re.M)
 return {'nodes':one(r'^Nodes:\s+(\d+)'),'meshes':one(r'^Meshes:\s+(\d+)'),'animations':one(r'^Animations:\s+(\d+)'),'textures':one(r'^Textures \(embed\.\):\s+(\d+)'),'materials':one(r'^Materials:\s+(\d+)'),'cameras':one(r'^Cameras:\s+(\d+)'),'lights':one(r'^Lights:\s+(\d+)'),'vertices':one(r'^Vertices:\s+(\d+)'),'faces':one(r'^Faces:\s+(\d+)'),'bones':one(r'^Bones:\s+(\d+)'),'animationChannels':one(r'^Animation Channels:\s+(\d+)'),'primitiveTriangles':bool(re.search(r'^Primitive Types:\s+triangles\s*$',out,re.M)),'boundsMin':floats(mn.group(1)) if mn else None,'boundsMax':floats(mx.group(1)) if mx else None}

def blender_probe(path:Path,evidence:Path)->tuple[dict[str,Any],list[str]]:
 script=evidence/'blender-probe.py'
 script.write_text('''import bpy,json,sys\np=sys.argv[-1]\nbpy.ops.wm.read_factory_settings(use_empty=True)\nr=bpy.ops.import_scene.gltf(filepath=p)\nobjs=list(bpy.context.scene.objects);meshes=[o for o in objs if o.type=="MESH"];arms=[o for o in objs if o.type=="ARMATURE"];acts=list(bpy.data.actions)\nx={"result":sorted(r),"objectCount":len(objs),"meshObjectCount":len(meshes),"armatureObjectCount":len(arms),"materialCount":len(bpy.data.materials),"actionCount":len(acts),"armatureBones":[len(o.data.bones) for o in arms],"meshTotals":{"vertices":sum(len(o.data.vertices) for o in meshes),"polygons":sum(len(o.data.polygons) for o in meshes),"materialSlots":sum(len(o.material_slots) for o in meshes)},"actions":sorted(a.name for a in acts)}\nprint("ORDIVON_JSON="+json.dumps(x,sort_keys=True,separators=(",",":")))\n''')
 p=run([str(BLENDER),'--background','--factory-startup','--python',str(script),'--',str(path)],240)
 (evidence/'blender.stdout.txt').write_bytes(p.stdout);(evidence/'blender.stderr.txt').write_bytes(p.stderr)
 m=re.search(rb'^ORDIVON_JSON=(.+)$',p.stdout,re.M)
 if p.returncode or not m:return {},['Blender headless import/probe failed']
 try:return json.loads(m.group(1)),[]
 except Exception:return {},['Blender probe JSON unreadable']

def godot_probe(path:Path,evidence:Path)->tuple[dict[str,Any],list[str]]:
 script=evidence/'godot-probe.gd'
 script.write_text('''extends SceneTree\nfunc _init():\n var p=OS.get_cmdline_user_args()[0]\n var doc=GLTFDocument.new();var state=GLTFState.new();var err=doc.append_from_file(p,state)\n var out={"appendError":err,"classes":{},"animations":0,"animationNames":[],"skeletonBones":[]}\n if err==OK:\n  var root=doc.generate_scene(state);var stack=[root]\n  while stack.size()>0:\n   var n=stack.pop_back();out.classes[n.get_class()]=int(out.classes.get(n.get_class(),0))+1\n   if n is AnimationPlayer:\n    for libname in n.get_animation_library_list():\n     var lib=n.get_animation_library(libname)\n     for aname in lib.get_animation_list():out.animationNames.append(String(aname));out.animations+=1\n   if n is Skeleton3D:out.skeletonBones.append(n.get_bone_count())\n   for c in n.get_children():stack.append(c)\n out.animationNames.sort();out.skeletonBones.sort()\n print("ORDIVON_JSON="+JSON.stringify(out));quit(0 if err==OK else 2)\n''')
 p=run([str(GODOT),'--headless','--path',str(evidence),'--script',str(script),'--',str(path.resolve())],120)
 (evidence/'godot.stdout.txt').write_bytes(p.stdout);(evidence/'godot.stderr.txt').write_bytes(p.stderr)
 m=re.search(rb'^ORDIVON_JSON=(.+)$',p.stdout,re.M)
 if p.returncode or not m:return {},['Godot GLTFDocument import/probe failed']
 try:return json.loads(m.group(1)),[]
 except Exception:return {},['Godot probe JSON unreadable']

def eq(prefix:str,got:Any,want:Any,failures:list[str],tol:float|None=None)->None:
 if tol is not None and isinstance(got,list) and isinstance(want,list) and len(got)==len(want):
  if any(abs(float(a)-float(b))>tol for a,b in zip(got,want)):failures.append(f'{prefix} differs from contract')
 elif got!=want:failures.append(f'{prefix} differs from contract')

def verify_glb(path:Path,contract_path:Path,evidence_dir:Path|None=None)->dict[str,Any]:
 fallback_pid='UNKNOWN'
 if not path.is_file():return {'schemaVersion':1,'kind':'artifact-design3d-verification','profileId':fallback_pid,'status':'FAIL','failures':['input is not a regular file']}
 try:c=json.loads(contract_path.read_text());fallback_pid=c.get('profileId','UNKNOWN') if isinstance(c,dict) else 'UNKNOWN'
 except Exception as e:return {'schemaVersion':1,'kind':'artifact-design3d-verification','profileId':fallback_pid,'status':'FAIL','failures':[f'contract unreadable: {e}']}
 failures,spec=validate_contract(c);pid=fallback_pid;ev=evidence_dir or Path(tempfile.mkdtemp(prefix='artifact-design3d-evidence-'));ev.mkdir(parents=True,exist_ok=True)
 res={'schemaVersion':1,'kind':'artifact-design3d-verification','profileId':pid,'status':'FAIL','artifact':{'path':str(path.resolve()),'size':path.stat().st_size,'sha256':sha(path)},'contract':{'sha256':sha(contract_path),'canonicalDigest':canonical(c)},'failures':failures,'tools':{}}
 if failures or spec is None:(ev/'verification.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');return res
 required=[('validator',VALIDATOR),('assimp',ASSIMP),('blender',BLENDER)]+([('godot',GODOT)] if spec['godot'] else [])
 for n,p in required:
  if not p.is_file() or not os.access(p,os.X_OK):failures.append(f'required mature external capability unavailable: {n}')
  else:res['tools'][n]={'path':str(p.resolve()),'sha256':sha(p)}
 if failures:res['failures']=failures;(ev/'verification.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');return res
 v=run([str(VALIDATOR),str(path)]);(ev/'khronos-validator.json').write_bytes(v.stdout if v.stdout else v.stderr)
 try:vr=json.loads(v.stdout) if v.stdout else {}
 except Exception:vr={}
 issues=vr.get('issues') or {};info=vr.get('info') or {};vf=[]
 if v.returncode!=0 or issues.get('numErrors')!=0:vf.append('Khronos glTF Validator reports errors')
 if issues.get('numWarnings')!=0:vf.append('profile requires zero Khronos validator warnings')
 if vr.get('mimeType')!='model/gltf-binary' or info.get('version')!='2.0':vf.append('artifact is not GLB/glTF 2.0')
 pf=[]
 if pid=='design-3d-glb-static-mesh-r1':
  want=c['scene'];expected={'animationCount':0,'materialCount':0,'hasMorphTargets':False,'hasSkins':False,'hasTextures':False,'hasDefaultScene':True,'drawCallCount':1}
  for k,w in expected.items():
   if info.get(k)!=w:pf.append(f'bounded profile fact differs: {k}')
  eq('validator vertex count',info.get('totalVertexCount'),want['vertexCount'],pf);eq('validator triangle count',info.get('totalTriangleCount'),want['triangleCount'],pf)
 else:
  want=c['validator']
  mapping={'vertexCount':'totalVertexCount','triangleCount':'totalTriangleCount'}
  for k,w in want.items():eq(f'validator {k}',info.get(mapping.get(k,k)),w,pf)
 failures.extend(vf+pf)
 a=run([str(ASSIMP),'info',str(path)]);aout=a.stdout.decode('utf-8','replace');(ev/'assimp-info.txt').write_text(aout+a.stderr.decode('utf-8','replace'));af=[];ai=parse_assimp(aout) if a.returncode==0 else {}
 if a.returncode!=0:af.append('Assimp import failed')
 if pid=='design-3d-glb-static-mesh-r1':
  want=c['scene'];checks={'nodes':'nodeCount','meshes':'meshCount','vertices':'vertexCount','faces':'triangleCount'}
  for gk,wk in checks.items():eq(f'Assimp {gk}',ai.get(gk),want[wk],af)
  if not ai.get('primitiveTriangles'):af.append('Assimp primitive type is not triangles')
  for k in ('animations','textures','bones','cameras','lights'):eq(f'Assimp {k}',ai.get(k),0,af)
  for label in ('boundsMin','boundsMax'):eq(f'Assimp {label}',ai.get(label),want[label],af,1e-6)
 else:
  want=c['assimp'];mapping={'nodeCount':'nodes','meshCount':'meshes','animationCount':'animations','textureCount':'textures','materialCount':'materials','cameraCount':'cameras','lightCount':'lights','vertexCount':'vertices','triangleCount':'faces','boneCount':'bones','animationChannelCount':'animationChannels','primitiveTriangles':'primitiveTriangles'}
  for wk,gk in mapping.items():eq(f'Assimp {wk}',ai.get(gk),want[wk],af)
  for label in ('boundsMin','boundsMax'):eq(f'Assimp {label}',ai.get(label),want[label],af,1e-6)
 failures.extend(af)
 bi,bf=blender_probe(path,ev)
 if not bf:
  if bi.get('result')!=['FINISHED']:bf.append('Blender importer did not finish')
  if pid=='design-3d-glb-static-mesh-r1':
   want=c['scene'];eq('Blender meshObjectCount',bi.get('meshObjectCount'),1,bf);eq('Blender objectCount',bi.get('objectCount'),1,bf);eq('Blender materialCount',bi.get('materialCount'),0,bf);eq('Blender actionCount',bi.get('actionCount'),0,bf);eq('Blender armatureObjectCount',bi.get('armatureObjectCount'),0,bf);eq('Blender vertices',(bi.get('meshTotals') or {}).get('vertices'),want['vertexCount'],bf);eq('Blender polygons',(bi.get('meshTotals') or {}).get('polygons'),want['triangleCount'],bf)
  else:
   want=c['blender']
   for k in ('objectCount','meshObjectCount','armatureObjectCount','materialCount','actionCount','armatureBones','actions'):eq(f'Blender {k}',bi.get(k),want[k],bf)
   for k in ('vertices','polygons','materialSlots'):eq(f'Blender meshTotals.{k}',(bi.get('meshTotals') or {}).get(k),want['meshTotals'][k],bf)
 failures.extend(bf)
 gi={};gf=[]
 if spec['godot']:
  gi,gf=godot_probe(path,ev)
  if not gf:
   want=c['godot'];eq('Godot appendError',gi.get('appendError'),0,gf);eq('Godot classes',gi.get('classes'),want['classes'],gf);eq('Godot animations',gi.get('animations'),want['animations'],gf);eq('Godot animationNames',gi.get('animationNames'),want['animationNames'],gf);eq('Godot skeletonBones',gi.get('skeletonBones'),want['skeletonBones'],gf)
  failures.extend(gf)
 result={'khronosConformance':{'status':'PASS' if not vf else 'FAIL','validatorVersion':vr.get('validatorVersion'),'errors':issues.get('numErrors'),'warnings':issues.get('numWarnings'),'evidenceSha256':sha(ev/'khronos-validator.json'),'failures':vf},'boundedProfileFacts':{'status':'PASS' if not pf else 'FAIL','info':info,'failures':pf},'assimpScene':{'status':'PASS' if not af else 'FAIL','facts':ai,'evidenceSha256':sha(ev/'assimp-info.txt'),'failures':af},'blenderImport':{'status':'PASS' if not bf else 'FAIL','facts':bi,'stdoutSha256':sha(ev/'blender.stdout.txt'),'stderrSha256':sha(ev/'blender.stderr.txt'),'failures':bf}}
 if spec['godot']:result['godotImport']={'status':'PASS' if not gf else 'FAIL','facts':gi,'stdoutSha256':sha(ev/'godot.stdout.txt'),'stderrSha256':sha(ev/'godot.stderr.txt'),'failures':gf}
 res.update(result);res.update({'status':'PASS' if not failures else 'FAIL','failures':failures,'boundary':spec['boundary']});(ev/'verification.json').write_text(json.dumps(res,indent=2,sort_keys=True,ensure_ascii=False)+'\n');return res

def main():
 ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('--contract',type=Path,required=True);ap.add_argument('--evidence-directory',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args();v=verify_glb(a.input,a.contract,a.evidence_directory);s=json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n';(a.output.write_text(s) if a.output else print(s,end=''));return 0 if v.get('status')=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
