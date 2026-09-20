#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,tempfile,sys
from pathlib import Path
from typing import Any
import jsonschema
ROOT=Path(__file__).resolve().parents[1]
SCHEMA=ROOT/'artifact-delivery/shadow-contracts/web-archive-warc-response-contract-v1.schema.json'
WARCIO_ROOT=Path('/opt/ordivon/external/warcio-py/1.8.1')
WARCIO=WARCIO_ROOT/'warcio'
WARCIO_SITE=WARCIO_ROOT/'site-packages'
NODE=Path('/usr/bin/node')
JSROOT=Path('/opt/ordivon/external/warcio-js/2.4.12/node_modules/warcio')

def run(a,env=None,timeout=120): return subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,env=env,timeout=timeout)
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canon(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def validate(c):
 s=json.loads(SCHEMA.read_text()); return [f"web-archive contract schema invalid: {e.message}" for e in sorted(jsonschema.Draft202012Validator(s,format_checker=jsonschema.FormatChecker()).iter_errors(c),key=lambda e:list(e.path))]
def py_view(path:Path):
 sys.path.insert(0,str(WARCIO_SITE))
 try:
  from warcio.archiveiterator import ArchiveIterator
  rows=[]
  with path.open('rb') as f:
   for r in ArchiveIterator(f):
    body=r.content_stream().read(); rows.append({'type':r.rec_type,'targetUri':r.rec_headers.get_header('WARC-Target-URI'),'warcDate':r.rec_headers.get_header('WARC-Date'),'recordId':r.rec_headers.get_header('WARC-Record-ID'),'blockDigest':r.rec_headers.get_header('WARC-Block-Digest'),'payloadDigest':r.rec_headers.get_header('WARC-Payload-Digest'),'httpStatus':int(r.http_headers.get_statuscode()) if r.http_headers else None,'contentType':r.http_headers.get_header('Content-Type') if r.http_headers else None,'payloadSha256':sha_bytes(body)})
  return rows,None
 except Exception as e:return [],str(e)
def js_view(path:Path,ev:Path):
 script=ev/'warcio-js-view.mjs'
 script.write_text('''import fs from "node:fs"; import crypto from "node:crypto"; import { WARCParser } from "/opt/ordivon/external/warcio-js/2.4.12/node_modules/warcio/dist/index.js"; const rows=[]; for await (const r of new WARCParser(fs.createReadStream(process.argv[2]))) { const body=await r.readFully(true); const ri=r.getResponseInfo(); rows.push({type:r.warcType,targetUri:r.warcTargetURI,warcDate:r.warcDate,recordId:r.warcHeader("WARC-Record-ID"),blockDigest:r.warcHeader("WARC-Block-Digest"),payloadDigest:r.warcHeader("WARC-Payload-Digest"),httpStatus:ri?.status??null,contentType:ri?.headers?.get("Content-Type")??null,payloadSha256:crypto.createHash("sha256").update(Buffer.from(body)).digest("hex")}); } console.log(JSON.stringify(rows));''')
 p=run([str(NODE),str(script),str(path)]); (ev/'warcio-js.stderr.txt').write_bytes(p.stderr)
 if p.returncode:return [],p.stderr.decode('utf-8','replace')
 try:return json.loads(p.stdout),None
 except Exception as e:return [],str(e)
def verify_warc(path:Path,contract_path:Path,evidence_dir:Path|None=None):
 if not path.is_file(): return {'status':'FAIL','failures':['input is not a regular file']}
 try:c=json.loads(contract_path.read_text())
 except Exception as e:return {'status':'FAIL','failures':[f'contract unreadable: {e}']}
 failures=validate(c); ev=evidence_dir or Path(tempfile.mkdtemp(prefix='artifact-webarchive-')); ev.mkdir(parents=True,exist_ok=True)
 res={'schemaVersion':1,'kind':'artifact-web-archive-verification','profileId':'web-archive-warc-response-r1','artifact':{'sha256':sha_file(path),'size':path.stat().st_size},'contract':{'sha256':sha_file(contract_path),'canonicalDigest':canon(c)},'status':'FAIL','failures':failures}
 if failures:(ev/'verification.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');return res
 with path.open('rb') as fh:
  first=fh.readline().rstrip(b'\r\n').decode('ascii','replace')
 version_fail=[]
 if first!='WARC/1.1':version_fail.append('R1 requires WARC/1.1')
 check=run([str(WARCIO),'check',str(path)]); (ev/'warcio-check.txt').write_bytes(check.stdout+check.stderr); integrity_fail=[]
 if check.returncode!=0:integrity_fail.append('warcio digest/integrity check failed')
 py,pe=py_view(path); js,je=js_view(path,ev); pyfail=[]; jsfail=[]
 if pe:pyfail.append('warcio Python parser failed: '+pe)
 if je:jsfail.append('warcio.js parser failed: '+je)
 if len(py)!=1:pyfail.append('R1 requires exactly one Python-parsed WARC record')
 if len(js)!=1:jsfail.append('R1 requires exactly one JS-parsed WARC record')
 want=c['capture']
 def cmp(row,label):
  fs=[]
  if not row:return fs
  expected={'type':'response','targetUri':want['targetUri'],'warcDate':want['warcDate'],'recordId':want['recordId'],'httpStatus':want['httpStatus'],'contentType':want['contentType'],'payloadSha256':want['payloadSha256']}
  for k,v in expected.items():
   if row.get(k)!=v:fs.append(f'{label} {k} differs from contract')
  if not row.get('blockDigest') or not row.get('payloadDigest'):fs.append(f'{label} missing required WARC digests')
  return fs
 if len(py)==1:pyfail+=cmp(py[0],'Python view')
 if len(js)==1:jsfail+=cmp(js[0],'JS view')
 cross=[]
 if len(py)==1 and len(js)==1:
  for k in ('type','targetUri','warcDate','recordId','blockDigest','payloadDigest','httpStatus','contentType','payloadSha256'):
   if py[0].get(k)!=js[0].get(k):cross.append(f'Python/JS views disagree on {k}')
 failures+=version_fail+integrity_fail+pyfail+jsfail+cross
 res.update({'warcVersion':{'status':'PASS' if not version_fail else 'FAIL','observed':first,'failures':version_fail},'warcIntegrity':{'status':'PASS' if not integrity_fail else 'FAIL','returnCode':check.returncode,'evidenceSha256':sha_file(ev/'warcio-check.txt'),'failures':integrity_fail},'pythonRecordView':{'status':'PASS' if not pyfail else 'FAIL','records':py,'failures':pyfail},'jsRecordView':{'status':'PASS' if not jsfail else 'FAIL','records':js,'stderrSha256':sha_file(ev/'warcio-js.stderr.txt'),'failures':jsfail},'crossView':{'status':'PASS' if not cross else 'FAIL','failures':cross},'status':'PASS' if not failures else 'FAIL','failures':failures,'boundary':'PASS is bounded to one WARC/1.1 HTTP response record with exact capture metadata and payload identity. It does not establish complete-site capture, browser state, dependency completeness or replay fidelity.'})
 (ev/'verification.json').write_text(json.dumps(res,indent=2,sort_keys=True,ensure_ascii=False)+'\n');return res

def main():
 ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('--contract',type=Path,required=True);ap.add_argument('--evidence-directory',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args();v=verify_warc(a.input,a.contract,a.evidence_directory);s=json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n';a.output.write_text(s) if a.output else print(s,end='');return 0 if v.get('status')=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
