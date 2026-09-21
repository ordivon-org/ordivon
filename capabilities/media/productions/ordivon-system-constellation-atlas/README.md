# Ordivon System Constellation Atlas

A cartographic/data-art snapshot of locally readable Ordivon Git repositories.

The artwork treats the repository landscape as a conceptual plane: each point binds an exact repository path and observed Git HEAD, while placement is deterministic composition rather than geography or dependency inference.

## Editable source

- `generate.py` — deterministic discovery/layout/SVG generator.
- `source/repositories.json` — structured snapshot with semantic boundary.
- `source/repositories.geojson` — vector-source carrier before GeoPackage conversion.

## Rendered / delivery carriers

- `render/ordivon-system-constellation.svg` — editable vector artwork.
- `render/ordivon-system-constellation.png` — raster inspection/render carrier.
- `render/ordivon-system-constellation.gpkg` — queryable GeoPackage layer.

## Build

Run `generate.py`, convert the GeoJSON to GeoPackage through GDAL/OGR with an explicitly declared local conceptual CRS, then render the SVG with librsvg.

The GeoPackage is a creative/query carrier. It does not turn conceptual coordinates into geographic facts.

## Snapshot versus forward generator

The committed source snapshot and rendered carriers record the 2026-09-15 observation and are
historical evidence. They are not rewritten merely because repository topology later changes.

The editable generator follows the current repository-selection contract for future observations:
standalone Ordivon repositories matching `/root/projects/ordivon-*` plus the canonical
`/root/projects/ordivon` monorepo when readable. Retired `/root/workstation-lab` is not a
forward discovery input. Historical snapshot rows that bind that repository remain valid evidence
about the creation-time observation.
