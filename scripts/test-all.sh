#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/test-structure.sh
uv run python scripts/test-admission.py
bash scripts/test-github-read-positive-control.sh
bash scripts/test-rclone.sh
bash scripts/test-postiz-surface.sh
bash scripts/test-openapi-generator.sh
printf 'PASS Distribution v2 R2 authority-bound external-first suite\n'
