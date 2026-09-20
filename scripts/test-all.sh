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
printf 'PASS Distribution deterministic repository reference suite\n'
