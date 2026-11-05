#!/usr/bin/env bash
set -euo pipefail
owner=$(cd "$(dirname "$0")/../.." && pwd)
exec /usr/bin/mise -C "$owner" exec -- uv tool run --from 'ttconv==1.2.3' tt "$@"
