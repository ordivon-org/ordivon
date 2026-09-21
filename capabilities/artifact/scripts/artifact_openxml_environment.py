#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def tree_digest(root:Path)->str:
    root=root.resolve();h=hashlib.sha256()
    for path in sorted(root.rglob('*'),key=lambda p:p.relative_to(root).as_posix()):
        rel=path.relative_to(root).as_posix()
        if path.is_symlink():
            target=os.readlink(path);tp=Path(target)
            if tp.is_absolute() or '..' in tp.parts: raise RuntimeError(f'unsafe generation symlink: {rel} -> {target}')
            payload=f'L\\0{rel}\\0{target}'.encode()
        elif path.is_dir(): payload=f'D\\0{rel}\\0{path.stat().st_mode & 0o777:o}'.encode()
        elif path.is_file(): payload=f'F\\0{rel}\\0{path.stat().st_mode & 0o777:o}\\0{sha(path)}'.encode()
        else: raise RuntimeError(f'unsupported generation node: {rel}')
        h.update(len(payload).to_bytes(8,'big'));h.update(payload)
    return 'sha256:'+h.hexdigest()

import argparse
import shutil
import subprocess
import sys
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
MAIN=Path('/root/projects/ordivon/capabilities/artifact')
LOCK_PATH=ROOT/'artifact-delivery/openxml-runtime-v1.lock.json'
DOTNET_WRAPPER=ROOT/'scripts/artifact_openxml_dotnet_wrapper.py'
VALIDATOR_WRAPPER=ROOT/'scripts/artifact_openxml_validator_wrapper.py'
EXTERNAL_EVIDENCE=ROOT/'scripts/artifact_openxml_external_evidence.py'
NIX=Path('/usr/bin/nix')
NIX_FLAKE=ROOT/'artifact-delivery/openxml-nix'
SYSTEM_PYTHON=Path(os.environ.get('ARTIFACT_PYTHON','/root/.local/share/mise/installs/python/3.14.7/bin/python3.14'))
NIX_FEATURES=['--extra-experimental-features','nix-command flakes']

def canonical(v:Any)->bytes:return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def run(args:list[str],**kwargs:Any)->subprocess.CompletedProcess[str]:return subprocess.run(args,text=True,capture_output=True,check=False,**kwargs)
def load_lock()->dict[str,Any]:
    v=json.loads(LOCK_PATH.read_text())
    if v.get('schemaVersion')!=1 or v.get('kind')!='artifact-openxml-runtime-lock':raise RuntimeError('OpenXML runtime lock invalid')
    return v

def nix_dotnet_status(lock:dict[str,Any])->dict[str,Any]:
    cfg=lock['nixDotnet']; flake=ROOT/cfg['flake']; flake_lock=flake/'flake.lock'
    if not NIX.is_file() or not flake_lock.is_file():raise RuntimeError('Artifact OpenXML Nix authority is absent')
    if 'sha256:'+sha(flake_lock)!=cfg['flakeLockSha256']:raise RuntimeError('Artifact OpenXML flake.lock digest drift')
    locked=json.loads(flake_lock.read_text()).get('nodes',{}).get('nixpkgs',{}).get('locked',{})
    if locked.get('rev')!=cfg['nixpkgsRevision'] or locked.get('narHash')!=cfg['nixpkgsNarHash']:raise RuntimeError('Artifact OpenXML nixpkgs lock identity drift')
    target=f"path:{flake}#{cfg['package']}"
    built=run([str(NIX),*NIX_FEATURES,'build','--no-link','--print-out-paths',target],timeout=300)
    if built.returncode:raise RuntimeError('Artifact OpenXML Nix closure build failed: '+built.stderr[-4000:])
    paths=[line.strip() for line in built.stdout.splitlines() if line.strip().startswith('/nix/store/')]
    if len(paths)!=1:raise RuntimeError(f'Artifact OpenXML Nix closure did not resolve exactly one store path: {paths}')
    store=Path(paths[0]); dotnet=store/'bin/dotnet'
    probe=run([str(dotnet),'--version'],timeout=60); version=probe.stdout.strip()
    if probe.returncode or version!=cfg['expectedSdkVersion']:raise RuntimeError(f'Artifact OpenXML Nix SDK drift: {version!r}')
    info_proc=run([str(NIX),*NIX_FEATURES,'path-info','--json-format','1','--json',str(store)],timeout=60)
    if info_proc.returncode:raise RuntimeError('Artifact OpenXML Nix path-info failed: '+info_proc.stderr[-2000:])
    info=json.loads(info_proc.stdout).get(str(store),{}); nar_hash=info.get('narHash')
    if not isinstance(nar_hash,str) or not nar_hash.startswith('sha256-'):raise RuntimeError('Artifact OpenXML Nix narHash missing')
    return {'storePath':str(store),'narHash':nar_hash,'observedSdkVersion':version,'flakeLockSha256':cfg['flakeLockSha256'],'nixpkgsRevision':cfg['nixpkgsRevision']}

