#!/usr/bin/env bash
set -euo pipefail
owner=$(cd "$(dirname "$0")/../.." && pwd)
exec /usr/bin/mise -C "$owner" exec -- uv tool run --python 3.13 --from 'opentimelineio==0.18.1' otiotool "$@"
