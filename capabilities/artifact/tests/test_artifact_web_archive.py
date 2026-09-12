import importlib.util,json,tempfile,unittest,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SPEC=importlib.util.spec_from_file_location('awa',ROOT/'scripts/artifact_web_archive.py');M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M);BASE=ROOT/'artifact-delivery/shadow-contracts/web-archive-warc-response-smoke-r1.json'
sys.path.insert(0,'/opt/ordivon/external/warcio-py/1.8.1/site-packages')
from warcio.warcwriter import WARCWriter
from warcio.statusandheaders import StatusAndHeaders
from io import BytesIO
PAY=b'<!doctype html><html><body>ordivon-webarchive-r1</body></html>\n'
def make(path,*,version='WARC/1.1',target='https://example.invalid/archive-r1',date='2026-09-12T10:00:00Z',extra=False):
 with path.open('wb') as f:
  w=WARCWriter(f,gzip=False);w.warc_version=version
  def wr(uri,body,rid):
   h=StatusAndHeaders('200 OK',[('Content-Type','text/html; charset=utf-8'),('Content-Length',str(len(body)))],protocol='HTTP/1.1')
   bio=BytesIO(body)
   try:
    r=w.create_warc_record(uri,'response',payload=bio,http_headers=h,warc_headers_dict={'WARC-Date':date,'WARC-Record-ID':rid})
    try: w.write_record(r)
    finally:
     rs=getattr(r,'raw_stream',None)
     if rs is not None and hasattr(rs,'close'): rs.close()
   finally: bio.close()
  wr(target,PAY,'<urn:uuid:11111111-2222-4333-8444-555555555555>')
  if extra:wr('https://example.invalid/extra',b'extra\n','<urn:uuid:aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee>')
class T(unittest.TestCase):
 def test_valid(self):
  with tempfile.TemporaryDirectory() as d:r=Path(d);p=r/'x.warc';make(p);v=M.verify_warc(p,BASE,r/'e');self.assertEqual(v['status'],'PASS',v)
 def test_wrong_target_contract(self):
  with tempfile.TemporaryDirectory() as d:r=Path(d);p=r/'x.warc';make(p);c=json.loads(BASE.read_text());c['capture']['targetUri']='https://example.invalid/wrong';cp=r/'c.json';cp.write_text(json.dumps(c));v=M.verify_warc(p,cp,r/'e');self.assertEqual(v['status'],'FAIL');self.assertEqual(v['warcIntegrity']['status'],'PASS')
 def test_warc10_valid_but_profile_fail(self):
  with tempfile.TemporaryDirectory() as d:r=Path(d);p=r/'x.warc';make(p,version='WARC/1.0');v=M.verify_warc(p,BASE,r/'e');self.assertEqual(v['status'],'FAIL');self.assertEqual(v['warcIntegrity']['status'],'PASS');self.assertIn('R1 requires WARC/1.1',v['failures'])
 def test_extra_record_valid_but_profile_fail(self):
  with tempfile.TemporaryDirectory() as d:r=Path(d);p=r/'x.warc';make(p,extra=True);v=M.verify_warc(p,BASE,r/'e');self.assertEqual(v['status'],'FAIL');self.assertEqual(v['warcIntegrity']['status'],'PASS')
 def test_corrupt_payload_fails_integrity(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);p=r/'x.warc';make(p);b=bytearray(p.read_bytes());needle=b'ordivon-webarchive-r1';i=b.index(needle);b[i]^=1;p.write_bytes(b);v=M.verify_warc(p,BASE,r/'e');self.assertEqual(v['status'],'FAIL');self.assertEqual(v['warcIntegrity']['status'],'FAIL')
 def test_wrong_payload_digest_contract_after_crossview_agreement(self):
  with tempfile.TemporaryDirectory() as d:r=Path(d);p=r/'x.warc';make(p);c=json.loads(BASE.read_text());c['capture']['payloadSha256']='0'*64;cp=r/'c.json';cp.write_text(json.dumps(c));v=M.verify_warc(p,cp,r/'e');self.assertEqual(v['status'],'FAIL');self.assertEqual(v['crossView']['status'],'PASS');self.assertEqual(v['warcIntegrity']['status'],'PASS')
 def test_binding_files(self):
  b=json.loads((ROOT/'artifact-delivery/shadow-bindings/web-archive-warc-response-local-r1.json').read_text());self.assertEqual(hashlib.sha256(Path('/opt/ordivon/external/warcio-py/1.8.1/warcio').read_bytes()).hexdigest(),b['bindings']['pythonWarc']['wrapperSha256']);self.assertEqual(hashlib.sha256(Path('/opt/ordivon/external/warcio-js/2.4.12/package-lock.json').read_bytes()).hexdigest(),b['bindings']['jsWarc']['packageLockSha256'])
if __name__=='__main__':unittest.main()
