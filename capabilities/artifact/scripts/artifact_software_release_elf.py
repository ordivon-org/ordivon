#!/usr/bin/env python3
"""Bounded Linux ELF release verifier: exact bytes, ELF facts, and network-isolated runtime readback."""
from __future__ import annotations
import argparse,hashlib,json,os,re,subprocess,tempfile
from pathlib import Path
from typing import Any
import jsonschema
ROOT=Path(__file__).resolve().parents[1]
SCHEMA=ROOT/'artifact-delivery/shadow-contracts/software-release-linux-elf-contract-v1.schema.json'
FILE=Path(os.environ.get('ARTIFACT_FILE','/usr/bin/file'))
READELF=Path(os.environ.get('ARTIFACT_READELF','/usr/bin/readelf'))
BWRAP=Path(os.environ.get('ARTIFACT_BWRAP','/usr/bin/bwrap'))

def run(argv:list[str],timeout:int=120,env:dict[str,str]|None=None):return subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout,env=env)
def sha(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def canonical(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def load(path:Path):return json.loads(path.read_text())
def validate_contract(c:Any)->list[str]:
 if not isinstance(c,dict):return ['linux-elf release contract must be an object']
 s=load(SCHEMA);return [f"linux-elf release contract schema invalid: {e.message}" for e in sorted(jsonschema.Draft202012Validator(s).iter_errors(c),key=lambda e:list(e.path))]
def parse_field(text:str,name:str)->str|None:
 m=re.search(rf'^\s*{re.escape(name)}:\s*(.+?)\s*$',text,re.M);return m.group(1) if m else None
def parse_readelf(header:str,program:str)->dict[str,Any]:
 im=re.search(r'\[Requesting program interpreter:\s*([^\]]+)\]',program)
 return {'class':parse_field(header,'Class'),'data':parse_field(header,'Data'),'osAbi':parse_field(header,'OS/ABI'),'type':parse_field(header,'Type'),'machine':parse_field(header,'Machine'),'interpreter':im.group(1).strip() if im else None}
def sandbox_command(subject:Path,args:list[str])->list[str]:
 cmd=[str(BWRAP),'--unshare-net','--ro-bind','/usr','/usr','--ro-bind','/etc','/etc','--ro-bind','/bin','/bin']
 for p in ('/lib','/lib64'):
  if Path(p).is_dir():cmd += ['--ro-bind',p,p]
 cmd += ['--dev','/dev','--proc','/proc','--tmpfs','/tmp','--dir','/tmp/home','--dir','/tmp/home/.local','--dir','/tmp/home/.local/share','--dir','/tmp/home/.config','--dir','/tmp/home/.cache','--setenv','HOME','/tmp/home','--setenv','XDG_DATA_HOME','/tmp/home/.local/share','--setenv','XDG_CONFIG_HOME','/tmp/home/.config','--setenv','XDG_CACHE_HOME','/tmp/home/.cache','--ro-bind',str(subject.resolve()),'/tmp/release','--chdir','/tmp','/tmp/release',*args]
 return cmd

def verify_linux_elf(path:Path,contract_path:Path,evidence_dir:Path|None=None)->dict[str,Any]:
 if not path.is_file():return {'schemaVersion':1,'kind':'artifact-linux-elf-release-verification','profileId':'software-release-linux-elf-executable-r1','status':'FAIL','failures':['input is not a regular file']}
 try:c=load(contract_path)
 except Exception as e:return {'schemaVersion':1,'kind':'artifact-linux-elf-release-verification','profileId':'software-release-linux-elf-executable-r1','status':'FAIL','failures':[f'contract unreadable: {e}']}
 failures=validate_contract(c);ev=evidence_dir or Path(tempfile.mkdtemp(prefix='artifact-linux-elf-release-'));ev.mkdir(parents=True,exist_ok=True)
 res={'schemaVersion':1,'kind':'artifact-linux-elf-release-verification','profileId':'software-release-linux-elf-executable-r1','status':'FAIL','artifact':{'path':str(path.resolve()),'size':path.stat().st_size,'sha256':sha(path),'executable':os.access(path,os.X_OK)},'contract':{'path':str(contract_path.resolve()),'sha256':sha(contract_path),'canonicalDigest':canonical(c)},'tools':{},'failures':failures}
 if failures:(ev/'verification.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');return res
 want_art=c['artifact'];identity_fail=[]
 if res['artifact']['sha256']!=want_art['sha256']:identity_fail.append('release SHA-256 differs from contract')
 if res['artifact']['size']!=want_art['byteLength']:identity_fail.append('release byte length differs from contract')
 if want_art['executable'] and not res['artifact']['executable']:identity_fail.append('release is not executable')
 failures.extend(identity_fail);res['byteIdentity']={'status':'PASS' if not identity_fail else 'FAIL','failures':identity_fail}
 if identity_fail:res['failures']=failures;(ev/'verification.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');return res
 for n,p in [('file',FILE),('readelf',READELF),('bubblewrap',BWRAP)]:
  if not p.is_file() or not os.access(p,os.X_OK):failures.append(f'required mature external capability unavailable: {n}')
  else:res['tools'][n]={'path':str(p.resolve()),'sha256':sha(p)}
 if failures:res['failures']=failures;(ev/'verification.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');return res
 # Independent descriptive view from libmagic/file.
 fp=run([str(FILE),'-b',str(path)]);file_text=fp.stdout.decode('utf-8','replace').strip();(ev/'file.txt').write_text(file_text+'\n')
 file_fail=[]
 if fp.returncode!=0:file_fail.append('file/libmagic inspection failed')
 for token in c['fileInspection']['requiredSubstrings']:
  if token not in file_text:file_fail.append(f'file description missing required token: {token}')
 failures.extend(file_fail);res['fileInspection']={'status':'PASS' if not file_fail else 'FAIL','description':file_text,'evidenceSha256':sha(ev/'file.txt'),'failures':file_fail}
 # GNU readelf independently binds ELF header + PT_INTERP facts.
 hp=run([str(READELF),'-h','--wide',str(path)]);pp=run([str(READELF),'-l','--wide',str(path)]);h=hp.stdout.decode('utf-8','replace');pr=pp.stdout.decode('utf-8','replace');(ev/'readelf-header.txt').write_text(h);(ev/'readelf-program.txt').write_text(pr)
 elf_fail=[];facts=parse_readelf(h,pr)
 if hp.returncode!=0 or pp.returncode!=0:elf_fail.append('GNU readelf rejected release')
 for k,w in c['elf'].items():
  if facts.get(k)!=w:elf_fail.append(f'ELF {k} differs from contract')
 failures.extend(elf_fail);res['elfStructure']={'status':'PASS' if not elf_fail else 'FAIL','facts':facts,'headerEvidenceSha256':sha(ev/'readelf-header.txt'),'programEvidenceSha256':sha(ev/'readelf-program.txt'),'failures':elf_fail}
 if file_fail or elf_fail:res['failures']=failures;(ev/'verification.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');return res
 # Final exact bytes are mounted read-only into a fresh bubblewrap namespace. Network is unshared;
 # only host runtime substrate (/usr,/bin,/lib*,/etc) is visible read-only, while HOME/XDG state is ephemeral tmpfs.
 rr=c['runtime'];rp=run(sandbox_command(path,list(rr['args'])),timeout=rr['timeoutSeconds']);stdout=rp.stdout.decode('utf-8','replace');stderr=rp.stderr.decode('utf-8','replace');(ev/'runtime.stdout.txt').write_text(stdout);(ev/'runtime.stderr.txt').write_text(stderr)
 runtime_fail=[]
 if rp.returncode!=rr['exitCode']:runtime_fail.append('sandbox runtime exit code differs from contract')
 for marker in rr['stdoutContains']:
  if marker not in stdout:runtime_fail.append(f'sandbox runtime stdout missing marker: {marker}')
 if stderr!=rr['stderrExact']:runtime_fail.append('sandbox runtime stderr differs from contract')
 failures.extend(runtime_fail);res['runtimeReadback']={'status':'PASS' if not runtime_fail else 'FAIL','exitCode':rp.returncode,'stdout':stdout,'stderr':stderr,'networkNamespace':'unshared','releaseMount':'read-only','userState':'ephemeral tmpfs','hostRuntimeSubstrate':'read-only /usr,/bin,/lib*,/etc','stdoutSha256':sha(ev/'runtime.stdout.txt'),'stderrSha256':sha(ev/'runtime.stderr.txt'),'failures':runtime_fail}
 res.update({'status':'PASS' if not failures else 'FAIL','failures':failures,'boundary':'PASS establishes exact release byte identity, bounded ELF64/System-V/x86-64 facts through libmagic and GNU readelf, and successful execution of those exact bytes in a Bubblewrap namespace with no host network, read-only release/runtime substrate, and ephemeral user state. It does not establish who built the executable, source-to-binary reproducibility, complete filesystem/security isolation, SBOM/vulnerability/signature/provenance claims, code signing/notarization, store packaging/release, cross-platform behavior, or caller-domain suitability.'})
 (ev/'verification.json').write_text(json.dumps(res,indent=2,sort_keys=True,ensure_ascii=False)+'\n');return res

def main():
 ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('--contract',type=Path,required=True);ap.add_argument('--evidence-directory',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args();v=verify_linux_elf(a.input,a.contract,a.evidence_directory);s=json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n';a.output.write_text(s) if a.output else print(s,end='');return 0 if v.get('status')=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
