from pathlib import Path
import os
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'capabilities/gluetun/acceptance/candidate-consequence.sh'

FAKE_CURL=r'''#!/usr/bin/env python3
import json,sys
a=sys.argv[1:]
url=next((x for x in reversed(a) if x.startswith("http://") or x.startswith("https://")), "")
out=None
if "-o" in a:
    out=a[a.index("-o")+1]
def write(s):
    if out and out!="/dev/null":
        open(out,"w").write(s)
if "openapi.okx.com" in url:
    write('{"code":"0","data":[{"ts":"1"}]}'); sys.exit(0)
if "data-api.binance.vision" in url:
    write('{"serverTime":1}'); sys.exit(0)
if url.startswith("http://127.0.0.1:") or url.startswith("http://10.252.246.1:"):
    sys.exit(7)
code="502" if "api.openai.com" in url else (
    "404" if ("api.anthropic.com" in url or "api.x.com" in url) else
    "401"
)
if "%{http_code}" in a:
    sys.stdout.write(code)
sys.exit(0)
'''

def test_http_502_from_proxy_is_not_provider_consequence_pass():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'curl'
        p.write_text(FAKE_CURL)
        p.chmod(0o755)
        env=os.environ.copy()
        env['PATH']=td+os.pathsep+env['PATH']
        env['PRIVATE_WITNESS_BIND']='127.0.0.1'
        r=subprocess.run(['/bin/bash',str(SCRIPT),'http://fake-proxy.invalid:1'],
                         text=True,capture_output=True,timeout=15,env=env,check=False)
        assert r.returncode != 0, r.stdout
        assert '"standing":"PASS"' not in r.stdout
