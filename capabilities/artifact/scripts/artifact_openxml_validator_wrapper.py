#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,os
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

import subprocess,sys

def main()->int:
    if len(sys.argv)!=2:
        print('usage: validate-openxml <artifact.pptx|artifact.docx|artifact.xlsx>',file=sys.stderr);return 2
    generation=Path(__file__).resolve().parents[1]
    binding=json.loads((generation/'binding.json').read_text())
    validator=generation/'validator'
    if tree_digest(validator)!=binding['validatorTreeDigest']: raise RuntimeError('OpenXML validator tree drifted')
    dotnet=generation/'bin/dotnet';dll=validator/'ArtifactOpenXmlValidator.dll'
    completed=subprocess.run([str(dotnet),str(dll),sys.argv[1]],check=False)
    return completed.returncode
if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as error:
        print(f'Artifact OpenXML validator carrier refused execution: {error}',file=sys.stderr);raise SystemExit(126)
