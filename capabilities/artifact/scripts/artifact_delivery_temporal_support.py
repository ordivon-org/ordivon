#!/usr/bin/env python3
"""Receipt-fenced local activities for Artifact Build & Delivery Temporal workflows."""
from __future__ import annotations
import fcntl, hashlib, json, os, shutil, subprocess, tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT_PYTHON = Path("/root/.local/share/ordivon-workstation/artifact-delivery-python-v1/current/bin/python")
DEFAULT_ARTIFACT_CLI = ROOT / "scripts/artifact_delivery.py"

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def file_fact(path: Path) -> dict[str,Any]:
    p=path.resolve()
    if not p.is_file(): raise RuntimeError(f"required file is absent: {p}")
    return {"name":p.name,"path":str(p),"size":p.stat().st_size,"sha256":sha256_file(p)}

def _expected_file(value: dict[str,Any], label: str) -> Path:
    if not isinstance(value,dict): raise RuntimeError(f"{label} must be a file commitment object")
    unknown=set(value)-{"path","sha256","name","size"}
    if unknown: raise RuntimeError(f"{label} contains unsupported fields: {sorted(unknown)}")
    if not isinstance(value.get('path'),str) or not isinstance(value.get('sha256'),str): raise RuntimeError(f"{label}.path and sha256 are required")
    p=Path(value['path']).resolve(); actual=file_fact(p)
    if actual['sha256']!=value['sha256']: raise RuntimeError(f"{label} SHA-256 drift")
    if value.get('name') is not None and value['name']!=actual['name']: raise RuntimeError(f"{label} name drift")
    if value.get('size') is not None and value['size']!=actual['size']: raise RuntimeError(f"{label} size drift")
    return p

def _simple_fact(value: dict[str,Any]) -> dict[str,Any]:
    digest=value.get('sha256') or (value.get('digest') or {}).get('sha256')
    return {"path":str(Path(value['path']).resolve()),"sha256":digest,"name":value.get('name') or Path(value['path']).name,"size":value.get('size')}

def _operation_key(stage:str, operation_id:str)->str:
    return hashlib.sha256(f"{stage}\0{operation_id}".encode()).hexdigest()

