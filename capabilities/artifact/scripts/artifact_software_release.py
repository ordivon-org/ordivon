#!/usr/bin/env python3
"""Standards-first shadow verifier for a bounded OCI software-release artifact."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, tempfile, uuid
from pathlib import Path
from typing import Any
import jsonschema

ROOT=Path(__file__).resolve().parents[1]
CONTRACT_SCHEMA=ROOT/'artifact-delivery/shadow-contracts/software-release-oci-contract-v1.schema.json'
SKOPEO=Path(os.environ.get('ARTIFACT_SKOPEO','/usr/bin/skopeo'))
PODMAN=Path(os.environ.get('ARTIFACT_PODMAN','/usr/bin/podman'))
SYFT=Path(os.environ.get('ARTIFACT_SYFT','/usr/bin/syft'))
TRIVY=Path(os.environ.get('ARTIFACT_TRIVY','/usr/bin/trivy'))
TRIVY_DB_ROOT=Path(os.environ.get('ARTIFACT_TRIVY_DB_ROOT','/opt/ordivon/external/trivy-db/20260912-r1'))
EXPECTED_DB_SHA='63b60b5493b28e6ce5b3a45753865055f890cea750b7138922963e25446975bf'
EXPECTED_DB_META_SHA='ad131f125e7913b23abbbe563e79920c333e52e290beb33a050bb640073a10b4'


def run(argv:list[str], timeout:int=180)->subprocess.CompletedProcess[bytes]:
    return subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout)

def sha_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def canonical_digest(v:Any)->str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def validate_contract(c:dict[str,Any])->list[str]:
    schema=json.loads(CONTRACT_SCHEMA.read_text())
    return [f"software-release contract schema invalid: {e.message}" for e in sorted(jsonschema.Draft202012Validator(schema).iter_errors(c),key=lambda e:list(e.path))]

def digest_blob(path:Path, digest:str, size:int|None=None)->list[str]:
    failures=[]
    if not digest.startswith('sha256:'): return ['unsupported non-sha256 OCI digest']
    p=path/'blobs'/'sha256'/digest.split(':',1)[1]
    if not p.is_file(): return [f'missing OCI blob {digest}']
    if sha_file(p)!=digest.split(':',1)[1]: failures.append(f'OCI blob digest mismatch {digest}')
    if size is not None and p.stat().st_size!=size: failures.append(f'OCI blob size mismatch {digest}')
    return failures

def read_json(path:Path)->dict[str,Any]: return json.loads(path.read_text())
def count_trivy(report:dict[str,Any], key:str)->int:
    return sum(len(r.get(key) or []) for r in report.get('Results') or [])

def scan_count_policy(report:dict[str,Any], key:str, maximum:int, label:str)->tuple[int,list[str]]:
    count=count_trivy(report,key)
    failures=[]
    if count>maximum: failures.append(f'{label} count exceeds object contract maximum')
    return count,failures


def verify_oci(layout:Path, contract_path:Path, evidence_dir:Path|None=None)->dict[str,Any]:
    failures=[]
    if not layout.is_dir(): return {'schemaVersion':1,'kind':'artifact-software-release-verification','profileId':'software-release-oci-image-r1','status':'FAIL','failures':['input is not an OCI layout directory']}
    try: contract=json.loads(contract_path.read_text())
    except Exception as e: return {'schemaVersion':1,'kind':'artifact-software-release-verification','profileId':'software-release-oci-image-r1','status':'FAIL','failures':[f'contract unreadable: {e}']}
    failures.extend(validate_contract(contract))
    evidence_dir=evidence_dir or Path(tempfile.mkdtemp(prefix='artifact-software-release-evidence-')); evidence_dir.mkdir(parents=True,exist_ok=True)
    result={'schemaVersion':1,'kind':'artifact-software-release-verification','profileId':'software-release-oci-image-r1','status':'FAIL','layout':str(layout.resolve()),'contract':{'path':str(contract_path.resolve()),'sha256':sha_file(contract_path),'canonicalDigest':canonical_digest(contract)},'failures':failures,'tools':{}}
    if failures:
        (evidence_dir/'verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); return result
    for n,p in [('skopeo',SKOPEO),('podman',PODMAN),('syft',SYFT),('trivy',TRIVY)]:
        if not p.is_file() or not os.access(p,os.X_OK): failures.append(f'required mature external capability unavailable: {n}')
        else: result['tools'][n]={'path':str(p.resolve()),'sha256':sha_file(p)}
    db=TRIVY_DB_ROOT/'cache/db/trivy.db'; dbmeta=TRIVY_DB_ROOT/'cache/db/metadata.json'
    if not db.is_file() or sha_file(db)!=EXPECTED_DB_SHA: failures.append('frozen Trivy DB bytes unavailable or drifted')
    if not dbmeta.is_file() or sha_file(dbmeta)!=EXPECTED_DB_META_SHA: failures.append('frozen Trivy DB metadata unavailable or drifted')
    if failures:
        result['failures']=failures; (evidence_dir/'verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); return result

    # OCI layout, descriptor, manifest, config and layer integrity.
    oci_fail=[]
    try:
        ol=read_json(layout/'oci-layout'); idx=read_json(layout/'index.json')
    except Exception as e:
        result['failures']=[f'OCI layout metadata unreadable: {e}']; (evidence_dir/'verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); return result
    if ol.get('imageLayoutVersion')!='1.0.0': oci_fail.append('OCI layout version is not 1.0.0')
    manifests=idx.get('manifests') or []
    if idx.get('schemaVersion')!=2 or idx.get('mediaType')!='application/vnd.oci.image.index.v1+json': oci_fail.append('index.json is not OCI image index v1')
    if len(manifests)!=1: oci_fail.append('R1 requires exactly one OCI manifest descriptor')
    desc=manifests[0] if len(manifests)==1 else {}
    manifest_digest=desc.get('digest','')
    if manifest_digest!=contract['image']['manifestDigest']: oci_fail.append('OCI manifest digest differs from object contract')
    oci_fail.extend(digest_blob(layout,manifest_digest,desc.get('size')) if manifest_digest else ['manifest descriptor missing digest'])
    manifest={}; config={}
    if manifest_digest.startswith('sha256:'):
        mp=layout/'blobs'/'sha256'/manifest_digest.split(':',1)[1]
        if mp.is_file():
            try: manifest=read_json(mp)
            except Exception: oci_fail.append('OCI manifest JSON unreadable')
    if manifest:
        if manifest.get('schemaVersion')!=2 or manifest.get('mediaType')!='application/vnd.oci.image.manifest.v1+json': oci_fail.append('manifest media type/schema invalid')
        cfg=manifest.get('config') or {}
        if cfg.get('mediaType')!='application/vnd.oci.image.config.v1+json': oci_fail.append('config media type invalid')
        if cfg.get('digest'): oci_fail.extend(digest_blob(layout,cfg['digest'],cfg.get('size')))
        for layer in manifest.get('layers') or []:
            if layer.get('mediaType')!='application/vnd.oci.image.layer.v1.tar+gzip': oci_fail.append('layer media type outside R1')
            if layer.get('digest'): oci_fail.extend(digest_blob(layout,layer['digest'],layer.get('size')))
        if cfg.get('digest','').startswith('sha256:'):
            cp=layout/'blobs'/'sha256'/cfg['digest'].split(':',1)[1]
            if cp.is_file():
                try: config=read_json(cp)
                except Exception: oci_fail.append('OCI config JSON unreadable')
    failures.extend(oci_fail)
    oci_ev={'status':'PASS' if not oci_fail else 'FAIL','manifestDigest':manifest_digest,'configDigest':(manifest.get('config') or {}).get('digest'),'layerDigests':[x.get('digest') for x in manifest.get('layers') or []],'failures':oci_fail}

    cfg_fail=[]; want=contract['image']; cconfig=config.get('config') or {}
    if config.get('os')!=want['os']: cfg_fail.append('OCI config os differs from contract')
    if config.get('architecture')!=want['architecture']: cfg_fail.append('OCI config architecture differs from contract')
    if cconfig.get('Entrypoint')!=want['entrypoint']: cfg_fail.append('OCI entrypoint differs from contract')
    if cconfig.get('WorkingDir')!=want['workingDir']: cfg_fail.append('OCI workingDir differs from contract')
    failures.extend(cfg_fail)

    # Generate SBOM from the exact final OCI layout before importing anywhere.
    sbom_path=evidence_dir/'sbom.spdx.json'
    sy=run([str(SYFT),f'oci-dir:{layout}','-o',f'spdx-json={sbom_path}'])
    sbom_fail=[]; sbom={}
    if sy.returncode!=0 or not sbom_path.is_file(): sbom_fail.append('Syft failed to generate SPDX SBOM from final OCI layout')
    else:
        try: sbom=read_json(sbom_path)
        except Exception: sbom_fail.append('Syft SPDX JSON unreadable')
    if sbom:
        if sbom.get('spdxVersion')!='SPDX-2.3': sbom_fail.append('SBOM is not SPDX-2.3')
        roots=[p for p in sbom.get('packages') or [] if p.get('primaryPackagePurpose')=='CONTAINER']
        if len(roots)!=1 or roots[0].get('versionInfo')!=manifest_digest: sbom_fail.append('SBOM CONTAINER root is not bound to final OCI manifest digest')
        packages={(p.get('name'),p.get('versionInfo')) for p in sbom.get('packages') or []}
        for req in contract['sbom']['requiredPackages']:
            if (req['name'],req['version']) not in packages: sbom_fail.append(f"required SBOM package missing: {req['name']}@{req['version']}")
    failures.extend(sbom_fail)

    tag=f'localhost/ordivon/artifact-software-release-r1:verify-{uuid.uuid4().hex[:12]}'
    cid=''; temp_root=Path(tempfile.mkdtemp(prefix='artifact-software-release-rootfs-'))
    rootfs_fail=[]; runtime_fail=[]; vuln_fail=[]; secret_fail=[]
    try:
        cp=run([str(SKOPEO),'copy',f'oci:{layout}:release',f'containers-storage:{tag}'])
        if cp.returncode!=0: rootfs_fail.append('Skopeo could not import final OCI layout for independent read-back')
        if not rootfs_fail:
            pc=run([str(PODMAN),'create','--network','none',tag]); cid=pc.stdout.decode().strip() if pc.returncode==0 else ''
            if not cid: rootfs_fail.append('Podman could not create read-back container')
        if cid:
            tar_path=evidence_dir/'rootfs.tar'
            exp=run([str(PODMAN),'export','-o',str(tar_path),cid])
            tar=subprocess.run(['/usr/bin/tar','-C',str(temp_root),'-xf',str(tar_path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            if exp.returncode!=0 or tar.returncode!=0: rootfs_fail.append('Podman rootfs export/read-back failed')
        for ef in want['expectedFiles']:
            fp=temp_root/ef['path'].lstrip('/')
            if not fp.is_file(): rootfs_fail.append(f"expected rootfs file missing: {ef['path']}")
            elif sha_file(fp)!=ef['sha256']: rootfs_fail.append(f"rootfs file digest differs from contract: {ef['path']}")
        failures.extend(rootfs_fail)

        # Frozen-DB vulnerability evidence over read-back rootfs.
        vuln_path=evidence_dir/'trivy-vulnerability.json'
        tv=run([str(TRIVY),'rootfs','--cache-dir',str(TRIVY_DB_ROOT/'cache'),'--scanners','vuln','--skip-db-update','--offline-scan','--format','json','--output',str(vuln_path),str(temp_root)])
        vuln={}
        if tv.returncode!=0 or not vuln_path.is_file(): vuln_fail.append('Trivy frozen-DB vulnerability scan failed')
        else:
            try: vuln=read_json(vuln_path)
            except Exception: vuln_fail.append('Trivy vulnerability report unreadable')
        if vuln:
            vcount,policy_fail=scan_count_policy(vuln,'Vulnerabilities',contract['security']['maximumVulnerabilities'],'vulnerability')
            vuln_fail.extend(policy_fail)
        else:
            vcount=-1
        failures.extend(vuln_fail)

        secret_path=evidence_dir/'trivy-secret.json'; secret_cache=evidence_dir/'trivy-secret-cache'
        ts=run([str(TRIVY),'rootfs','--cache-dir',str(secret_cache),'--scanners','secret','--format','json','--output',str(secret_path),str(temp_root)])
        secret={}
        if ts.returncode!=0 or not secret_path.is_file(): secret_fail.append('Trivy secret scan failed')
        else:
            try: secret=read_json(secret_path)
            except Exception: secret_fail.append('Trivy secret report unreadable')
        if secret:
            scount,policy_fail=scan_count_policy(secret,'Secrets',contract['security']['maximumSecrets'],'secret')
            secret_fail.extend(policy_fail)
        else:
            scount=-1
        failures.extend(secret_fail)

        # Runtime read-back from final imported image; network disabled.
        rr=contract['runtime']
        pr=run([str(PODMAN),'start','-a',cid]) if cid else subprocess.CompletedProcess([],1,b'',b'no cid')
        stdout=pr.stdout.decode('utf-8','replace'); stderr=pr.stderr.decode('utf-8','replace')
        if pr.returncode!=rr['exitCode']: runtime_fail.append('runtime exit code differs from contract')
        if stdout!=rr['stdoutExact']: runtime_fail.append('runtime stdout differs from contract')
        if stderr!=rr['stderrExact']: runtime_fail.append('runtime stderr differs from contract')
        failures.extend(runtime_fail)
    finally:
        if cid: run([str(PODMAN),'rm','-f',cid],timeout=60)
        run([str(PODMAN),'rmi','-f',tag],timeout=60)
        shutil.rmtree(temp_root,ignore_errors=True)

    result.update({
      'ociIdentity':oci_ev,
      'platformConfig':{'status':'PASS' if not cfg_fail else 'FAIL','os':config.get('os'),'architecture':config.get('architecture'),'entrypoint':cconfig.get('Entrypoint'),'workingDir':cconfig.get('WorkingDir'),'failures':cfg_fail},
      'rootfsReadback':{'status':'PASS' if not rootfs_fail else 'FAIL','expectedFiles':want['expectedFiles'],'failures':rootfs_fail},
      'sbom':{'status':'PASS' if not sbom_fail else 'FAIL','format':sbom.get('spdxVersion'),'packageCount':len(sbom.get('packages') or []) if sbom else 0,'reportSha256':sha_file(sbom_path) if sbom_path.is_file() else None,'failures':sbom_fail},
      'vulnerabilityScan':{'status':'PASS' if not vuln_fail else 'FAIL','dbSnapshot':contract['security']['trivyDbSnapshot'],'dbSha256':EXPECTED_DB_SHA,'vulnerabilityCount':vcount,'maximum':contract['security']['maximumVulnerabilities'],'reportSha256':sha_file(vuln_path) if vuln_path.is_file() else None,'failures':vuln_fail},
      'secretScan':{'status':'PASS' if not secret_fail else 'FAIL','secretCount':scount,'maximum':contract['security']['maximumSecrets'],'reportSha256':sha_file(secret_path) if secret_path.is_file() else None,'failures':secret_fail},
      'runtimeReadback':{'status':'PASS' if not runtime_fail else 'FAIL','exitCode':pr.returncode if 'pr' in locals() else None,'stdout':stdout if 'stdout' in locals() else None,'stderr':stderr if 'stderr' in locals() else None,'network':'none','failures':runtime_fail},
      'status':'PASS' if not failures else 'FAIL','failures':failures,
      'boundary':'PASS is bounded to one exact single-platform OCI Image Layout under one software-release object contract. It establishes OCI descriptor integrity, linux/amd64 config/entrypoint, exact rootfs file identity, SPDX-2.3 SBOM binding, frozen-snapshot vulnerability count, secret count and network-disabled runtime read-back. It does not establish build authorship, production deployment safety, vulnerability absence outside the frozen DB snapshot, multi-platform semantics, registry policy, or signature/provenance trust handled by the separate common release envelope.'
    })
    (evidence_dir/'verification.json').write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
    return result


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('layout',type=Path); ap.add_argument('--contract',type=Path,required=True); ap.add_argument('--evidence-directory',type=Path); ap.add_argument('--output',type=Path); a=ap.parse_args()
    v=verify_oci(a.layout,a.contract,a.evidence_directory); s=json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n'
    if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(s)
    else: print(s,end='')
    return 0 if v.get('status')=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())
