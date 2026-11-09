#!/usr/bin/env python3
"""Deliver one offline HTML5 document from Markdown using Pandoc and native consumers.

One bounded customer outcome, not a general job engine or a substitute for Web deployment.
Verification uses the already-installed Nu Html Checker and browser/Axe providers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from artifact_verifiers.document import toolchain as document_toolchain
from artifact_verifiers.web.browser import verify_web_local
from artifact_verifiers.web.conformance import verify_html_conformance

TEMPLATE = """<!doctype html>
<html lang="$lang$">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title$</title>
</head>
<body>
<main>
$body$
</main>
</body>
</html>
"""
LANGUAGE = re.compile(r"^[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,8})*$")


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def failure(destination: Path, message: str) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "artifact-offline-html-delivery",
        "status": "FAIL",
        "destination": str(destination),
        "failures": [message],
    }


class OfflineResourceCheck(HTMLParser):
    """Only claim an offline single-file output when linked rendering assets are embedded."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.problems: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag in {"img", "script", "audio", "video", "source", "iframe"}:
            address = values.get("src")
            if address and not address.startswith("data:"):
                self.problems.append(f"nonembedded {tag} resource")
        if tag == "link" and "stylesheet" in (values.get("rel") or "").split():
            address = values.get("href")
            if address and not address.startswith("data:"):
                self.problems.append("nonembedded stylesheet")
        if tag == "a":
            address = values.get("href") or ""
            if address and not address.startswith(("#", "https://", "http://", "mailto:", "tel:")):
                self.problems.append("nonportable relative link")


def accepted_browser(result: dict[str, Any]) -> bool:
    if result.get("status") != "PASS" or result.get("digestBound") is not True:
        return False
    report = result.get("verifierOutput") or {}
    browsers = report.get("browsers") or {}
    chromium = browsers.get("chromium") or {}
    firefox = browsers.get("firefox") or {}
    return (
        chromium.get("status") == "PASS"
        and firefox.get("status") == "PASS"
        and (chromium.get("accessibility") or {}).get("status") == "PASS"
    )


def deliver(
    source: Path,
    destination: Path,
    *,
    language: str = "en",
    title: str | None = None,
    replace: bool = False,
) -> dict[str, Any]:
    """Produce, validate, independently consume, publish and read back a local HTML file."""
    source = source.resolve()
    destination = destination.absolute()
    if not source.is_file() or source.suffix.lower() not in {".md", ".markdown"}:
        return failure(destination, "source must be an existing Markdown document")
    if destination.suffix.lower() != ".html" or destination.is_symlink():
        return failure(destination, "destination must be a non-symlink .html path")
    if not LANGUAGE.fullmatch(language):
        return failure(destination, "language must be a valid explicit BCP47-style language tag")
    if title is not None and not title.strip():
        return failure(destination, "title must not be empty")
    pandoc = document_toolchain.selected_external_file(
        "ARTIFACT_PANDOC", document_toolchain.GLOBAL_PANDOC
    )
    if not pandoc.is_file():
        return failure(destination, f"Pandoc unavailable: {pandoc}")
    try:
        original = source.read_bytes()
        if not original.strip():
            return failure(destination, "source is empty")
        original_sha = hashlib.sha256(original).hexdigest()
        source_text = original.decode("utf-8")
        heading = re.search(r"^#\s+(.+?)\s*$", source_text, flags=re.MULTILINE)
        page_title = title or (heading.group(1) if heading else source.stem)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix=".artifact-html-", dir=destination.parent
        ) as temporary:
            work = Path(temporary)
            snapshot = work / "input.md"
            snapshot.write_bytes(original)
            template = work / "page.html5"
            template.write_text(TEMPLATE, encoding="utf-8")
            candidate = work / "document.html"
            command = [
                str(pandoc), str(snapshot), "--from=markdown", "--to=html5",
                "--standalone", "--embed-resources", f"--resource-path={source.parent}",
                f"--template={template}", "-M", f"lang={language}", "-M",
                f"title={page_title}", "-o", str(candidate),
            ]
            produced = subprocess.run(
                command, cwd=source.parent, capture_output=True, text=True,
                timeout=120, check=False,
            )
            if produced.returncode != 0 or not candidate.is_file():
                return failure(
                    destination, f"Pandoc failed: {produced.stderr[-1200:]}"
                )
            offline = OfflineResourceCheck()
            offline.feed(candidate.read_text(encoding="utf-8"))
            if offline.problems:
                return failure(destination, "; ".join(offline.problems))
            conformance = verify_html_conformance(candidate)
            if conformance.get("status") != "PASS":
                return failure(destination, "Nu Html Checker did not PASS")
            before = verify_web_local(candidate)
            if not accepted_browser(before):
                return failure(destination, "Chromium/Firefox or axe consumer did not PASS")
            candidate_sha = digest(candidate)
            if destination.exists():
                if digest(destination) != candidate_sha and not replace:
                    return failure(destination, "destination already exists with different bytes")
                if digest(destination) != candidate_sha:
                    os.replace(candidate, destination)
            else:
                # Atomic no-clobber publication of already-accepted candidate bytes.
                os.link(candidate, destination)
            final_sha = digest(destination)
            if final_sha != candidate_sha:
                return failure(destination, "delivered bytes differ from accepted bytes")
            # Read the actual delivery path through the real target browsers, not a request consumer ID.
            delivered_consumer = verify_web_local(destination)
            if not accepted_browser(delivered_consumer):
                return failure(destination, "target browsers rejected delivered file")
            browsers = delivered_consumer["verifierOutput"]["browsers"]
            result = {
                "schemaVersion": 1,
                "kind": "artifact-offline-html-delivery",
                "status": "DELIVERED",
                "source": {"path": str(source), "sha256": original_sha},
                "destination": str(destination),
                "artifact": {
                    "sha256": final_sha, "byteLength": destination.stat().st_size,
                    "format": "text/html; charset=utf-8",
                },
                "builder": {"name": "Pandoc", "executable": str(pandoc)},
                "acceptance": {
                    "nuHtmlChecker": "PASS",
                    "chromium": browsers["chromium"]["status"],
                    "firefox": browsers["firefox"]["status"],
                    "automatedAccessibility": browsers["chromium"]["accessibility"]["status"],
                    "actualDeliveryPathReadback": "PASS",
                    "offlineResourceReferences": "SELF_CONTAINED",
                },
                "notEvaluated": [
                    "deployed web origin and remote download",
                    "human editorial and visual judgment",
                    "WebKit (not installed on this host)",
                    "transitive tool dependency or source resource provenance",
                ],
            }
            # Store a compact receipt beside the delivered file, never a new registry.
            receipt = destination.with_suffix(".delivery.json")
            scratch_receipt = work / "receipt.json"
            scratch_receipt.write_text(
                json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            os.replace(scratch_receipt, receipt)
            return result
    except (OSError, UnicodeError, subprocess.SubprocessError, ValueError) as exc:
        return failure(destination, f"{type(exc).__name__}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--language", default="en")
    parser.add_argument("--title")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    result = deliver(
        args.source, args.destination,
        language=args.language, title=args.title, replace=args.replace,
    )
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result["status"] == "DELIVERED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
