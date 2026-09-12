#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
err="$(mktemp)"
trap 'rm -f "$err"' EXIT
if uv run python scripts/produce_effect_authority.py --intent evidence/r3-github-create-issue-intent.json --approval-input approval.json --now 2026-09-12T00:20:00Z >/dev/null 2>"$err"; then
  echo 'FAIL effect authority producer accepted ambient approval path' >&2
  exit 1
fi
grep -q 'ORDIVON_INPUT_ROOT is required; approval must arrive through Runtime execBound' "$err"
printf 'PASS effect authority producer refuses ambient approval input\n'
