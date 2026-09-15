#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$ROOT/render"
python "$ROOT/generate.py"
rm -f "$OUT/archive-archipelago-001.gpkg" "$OUT/archive-archipelago-001.png"
export OGR_CURRENT_DATE='2026-09-15T00:00:00.000Z'
SRS='LOCAL_CS["Ordivon Archive Plane",LOCAL_DATUM["Conceptual",0],UNIT["unit",1]]'
/usr/bin/ogr2ogr -f GPKG "$OUT/archive-archipelago-001.gpkg" "$OUT/works.geojson" -nln works -a_srs "$SRS"
/usr/bin/ogr2ogr -update -append "$OUT/archive-archipelago-001.gpkg" "$OUT/owners.geojson" -nln owners -a_srs "$SRS"
/usr/bin/ogr2ogr -update -append "$OUT/archive-archipelago-001.gpkg" "$OUT/relations.geojson" -nln relations -a_srs "$SRS"
/usr/bin/rsvg-convert -w 1600 -h 1000 -o "$OUT/archive-archipelago-001.png" "$OUT/archive-archipelago-001.svg"

/usr/bin/python "$ROOT/build_interactive.py"
