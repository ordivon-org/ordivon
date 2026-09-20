import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];SPEC=importlib.util.spec_from_file_location('am',ROOT/'scripts/artifact_message.py');M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M);BASE=ROOT/'artifact-delivery/shadow-contracts/message-internet-text-smoke-r1.json'
def raw(*,subject='Ordivon message R1',body='ordivon-message-r1 body',eol='\r\n',extra='',ctype='text/plain; charset=utf-8'):
 lines=['Date: Sat, 12 Sep 2026 10:00:00 +0000','From: Alice Example <alice@example.invalid>','To: Bob Example <bob@example.invalid>',f'Subject: {subject}','Message-ID: <ordivon-message-r1@example.invalid>','MIME-Version: 1.0',f'Content-Type: {ctype}','Content-Transfer-Encoding: 8bit']
 if extra:lines.append(extra)
 return (eol.join(lines)+eol+eol+body+eol).encode()
class T(unittest.TestCase):
 def runv(self,b,c=None):
  d=tempfile.TemporaryDirectory();r=Path(d.name);p=r/'m.eml';p.write_bytes(b);cp=BASE if c is None else r/'c.json';
  if c is not None:cp.write_text(json.dumps(c))
  v=M.verify_message(p,cp,r/'e');d.cleanup();return v
 def test_valid(self):self.assertEqual(self.runv(raw())['status'],'PASS')
 def test_wrong_subject_contract(self):
  c=json.loads(BASE.read_text());c['message']['subject']='Wrong';v=self.runv(raw(),c);self.assertEqual(v['status'],'FAIL');self.assertEqual(v['crossView']['status'],'PASS')
 def test_lf_only_parseable_but_raw_policy_fail(self):
  v=self.runv(raw(eol='\n'));self.assertEqual(v['status'],'FAIL');self.assertIn('message contains bare LF',v['failures'])
 def test_duplicate_message_id_fails_raw_policy(self):
  v=self.runv(raw(extra='Message-ID: <duplicate@example.invalid>'));self.assertEqual(v['status'],'FAIL');self.assertIn('R1 requires exactly one Message-ID header',v['failures'])
 def test_multipart_valid_message_outside_profile(self):
  b=(b'Date: Sat, 12 Sep 2026 10:00:00 +0000\r\nFrom: Alice Example <alice@example.invalid>\r\nTo: Bob Example <bob@example.invalid>\r\nSubject: Ordivon message R1\r\nMessage-ID: <ordivon-message-r1@example.invalid>\r\nMIME-Version: 1.0\r\nContent-Type: multipart/mixed; boundary="x"\r\nContent-Transfer-Encoding: 8bit\r\n\r\n--x\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nordivon-message-r1 body\r\n--x--\r\n');v=self.runv(b);self.assertEqual(v['status'],'FAIL');self.assertTrue(any('multipart' in x.lower() or 'MIME facts' in x for x in v['failures']))
 def test_changed_body_both_parsers_agree_but_contract_fail(self):
  v=self.runv(raw(body='different'));self.assertEqual(v['status'],'FAIL');self.assertEqual(v['crossView']['status'],'PASS');self.assertTrue(any('bodySha256' in x for x in v['failures']))
 def test_html_valid_mime_outside_profile(self):
  v=self.runv(raw(ctype='text/html; charset=utf-8'));self.assertEqual(v['status'],'FAIL');self.assertTrue(any('MIME facts' in x for x in v['failures']))
 def test_binding_digests(self):
  b=json.loads((ROOT/'artifact-delivery/shadow-bindings/message-internet-text-local-r1.json').read_text());py=Path(b['bindings']['pythonParser']['pythonPath']);node=Path(b['bindings']['nodeParser']['nodePath']);self.assertEqual(hashlib.sha256(py.read_bytes()).hexdigest(),b['bindings']['pythonParser']['pythonSha256']);self.assertEqual(hashlib.sha256(node.read_bytes()).hexdigest(),b['bindings']['nodeParser']['nodeSha256']);self.assertEqual(hashlib.sha256(Path('/opt/ordivon/external/mailparser-js/3.9.26/package-lock.json').read_bytes()).hexdigest(),b['bindings']['nodeParser']['packageLockSha256'])
if __name__=='__main__':unittest.main()
