#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 /absolute/path/to/zap.sh" >&2
  exit 64
fi
ZAP_SH=$1
if [[ "$ZAP_SH" != /* || ! -x "$ZAP_SH" ]]; then
  echo "zap.sh must be an absolute executable path" >&2
  exit 64
fi

REPO=$(cd "$(dirname "$0")/.." && pwd)
ROOT=/tmp/ordivon-security-v2-zap-r1
TARGET=http://127.0.0.1:18080
PROXY_PORT=19090
EXPECTED_VERSION=2.17.0

VERSION=$("$ZAP_SH" -version 2>/dev/null | tail -n 1)
if [[ "$VERSION" != "$EXPECTED_VERSION" ]]; then
  echo "expected ZAP $EXPECTED_VERSION, observed $VERSION" >&2
  exit 65
fi

if ss -lnt | grep -Eq ":(18080|${PROXY_PORT})\\b"; then
  echo "required local acceptance port is already in use" >&2
  exit 66
fi

rm -rf "$ROOT"
mkdir -p "$ROOT/report" "$ROOT/zap-home"
: > "$ROOT/requests.log"

python - "$ROOT" "$TARGET" <<'PY'
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
target = sys.argv[2]
authority = {
    "authorityId": "security-authority:zap-local-r1",
    "actorId": "actor:security-operator",
    "zoneRefs": [target],
    "capabilities": ["security.active_scan"],
}
authority["authorityDigest"] = "sha256:" + hashlib.sha256(
    json.dumps(authority, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
request = {
    "requestId": "security-effect-request:zap-local-r1",
    "actorId": "actor:security-operator",
    "authorityId": authority["authorityId"],
    "zoneRef": target,
    "capability": "security.active_scan",
    "effectType": "owasp-zap.active-scan",
    "targetUrl": target,
}
request["requestDigest"] = "sha256:" + hashlib.sha256(
    json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
with (root / "admission-input.json").open("w") as handle:
    json.dump({"actorIds": [request["actorId"]], "authorities": [authority], "request": request}, handle, indent=2)
    handle.write("\n")
PY

opa eval -f json \
  -d "$REPO/policies/effect_admission.rego" \
  -i "$ROOT/admission-input.json" \
  'data.ordivon.security.v2.effect_admission.decision' \
  > "$ROOT/admission-eval.json"

python - "$ROOT" <<'PY'
import json
import pathlib
import sys
root = pathlib.Path(sys.argv[1])
eval_doc = json.loads((root / "admission-eval.json").read_text())
decision = eval_doc["result"][0]["expressions"][0]["value"]
if not decision.get("admitted"):
    raise SystemExit(f"active scan not admitted: {decision}")
if decision.get("zoneRef") != "http://127.0.0.1:18080" or decision.get("capability") != "security.active_scan":
    raise SystemExit(f"unexpected admission binding: {decision}")
(root / "admission-decision.json").write_text(json.dumps(decision, indent=2) + "\n")
PY

cp "$REPO/profiles/zap/local-authorized-r1.yaml" "$ROOT/plan.yaml"
python "$REPO/fixtures/zap_reflected_xss_server.py" --host 127.0.0.1 --port 18080 --log "$ROOT/requests.log" \
  > "$ROOT/server.stdout" 2> "$ROOT/server.stderr" &
TARGET_PID=$!
cleanup() {
  kill "$TARGET_PID" 2>/dev/null || true
  wait "$TARGET_PID" 2>/dev/null || true
}
trap cleanup EXIT

ready=false
for _ in $(seq 1 50); do
  if curl -fsS "$TARGET/" >/dev/null 2>&1; then
    ready=true
    break
  fi
  sleep 0.1
done
if [[ "$ready" != true ]]; then
  echo "local target did not become ready" >&2
  exit 67
fi
curl -fsS "$TARGET/search?q=acceptance-seed" >/dev/null

timeout 150s "$ZAP_SH" -cmd -host 127.0.0.1 -port "$PROXY_PORT" -dir "$ROOT/zap-home" -autorun "$ROOT/plan.yaml" \
  > "$ROOT/zap.stdout" 2> "$ROOT/zap.stderr"

test -s "$ROOT/report/zap-report.json"
python - "$ROOT" <<'PY'
import hashlib
import json
import pathlib
import sys
root = pathlib.Path(sys.argv[1])
report = json.loads((root / "report/zap-report.json").read_text())
alerts = [a for site in report.get("site", []) for a in site.get("alerts", [])]
xss = [a for a in alerts if str(a.get("pluginid")) == "40012"]
request_count = sum(1 for _ in (root / "requests.log").open())
if report.get("@version") != "2.17.0":
    raise SystemExit(f"unexpected report version: {report.get('@version')}")
if len(report.get("site", [])) != 1:
    raise SystemExit(f"expected exactly one site: {len(report.get('site', []))}")
if len(xss) != 1:
    raise SystemExit(f"expected exactly one reflected-XSS alert, observed {len(xss)}")
if request_count <= 5:
    raise SystemExit(f"active scan generated too few target requests: {request_count}")
files = [
    "admission-input.json",
    "admission-decision.json",
    "plan.yaml",
    "report/zap-report.json",
    "requests.log",
]
digests = {}
for rel in files:
    digests[rel] = "sha256:" + hashlib.sha256((root / rel).read_bytes()).hexdigest()
summary = {
    "schemaVersion": 1,
    "kind": "ordivon.security.zap-authorized-local-acceptance",
    "standing": "AUTHORIZED_ACTIVE_SCAN_VERIFIED",
    "target": "http://127.0.0.1:18080",
    "zapVersion": report.get("@version"),
    "requestCount": request_count,
    "alertCount": len(alerts),
    "reflectedXss40012Count": len(xss),
    "evidenceDigests": digests,
}
(root / "acceptance-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(json.dumps(summary, sort_keys=True))
PY
