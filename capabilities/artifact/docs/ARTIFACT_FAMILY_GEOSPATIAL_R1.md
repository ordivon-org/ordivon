# Artifact E2E — Geospatial Family R1

## Standing

`SHADOW_PROFILE_LIVE_PROVEN`

Geospatial is the third non-Office pressure test of the standards-first Artifact model. It is deliberately narrower than “GIS support”: R1 proves one OGC GeoPackage 1.4.0 container carrying exactly one 2D Point feature layer under one object contract.

## External authority structure

The selected external authority is **OGC GeoPackage Encoding Standard 1.4.0 (12-128r19)**. The registered media type is `application/geopackage+sqlite3`.

GeoPackage is not merely “SQLite with geometry”. R1 keeps four evidence layers separate:

1. **OGC GeoPackage conformance** — GDAL's dedicated GeoPackage full validator;
2. **SQLite container truth** — SQLite integrity plus GeoPackage header/version pragmas and native metadata tables;
3. **geospatial interpretation** — OGR interpretation of layer, geometry, CRS, fields and feature count;
4. **object contract** — the exact layer/schema/CRS/key requirements for this artifact instance.

A valid SQLite database is therefore not sufficient to be a GeoPackage, and a conformant GeoPackage is not sufficient to satisfy a concrete Artifact object contract.

## First bounded profile

`geospatial-geopackage-point-r1`

Classification:

```text
family             geospatial
representation     geospatial-database
format             OGC GeoPackage
media type         application/geopackage+sqlite3
conformance        OGC GeoPackage 1.4.0 bounded Point profile
purpose            interchange / analysis
```

R1 admits only:

- SQLite Format 3 GeoPackage container;
- GeoPackage `application_id = 0x47504B47` (`GPKG`);
- `user_version = 10400` for 1.4.0;
- exactly one `features` layer in `gpkg_contents`;
- exactly one 2D `POINT` geometry column (`z=0`, `m=0`);
- one explicit CRS authority/code in the object contract;
- bounded scalar attribute types;
- one logical primary key over attributes;
- optional minimum/maximum feature counts.

Tiles, attributes-only layers, line/polygon topology, raster/tile semantics and application-specific extension semantics remain outside R1.

## Object contract

Schema:

`artifact-delivery/shadow-contracts/geospatial-vector-contract-v1.schema.json`

Smoke contract:

`artifact-delivery/shadow-contracts/geospatial-geopackage-point-smoke-r1.json`

The smoke object requires:

```text
layer      places
fid        fid
geometry   geom / POINT / EPSG:4326
fields     code:integer, name:string, score:real
logical PK code
features   >= 1
```

The object contract is request-bound by digest. CRS, layer name and attribute schema are not elevated into the reusable family profile.

## Capability binding

### GDAL 3.13.3 + python-gdal 3.13.3-2

The host already contained GDAL 3.13.3, including `gdal driver gpkg validate --full-check`, but the first real validator run failed before inspecting the artifact because the command imports Python `osgeo_utils` and `python-gdal` was absent.

That failure was retained as an environment/capability-binding failure, not misclassified as GeoPackage failure.

The exact matching Arch package was then frozen without changing the host package DB:

- `/opt/ordivon/external/python-gdal/3.13.3-2/`
- package SHA-256 `105612c33b5b135b0033e700998a5ccd4eff0caedd2fa558f015fdf52855d956`;
- detached Arch signature: PASS, signer Robin Candau;
- host GDAL package: `gdal 3.13.3-2`;
- host `/usr/bin/gdal` SHA-256 `7f798db2edb837fa6949db241683599e99a21b4373048d7027011cc629648de3`.

The capability-scoped wrapper adds only the frozen `osgeo`/`osgeo_utils` package path and then invokes the exact host GDAL runtime. It does not claim the entire general-purpose `python-gdal` declared package dependency graph is required by this validator path.

### SQLite 3.53.4

Frozen signed carrier:

- `/opt/ordivon/external/sqlite/3.53.4-1/sqlite3`;
- binary SHA-256 `c1aab8828de807216a1fc64573e9e418560e9c817ad8d4501dc3d669c088d122`;
- package SHA-256 `910e7e59acc3a51c7e3468bb45c7ca20d5e987eaf2c26e4e8ad9f0624bef76d2`;
- detached Arch signature: PASS, signer Andreas Radke.

SQLite is used for container integrity and native `gpkg_*` metadata-table observations. It is not treated as an OGC or geometry-semantics validator.

### OGR 3.13.3

OGR contributes the geospatial consumer interpretation:

- `ogrinfo -json` for layer/FID/geometry/CRS/field/feature-count facts;
- `ogr2ogr` GeoJSON projection for an independent logical view of feature attributes.

Raw SQLite attributes and OGR GeoJSON properties are canonicalized by the contract primary key and compared exactly.

## Live proof

Runtime job:

`job-01a095bb-bf2d-7ea2-8a47-44c78be86d80`

Exact smoke artifact:

- SHA-256 `d8328abbdce0a15072f4cdb11e23005ce4e17911182f6e04d214308ebc4d2ddb`;
- size 106,496 bytes;
- contract canonical digest `9b46080d68508d56def6f1ea526e3cbedc161616eed0fdf4f343a1c743a64e65`.

Observed native facts:

```text
SQLite integrity      ok
application_id        1196444487 / 0x47504B47 / GPKG
user_version          10400
layer                 places / features
geometry column       geom
geometry type         POINT
z / m                 0 / 0
SRS                   EPSG:4326
feature count         3
```

GDAL full GeoPackage validation: PASS.

SQLite attribute rows and OGR GeoJSON properties independently canonicalized to the same digest:

`7f5552d3eeef5f19a7ad7b7b2a7e23ee6a15cf811b3847eaff2b7b8a992ccdca`

## Falsifiers proven

Six focused tests pass:

1. conformant GeoPackage + matching Point object contract → PASS;
2. SQLite remains internally valid after `application_id` is changed to zero, but GeoPackage conformance → FAIL;
3. GeoPackage remains fully conformant but contract changes CRS from EPSG:4326 to EPSG:3857 → Artifact FAIL;
4. contract attempts to widen the bounded profile from POINT to LINESTRING → contract/profile FAIL before evidence promotion;
5. GeoPackage remains conformant but logical key values are duplicated → Artifact FAIL;
6. contract primary key references an undeclared attribute → contract FAIL before evidence promotion.

The second falsifier establishes the key distinction:

```text
SQLiteValid != GeoPackageConformant
```

The third and fifth establish:

```text
GeoPackageConformant != ObjectContractSatisfied
```

## Geometry-validity boundary

`gdal vector check-geometry` was evaluated but is intentionally not a required R1 gate. GDAL itself reports that Point geometries are always valid/simple. Adding the check would increase ceremony without increasing information for this profile.

When LineString/Polygon/Multi* families are admitted, geometry/topology validity must become an explicit family/profile-specific evidence requirement rather than being assumed from this Point result.

## Architectural consequence

Geospatial independently confirms the same common waist found by Dataset:

```text
Family/Profile
Object Contract
Capability Binding
Evidence
```

It also proves that `targetAuthority` is not always a native application or implementation matrix: a **standard validator** is a first-class authority class. Profile v2 must therefore keep `standard-validator` alongside native-consumer and implementation-matrix authorities.
