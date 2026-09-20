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
