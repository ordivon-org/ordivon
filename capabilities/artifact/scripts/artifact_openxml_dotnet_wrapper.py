#!/usr/bin/env python3
from __future__ import annotations
import json,os,sys
from pathlib import Path

def main()->int:
    generation=Path(__file__).resolve().parents[1]
    binding=json.loads((generation/'binding.json').read_text())
    store=Path(str(binding.get('dotnetNixStorePath','')))
    if not str(store).startswith('/nix/store/') or not store.is_dir():raise RuntimeError('bound OpenXML Nix store path is absent or invalid')
    actual=store/'bin/dotnet'
    if not actual.is_file() or not os.access(actual,os.X_OK):raise RuntimeError('bound OpenXML Nix dotnet executable is absent')
    env=dict(os.environ);env['DOTNET_MULTILEVEL_LOOKUP']='0'
    os.execve(str(actual),[str(actual),*sys.argv[1:]],env)
    return 127
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        print(f'Artifact OpenXML dotnet carrier refused execution: {error}',file=sys.stderr);raise SystemExit(126)
