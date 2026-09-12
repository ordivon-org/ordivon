#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/test-structure.sh
uv run python scripts/test-admission.py
uv run python scripts/test-approval-request.py
uv run python scripts/test-effect-authority-producer.py
bash scripts/test-effect-authority-entrypoint.sh
bash scripts/test-bound-entrypoint.sh
uv run python scripts/test-reconciliation.py
bash scripts/test-github-read-positive-control.sh
bash scripts/test-github-provider-readback.sh
bash scripts/test-rclone.sh
bash scripts/test-postiz-surface.sh
bash scripts/test-openapi-generator.sh
printf 'PASS Distribution v2 R6 approval-ingress-ready carrier-coverage suite\n'
