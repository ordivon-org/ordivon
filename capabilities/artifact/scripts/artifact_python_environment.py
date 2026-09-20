#!/usr/bin/env python3
"""Materialize the stable Artifact Delivery Python generation from an Artifact-owned uv lock."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
MAIN=Path('/root/projects/ordivon-artifact-v2')
LOCK_PATH=ROOT/'artifact-delivery/artifact-python-runtime-v1.lock.json'
WRAPPER_SOURCE=ROOT/'scripts/artifact_python_wrapper.py'
UV=Path(os.environ.get('ARTIFACT_UV','/root/.local/share/mise/installs/uv/0.12.16/uv-x86_64-unknown-linux-musl/uv'))
SYSTEM_PYTHON=Path(os.environ.get('ARTIFACT_PYTHON','/root/.local/share/mise/installs/python/3.14.7/bin/python3.14'))


def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def canonical(value:Any)->bytes:return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()


def tree_digest(root:Path)->str:
    root=root.resolve();h=hashlib.sha256()
    for path in sorted(root.rglob('*'),key=lambda p:p.relative_to(root).as_posix()):
        rel=path.relative_to(root).as_posix()
        if path.is_symlink():payload=f'L\0{rel}\0{os.readlink(path)}'.encode()
        elif path.is_dir():payload=f'D\0{rel}\0{path.stat().st_mode & 0o777:o}'.encode()
        elif path.is_file():payload=f'F\0{rel}\0{path.stat().st_mode & 0o777:o}\0{sha(path)}'.encode()
        else:raise RuntimeError(f'unsupported Artifact Python generation node: {rel}')
        h.update(len(payload).to_bytes(8,'big'));h.update(payload)
    return 'sha256:'+h.hexdigest()


def make_read_only(root:Path)->None:
    for p in sorted(root.rglob('*'),reverse=True):
        if p.is_symlink():continue
        if p.is_dir():os.chmod(p,0o555)
        elif p.is_file():os.chmod(p,0o555 if os.access(p,os.X_OK) else 0o444)
    os.chmod(root,0o555)


def load_lock()->dict[str,Any]:
    value=json.loads(LOCK_PATH.read_text())
    if value.get('schemaVersion')!=1 or value.get('kind')!='artifact-python-runtime-lock':raise RuntimeError('Artifact Python runtime lock invalid')
    return value


def run(args:list[str],**kwargs:Any)->subprocess.CompletedProcess[str]:return subprocess.run(args,text=True,capture_output=True,check=False,**kwargs)


def project_status(lock:dict[str,Any])->dict[str,str]:
    cfg=lock['uvProject'];project=ROOT/cfg['path'];pyproject=project/'pyproject.toml';uvlock=project/'uv.lock'
    if not UV.is_file() or not pyproject.is_file() or not uvlock.is_file():raise RuntimeError('Artifact Python uv authority is absent')
    observed={'pyprojectSha256':'sha256:'+sha(pyproject),'uvLockSha256':'sha256:'+sha(uvlock)}
    if observed['pyprojectSha256']!=cfg['pyprojectSha256'] or observed['uvLockSha256']!=cfg['uvLockSha256']:raise RuntimeError('Artifact Python uv project digest drift')
    check=run([str(UV),'lock','--check','--offline','--python',str(SYSTEM_PYTHON),'--project',str(project)],timeout=60)
    if check.returncode:raise RuntimeError('Artifact Python uv.lock is not frozen/current: '+check.stderr[-3000:])
    return {'project':str(project),**observed}


def python_status(lock:dict[str,Any])->dict[str,str]:
    if not SYSTEM_PYTHON.is_file():raise RuntimeError('Artifact Python interpreter authority is absent')
    p=run([str(SYSTEM_PYTHON),'-c','import json,platform,sys;print(json.dumps({"version":platform.python_version(),"executable":sys.executable}))'],timeout=30)
    if p.returncode:raise RuntimeError('Artifact Python interpreter probe failed: '+p.stderr[-2000:])
    observed=json.loads(p.stdout)
    if observed['version']!=lock['pythonRuntime']:raise RuntimeError(f"Artifact Python authority drifted: {observed['version']}")
    resolved=SYSTEM_PYTHON.resolve(strict=True)
    return {'version':observed['version'],'requestedPath':str(SYSTEM_PYTHON),'resolvedPath':str(resolved),'sha256':'sha256:'+sha(resolved)}


def dependency_probe(python:Path,expected:dict[str,str])->dict[str,Any]:
    code=("import json,platform;from importlib.metadata import version;import lxml.etree,pptx,PIL,jsonschema,xlsxwriter,opentelemetry.sdk,temporalio;"
          f"names={json.dumps(sorted(expected))};"
          "print(json.dumps({'python':platform.python_version(),'versions':{n:version(n) for n in names},'libxml':lxml.etree.LIBXML_VERSION,'libxslt':lxml.etree.LIBXSLT_VERSION},sort_keys=True))")
    p=run([str(python),'-c',code],env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},timeout=45)
    if p.returncode:raise RuntimeError('Artifact Python dependency probe failed: '+p.stderr[-3000:])
    value=json.loads(p.stdout)
    if value.get('versions')!=dict(sorted(expected.items())):raise RuntimeError(f"Artifact Python package version drift: {value.get('versions')}")
    return value


def generation_spec(lock:dict[str,Any],project:dict[str,str],python:dict[str,str])->dict[str,Any]:
    return {'schemaVersion':1,'lockSha256':'sha256:'+sha(LOCK_PATH),'wrapperSha256':'sha256:'+sha(WRAPPER_SOURCE),'pythonRuntime':lock['pythonRuntime'],'pythonPackages':lock['pythonPackages'],'uvProjectPyprojectSha256':project['pyprojectSha256'],'uvLockSha256':project['uvLockSha256'],'pythonExecutableResolvedPath':python['resolvedPath'],'pythonExecutableSha256':python['sha256']}


def probe_wrapper(wrapper:Path)->dict[str,Any]:
    p=run([str(wrapper),'-c',"import json,lxml.etree,pptx,PIL,jsonschema,xlsxwriter,opentelemetry.sdk;print(json.dumps({'status':'PASS','libxml':lxml.etree.LIBXML_VERSION,'libxslt':lxml.etree.LIBXSLT_VERSION}))"],env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},timeout=45)
    if p.returncode:raise RuntimeError('published Artifact Python wrapper probe failed: '+p.stderr[-3000:])
    return json.loads(p.stdout)


def status(stable_root:Path|None=None)->dict[str,Any]:
    lock=load_lock();base=(stable_root or Path(lock['stableRoot']));current=base/'current';result={'schemaVersion':1,'kind':'artifact-python-environment-status','stableRoot':str(base),'stablePython':str(current/'bin/python'),'currentPresent':current.exists() or current.is_symlink(),'ready':False}
    if not current.is_symlink():return result
    try:
        resolved=current.resolve(strict=True)
        if base.resolve() not in resolved.parents:raise RuntimeError('current generation escapes stable root')
        binding=json.loads((resolved/'binding.json').read_text());probe=probe_wrapper(resolved/'bin/python')
        result.update({'ready':True,'generationId':resolved.name,'binding':binding,'probe':probe})
    except Exception as error:result['error']=str(error)
    return result


def build_generation(base:Path,lock:dict[str,Any],project:dict[str,str],python:dict[str,str])->tuple[str,Path,dict[str,Any]]:
    spec=generation_spec(lock,project,python);gid=hashlib.sha256(canonical(spec)).hexdigest();generations=base/'generations';generations.mkdir(parents=True,exist_ok=True);final=generations/gid
    if final.exists():return gid,final,json.loads((final/'binding.json').read_text())
    staging=generations/f'.{gid}.staging-{os.getpid()}'
    if staging.exists():shutil.rmtree(staging)
    staging.mkdir(mode=0o700)
    try:
        venv=staging/'.venv';env={**os.environ,'UV_PROJECT_ENVIRONMENT':str(venv),'PYTHONDONTWRITEBYTECODE':'1'}
        sync=run([str(UV),'sync','--frozen','--offline','--no-dev','--python',str(SYSTEM_PYTHON),'--project',project['project']],env=env,timeout=180)
        if sync.returncode:raise RuntimeError('offline frozen Artifact Python uv sync failed: '+sync.stderr[-5000:])
        observed=dependency_probe(venv/'bin/python',lock['pythonPackages'])
        provenance=staging/'provenance';provenance.mkdir();shutil.copy2(ROOT/lock['uvProject']['path']/'pyproject.toml',provenance/'pyproject.toml');shutil.copy2(ROOT/lock['uvProject']['path']/'uv.lock',provenance/'uv.lock')
        make_read_only(venv);venv_digest=tree_digest(venv)
        bindir=staging/'bin';bindir.mkdir();wrapper=bindir/'python';shutil.copy2(WRAPPER_SOURCE,wrapper);os.chmod(wrapper,0o755)
        binding={**spec,'kind':'artifact-python-generation-binding','generationId':gid,'venvTreeDigest':venv_digest,'lxmlRuntimeLibraries':{'libxml':observed['libxml'],'libxslt':observed['libxslt']},'materializationAuthority':'artifact-owned-uv-lock-frozen-offline-sync','nonClaims':lock['nonClaims']}
        (staging/'binding.json').write_text(json.dumps(binding,sort_keys=True,indent=2)+'\n');os.chmod(staging/'binding.json',0o444)
        probe_wrapper(wrapper)
        os.replace(staging,final)
        return gid,final,binding
    finally:
        if staging.exists():shutil.rmtree(staging)


def apply()->dict[str,Any]:
    if ROOT.resolve()!=MAIN.resolve():raise RuntimeError('Artifact Python environment apply is fenced to canonical /root/projects/ordivon-artifact-v2 source')
    lock=load_lock();project=project_status(lock);python=python_status(lock);base=Path(lock['stableRoot']);base.mkdir(parents=True,exist_ok=True);gid,final,binding=build_generation(base,lock,project,python)
    current=base/'current'
    if current.exists() and not current.is_symlink():raise RuntimeError('Artifact Python current target is not an atomic symlink authority')
    tmp=base/f'.current-{os.getpid()}'
    if tmp.exists() or tmp.is_symlink():tmp.unlink()
    os.symlink(Path('generations')/gid,tmp);os.replace(tmp,current)
    dfd=os.open(base,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(dfd)
    finally:os.close(dfd)
    observed=status(base)
    if not observed.get('ready') or observed.get('generationId')!=gid:raise RuntimeError('Artifact Python current publication did not verify')
    return {'schemaVersion':1,'kind':'artifact-python-environment-materialization-receipt','truthRole':'stable-python-runtime-materialization-not-artifact-acceptance','generationId':gid,'stablePython':str(current/'bin/python'),'binding':binding,'status':observed}


def plan()->dict[str,Any]:
    lock=load_lock();issues=[]
    try:project=project_status(lock);python=python_status(lock);spec=generation_spec(lock,project,python)
    except Exception as error:project=None;python=None;spec=None;issues.append(str(error))
    current=status(Path(lock['stableRoot']))
    desired_generation_id=hashlib.sha256(canonical(spec)).hexdigest() if spec is not None else None
    current_matches_desired=bool(
        desired_generation_id
        and current.get('ready')
        and current.get('generationId')==desired_generation_id
    )
    return {'schemaVersion':1,'kind':'artifact-python-environment-plan','mainSourceAuthority':ROOT.resolve()==MAIN.resolve(),'stableRoot':lock['stableRoot'],'stablePython':lock['stablePython'],'uvProjectReady':project is not None,'pythonReady':python is not None,'generationSpec':spec,'desiredGenerationId':desired_generation_id,'current':current,'currentMatchesDesired':current_matches_desired,'issues':issues,'applyEligible':ROOT.resolve()==MAIN.resolve() and project is not None and python is not None}


def main()->int:
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args();value=apply() if args.apply else plan();print(json.dumps(value,sort_keys=True,indent=2));return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:print(json.dumps({'schemaVersion':1,'kind':'artifact-python-environment-error','error':str(error)},sort_keys=True),file=os.sys.stderr);raise SystemExit(1)