def nuget_sources(lock:dict[str,Any])->list[dict[str,str]]:
    result=[]
    for row in [*lock['nugetPackages'], *lock.get('sdkRestoreSupportPackages',[])]:
        package=row['id'].lower();version=row['version']
        path=Path('/root/.nuget/packages')/package/version/f'{package}.{version}.nupkg'
        if not path.is_file():raise RuntimeError(f'NuGet package absent: {row["id"]} {version}')
        observed=sha(path)
        if observed!=row['nupkgSha256']:raise RuntimeError(f'NuGet package digest drift: {row["id"]}')
        result.append({'id':row['id'],'version':version,'path':str(path),'sha256':'sha256:'+observed})
    return result

def source_digests(lock:dict[str,Any])->dict[str,str]:
    result={}
    for key in ('sourceProject','sourceProgram'):
        path=ROOT/lock[key]
        if not path.is_file():raise RuntimeError(f'OpenXML validator source absent: {path}')
        result[key]='sha256:'+sha(path)
    return result

def generation_spec(lock:dict[str,Any],dotnet:dict[str,Any],nuget:list[dict[str,str]])->dict[str,Any]:
    validator_ids={row['id'] for row in lock['nugetPackages']}
    return {'schemaVersion':1,'methodId':lock['methodId'],'lockSha256':'sha256:'+sha(LOCK_PATH),'dotnetWrapperSha256':'sha256:'+sha(DOTNET_WRAPPER),'validatorWrapperSha256':'sha256:'+sha(VALIDATOR_WRAPPER),'dotnetNixStorePath':dotnet['storePath'],'dotnetNixNarHash':dotnet['narHash'],'artifactNixFlakeLockSha256':dotnet['flakeLockSha256'],'nixpkgsRevision':dotnet['nixpkgsRevision'],'observedDotnetSdk':dotnet['observedSdkVersion'],'targetFramework':lock['targetFramework'],'nugetPackages':[{k:r[k] for k in ('id','version','sha256')} for r in nuget if r['id'] in validator_ids],'sdkRestoreSupportPackages':[{k:r[k] for k in ('id','version','sha256')} for r in nuget if r['id'] not in validator_ids],**source_digests(lock)}

def make_read_only(root:Path)->None:
    for p in root.rglob('*'):
        if p.is_symlink():continue
        if p.is_dir():os.chmod(p,0o555)
        elif p.is_file():os.chmod(p,0o555 if os.access(p,os.X_OK) else 0o444)
    os.chmod(root,0o555)

