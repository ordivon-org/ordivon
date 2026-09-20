#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
number=72
expected_id=5036001838
expected_node='I_kwDOSEmM188AAAABLCtKLg'
body="$(mktemp)"
trap 'rm -f "$body"' EXIT
gh api "repos/ordivon-org/ordivon-runtime/issues/$number" > "$body"
actual_id="$(jq -r '.id' "$body")"
actual_node="$(jq -r '.node_id' "$body")"
actual_number="$(jq -r '.number' "$body")"
[[ "$actual_id" == "$expected_id" ]] || { echo "FAIL github readback id=$actual_id expected=$expected_id" >&2; exit 1; }
[[ "$actual_node" == "$expected_node" ]] || { echo "FAIL github readback node_id=$actual_node expected=$expected_node" >&2; exit 1; }
[[ "$actual_number" == "$number" ]] || { echo "FAIL github readback number=$actual_number expected=$number" >&2; exit 1; }
printf 'PASS GitHub provider-native object readback issue=%s id=%s node=%s state=%s\n' \
  "$actual_number" "$actual_id" "$actual_node" "$(jq -r '.state' "$body")"