def _require_public_file_commitment(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    unknown = set(value) - {"path", "sha256", "name", "size"}
    if unknown:
        raise ValueError(f"{label} contains unsupported fields: {sorted(unknown)}")
    if not isinstance(value.get("path"), str) or not value["path"]:
        raise ValueError(f"{label}.path is required")
    digest = value.get("sha256")
    if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise ValueError(f"{label}.sha256 must be a lowercase SHA-256 hex digest")
    return value

def validate_public_trust_material_envelope(value: object) -> dict[str, Any]:
    """Validate public verification material before it can be sent into Temporal history."""
    if not isinstance(value, dict):
        raise ValueError("trust material must be an object")
    allowed = {"trustPolicy", "bundles", "signerIds"}
    unknown = set(value) - allowed
    if unknown:
        raise ValueError(f"trust material contains unsupported fields: {sorted(unknown)}")
    if set(value) != allowed:
        raise ValueError("trust material requires exactly trustPolicy, bundles and signerIds")
    _require_public_file_commitment(value["trustPolicy"], "trustPolicy")
    bundles = value["bundles"]
    signer_ids = value["signerIds"]
    if not isinstance(bundles, dict) or not bundles:
        raise ValueError("trust material bundles must be a non-empty object")
    if not isinstance(signer_ids, dict) or set(signer_ids) != set(bundles):
        raise ValueError("trust material signerIds must exactly match bundle gates")
    for gate, fact in bundles.items():
        if not isinstance(gate, str) or not gate:
            raise ValueError("trust material bundle gate names must be non-empty strings")
        _require_public_file_commitment(fact, f"bundles.{gate}")
        signer = signer_ids[gate]
        if not isinstance(signer, str) or not signer:
            raise ValueError(f"signerIds.{gate} must be a non-empty string")
    return value

class ReceiptFencedArtifactExecutor:
    def __init__(self,state_root:Path,*,artifact_python:Path=DEFAULT_ARTIFACT_PYTHON,artifact_cli:Path=DEFAULT_ARTIFACT_CLI)->None:
        self.state_root=state_root.resolve(); self.artifact_python=artifact_python.absolute(); self.artifact_cli=artifact_cli.resolve()
        if not self.artifact_python.is_file(): raise RuntimeError(f"Artifact Delivery Python is absent: {self.artifact_python}")
        if not self.artifact_cli.is_file(): raise RuntimeError(f"Artifact Delivery CLI is absent: {self.artifact_cli}")
        (self.state_root/'operations').mkdir(parents=True,exist_ok=True); (self.state_root/'locks').mkdir(parents=True,exist_ok=True)
    def _run_cli(self,args:list[str],*,timeout:int=300)->subprocess.CompletedProcess[str]:
        return subprocess.run([str(self.artifact_python),str(self.artifact_cli),*args],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout,env=dict(os.environ))
    @staticmethod
    def _cli_failure_message(label:str,p:subprocess.CompletedProcess[str],report:Path|None=None)->str:
        details=[]
        if report is not None and report.is_file():
            try:
                report_text=report.read_text(encoding='utf-8').strip()
            except (OSError,UnicodeError):
                report_text=''
            if report_text: details.append(f"report={report_text[-4000:]}")
        for stream in ('stdout','stderr'):
            text=getattr(p,stream,'') or ''
            if text.strip(): details.append(f"{stream}={text[-4000:]}")
        if not details: details.append('no diagnostic output')
        return f"{label} failed (exit={p.returncode}): " + ' | '.join(details)
    def _receipt_view(self,opdir:Path,receipt:dict[str,Any],*,replayed:bool)->dict[str,Any]:
        roles={role:file_fact(opdir/rel) for role,rel in receipt['roles'].items()}
        return {"schemaVersion":1,"kind":"artifact-delivery-temporal-activity-result","stage":receipt['stage'],"operationId":receipt['operationId'],"replayed":replayed,"operationDirectory":str(opdir),"inputs":receipt['inputs'],"roles":roles,"metadata":receipt.get('metadata',{})}
    def _verify_receipt(self,opdir:Path,r:dict[str,Any],stage:str,operation_id:str,inputs:dict[str,Any])->None:
        if r.get('stage')!=stage or r.get('operationId')!=operation_id: raise RuntimeError('committed activity receipt identity mismatch')
        if r.get('inputs')!=inputs: raise RuntimeError('operationId reuse attempted with different immutable inputs')
        if not isinstance(r.get('outputs'),dict) or not r['outputs']: raise RuntimeError('committed activity receipt has no outputs')
        for rel,expected in r['outputs'].items():
            actual=file_fact(opdir/rel)
            if actual['sha256']!=expected.get('sha256') or actual['size']!=expected.get('size'): raise RuntimeError(f"committed activity output drift: {rel}")
    def _fenced(self,stage:str,operation_id:str,inputs:dict[str,Any],producer:Callable[[Path],tuple[dict[str,str],dict[str,Any]]])->dict[str,Any]:
        if not operation_id: raise RuntimeError('operationId is required')
        key=_operation_key(stage,operation_id); stage_root=self.state_root/'operations'/stage; stage_root.mkdir(parents=True,exist_ok=True); final=stage_root/key
        with (self.state_root/'locks'/f'{key}.lock').open('a+b') as lock:
            fcntl.flock(lock.fileno(),fcntl.LOCK_EX); rp=final/'activity-receipt.json'
            if rp.is_file():
                r=json.loads(rp.read_text()); self._verify_receipt(final,r,stage,operation_id,inputs); return self._receipt_view(final,r,replayed=True)
            # The underlying Artifact Delivery JSON receipts contain absolute evidence paths.
            # Produce directly in the deterministic final operation directory and use the receipt
            # file itself as the commit marker. A directory without that marker is an abandoned
            # attempt and is safe to delete/rebuild because no committed Activity standing exists.
            if final.exists(): shutil.rmtree(final)
            final.mkdir(parents=True)
            try:
                roles,metadata=producer(final); outs={}; normalized={}
                for role,rel in roles.items():
                    relp=Path(rel)
                    if relp.is_absolute() or '..' in relp.parts: raise RuntimeError(f'invalid activity output role path: {rel}')
                    fact=file_fact(final/relp); normalized[role]=relp.as_posix(); outs[relp.as_posix()]={k:fact[k] for k in ('sha256','size','name')}
                if not outs: raise RuntimeError('activity producer returned no outputs')
                r={"schemaVersion":1,"kind":"artifact-delivery-temporal-activity-receipt","stage":stage,"operationId":operation_id,"inputs":inputs,"roles":normalized,"outputs":outs,"metadata":metadata}
                receipt_tmp=final/'.activity-receipt.json.tmp'
                with receipt_tmp.open('w') as handle:
                    handle.write(json.dumps(r,indent=2,sort_keys=True)+'\n'); handle.flush(); os.fsync(handle.fileno())
                os.replace(receipt_tmp,final/'activity-receipt.json')
                return self._receipt_view(final,r,replayed=False)
            except Exception:
                shutil.rmtree(final,ignore_errors=True); raise
    def prepare(self,value:dict[str,Any])->dict[str,Any]:
        oid=str(value['operationId']); request_path=_expected_file(dict(value['request']),'request'); inputs={'request':file_fact(request_path)}
        def produce(tmp:Path):
            out=tmp/'derived-plan.json'; p=self._run_cli(['compile-request',str(request_path),'--output',str(out)])
            if p.returncode or not out.is_file(): raise RuntimeError(self._cli_failure_message("compile-request",p,out))
            plan=json.loads(out.read_text())
            if plan.get('status')!='PASS': raise RuntimeError(f"derived plan did not PASS: {plan.get('failures')}")
            return {'plan':'derived-plan.json'},{'requestId':plan.get('requestId'),'profile':_simple_fact(plan['resolvedInputs']['profile']),'source':_simple_fact(plan['resolvedInputs']['source']),'requiredGates':plan.get('requiredGates',[])}
        return self._fenced('prepare',oid,inputs,produce)
    def build(self,value:dict[str,Any])->dict[str,Any]:
        oid=str(value['operationId']); request_path=_expected_file(dict(value['request']),'request'); inputs={'request':file_fact(request_path)}
        def produce(tmp:Path):
            artifacts=tmp/'artifacts'; report=tmp/'build-stage.json'; p=self._run_cli(['build-request',str(request_path),'--output-directory',str(artifacts),'--output',str(report)])
            if p.returncode or not report.is_file(): raise RuntimeError(self._cli_failure_message("build-request",p,report))
            result=json.loads(report.read_text())
            if result.get('status')!='PASS': raise RuntimeError(f"build stage did not PASS: {result.get('failures')}")
            artifact_path=Path(result['artifact']['path'])
            if artifact_path.parent.resolve()!=artifacts.resolve() or not artifact_path.is_file(): raise RuntimeError('build output escaped activity staging directory')
            return {'buildReport':'build-stage.json','artifact':f'artifacts/{artifact_path.name}'},{'artifactName':artifact_path.name,'adapter':result.get('plan',{}).get('buildAdapter')}
        return self._fenced('build',oid,inputs,produce)
    def verify(self,value:dict[str,Any])->dict[str,Any]:
        oid=str(value['operationId']); profile_path=_expected_file(dict(value['profile']),'profile'); artifact_path=_expected_file(dict(value['artifact']),'artifact'); inputs={'profile':file_fact(profile_path),'artifact':file_fact(artifact_path)}
        def produce(tmp:Path):
            evidence=tmp/'evidence'; report=tmp/'verify-stage.json'; p=self._run_cli(['verify-stage','--profile',str(profile_path),'--artifact',str(artifact_path),'--output-directory',str(evidence),'--output',str(report)])
            if p.returncode or not report.is_file(): raise RuntimeError(self._cli_failure_message("verify-stage",p,report))
            result=json.loads(report.read_text())
            if result.get('status')!='PASS': raise RuntimeError(f"verify stage did not PASS: {result.get('failures')}")
            roles={'verifyReport':'verify-stage.json'}; gates=[]
            for path in sorted(evidence.glob('*.json')):
                rel=f'evidence/{path.name}'
                if path.name.endswith('.vsa.json'):
                    gate=path.name[:-9]; roles[f'gateVsa:{gate}']=rel; gates.append(gate)
                elif path.name.endswith('.raw.json'):
                    gate=path.name[:-9]; roles[f'rawEvidence:{gate}']=rel
            return roles,{'profileVerificationComplete':bool(result.get('profileVerificationComplete')),'gateVsas':gates}
        return self._fenced('verify',oid,inputs,produce)
    def _validate_trust_material(self,value:dict[str,Any])->dict[str,Any]:
        unknown=set(value)-{'trustPolicy','bundles','signerIds'}
        if unknown: raise RuntimeError(f"trust material contains unsupported fields: {sorted(unknown)}")
        if set(value)!={'trustPolicy','bundles','signerIds'}: raise RuntimeError('trust material requires exactly trustPolicy, bundles and signerIds')
        tp=file_fact(_expected_file(dict(value['trustPolicy']),'trustPolicy')); bundles_value=value['bundles']; signers=value['signerIds']
        if not isinstance(bundles_value,dict) or not bundles_value: raise RuntimeError('trust material bundles must be non-empty')
        if not isinstance(signers,dict) or set(signers)!=set(bundles_value): raise RuntimeError('trust material signerIds must exactly match bundle gates')
        bundles={}
        for gate,fact in sorted(bundles_value.items()):
            bundles[gate]=file_fact(_expected_file(dict(fact),f'bundles.{gate}'))
            if not isinstance(signers[gate],str) or not signers[gate]: raise RuntimeError(f'signerIds.{gate} must be non-empty')
        commitment={'trustPolicy':tp,'bundles':bundles,'signerIds':dict(sorted(signers.items()))}
        return {'trustPolicy':tp,'bundles':bundles,'signerIds':dict(sorted(signers.items())),'commitment':commitment}
    def verify_trust(self,value:dict[str,Any])->dict[str,Any]:
        oid=str(value['operationId']); profile_path=_expected_file(dict(value['profile']),'profile'); artifact_path=_expected_file(dict(value['artifact']),'artifact'); trust=self._validate_trust_material(dict(value['trustMaterial'])); gate_vsas=dict(value['gateVsas']); normalized={}
        for gate,fact in sorted(gate_vsas.items()): normalized[gate]=file_fact(_expected_file(dict(fact),f'gateVsas.{gate}'))
        inputs={'profile':file_fact(profile_path),'artifact':file_fact(artifact_path),'gateVsas':normalized,'trustMaterial':trust['commitment']}
        def produce(tmp:Path):
            out=tmp/'trusted-vsa-aggregation.json'; args=['aggregate-vsa-gates','--profile',str(profile_path),'--subject',str(artifact_path)]
            for gate,fact in sorted(normalized.items()): args += ['--gate',f"{gate}={fact['path']}"]
            for gate,fact in sorted(trust['bundles'].items()): args += ['--bundle',f"{gate}={fact['path']}"]
            for gate,sid in sorted(trust['signerIds'].items()): args += ['--signer',f'{gate}={sid}']
            args += ['--trust-policy',trust['trustPolicy']['path'],'--output',str(out)]; p=self._run_cli(args)
            if p.returncode or not out.is_file(): raise RuntimeError(self._cli_failure_message("trusted VSA aggregation",p,out))
            result=json.loads(out.read_text())
            if result.get('status')!='PASS': raise RuntimeError(f"trusted VSA aggregation did not PASS: {result.get('failures')}")
            return {'trustAggregation':'trusted-vsa-aggregation.json'},{'trustedGates':sorted(result.get('components',{}))}
        return self._fenced('trust',oid,inputs,produce)
    def package(self,value:dict[str,Any])->dict[str,Any]:
        oid=str(value['operationId']); profile_path=_expected_file(dict(value['profile']),'profile'); artifact_path=_expected_file(dict(value['artifact']),'artifact'); verify_report_path=_expected_file(dict(value['verifyReport']),'verifyReport'); local=bool(value.get('allowLocalUnsignedDevelopment',False)); trust=None if local else self._validate_trust_material(dict(value.get('trustMaterial') or {})); inputs={'profile':file_fact(profile_path),'artifact':file_fact(artifact_path),'verifyReport':file_fact(verify_report_path),'allowLocalUnsignedDevelopment':local}
        if trust is not None: inputs['trustMaterial']=trust['commitment']
        def produce(tmp:Path):
            pkg=tmp/'package'; out=tmp/'package-stage.json'; args=['package-stage','--profile',str(profile_path),'--primary',str(artifact_path),'--verify-report',str(verify_report_path),'--output-directory',str(pkg),'--output',str(out)]
            if local: args.append('--allow-local-unsigned')
            else:
                assert trust is not None
                for gate,fact in sorted(trust['bundles'].items()): args += ['--gate-bundle',f"{gate}={fact['path']}"]
                for gate,sid in sorted(trust['signerIds'].items()): args += ['--gate-signer',f'{gate}={sid}']
                args += ['--trust-policy',trust['trustPolicy']['path']]
            p=self._run_cli(args)
            if p.returncode or not out.is_file(): raise RuntimeError(self._cli_failure_message("package-stage",p,out))
            result=json.loads(out.read_text())
            if result.get('status')!='PASS': raise RuntimeError(f"package stage did not PASS: {result.get('failures')}")
            roles={'packageReport':'package-stage.json'}
            for role,name in [('packageIndex','package-index.json'),('releaseManifest','release-manifest.json')]:
                if (pkg/name).is_file(): roles[role]=f'package/{name}'
            return roles,{'releaseReady':bool(result.get('releaseReady')),'trustStanding':result.get('trustStanding'),'packageRelativePath':'package'}
        result=self._fenced('package',oid,inputs,produce); result['packageDirectory']=str(Path(result['operationDirectory'])/'package'); return result
