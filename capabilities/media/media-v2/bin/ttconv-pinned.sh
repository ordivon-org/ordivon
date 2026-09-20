#!/usr/bin/env bash
set -euo pipefail
exec /usr/bin/uv tool run --from 'ttconv==1.2.3' tt "$@"
