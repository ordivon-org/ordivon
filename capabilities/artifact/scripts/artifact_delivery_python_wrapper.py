#!/usr/bin/env python3
"""Stable Artifact Delivery Python carrier for one frozen uv generation."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys
from pathlib import Path


def _sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def tree_digest(root:Path)->str:
    root=root.resolve();h=hashlib.sha256()
    if not root.is_dir():raise RuntimeError(f'Artifact Python venv missing: {root}')
    for path in sorted(root.rglob('*'),key=lambda p:p.relative_to(root).as_posix()):
        rel=path.relative_to(root).as_posix()
        if path.is_symlink():payload=f'L\0{rel}\0{os.readlink(path)}'.encode()
        elif path.is_dir():payload=f'D\0{rel}\0{path.stat().st_mode & 0o777:o}'.encode()
        elif path.is_file():payload=f'F\0{rel}\0{path.stat().st_mode & 0o777:o}\0{_sha(path)}'.encode()
        else:raise RuntimeError(f'unsupported Artifact Python venv node: {rel}')
        h.update(len(payload).to_bytes(8,'big'));h.update(payload)
    return 'sha256:'+h.hexdigest()


def main()->int:
    generation=Path(__file__).resolve().parents[1];binding_path=generation/'binding.json'
    if not binding_path.is_file():raise RuntimeError('Artifact Python generation binding is absent')
    binding=json.loads(binding_path.read_text())
    if binding.get('schemaVersion')!=1 or binding.get('kind')!='artifact-delivery-python-generation-binding':raise RuntimeError('Artifact Python generation binding contract mismatch')
    if 'sha256:'+_sha(Path(__file__).resolve())!=binding.get('wrapperSha256'):raise RuntimeError('Artifact Python wrapper bytes drifted')
    venv=generation/'.venv'
    if tree_digest(venv)!=binding.get('venvTreeDigest'):raise RuntimeError('Artifact Python uv environment bytes drifted')
    venv_python=venv/'bin/python'
    resolved=venv_python.resolve(strict=True)
    if str(resolved)!=binding.get('pythonExecutableResolvedPath') or 'sha256:'+_sha(resolved)!=binding.get('pythonExecutableSha256'):raise RuntimeError('Artifact Python interpreter bytes drifted')
    expected=dict(binding['pythonPackages'])
    code=("import json,platform;from importlib.metadata import version;import lxml.etree,pptx,PIL,jsonschema,xlsxwriter,opentelemetry.sdk;"
          f"names={json.dumps(sorted(expected))};"
          "print(json.dumps({'python':platform.python_version(),'versions':{n:version(n) for n in names},'libxml':lxml.etree.LIBXML_VERSION,'libxslt':lxml.etree.LIBXSLT_VERSION},sort_keys=True))")
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    probe=subprocess.run([str(venv_python),'-c',code],text=True,capture_output=True,env=env,check=False,timeout=30)
    if probe.returncode:raise RuntimeError('Artifact Python dependency probe failed: '+probe.stderr[-2000:])
    observed=json.loads(probe.stdout)
    if observed.get('python')!=binding.get('pythonRuntime'):raise RuntimeError('Artifact Python runtime version drifted')
    if observed.get('versions')!=dict(sorted(expected.items())):raise RuntimeError(f"Artifact Python package version drift: {observed.get('versions')}")
    libs={'libxml':observed.get('libxml'),'libxslt':observed.get('libxslt')}
    if libs!=binding.get('lxmlRuntimeLibraries'):raise RuntimeError(f'Artifact Python lxml native library identity drift: {libs}')
    os.execve(str(venv_python),[str(venv_python),*sys.argv[1:]],env);return 127

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:print(f'Artifact Python carrier refused execution: {error}',file=sys.stderr);raise SystemExit(126)
