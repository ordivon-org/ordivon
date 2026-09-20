import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('artifact_software_release_elf',ROOT/'scripts/artifact_software_release_elf.py')
M=importlib.util.module_from_spec(SPEC);assert SPEC.loader;SPEC.loader.exec_module(M)
FIXTURE=Path('/usr/bin/printf')

def contract(path:Path, *, marker='ELF_RELEASE_TEST_MARKER', interpreter='/lib64/ld-linux-x86-64.so.2'):
 return {'contractVersion':1,'id':'test-linux-elf-release','profileId':'software-release-linux-elf-executable-r1','artifact':{'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'byteLength':path.stat().st_size,'executable':True},'fileInspection':{'requiredSubstrings':['ELF 64-bit LSB','x86-64']},'elf':{'class':'ELF64','data':"2's complement, little endian",'osAbi':'UNIX - System V','type':'DYN (Position-Independent Executable file)','machine':'Advanced Micro Devices X86-64','interpreter':interpreter},'runtime':{'args':[marker+'\n'],'exitCode':0,'stdoutContains':[marker],'stderrExact':'','timeoutSeconds':10}}

class LinuxElfReleaseTests(unittest.TestCase):
 def require(self):
  for p in (FIXTURE,M.FILE,M.READELF,M.BWRAP):
   if not p.is_file():self.skipTest(str(p))
 def write_contract(self,root:Path,c):
  p=root/'contract.json';p.write_text(json.dumps(c));return p
 def test_binding_digests(self):
  b=json.loads((ROOT/'artifact-delivery/shadow-bindings/software-release-linux-elf-executable-local-r1.json').read_text())
  self.assertEqual(b['status'],'LOCAL_LIVE_PROVEN')
  for key,path in [('formatInspection','/usr/bin/file'),('elfInspection','/usr/bin/readelf'),('runtimeReadback','/usr/bin/bwrap')]:
   self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(),b['bindings'][key]['binarySha256'])
 def test_valid_linux_elf_passes(self):
  self.require()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);c=contract(FIXTURE);v=M.verify_linux_elf(FIXTURE,self.write_contract(r,c),r/'e');self.assertEqual(v['status'],'PASS',v);self.assertEqual(v['runtimeReadback']['networkNamespace'],'unshared')
 def test_wrong_sha_fails_before_external_tools(self):
  self.require()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);c=contract(FIXTURE);c['artifact']['sha256']='0'*64;v=M.verify_linux_elf(FIXTURE,self.write_contract(r,c),r/'e');self.assertEqual(v['status'],'FAIL');self.assertIn('release SHA-256 differs from contract',v['failures']);self.assertNotIn('fileInspection',v)
 def test_wrong_interpreter_fails_structure(self):
  self.require()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);c=contract(FIXTURE,interpreter='/wrong/ld.so');v=M.verify_linux_elf(FIXTURE,self.write_contract(r,c),r/'e');self.assertEqual(v['status'],'FAIL');self.assertIn('ELF interpreter differs from contract',v['failures']);self.assertNotIn('runtimeReadback',v)
 def test_missing_runtime_marker_fails_after_elf_passes(self):
  self.require()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);c=contract(FIXTURE,marker='ACTUAL_MARKER');c['runtime']['stdoutContains']=['NEVER_EMITTED'];v=M.verify_linux_elf(FIXTURE,self.write_contract(r,c),r/'e');self.assertEqual(v['status'],'FAIL');self.assertEqual(v['elfStructure']['status'],'PASS');self.assertIn('sandbox runtime stdout missing marker: NEVER_EMITTED',v['failures'])
 def test_non_elf_bytes_fail_closed(self):
  self.require()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);p=r/'fake';p.write_bytes(b'not an elf\n');p.chmod(0o755);c=contract(p);v=M.verify_linux_elf(p,self.write_contract(r,c),r/'e');self.assertEqual(v['status'],'FAIL');self.assertTrue(v['fileInspection']['status']=='FAIL' or v['elfStructure']['status']=='FAIL')
if __name__=='__main__':unittest.main()
