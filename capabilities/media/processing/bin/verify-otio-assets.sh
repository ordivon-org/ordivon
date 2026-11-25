#!/usr/bin/env bash
set -euo pipefail
owner=$(cd "$(dirname "$0")/../.." && pwd)
export UV_PYTHON=3.13
export PYTHONPATH="$owner/src"
exec /usr/bin/mise -C "$owner" exec -- uv run --no-project --with 'opentimelineio==0.18.1' --with 'jsonschema==4.26.0' python -m ordivon_studio.editorial_asset_binding "$@"
