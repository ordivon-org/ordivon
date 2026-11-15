from __future__ import annotations

import base64
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "publish" / "runtime-introduction-portfolio.zip"
SOURCES = {
    "index.html": "publish/portfolio-index.html",
    "video/runtime-introduction-en.mp4": "render/runtime-introduction-20261109-en.mp4",
    "video/runtime-introduction-zh-vertical.mp4": "render/runtime-introduction-20261109-zh-vertical.mp4",
    "posters/runtime-introduction.png": "render/runtime-introduction-poster.png",
    "posters/runtime-short-zh.png": "render/runtime-short-zh-poster.png",
    "captions/narration.en.vtt": "timed-text/standard/narration.en.vtt",
    "captions/narration.en.srt": "timed-text/standard/narration.en.srt",
    "article/runtime-introduction-en.md": "publish/runtime-introduction-en.md",
    "interactive/index.html": "interactive/runtime-architecture.html",
}
README = (
    "Ordivon Runtime Introduction — 2026 historical explanatory edition\n"
    "Open index.html in a browser after extracting this ZIP.\n"
    "Videos, English captions, and interactive HTML open locally via file://.\n"
    "The HTML carries the exact WebVTT data for offline Chromium and Firefox.\n"
    "Separate caption files are retained for downloads and video editors.\n"
    "All content is source-revision bound; it is not a current feature inventory.\n"
    "No claim of YouTube/Douyin/Upwork publication or audience response.\n"
).encode()


def entry(name: str, data: bytes) -> tuple[zipfile.ZipInfo, bytes]:
    info = zipfile.ZipInfo(name, date_time=(2026, 11, 9, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    return info, data


def main() -> None:
    entries = {}
    for name, relative in SOURCES.items():
        path = ROOT / relative
        entries[name] = path.read_bytes()
    # One selected WebVTT track must work from file:// in Chromium as well as
    # over HTTP, without making nontechnical readers launch a local server.
    # Keep the separate exact VTT/SRT downloads in the same ZIP.
    track_src = 'src="captions/narration.en.vtt"'
    index_html = entries["index.html"].decode("utf-8")
    if index_html.count(track_src) != 1:
        raise ValueError("portfolio template must contain exactly one English caption track")
    embedded = "data:text/vtt;base64," + base64.b64encode(
        entries["captions/narration.en.vtt"]
    ).decode("ascii")
    entries["index.html"] = index_html.replace(
        track_src, f'src="{embedded}"'
    ).encode("utf-8")
    entries["README.txt"] = README
    assets = {
        name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        for name, data in sorted(entries.items())
    }
    manifest = {
        "schemaVersion": 1,
        "kind": "ordivon.media.consumer-byte-manifest",
        "productionId": "runtime-introduction",
        "sourceBinding": "historic-runtime-5dd206c74a2b9151fb0a87579ba2200aaf892633",
        "factsBoundary": "historic source-derived explanation; not current Runtime authority",
        "humanAudienceResult": "NOT_MEASURED",
        "assets": assets,
    }
    entries["manifest.json"] = (json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(DEST, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=7) as archive:
        for name, data in sorted(entries.items()):
            info, payload = entry(name, data)
            archive.writestr(info, payload)
    with zipfile.ZipFile(DEST) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == set(entries)
        for name, metadata in assets.items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == metadata["sha256"]
    print(f"PORTFOLIO_BUILT {DEST} {DEST.stat().st_size} sha256:{hashlib.sha256(DEST.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
