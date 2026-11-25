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
TMP="$(mktemp -d)"
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
python3 - "$repo" <<'PY'
import os
import sys
from pathlib import Path
root = Path(sys.argv[1])
(root / "docs" / "line\nbreak.md").write_text("/legacy/source\n", encoding="utf-8")
(root / "docs" / os.fsdecode(b"\xff.md")).write_text("/legacy/source\n", encoding="utf-8")
PY
git -C "$repo" add .
git -C "$repo" commit -q -m baseline

python3 "$CHECKER" --repo "$repo" --policy policy.json
python3 "$CHECKER" --repo "$repo" --policy policy.json --json >"$TMP/pass.json"
python3 - "$TMP/pass.json" <<'PY'
import json,sys
v=json.load(open(sys.argv[1]))
assert v["status"] == "PASS"
assert v["trackedReferenceFileCount"] == 7
assert {row["path"] for row in v["allowed"]} >= {
    "docs/line\nbreak.md", "docs/\udcff.md"
}
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

# Inverse retirement check must include the staged source, even when its
# forbidden reference is hidden by an unstaged edit or sparse worktree.
git -C "$repo" add src/current.py
printf 'clean = true\n' >"$repo/src/current.py"
set +e
python3 "$CHECKER" --repo "$repo" --policy policy.json --json >"$TMP/staged-fail.json"
stage_rc=$?
set -e
# Collect both independent controls before asserting.
git -C "$repo" update-index --skip-worktree src/current.py
rm -- "$repo/src/current.py"
set +e
python3 "$CHECKER" --repo "$repo" --policy policy.json --json >"$TMP/sparse-fail.json"
sparse_rc=$?
set -e
printf 'native staged-hidden rc=%s sparse-hidden rc=%s\n' "$stage_rc" "$sparse_rc"
git -C "$repo" update-index --no-skip-worktree src/current.py
git -C "$repo" checkout -- src/current.py
test "$stage_rc" -eq 1
test "$sparse_rc" -eq 1
python3 - "$TMP/staged-fail.json" "$TMP/sparse-fail.json" <<'PYTEST'
import json,sys
for path in sys.argv[1:]:
    v=json.load(open(path))
    assert v["status"]=="FAIL"
    assert v["forbidden"]==["src/current.py"]
PYTEST
# Foreign repository/index selectors must not hide the intended subject.
foreign="$TMP/foreign"
git init -q "$foreign"
git -C "$foreign" config user.name test
git -C "$foreign" config user.email test@example.invalid
cp "$repo/policy.json" "$foreign/policy.json"
git -C "$foreign" add policy.json
git -C "$foreign" commit -qm foreign
set +e
env GIT_DIR="$foreign/.git" GIT_WORK_TREE="$foreign" GIT_INDEX_FILE="$foreign/.git/index" \
  python3 "$CHECKER" --repo "$repo" --policy policy.json --json >"$TMP/foreign-fail.json"
foreign_rc=$?
set -e
test "$foreign_rc" -eq 1
python3 - "$TMP/foreign-fail.json" <<'PYTEST'
import json,sys
v=json.load(open(sys.argv[1]))
assert v["forbidden"] == ["src/current.py"]
assert v["runtimeConsumerStanding"] == "UNKNOWN"
assert v["retirementAdmissible"] is False
PYTEST

# An unresolved three-stage index is not a complete stage-0 source set.
# A clean worktree and clean stage 2 can hide a prohibited stage 3 object.
base="$(git -C "$repo" rev-parse HEAD:src/current.py)"
ours="$(printf 'clean ours\n' | git -C "$repo" hash-object -w --stdin)"
theirs="$(git -C "$repo" rev-parse :src/current.py)"
printf 'clean ours\n' >"$repo/src/current.py"
printf '0 %040d\tsrc/current.py\n100644 %s 1\tsrc/current.py\n100644 %s 2\tsrc/current.py\n100644 %s 3\tsrc/current.py\n' \
  0 "$base" "$ours" "$theirs" | git -C "$repo" update-index --index-info
set +e
python3 "$CHECKER" --repo "$repo" --policy policy.json --json >"$TMP/unmerged.json" 2>"$TMP/unmerged.err"
unmerged_rc=$?
set -e
printf 'unmerged native rc=%s\n' "$unmerged_rc"
test "$unmerged_rc" -ne 0
test ! -s "$TMP/unmerged.json"
grep -F 'unmerged index' "$TMP/unmerged.err"
printf 'LEGACY = "/legacy/source"\n' >"$repo/src/current.py"
git -C "$repo" add src/current.py

# Missing staged blob: native grep may exit 0 or 1 with diagnostics.
# This is an incomplete observation, not a legitimate PASS/FAIL verdict.
git -C "$repo" config remote.origin.promisor true
git -C "$repo" config remote.origin.partialclonefilter blob:none
git -C "$repo" config remote.origin.url "$TMP/unavailable-origin"
oid="$(git -C "$repo" rev-parse :src/current.py)"
rm -- "$repo/.git/objects/${oid:0:2}/${oid:2}"
set +e
python3 "$CHECKER" --repo "$repo" --policy policy.json --json >"$TMP/missing.json" 2>"$TMP/missing.err"
missing_rc=$?
set -e
test "$missing_rc" -ne 0
test ! -s "$TMP/missing.json"
grep -F 'observation incomplete' "$TMP/missing.err"
echo "PASS archived-source boundary smoke"