def build_generation(base:Path,lock:dict[str,Any],dotnet_authority:dict[str,Any],nuget:list[dict[str,str]])->tuple[str,Path,dict[str,Any]]:
    spec=generation_spec(lock,dotnet_authority,nuget);gid=hashlib.sha256(canonical(spec)).hexdigest();gens=base/'generations';gens.mkdir(parents=True,exist_ok=True);final=gens/gid
    if final.exists():return gid,final,json.loads((final/'binding.json').read_text())
    staging=gens/f'.{gid}.staging-{os.getpid()}'
    if staging.exists():shutil.rmtree(staging)
    staging.mkdir(mode=0o700)
    try:
        feed=staging/'provenance/nuget';feed.mkdir(parents=True)
        for row in nuget:shutil.copy2(row['path'],feed/Path(row['path']).name)
        shutil.copy2(NIX_FLAKE/'flake.nix',staging/'provenance/openxml-nix-flake.nix');shutil.copy2(NIX_FLAKE/'flake.lock',staging/'provenance/openxml-nix-flake.lock')
        source=staging/'source';source.mkdir();shutil.copy2(ROOT/lock['sourceProject'],source/'ArtifactOpenXmlValidator.csproj');shutil.copy2(ROOT/lock['sourceProgram'],source/'Program.cs')
        packages=staging/'packages';obj=staging/'obj';out=staging/'validator';out.mkdir()
        env={**os.environ,'DOTNET_MULTILEVEL_LOOKUP':'0','NUGET_PACKAGES':str(packages),'DOTNET_CLI_HOME':str(staging/'dotnet-home')}
        dotnet=Path(dotnet_authority['storePath'])/'bin/dotnet'
        restore=run([str(dotnet),'restore',str(source/'ArtifactOpenXmlValidator.csproj'),'--source',str(feed),'--packages',str(packages),'--ignore-failed-sources'],env=env,timeout=120)
        if restore.returncode:raise RuntimeError('private-feed OpenXML restore failed: '+restore.stderr[-4000:]+restore.stdout[-2000:])
        build=run([str(dotnet),'build',str(source/'ArtifactOpenXmlValidator.csproj'),'-c','Release','--no-restore','-o',str(out)],env=env,timeout=120)
        if build.returncode:raise RuntimeError('OpenXML validator build failed: '+build.stderr[-4000:]+build.stdout[-2000:])
        shutil.rmtree(packages,ignore_errors=True);shutil.rmtree(staging/'dotnet-home',ignore_errors=True)
        bindir=staging/'bin';bindir.mkdir();shutil.copy2(DOTNET_WRAPPER,bindir/'dotnet');shutil.copy2(VALIDATOR_WRAPPER,bindir/'validate-openxml');os.chmod(bindir/'dotnet',0o755);os.chmod(bindir/'validate-openxml',0o755)
        if obj.exists():shutil.rmtree(obj,ignore_errors=True)
        make_read_only(out)
        binding={**spec,'kind':'artifact-openxml-generation-binding','generationId':gid,'validatorTreeDigest':tree_digest(out),'materializationAuthority':'artifact-owned-nix-dotnet-closure-plus-exact-private-nuget-feed','nonClaims':lock['nonClaims']}
        (staging/'binding.json').write_text(json.dumps(binding,sort_keys=True,indent=2)+'\n');os.chmod(staging/'binding.json',0o444)
        probe=run([str(bindir/'dotnet'),'--version'],timeout=60)
        if probe.returncode or probe.stdout.strip()!=dotnet_authority['observedSdkVersion']:raise RuntimeError('stable OpenXML Nix dotnet wrapper probe failed: '+probe.stderr[-2000:])
        os.replace(staging,final)
        return gid,final,binding
    finally:
        if staging.exists():shutil.rmtree(staging)

def verify_external_evidence(validator:Path)->dict[str,Any]:
    if not EXTERNAL_EVIDENCE.is_file():raise RuntimeError('OpenXML external evidence runner absent')
    completed=run([str(SYSTEM_PYTHON),str(EXTERNAL_EVIDENCE),'--validator',str(validator)],timeout=120)
    if completed.returncode:raise RuntimeError('OpenXML external evidence gate failed: '+completed.stderr[-2000:]+completed.stdout[-4000:])
    try:result=json.loads(completed.stdout)
    except Exception as error:raise RuntimeError('OpenXML external evidence gate returned invalid JSON') from error
    if result.get('methodId')!='artifact.openxml.conformance.v1':raise RuntimeError('OpenXML external evidence method mismatch')
    if result.get('standing')!='PASS_BOUNDED_EXTERNAL_EVIDENCE':raise RuntimeError('OpenXML external evidence standing is not PASS_BOUNDED_EXTERNAL_EVIDENCE')
    if result.get('methodPromotion')!='GRADUATED_BOUNDED_STRUCTURAL_GATE':raise RuntimeError('OpenXML external evidence does not permit bounded method promotion')
    if result.get('ivvStanding')!='NOT_CLAIMED':raise RuntimeError('OpenXML external evidence must preserve IVV NOT_CLAIMED')
    if result.get('corpusDigestMatchesFreeze') is not True:raise RuntimeError('OpenXML external evidence corpus digest drift')
    return result

