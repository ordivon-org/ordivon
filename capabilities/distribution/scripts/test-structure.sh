#!/usr/bin/env bash
set -euo pipefail
for f in external-lock.json composition-v1.json adapters/*.json contracts/*.json; do jq -e . "$f" >/dev/null; done
python - <<'PYOPA'
import json
from pathlib import Path
import re
import tomllib

tools = tomllib.loads(Path("mise.toml").read_text())["tools"]
provider = json.loads(Path("external-lock.json").read_text())["activated"]["opa"]
version = tools["opa"]
assert provider["release"] == f"v{version}", "OPA source release and local mise version drift"
assert provider["containerImage"] == f"docker.io/openpolicyagent/opa:{version}-static", "OPA OCI tag drift"
assert re.fullmatch(r"sha256:[a-f0-9]{64}", provider["containerDigest"]), "OPA OCI digest invalid"
assert re.fullmatch(r"[a-f0-9]{40}", provider["revision"]), "OPA upstream commit invalid"
print(f"PASS native OPA CLI/OCI digest owner binding: {version}")
PYOPA
# Cross-provider policy must not recreate provider catalogs or authorization matrices.
if grep -Eiq '\b(youtube|tiktok|douyin|bilibili|reddit|xiaohongshu|twitter|github)\b' policy/distribution.rego; then
  echo 'FAIL provider-specific facts leaked into cross-provider policy' >&2
  exit 1
fi
if grep -Eiq '(tweet\.write|tweet\.read|video\.create|youtube\.upload|youtube\.read|reddit-user-action|tiktok-video|douyin-video)' policy/distribution.rego; then
  echo 'FAIL provider authorization catalog leaked into cross-provider policy' >&2
  exit 1
fi
# Caller-supplied effect classification and boolean user authorization are forbidden in v2 intent.
if grep -Eq '"mode"|exactEffectAuthorized' contracts/distribution-intent.schema.json; then
  echo 'FAIL untrusted effect classification or boolean authority leaked into intent contract' >&2
  exit 1
fi
# Retired executable surfaces must not remain wired into CI or forward scripts.
retired_surfaces=(
  'scripts/temporal_integration_dispatch_smoke.py'
  'scripts/test-temporal-integration-boundary.py'
  'scripts/distribution_preflight.py'
  'scripts/test-distribution-preflight.py'
  'contracts/distribution-preflight.schema.json'
  'profiles/steam-linux-directory-r1.json'
)
for retired in "${retired_surfaces[@]}"; do
  matches="$(grep -R -F -n --exclude='test-structure.sh' -- "$retired" .github scripts 2>/dev/null || true)"
  if [ -n "$matches" ]; then
    echo "FAIL retired Distribution surface remains executable: $retired" >&2
    printf '%s\n' "$matches" >&2
    exit 1
  fi
done
printf 'PASS external-first authority-bound structure\n'
