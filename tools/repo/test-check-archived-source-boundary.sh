#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
CHECKER="$SCRIPT_DIR/check_archived_source_boundary.py"
python3 - "$CHECKER" <<'PY'
import importlib.util
import sys
spec = importlib.util.spec_from_file_location("retired_source_boundary", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
cases = (
    ("history.md", "**/*.md", True),
    ("docs/deep/history.md", "**/*.md", True),
    ("docs/deep/history.md", "docs/*.md", False),
    ("productions/w1/source/valid.json", "**/productions/*/source/**", True),
    ("productions/w1/extra/source/invalid.json", "**/productions/*/source/**", False),
)
for path, pattern, expected in cases:
    actual = module.matches_glob(path, pattern)
    if actual is not expected:
        raise SystemExit(f"glob contract mismatch: {path} ~ {pattern}: {actual} != {expected}")
PY
TMP="$(mktemp -d /root/ordivon-migration-tmp/archived-source-boundary-test.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

repo="$TMP/repo"
git init -q -b main "$repo"
git -C "$repo" config user.name test
git -C "$repo" config user.email test@example.invalid
mkdir -p "$repo/docs" "$repo/artifacts/history" "$repo/tests" "$repo/src" "$repo/productions/w1/source"
cat >"$repo/policy.json" <<'EOF'
{
  "schemaVersion": 1,
  "kind": "ordivon.archived-source-reference-policy",
  "id": "legacy",
  "legacyLocator": "/legacy/source",
  "archivedSource": {
    "revision": "deadbeef",
    "standing": "ARCHIVED_IN_PLACE",
    "preserveGitHistoryForHistoricalLookup": true
  },
  "allowedReferenceClasses": [
    {"id": "docs", "globs": ["**/*.md"], "reason": "docs"},
    {"id": "artifacts", "globs": ["**/artifacts/**"], "reason": "history"},
    {"id": "production", "globs": ["**/productions/*/source/**"], "reason": "frozen source"}
  ],
  "allowedExactPaths": [
    {"path": "tests/negative.py", "reason": "negative fixture"}
  ]
}
EOF
printf 'historical /legacy/source\n' >"$repo/docs/history.md"
printf '{"source":"/legacy/source"}\n' >"$repo/artifacts/history/evidence.json"
printf 'assert "/legacy/source"\n' >"$repo/tests/negative.py"
printf 'clean = true\n' >"$repo/src/current.py"
printf '/legacy/source\n' >"$repo/productions/w1/source/valid.json"
git -C "$repo" add .
git -C "$repo" commit -q -m baseline

python3 "$CHECKER" --repo "$repo" --policy policy.json
python3 "$CHECKER" --repo "$repo" --policy policy.json --json >"$TMP/pass.json"
python3 - "$TMP/pass.json" <<'PY'
import json,sys
v=json.load(open(sys.argv[1]))
assert v["status"] == "PASS"
assert v["trackedReferenceFileCount"] == 5
assert v["forbiddenReferenceFileCount"] == 0
PY

mkdir -p "$repo/productions/w1/extra/source"
printf '/legacy/source\n' >"$repo/productions/w1/extra/source/invalid.json"
git -C "$repo" add productions/w1/extra/source/invalid.json
set +e
python3 "$CHECKER" --repo "$repo" --policy policy.json --json >"$TMP/path-fail.json"
path_rc=$?
set -e
test "$path_rc" -eq 1
python3 - "$TMP/path-fail.json" <<'PY'
import json,sys
v=json.load(open(sys.argv[1]))
assert v["status"] == "FAIL"
assert v["forbidden"] == ["productions/w1/extra/source/invalid.json"]
PY
git -C "$repo" rm -fq -- productions/w1/extra/source/invalid.json

printf 'LEGACY = "/legacy/source"\n' >"$repo/src/current.py"
set +e
python3 "$CHECKER" --repo "$repo" --policy policy.json --json >"$TMP/fail.json"
rc=$?
set -e
test "$rc" -eq 1
python3 - "$TMP/fail.json" <<'PY'
import json,sys
v=json.load(open(sys.argv[1]))
assert v["status"] == "FAIL"
assert v["forbidden"] == ["src/current.py"]
PY

echo "PASS archived-source boundary smoke"
