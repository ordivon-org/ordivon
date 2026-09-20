#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
err="$(mktemp)"
trap 'rm -f "$err"' EXIT
if uv run python scripts/admission_bound.py --intent evidence/r2-github-public-read-envelope.json --provider-input provider-observation.json --now 2026-09-11T11:30:00Z >/dev/null 2>"$err"; then
  echo 'FAIL bound admission succeeded without Runtime input root' >&2
  exit 1
fi
grep -q 'ORDIVON_INPUT_ROOT is required; use Runtime execBound' "$err"
printf 'PASS bound admission refuses ambient/non-execBound invocation\n'
