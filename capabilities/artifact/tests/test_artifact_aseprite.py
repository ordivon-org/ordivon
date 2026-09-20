import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT=Path(__file__).resolve().parents[1];SPEC=importlib.util.spec_from_file_location('artifact_aseprite',ROOT/'scripts/artifact_aseprite.py');M=importlib.util.module_from_spec(SPEC);assert SPEC.loader;SPEC.loader.exec_module(M)
def make_source(root:Path):
 png=root/'input.png';im=Image.new('RGBA',(8,8),(0,0,0,0));im.putpixel((2,2),(255,0,0,255));im.putpixel((3,2),(0,255,0,255));im.save(png);src=root/'source.aseprite';p=subprocess.run([str(M.ASEPRITE),'-b',str(png),'--save-as',str(src)],capture_output=True);assert p.returncode==0,p.stderr.decode();return src
def export_expected(root:Path,src:Path):
 sheet=root/'sheet.png';data=root/'sheet.json';p=subprocess.run([str(M.ASEPRITE),'-b','--list-tags',str(src),'--sheet-type','horizontal','--format','json-array','--sheet',str(sheet),'--data',str(data)],capture_output=True);assert p.returncode==0,p.stderr.decode();meta=json.loads(data.read_text());return {'sheetType':'horizontal','dataFormat':'json-array','listTags':True,'sheetBasename':'sheet.png','dataBasename':'sheet.json','width':meta['meta']['size']['w'],'height':meta['meta']['size']['h'],'frameCount':len(meta['frames']),'expectedPngSha256':hashlib.sha256(sheet.read_bytes()).hexdigest(),'expectedNativeMetadataSha256':hashlib.sha256(data.read_bytes()).hexdigest()}
def contract(root:Path,export):
 p=root/'contract.json';p.write_text(json.dumps({'contractVersion':1,'id':'aseprite-smoke-r1','profileId':'design-2d-aseprite-horizontal-sheet-r1','export':export}));return p
class ArtifactAsepriteTests(unittest.TestCase):
 def req(self):
  if not M.ASEPRITE.is_file():self.skipTest(str(M.ASEPRITE))
 def test_native_source_export_is_byte_deterministic_and_png_profile_passes(self):
  self.req()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);src=make_source(r);want=export_expected(r,src);c=contract(r,want);v=M.verify_aseprite(src,c,r/'e');self.assertEqual(v['status'],'PASS',v);self.assertTrue(v['nativeDeterministicExport']['pngExactAcrossRuns']);self.assertTrue(v['nativeDeterministicExport']['metadataExactAcrossRuns']);self.assertEqual(v['derivedStillImageProfile']['status'],'PASS')
 def test_wrong_png_digest_fails_identity(self):
  self.req()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);src=make_source(r);want=export_expected(r,src);want['expectedPngSha256']='0'*64;c=contract(r,want);v=M.verify_aseprite(src,c,r/'e');self.assertEqual(v['status'],'FAIL');self.assertEqual(v['derivativeIdentity']['status'],'FAIL')
 def test_wrong_native_metadata_digest_fails_identity(self):
  self.req()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);src=make_source(r);want=export_expected(r,src);want['expectedNativeMetadataSha256']='0'*64;c=contract(r,want);v=M.verify_aseprite(src,c,r/'e');self.assertEqual(v['status'],'FAIL');self.assertEqual(v['derivativeIdentity']['status'],'FAIL')
 def test_wrong_frame_count_fails_native_facts(self):
  self.req()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);src=make_source(r);want=export_expected(r,src);want['frameCount']+=1;c=contract(r,want);v=M.verify_aseprite(src,c,r/'e');self.assertEqual(v['status'],'FAIL');self.assertEqual(v['nativeMetadataFacts']['status'],'FAIL')
 def test_invalid_source_fails_native_export(self):
  self.req()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);src=r/'bad.aseprite';src.write_bytes(b'not aseprite');want={'sheetType':'horizontal','dataFormat':'json-array','listTags':True,'sheetBasename':'sheet.png','dataBasename':'sheet.json','width':8,'height':8,'frameCount':1,'expectedPngSha256':'0'*64,'expectedNativeMetadataSha256':'0'*64};c=contract(r,want);v=M.verify_aseprite(src,c,r/'e');self.assertEqual(v['status'],'FAIL');self.assertEqual(v['nativeDeterministicExport']['status'],'FAIL')
if __name__=='__main__':unittest.main()
