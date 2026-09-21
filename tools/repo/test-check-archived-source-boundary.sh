#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
CHECKER="$SCRIPT_DIR/check_archived_source_boundary.py"
TMP="$(mktemp -d /root/ordivon-migration-tmp/archived-source-boundary-test.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

repo="$TMP/repo"
git init -q -b main "$repo"
git -C "$repo" config user.name test
git -C "$repo" config user.email test@example.invalid
mkdir -p "$repo/docs" "$repo/artifacts/history" "$repo/tests" "$repo/src"
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
    {"id": "artifacts", "globs": ["**/artifacts/**"], "reason": "history"}
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
git -C "$repo" add .
git -C "$repo" commit -q -m baseline

python3 "$CHECKER" --repo "$repo" --policy policy.json
python3 "$CHECKER" --repo "$repo" --policy policy.json --json >"$TMP/pass.json"
python3 - "$TMP/pass.json" <<'PY'
import json,sys
v=json.load(open(sys.argv[1]))
assert v["status"] == "PASS"
assert v["trackedReferenceFileCount"] == 4
assert v["forbiddenReferenceFileCount"] == 0
PY

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
