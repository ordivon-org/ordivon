#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/test-structure.sh
uv run python scripts/test-admission.py
bash scripts/test-bound-entrypoint.sh
uv run python scripts/test-reconciliation.py
bash scripts/test-github-read-positive-control.sh
bash scripts/test-rclone.sh
bash scripts/test-postiz-surface.sh
bash scripts/test-openapi-generator.sh
printf 'PASS Distribution v2 R3 runtime-bound external-first suite\n'
