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

## Agent-native graphics: optional derived owner-count preview (R1)

This frozen Production already has an approved map, SVG, PNG and accessible
standalone interactive view. **Do not replace them** with a generic chart or
infer semantic distance/dependency from conceptual map coordinates.

`archive_source.py` is the *production-local* validated read of the frozen
catalog for the existing map and the optional chart. It rejects duplicate
Work IDs, orphan catalog relations and relation types that this Production
cannot represent faithfully. A change to that semantics must update the map,
chart and negative consumer checks together.

The optional declarative chart is generated without JavaScript dependencies:

```bash
python3 productions/archive-archipelago-001/generate_owner_summary_vegalite.py \
  --output out/agent-graphics/archive-owner-summary.vl.json
```

The result is an editable **Vega-Lite v6** JSON source, not an approved
Production Output. It includes the actual input file SHA-256 separately from
the snapshot's declared `catalogDigest`; those digests have different meanings.
The external evaluation at
`/root/projects/ordivon-upstreams/agent-graphics-20261114-r1/`
verified an SVG and PNG through pinned Vega-Lite 6.5.0 / Vega 6.4.0,
without adding an implicit runtime dependency to Media or a new output status.

Native consumer tests:

```bash
cd capabilities/media
python3 -m unittest tests.test_archive_graphics_source_truth tests.test_archive_vegalite_spec -v
```

They cover the exact approved SVG, manifest and web data bytes; source-driven
count changes; identity and relation negative controls; and the editable chart
specification. These native checks remain necessary even if a separate formal
model later proves an abstract counting or relationship invariant.
