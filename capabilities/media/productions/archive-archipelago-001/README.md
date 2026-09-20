# Archive Archipelago 001

A source-first cartographic/data-art portrait of an exact frozen Ordivon Creative Library snapshot: **303 Works**, **4 owner archipelagos**, and **45 catalogued relations**. The archive plane is conceptual composition, not geography, dependency, chronology, or semantic-distance truth.

## Carriers

- `render/archive-archipelago-001.gpkg` — deterministic queryable GeoPackage with Works, owners, and exact catalogued relation layers.
- `render/archive-archipelago-001.svg` — editable editorial still with sparse representative labels and relation-type legend.
- `render/archive-archipelago-001.png` — 1600×1000 inspection/delivery still.
- `interactive/index.html` + CSS/JS/data — editable web source.
- `interactive/archive-archipelago-001.html` — self-contained interactive delivery carrier.

Interactive controls include owner filtering, title/ID search, featured-only filtering, exact registered-neighbor detail, optional relation-route pulse, reduced-motion behavior, and an internally pannable mobile map. Keyboard traversal uses one map-level Tab stop plus bounded native search-result buttons; exact Work-ID search was verified to reach all 303 Works without forcing 303 visual map points into the Tab sequence. On narrow pointer surfaces, background taps use a screen-space nearest-visible-node resolver within 22 CSS px with drag suppression; this improves touch exploration without turning the 303 visual marks back into semantic controls. The pulse animates only already-catalogued routes; it does not create inferred relations.

## Build

`Creative Library snapshot → generate.py → GeoJSON + SVG + interaction data → GDAL/OGR GeoPackage + librsvg PNG → build_interactive.py standalone HTML`

`build.sh` pins `OGR_CURRENT_DATE` so source-identical GeoPackage rebuilds remain byte-stable.

## Consumption / polish

The work has been consumed through GDAL/OGR, SQLite, librsvg, ImageMagick, Runtime native image transport, the Workstation-bound Chromium/Playwright route, and the mature Artifact Web toolchain. The standalone carrier currently passes Nu Html Checker with zero messages, Chromium 153 + axe with zero violations, and Firefox 155 local launch. WebKit remains unpromoted on the unsupported local Arch path.

Board collaboration informed composition only: owner islands remain stable, dense work labels move into interaction, and optional motion is limited to real catalogued relations. Board messages are not source authority.
