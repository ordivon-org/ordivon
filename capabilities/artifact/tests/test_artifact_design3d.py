import pytest
import hashlib,importlib.util,json,struct,tempfile,unittest
from pathlib import Path
pytestmark = pytest.mark.integration

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('artifact_design3d',ROOT/'scripts/artifact_design3d.py'); MODULE=importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(MODULE)
BASE=ROOT/'artifact-delivery/shadow-contracts/design-3d-glb-static-mesh-smoke-r1.json'

def glb(path:Path, *, material=False, wrong_declared_max=False, extra_node=False):
 b=struct.pack('<9f3H',0,0,0,1,0,0,0,1,0,0,1,2); b+=b'\0'*((-len(b))%4)
 maxv=[2,2,0] if wrong_declared_max else [1,1,0]
 g={'asset':{'version':'2.0'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0}],'meshes':[{'primitives':[{'attributes':{'POSITION':0},'indices':1,'mode':4}]}],'buffers':[{'byteLength':42}],'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':36,'target':34962},{'buffer':0,'byteOffset':36,'byteLength':6,'target':34963}],'accessors':[{'bufferView':0,'componentType':5126,'count':3,'type':'VEC3','min':[0,0,0],'max':maxv},{'bufferView':1,'componentType':5123,'count':3,'type':'SCALAR','min':[0],'max':[2]}]}
 if material: g['materials']=[{}]; g['meshes'][0]['primitives'][0]['material']=0
 if extra_node: g['nodes'].append({}); g['scenes'][0]['nodes'].append(1)
 j=json.dumps(g,separators=(',',':'),sort_keys=True).encode(); j+=b' '*((-len(j))%4); total=12+8+len(j)+8+len(b)
 with path.open('wb') as f: f.write(struct.pack('<4sII',b'glTF',2,total)); f.write(struct.pack('<I4s',len(j),b'JSON')); f.write(j); f.write(struct.pack('<I4s',len(b),b'BIN\0')); f.write(b)

class Design3DTests(unittest.TestCase):
 def req(self):
  for p in (MODULE.VALIDATOR,MODULE.ASSIMP,MODULE.BLENDER):
   if not p.is_file(): self.skipTest(str(p))
 def test_binding_digests(self):
  b=json.loads((ROOT/'artifact-delivery/shadow-bindings/design-3d-glb-static-mesh-local-r1.json').read_text())
  self.assertEqual(hashlib.sha256(Path('/usr/bin/assimp').read_bytes()).hexdigest(),b['bindings']['independentConsumerA']['binarySha256'])
  self.assertEqual(hashlib.sha256(Path('/usr/bin/blender').read_bytes()).hexdigest(),b['bindings']['independentConsumerB']['binarySha256'])
  self.assertEqual(hashlib.sha256(Path('/opt/ordivon/external/gltf-validator/2.0.0-dev.3.10/validate.mjs').read_bytes()).hexdigest(),b['bindings']['standardValidator']['moduleWrapperSha256'])
  install=json.loads(Path('/opt/ordivon/external/gltf-validator/2.0.0-dev.3.10/ORDIVON-INSTALL.json').read_text())
  self.assertEqual(install['packageArchiveSha256'],b['bindings']['standardValidator']['packageArchiveSha256'])
 def test_rich_profile_binding_tool_digests(self):
  for name in ('design-3d-glb-material-scene-local-r1.json','design-3d-glb-skinned-animation-local-r1.json'):
   b=json.loads((ROOT/'artifact-delivery/shadow-bindings'/name).read_text())
   self.assertEqual(b['status'],'LOCAL_LIVE_PROVEN')
   self.assertEqual(hashlib.sha256(Path('/usr/bin/assimp').read_bytes()).hexdigest(),b['bindings']['independentConsumerA']['binarySha256'])
   self.assertEqual(hashlib.sha256(Path('/usr/bin/blender').read_bytes()).hexdigest(),b['bindings']['independentConsumerB']['binarySha256'])
   self.assertEqual(hashlib.sha256(Path('/usr/bin/godot').read_bytes()).hexdigest(),b['bindings']['targetConsumer']['binarySha256'])
   self.assertTrue(b['proof']['khronosZeroErrorsWarnings'])

 def test_valid_triangle_passes(self):
  self.req()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d); p=r/'x.glb'; glb(p); v=MODULE.verify_glb(p,BASE,r/'e'); self.assertEqual(v['status'],'PASS',v)
 def test_valid_glb_wrong_bounds_contract_fails(self):
  self.req()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d); p=r/'x.glb'; glb(p); c=json.loads(BASE.read_text()); c['scene']['boundsMax']=[2,2,0]; cp=r/'c.json'; cp.write_text(json.dumps(c)); v=MODULE.verify_glb(p,cp,r/'e'); self.assertEqual(v['status'],'FAIL'); self.assertEqual(v['khronosConformance']['status'],'PASS'); self.assertIn('Assimp boundsMax differs from contract',v['failures'])
 def test_material_is_valid_gltf_but_outside_profile(self):
  self.req()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d); p=r/'x.glb'; glb(p,material=True); v=MODULE.verify_glb(p,BASE,r/'e'); self.assertEqual(v['status'],'FAIL'); self.assertEqual(v['khronosConformance']['status'],'PASS'); self.assertIn('bounded profile fact differs: materialCount',v['failures'])
 def test_accessor_declared_bounds_mismatch_fails_khronos(self):
  self.req()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d); p=r/'x.glb'; glb(p,wrong_declared_max=True); v=MODULE.verify_glb(p,BASE,r/'e'); self.assertEqual(v['status'],'FAIL'); self.assertEqual(v['khronosConformance']['status'],'FAIL')
 def test_extra_node_is_valid_but_contract_fails_assimp(self):
  self.req()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d); p=r/'x.glb'; glb(p,extra_node=True); v=MODULE.verify_glb(p,BASE,r/'e'); self.assertEqual(v['status'],'FAIL'); self.assertEqual(v['khronosConformance']['status'],'PASS'); self.assertIn('Assimp nodes differs from contract',v['failures'])
 def test_corrupt_header_fails_closed(self):
  self.req()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d); p=r/'x.glb'; glb(p); b=bytearray(p.read_bytes()); b[0]^=0x10; p.write_bytes(b); v=MODULE.verify_glb(p,BASE,r/'e'); self.assertEqual(v['status'],'FAIL'); self.assertEqual(v['khronosConformance']['status'],'FAIL')
if __name__=='__main__': unittest.main()
