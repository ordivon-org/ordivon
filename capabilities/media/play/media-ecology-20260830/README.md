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
