#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'temporal_integration_dispatch_smoke.py'
s=p.read_text()
assert 'ORDIVON_DISTRIBUTION_INTEGRATION_URL' in s
for forbidden in ['ordivon-dist-adapter-smoke-v1','/webhook/ordivon','n8n','issue create','release create','--method POST']:
    assert forbidden not in s,forbidden
assert "externalEffectPerformed') is not False" in s
assert "RetryPolicy(maximum_attempts=2)" in s
print('PASS Distribution Temporal integration adapter remains implementation-neutral')
