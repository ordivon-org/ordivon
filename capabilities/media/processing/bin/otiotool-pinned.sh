#!/usr/bin/env bash
set -euo pipefail
owner=$(cd "$(dirname "$0")/../.." && pwd)
# OTIO 0.18.1 bundles pybind11 2.13.6, whose Python configuration fails
# under Studio's CPython 3.15. Bind only this provider to a working interpreter.
# Do not downgrade Media Core or replace the native OTIO provider.
export UV_PYTHON=3.13
exec /usr/bin/mise -C "$owner" exec -- uv tool run --from 'opentimelineio==0.18.1' otiotool "$@"
