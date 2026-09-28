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

# Repository-relative archived trees ignore self-references, pin exact Git tree identity,
# and fail closed on any new outside reference.
mkdir -p "$repo/meta/next"
printf 'self meta/next/ historical marker\n' >"$repo/meta/next/record.txt"
printf 'historical meta/next/record.txt\n' >"$repo/docs/relative-history.md"
git -C "$repo" add .
git -C "$repo" commit -q -m relative-baseline
tree_oid="$(git -C "$repo" rev-parse HEAD:meta/next)"
python3 - "$repo/relative-policy.json" "$tree_oid" <<'PY2'
import json,sys
path,tree=sys.argv[1:]
json.dump({
  "schemaVersion":1,
  "kind":"ordivon.archived-source-reference-policy",
  "id":"relative-tree",
  "legacyLocator":"meta/next/",
  "archivedSource":{"revision":"deadbeef","standing":"ARCHIVED_IN_PLACE","preserveGitHistoryForHistoricalLookup":True},
  "archivedTree":{"path":"meta/next","expectedGitTree":tree},
  "allowedReferenceClasses":[],
  "allowedExactPaths":[{"path":"docs/relative-history.md","reason":"historical navigation"}]
},open(path,"w"),indent=2)
PY2
git -C "$repo" add relative-policy.json
git -C "$repo" commit -q -m relative-policy
python3 "$CHECKER" --repo "$repo" --policy relative-policy.json
printf 'new meta/next/current\n' >"$repo/src/current.py"
git -C "$repo" add src/current.py
git -C "$repo" commit -q -m forbidden-relative-reference
set +e
python3 "$CHECKER" --repo "$repo" --policy relative-policy.json >/dev/null
rc=$?
set -e
test "$rc" -eq 1
git -C "$repo" reset -q --hard HEAD~1
printf 'mutated\n' >>"$repo/meta/next/record.txt"
git -C "$repo" add meta/next/record.txt
git -C "$repo" commit -q -m mutate-archive
set +e
python3 "$CHECKER" --repo "$repo" --policy relative-policy.json >/dev/null
rc=$?
set -e
test "$rc" -eq 1

echo "PASS archived-source boundary smoke"
