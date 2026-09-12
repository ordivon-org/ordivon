# Artifact E2E — Standards-first Taxonomy R1

## Standing

`SHADOW_MODEL_NO_RUNTIME_CUTOVER`

This document starts the next Artifact E2E phase from external content/format standards rather than from the current implementation. It deliberately does **not** replace `profile-v1.schema.json` yet and does not change any production profile or Temporal workflow.

## Why the existing `artifactClass` cannot simply be expanded

The current enum mixes different classification dimensions:

- `presentation`, `document`, `spreadsheet`, `web` are operational artifact families;
- `fixed-view` is a representation property;
- `accessible` is a conformance/use purpose;
- `archive` was used as a preservation purpose/profile.

That is workable for the original bounded profiles, but it is the wrong expansion axis for images, media, datasets, geospatial data, 3D, software releases, web archives and messages. Adding more names to the same enum would preserve the category error.

The replacement model therefore separates six axes:

1. **family** — which external standards/tool/target ecosystem owns native semantics;
2. **representation** — structured markup, fixed layout, raster, vector, database, columnar, AV container, scene, executable package, capture container, etc.;
3. **format** — the concrete serialization/media type;
4. **conformance profile** — PDF/A, PDF/UA, EPUB, WCAG target, professional media profile, and so on;
5. **target authority** — the native consumer/runtime/viewer/editor required for target acceptance;
6. **purpose** — authoring, exchange, portable view, accessibility, preservation, publication, distribution, etc.

These axes are orthogonal. A PDF/UA-2 document is therefore not an `accessible` artifact family. It is a `fixed-document` whose format is PDF 2.0, whose conformance profile is PDF/UA-2, and whose purpose includes accessibility.

## External taxonomy anchors

Two outside structures are used for the first cut rather than inventing an Ordivon ontology:

- **IANA Media Types Registry / RFC 6838** supplies standardized media-type identity across `application`, `audio`, `font`, `image`, `message`, `model`, `text`, `video`, etc. This is a serialization/transport taxonomy, not a sufficient Artifact workflow taxonomy.
- **Library of Congress Recommended Formats Statement 2025–2026** supplies a practical content-oriented taxonomy covering textual works, still images, moving images, audio, musical scores, datasets, GIS/cartographic works, design/3D, software/video games, web archives and email.

Artifact routing sits between those layers: it uses practical operational families while preserving the actual native standard of each format.

## Operational families

| Family | Primary external standards/ecosystem | Current Artifact profile | Local mechanical substrate |
| --- | --- | --- | --- |
| `text-document` | OOXML/ISO 29500, ODF, EPUB 3.3 | `document-r1` | strong/partial |
| `fixed-document` | PDF 2.0, PDF/A-4, PDF/UA-2 | `pdf-fixed-r1`, `pdf-accessible-r1` | strong |
| `presentation` | PresentationML/OOXML | three PPTX profiles | strong + external PowerPoint target |
| `spreadsheet` | SpreadsheetML/OOXML, ODF | `spreadsheet-r1` | strong/partial |
| `dataset` | JSON/CSV, Parquet, Arrow, HDF/netCDF as selected | shadow `dataset-parquet-flat-r1` | DuckDB + PyArrow native schema/row matrix live-proven |
| `still-image` | PNG 3, SVG 2, JPEG/TIFF/AVIF families | shadow `still-image-png-srgb-r1` | pngcheck + ExifTool + ImageMagick/libvips matrix live-proven |
| `audio` | RFC 9639 FLAC; BWF/WAVE or other standards when selected | shadow `audio-flac-pcm16-r1` | reference FLAC + FFmpeg independent decoder matrix live-proven |
| `moving-image` | RFC 9559 Matroska; RFC 9043 FFV1; SMPTE IMF when profile-selected | shadow `moving-image-matroska-ffv1-v3-r1` | MediaConch + MediaInfo + FFprobe/FFmpeg bounded preservation profile live-proven |
| `web` | HTML Living Standard, CSS, WCAG 2.2 | `web-r1` | strong; WebKit remains supported-runner bounded |
| `geospatial` | OGC GeoPackage, GeoTIFF, GeoJSON/OGC ecosystem | shadow `geospatial-geopackage-point-r1` | OGC/GDAL validator + SQLite + OGR contract proof live-proven |
| `design-3d` | ISO/IEC 12113 glTF 2.0; STEP/IFC/3MF when selected | none | Blender present; official glTF Validator absent |
| `software-release` | OCI, SLSA, in-toto, Sigstore, SPDX/CycloneDX | no family profile yet | ORAS/OPA/Cosign + Syft/Trivy present |
| `web-archive` | ISO 28500 WARC, WACZ ecosystem | none | specialist tools absent |
| `message` | RFC 5322 + MIME | none | no dedicated Artifact profile/validator |

Specialist families such as musical notation, medical/DICOM and computational notebooks remain extension candidates. They should be admitted when a real workload requires their domain-specific authority, not preemptively folded into a universal model.

## Important standard boundaries

### Office is three operational families, not one generic document AST

ECMA-376 / ISO/IEC 29500 defines the OOXML vocabularies and package conventions, but WordprocessingML, PresentationML and SpreadsheetML have materially different target semantics. Artifact therefore keeps document, presentation and spreadsheet routing separate even though they share OPC/OpenXML mechanics.

### PDF profiles are profiles, not families

