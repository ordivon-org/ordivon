#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,os,re,subprocess,tempfile
from datetime import timezone
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from pathlib import Path
import jsonschema
ROOT=Path(__file__).resolve().parents[1]
SCHEMA=ROOT/'artifact-delivery/shadow-contracts/message-internet-text-contract-v1.schema.json'
NODE=Path(os.environ.get('ARTIFACT_NODE','/root/.local/share/mise/installs/node/26.9.0/bin/node')); MAILPARSER=Path('/opt/ordivon/external/mailparser-js/3.9.26/node_modules/mailparser')
REQ=['Date','From','To','Subject','Message-ID','MIME-Version','Content-Type','Content-Transfer-Encoding']
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha_file(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canon(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def validate(c):
 s=json.loads(SCHEMA.read_text());return [f"message contract schema invalid: {e.message}" for e in sorted(jsonschema.Draft202012Validator(s,format_checker=jsonschema.FormatChecker()).iter_errors(c),key=lambda e:list(e.path))]
def norm_date(v):return parsedate_to_datetime(v).astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def py_view(raw):
 try:
  m=BytesParser(policy=policy.default).parsebytes(raw)
  def addrs(h):return [{'name':a.display_name or '', 'address':a.addr_spec} for a in h.addresses] if h else []
  body=m.get_content() if not m.is_multipart() else None
  canonical_body=body.replace('\r\n','\n').replace('\r','\n') if isinstance(body,str) else None
  return {'defects':[type(x).__name__ for x in m.defects],'from':addrs(m['From']),'to':addrs(m['To']),'subject':str(m['Subject']) if m['Subject'] is not None else None,'messageId':str(m['Message-ID']) if m['Message-ID'] is not None else None,'date':norm_date(str(m['Date'])) if m['Date'] else None,'contentType':m.get_content_type(),'charset':m.get_content_charset(),'cte':str(m['Content-Transfer-Encoding']) if m['Content-Transfer-Encoding'] else None,'mimeVersion':str(m['MIME-Version']) if m['MIME-Version'] else None,'multipart':m.is_multipart(),'bodySha256':sha_bytes(canonical_body.encode('utf-8')) if isinstance(canonical_body,str) else None},None
 except Exception as e:return {},str(e)
def node_view(path,ev):
 script=ev/'mailparser-view.cjs';script.write_text('''const fs=require("fs"),crypto=require("crypto");const {simpleParser}=require("/opt/ordivon/external/mailparser-js/3.9.26/node_modules/mailparser");(async()=>{const m=await simpleParser(fs.readFileSync(process.argv[2]));const A=x=>(x?.value||[]).map(v=>({name:v.name||"",address:v.address||""}));const ct=m.headers.get("content-type")||{};const iso=m.date?m.date.toISOString():null;const d=iso&&iso.endsWith(".000Z")?iso.slice(0,-5)+"Z":iso;const CR=String.fromCharCode(13),LF=String.fromCharCode(10);const text=(m.text||"").split(CR+LF).join(LF).split(CR).join(LF);console.log(JSON.stringify({from:A(m.from),to:A(m.to),subject:m.subject??null,messageId:m.messageId??null,date:d,contentType:ct.value||null,charset:ct.params?.charset||null,cte:m.headers.get("content-transfer-encoding")||null,mimeVersion:m.headers.get("mime-version")||null,attachments:m.attachments.length,html:!!m.html,bodySha256:crypto.createHash("sha256").update(Buffer.from(text,"utf8")).digest("hex")}));})().catch(e=>{console.error(e);process.exit(1)});''')
 p=subprocess.run([str(NODE),str(script),str(path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=60);(ev/'mailparser.stderr.txt').write_bytes(p.stderr)
 if p.returncode:return {},p.stderr.decode('utf-8','replace')
 try:return json.loads(p.stdout),None
 except Exception as e:return {},str(e)
def verify_message(path,contract_path,evidence_dir=None):
 path=Path(path);contract_path=Path(contract_path)
 if not path.is_file():return {'status':'FAIL','failures':['input is not a regular file']}
 try:c=json.loads(contract_path.read_text())
 except Exception as e:return {'status':'FAIL','failures':[f'contract unreadable: {e}']}
 failures=validate(c);ev=Path(evidence_dir) if evidence_dir else Path(tempfile.mkdtemp(prefix='artifact-message-'));ev.mkdir(parents=True,exist_ok=True);raw=path.read_bytes();res={'schemaVersion':1,'kind':'artifact-message-verification','profileId':'message-internet-text-r1','artifact':{'sha256':sha_bytes(raw),'size':len(raw)},'contract':{'sha256':sha_file(contract_path),'canonicalDigest':canon(c)},'status':'FAIL','failures':failures}
 if failures:(ev/'verification.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');return res
 rf=[]
 if b'\x00' in raw:rf.append('NUL byte outside bounded R1')
 # Every LF must be preceded by CR and every CR must be followed by LF.
 for i,b in enumerate(raw):
  if b==10 and (i==0 or raw[i-1]!=13):rf.append('message contains bare LF');break
 for i,b in enumerate(raw):
  if b==13 and (i+1>=len(raw) or raw[i+1]!=10):rf.append('message contains bare CR');break
 lines=raw.split(b'\r\n')
 if any(len(x)>998 for x in lines):rf.append('physical line exceeds RFC 5322 hard limit 998 characters')
 if b'\r\n\r\n' not in raw:rf.append('missing header/body separator')
 header=raw.split(b'\r\n\r\n',1)[0].decode('utf-8','replace');counts={h:len(re.findall(r'(?im)^'+re.escape(h)+r':',header)) for h in REQ}
 for h in REQ:
  if counts[h]!=1:rf.append(f'R1 requires exactly one {h} header')
 if re.search(r'(?im)^(Cc|Bcc):',header):rf.append('Cc/Bcc outside bounded R1')
 pv,pe=py_view(raw);pf=[]
 if pe:pf.append('Python email parser failed: '+pe)
 if pv:
  if pv['defects']:pf.append('Python email parser reports defects')
  if pv['multipart']:pf.append('multipart message outside bounded R1')
  if pv['contentType']!='text/plain' or (pv['charset'] or '').lower()!='utf-8' or (pv['cte'] or '').lower()!='8bit' or pv['mimeVersion']!='1.0':pf.append('Python MIME facts outside bounded R1')
  if len(pv['from'])!=1 or len(pv['to'])!=1:pf.append('R1 requires one From and one To address')
 nv,ne=node_view(path,ev);nf=[]
 if ne:nf.append('mailparser failed: '+ne)
 if nv:
  if nv['attachments']!=0 or nv['html']:nf.append('mailparser observes attachment/html outside bounded R1')
  if nv['contentType']!='text/plain' or (nv['charset'] or '').lower()!='utf-8' or (nv['cte'] or '').lower()!='8bit' or nv['mimeVersion']!='1.0':nf.append('mailparser MIME facts outside bounded R1')
 want=c['message']
 def contract_facts(v,label):
  fs=[]
  exp={'from':[want['from']],'to':[want['to']],'subject':want['subject'],'messageId':want['messageId'],'date':want['date'],'bodySha256':want['bodySha256']}
  for k,e in exp.items():
   if v.get(k)!=e:fs.append(f'{label} {k} differs from contract')
  return fs
 if pv:pf+=contract_facts(pv,'Python view')
 if nv:nf+=contract_facts(nv,'Node view')
 cross=[]
 if pv and nv:
  for k in ('from','to','subject','messageId','date','contentType','charset','cte','mimeVersion','bodySha256'):
   if pv.get(k)!=nv.get(k):cross.append(f'Python/Node views disagree on {k}')
 failures+=rf+pf+nf+cross
 res.update({'rawSyntaxPolicy':{'status':'PASS' if not rf else 'FAIL','headerCounts':counts,'failures':rf},'pythonParser':{'status':'PASS' if not pf else 'FAIL','view':pv,'failures':pf},'nodeParser':{'status':'PASS' if not nf else 'FAIL','view':nv,'stderrSha256':sha_file(ev/'mailparser.stderr.txt'),'failures':nf},'crossView':{'status':'PASS' if not cross else 'FAIL','failures':cross},'status':'PASS' if not failures else 'FAIL','failures':failures,'boundary':'PASS is bounded to one CRLF-encoded RFC 5322/MIME 1.0 single-part UTF-8 text/plain message with exact address/header/body identity. It does not establish SMTP delivery, sender authentication, DKIM/SPF/DMARC/ARC, mailbox-container semantics, multipart attachments or content truth.'})
 (ev/'verification.json').write_text(json.dumps(res,indent=2,sort_keys=True,ensure_ascii=False)+'\n');return res
def main():
 ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('--contract',type=Path,required=True);ap.add_argument('--evidence-directory',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args();v=verify_message(a.input,a.contract,a.evidence_directory);s=json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n';a.output.write_text(s) if a.output else print(s,end='');return 0 if v.get('status')=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
