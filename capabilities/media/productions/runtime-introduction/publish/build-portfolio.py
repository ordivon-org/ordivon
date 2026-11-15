from __future__ import annotations

import base64
import hashlib
import json
import zipfile
from pathlib import Path

from markdown_it import MarkdownIt

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
    "The article opens as formatted HTML; its Markdown source remains in the ZIP.\n"
    "All content is source-revision bound; it is not a current feature inventory.\n"
    "No claim of YouTube/Douyin/Upwork publication or audience response.\n"
).encode()


def render_article(markdown: bytes) -> bytes:
    # Markdown is the editable source; mature markdown-it owns headings,
    # emphasis, lists, and the actual timed demonstration table.
    body = MarkdownIt("commonmark", {"html": False}).enable("table").render(
        markdown.decode("utf-8")
    )
    return (
        """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<title>Ordivon Runtime | Technical Article</title>
<style>
:root{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;
background:#08121b;color:#e7f2ef}
*{box-sizing:border-box}body{margin:0}
.wrap{width:min(850px,calc(100% - 32px));margin-inline:auto}
nav{display:flex;flex-wrap:wrap;justify-content:space-between;gap:16px;
padding:23px 0;border-bottom:1px solid #284448;font-size:.9rem}
a{color:#b7f6ce;text-underline-offset:4px}
a:focus-visible{outline:3px solid #ccf99e;outline-offset:4px}
main{padding:48px 0 75px}article{font-size:1.03rem;line-height:1.75;overflow-wrap:anywhere}
h1{font-size:clamp(2.25rem,6.5vw,4rem);line-height:1.12;
letter-spacing:-.05em;margin:0 0 32px}
h2{font-size:clamp(1.35rem,4vw,1.9rem);letter-spacing:-.025em;margin:42px 0 14px}
p,li{color:#cbd8da}p{margin:15px 0}li{padding:3px 0}
strong{color:#edf7ef}ul{padding-inline-start:26px}
table{display:block;max-width:100%;overflow-x:auto;border-collapse:collapse;
margin:20px 0 28px;font-size:.9rem}
th,td{padding:11px 13px;border:1px solid #355451;text-align:left;
vertical-align:top;min-width:115px}
th{background:#1b3534;color:#edf9f2;white-space:nowrap}
tr:nth-child(even){background:#10252b}
.notice{border-left:3px solid #8ce0af;padding:12px 18px;background:#12262a;
color:#c6d7d2;font-size:.9rem;line-height:1.65;margin:32px 0}
footer{padding:24px 0 45px;border-top:1px solid #284448;
font-size:.8rem;color:#a6c1c2}
@media print{:root{background:white;color:black}
p,li{color:#333}th,td{border-color:#aaa}a{color:#145c40}}
</style></head><body>
<nav class="wrap" aria-label="Article navigation">
<a href="../index.html">Back to the edition</a>
<a href="runtime-introduction-en.md" download>Download editable Markdown</a>
</nav>
<main class="wrap"><article>
"""
        + body
        + """</article>
<aside class="notice">Historical evidence boundary: this August 2026
Runtime demonstration is an authored explanation, not live infrastructure
status, an external publication receipt, or a claim of user comprehension.</aside>
</main><footer class="wrap">Ordivon Media · source-bound article · no external assets
or scripts</footer></body></html>
"""
    ).encode("utf-8")


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
    # The two shipped HTML views link to a semantic offline article; preserve
    # their approved source files and retain the Markdown master separately.
    article_source = "article/runtime-introduction-en.md"
    article_reader = "article/runtime-introduction-en.html"
    index = entries["index.html"].decode("utf-8")
    if index.count(f'href="{article_source}"') != 1:
        raise ValueError("portfolio index has no unique article link")
    entries["index.html"] = index.replace(
        f'href="{article_source}"', f'href="{article_reader}"'
    ).encode("utf-8")
    # Source interactive HTML links to real Production-relative files.
    # Its ZIP copy instead needs the consumer package's own layout.
    interactive = entries["interactive/index.html"].decode("utf-8")
    for source_link, package_link in (
        ('href="../README.md">Back to production overview',
         'href="../index.html">Back to the edition'),
        ('href="../publish/runtime-introduction-en.md">Read the source article',
         f'href="../{article_reader}">Read the article'),
        ('href="../render/runtime-introduction-20261109-en.mp4"',
         'href="../video/runtime-introduction-en.mp4"'),
    ):
        if interactive.count(source_link) != 1:
            raise ValueError("interactive source link is missing or ambiguous")
        interactive = interactive.replace(source_link, package_link, 1)
    entries["interactive/index.html"] = interactive.encode("utf-8")
    entries[article_reader] = render_article(entries[article_source])
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
