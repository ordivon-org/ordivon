# Geospatial reference

## Bounded proven profile

`geospatial-geopackage-point-r1`

- OGC GeoPackage Encoding Standard 1.4.0 (12-128r19)
- `application/geopackage+sqlite3`
- exactly one features layer with one 2D POINT geometry column
- explicit CRS and bounded scalar attributes
- logical primary key in object contract
- Standing: `SHADOW_PROFILE_LIVE_PROVEN`

## Prior proven providers

- GDAL 3.13.3 — GeoPackage full conformance validation
- SQLite 3.53.4 — container integrity/native metadata observations
- OGR 3.13.3 — geospatial layer/geometry/CRS/field interpretation

## Boundary

Valid SQLite != conforming GeoPackage. Conforming GeoPackage != object-contract acceptance.

## Source evidence

`/root/projects/ordivon/capabilities/artifact/docs/ARTIFACT_FAMILY_GEOSPATIAL_R1.md`
