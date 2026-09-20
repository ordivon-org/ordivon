#!/usr/bin/env bash
set -euo pipefail
exec /usr/bin/uv tool run --from 'opentimelineio==0.18.1' otiotool "$@"
