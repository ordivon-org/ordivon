# Ordivon Creative Library

A local, read-only browser over the historical Creative Archive.

The Library does not redefine work identity. PostgreSQL `ordivon_assets.creative_archive` remains the archive authority; a frozen JSON export is the reproducible fallback. `scripts/creative_library.py build` compiles either authority into a carrier-aware catalog, and `serve` resolves every retained carrier from its exact Git revision.

## Safety boundary

- The default server binds only to `127.0.0.1`.
- Historical HTML is served with a restrictive CSP and is embedded with an iframe sandbox.
- Raw carrier paths must already exist in the exact catalogued Git tree; path traversal is rejected.
- Current working-tree bytes are never substituted for historical carrier bytes.
- Browsability does not imply physical validation, publication approval, artistic quality, or Human value.

## Build

From the committed archive snapshot:

```bash
python3 scripts/creative_library.py build \
  --archive-json artifacts/creative-archive/historical-works-r2-source-complete.json \
  --output artifacts/creative-library/catalog-v1.json
```

From the PostgreSQL archive authority:

```bash
python3 scripts/creative_library.py build \
  --postgres \
  --pg-socket /var/lib/postgres/ordivon-data-r5-pg-14550-v4 \
  --pg-port 55434 \
  --database ordivon_assets \
  --output artifacts/creative-library/catalog-v1.json
```

## Browse

```bash
python3 scripts/creative_library.py serve \
  --catalog artifacts/creative-library/catalog-v1.json \
  --bind 127.0.0.1 \
  --port 8765
```

Then open `http://127.0.0.1:8765/`.

## Derived previews

R2 adds a separate digest-bound preview layer for historical engineering/game works whose exact source roots do not already contain a useful browser-native visual carrier. These previews are never inserted into the original `carriers` array. The catalog records them as `derivedPreview`, the server exposes them only through `/derived/<work-id>`, and the UI labels them **Derived preview**.

The current derived manifest contains six projections: four deterministic Godot frame captures, one deterministic KiCad 2D SVG plot, and one cross-work CAD preview whose source work shares the exact same combined STEP Git blob. Every preview has a provenance receipt and SHA-256 fence under `artifacts/creative-library/derived/`.

The KiCad 3D raytracer was explicitly rejected as the frozen preview path because independent runs were pixel-nondeterministic. The retained KiCad SVG export is byte-identical across repeats.