def status(base:Path|None=None)->dict[str,Any]:
    lock=load_lock();root=base or Path(lock['stableRoot']);current=root/'current';result={'schemaVersion':1,'kind':'artifact-openxml-environment-status','stableRoot':str(root),'stableDotnet':str(current/'bin/dotnet'),'stableValidator':str(current/'bin/validate-openxml'),'currentPresent':current.exists() or current.is_symlink(),'ready':False}
    if not current.is_symlink():return result
    try:
        resolved=current.resolve(strict=True)
        if root.resolve() not in resolved.parents:raise RuntimeError('OpenXML current escapes stable root')
        binding=json.loads((resolved/'binding.json').read_text())
        p=run([str(resolved/'bin/dotnet'),'--version'],timeout=60)
        if p.returncode or p.stdout.strip()!=binding['observedDotnetSdk']:raise RuntimeError('OpenXML stable dotnet probe failed')
        result.update({'ready':True,'generationId':resolved.name,'binding':binding,'dotnetVersion':p.stdout.strip()})
    except Exception as e:result['error']=str(e)
    return result

def plan()->dict[str,Any]:
    lock=load_lock();issues=[]
    try:dotnet=nix_dotnet_status(lock);ng=nuget_sources(lock);spec=generation_spec(lock,dotnet,ng)
    except Exception as e:dotnet=None;ng=[];spec=None;issues.append(str(e))
    current=status(Path(lock['stableRoot']))
    return {'schemaVersion':1,'kind':'artifact-openxml-environment-plan','mainSourceAuthority':ROOT.resolve()==MAIN.resolve(),'nixDotnetReady':dotnet is not None,'nugetClosureReady':bool(ng),'generationSpec':spec,'current':current,'issues':issues,'applyEligible':ROOT.resolve()==MAIN.resolve() and dotnet is not None and bool(ng)}

def apply()->dict[str,Any]:
    if ROOT.resolve()!=MAIN.resolve():raise RuntimeError('OpenXML environment apply is fenced to canonical /root/projects/ordivon/capabilities/artifact source')
    lock=load_lock();dotnet=nix_dotnet_status(lock);ng=nuget_sources(lock);base=Path(lock['stableRoot']);base.mkdir(parents=True,exist_ok=True);gid,final,binding=build_generation(base,lock,dotnet,ng)
    external_evidence=verify_external_evidence(final/'bin/validate-openxml')
    current=base/'current'
    if current.exists() and not current.is_symlink():raise RuntimeError('OpenXML current is not atomic symlink authority')
    tmp=base/f'.current-{os.getpid()}'
    if tmp.exists() or tmp.is_symlink():tmp.unlink()
    os.symlink(Path('generations')/gid,tmp);os.replace(tmp,current)
    dfd=os.open(base,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(dfd)
    finally:os.close(dfd)
    observed=status(base)
    if not observed.get('ready') or observed.get('generationId')!=gid:raise RuntimeError('OpenXML publication did not verify')
    return {'schemaVersion':1,'kind':'artifact-openxml-environment-materialization-receipt','truthRole':'stable-openxml-method-runtime-materialization-not-subject-conformance','generationId':gid,'stableDotnet':lock['stableDotnet'],'stableValidator':lock['stableValidator'],'binding':binding,'externalEvidence':{'corpusId':external_evidence['corpusId'],'corpusResultDigest':external_evidence['corpusResultDigest'],'standing':external_evidence['standing'],'ivvStanding':external_evidence['ivvStanding'],'methodPromotion':external_evidence['methodPromotion']},'status':observed}

def main()->int:
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args();print(json.dumps(apply() if args.apply else plan(),sort_keys=True,indent=2));return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as e:print(json.dumps({'schemaVersion':1,'kind':'artifact-openxml-environment-error','error':str(e)},sort_keys=True),file=sys.stderr);raise SystemExit(1)