`PDF`, `PDF/A-4` and `PDF/UA-2` remain within `fixed-document`. `qpdf` can establish bounded structural facts; veraPDF can establish profile conformance facts; neither substitutes for target viewing, visual correctness or human accessibility/use acceptance.

### Web combines multiple standards and a runtime

HTML/CSS/SVG syntax/conformance, browser execution and WCAG-oriented accessibility are independent evidence surfaces. Nu Html Checker, Playwright/browser targets and axe remain separate contributors. A server health check is not an Artifact PASS.

### Images and media are native-format ecosystems

There is no reason to create an Ordivon image/video intermediate format. PNG, SVG, codec/container and professional media standards remain native. Artifact profiles select format-specific validators plus target/render/QC evidence.

### Geospatial is not just `dataset`

Coordinate reference systems, geometry validity, georeferencing, tiling and spatial metadata create separate semantics. The OGC GeoPackage standard, for example, defines schema, integrity assertions and content constraints on a SQLite container. GDAL already exposes GeoPackage validation and should be used rather than duplicating those rules.

### 3D is not an image extension

A glTF asset carries scene graph, meshes, materials, textures, skins and animation semantics. glTF 2.0 is ISO/IEC 12113:2022 and has an official Khronos validator. CAD/BIM/manufacturing formats remain separate profile-selected subdomains rather than being normalized through glTF.

### Software releases share the release substrate but add software-specific evidence

OCI/ORAS/OPA/Sigstore/in-toto already give Artifact a mature release envelope. A `software-release` profile would add native build identity, SBOM, vulnerability/policy and target install/runtime facts rather than creating another package system. Syft and Trivy are already present locally, but no production Artifact software profile exists yet.

## Mapping the current production profiles

| Current `artifactClass` | R1 interpretation |
| --- | --- |
| `document` | family=`text-document` |
| `presentation` | family=`presentation` |
| `spreadsheet` | family=`spreadsheet` |
| `web` | family=`web` |
| `fixed-view` | family=`fixed-document`, representation=`fixed-layout` |
| `accessible` | family=`fixed-document`, purpose=`accessibility`, profile=`PDF/UA-2` |
| `archive` | family=`fixed-document`, purpose=`preservation`, profile=`PDF/A-4` |

`archive` is especially important: generic archival packaging is already a different cross-cutting concern, and web capture has its own WARC family. PDF/A should not consume the word `archive` as an Artifact family.

## Coverage result

The production profile library currently covers **5 of the 14 operational families**:

- text document;
- fixed document;
- presentation;
- spreadsheet;
- web.

Nine non-production shadow families are now live-proven without extending the legacy `artifactClass` enum: **still-image**, **dataset**, **geospatial**, **audio**, **moving-image**, **software-release**, **design-3d**, **web-archive**, and **message**. The production count remains five while the standards-first model has survived raster/visual, typed tabular, and CRS/geometry/container-standard domains.

A shadow `profile-v2` schema now maps all eight current production v1 profiles plus nine standards-first shadow profiles (Still Image, Dataset, Geospatial, Audio, Moving Image, Software Release, Design/3D, Web Archive and Message) with semantic-field preservation and a green 223-test full regression. All 14 operational Artifact taxonomy families now have at least one actual profile. Message adds raw-vs-decoded representation semantics and independent parser evidence without requiring another common classification axis. Production remains on v1; v2 is not cut over.

The workstation already has useful mature mechanical tools for several uncovered families:

- still image: ImageMagick 7.1.2-29, libvips, librsvg;
- audio/video: FFmpeg/ffprobe 9.0;
- datasets: jq 1.8.2, DuckDB and the isolated PyArrow carrier;
- geospatial: GDAL 3.13.3;
- design/3D: Blender (but no official Khronos glTF Validator yet);
- software release: Syft, Trivy, Cosign, ORAS and OPA.

Therefore the dominant gap is **not a new Artifact architecture**. It is missing family-specific profiles, standards bindings and specialist validators.

## What not to change yet

Do not immediately replace `profile-v1.schema.json`. Existing production evidence and Golden acceptance are already bound to it.

Do not add the missing families to the old `artifactClass` enum. That would encode the old category mistake more deeply.

Do not introduce a universal document/media/data AST.

Do not make every tool a mandatory global dependency. Tools remain profile-selected capabilities.

## Migration sequence

1. Keep current production profiles and v1 schema authoritative.
2. Use `artifact-delivery/taxonomy-v1.json` as a shadow classification layer.
3. Build at least two uncovered, non-Office family profiles end-to-end using mature external standards/tools.
4. Observe which fields are genuinely common across those families.
5. Only then define `profile-v2` with orthogonal `family / representation / format / conformanceProfile / targetAuthority / purpose` fields.
6. Differentially map every current v1 profile into v2 and prove acceptance equivalence before retiring v1.

## Recommended next family order

The lowest-risk order is determined by existing mature local substrate, not by perceived architectural importance:

1. **software-release** — existing OCI/OPA/Sigstore/Syft/Trivy substrate makes the release waist strong, but ownership boundaries with Engineer E2E must remain explicit;
2. **design-3d** — add official Khronos glTF Validator before claiming glTF conformance;
2. **EPUB/text-document extension**, **web-archive** and **message** after their specialist validators are materialized.

This ordering deliberately tests different semantic regimes before any profile-v2 schema is frozen.
