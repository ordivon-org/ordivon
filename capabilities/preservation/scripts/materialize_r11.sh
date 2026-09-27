#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)
SRC="$ROOT/config/archivematica-preservation-r11.compose.yml"
DST=/opt/ordivon/external/archivematica/1.18.0/overlays/docker-compose.clamav-r6.yml
install -m 0644 "$SRC" "$DST"
cmp -s "$SRC" "$DST"
printf 'preservation-r11-materialized=PASS\n'
