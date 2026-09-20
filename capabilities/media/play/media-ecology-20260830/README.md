# Media Ecology natural pilot — 2026-08-30

This directory retains the bounded natural inputs used to test the first Media Ecology engineering profile.

- `board-snapshot.json` — an explicit Host Board projection for topic `ordivon-media-ecology` at Board sequence 3319. It is a test input, not a replacement for current Host Board truth.
- `daily-cabinet.collection.json` — a generic Collection manifest reconstructed from the real Daily Cabinet source relations. It contains five members and nine exact source-object SHA-256 digests across Media, Game and Workstation.

Run from the Media repository:

```text
uv run ordivon-studio ecology project \
  --board play/media-ecology-20260830/board-snapshot.json \
  --collection play/media-ecology-20260830/daily-cabinet.collection.json
```

The resulting Thread and Feed are derived projections. The Board remains collaboration authority, and every Collection member remains owned by its declared source.

Human encounter pilot:

```text
.venv/bin/python play/media-ecology-20260830/build.py
.venv/bin/python play/media-ecology-20260830/browser-check.py
```

`build.py` deterministically generates `projection.json` and `index.html`. `browser-check.py` uses the current Workstation-managed Playwright Chromium binding at desktop and mobile viewports, rejects horizontal overflow, checks the expected activity/member counts, and retains screenshot digests rather than screenshot payloads in `browser-acceptance.json`.

Source-fence note: `board-snapshot.json` predates Host's machine-readable Board query fence. Current builds therefore retain it as `selectionMode=unknown-legacy-response` and explicitly make no completeness claim. New Host Board snapshots preserve `latest-window` versus `incremental-page` selection semantics for downstream Media recovery.

## Large projection rendering

`build.py` can render an existing ecology projection without rewriting it. Human-card limits are presentation-only chronological windows, not ranking:

```bash
python build.py --projection /path/to/project.json --html /tmp/ecology.html --activity-limit 24 --thread-limit 24
```

The generated page exposes both visible and total counts in its DOM and labels the windows `not priority`. Source-set inputs are shown as independent acquisition scopes rather than collapsed into a false single scan.
